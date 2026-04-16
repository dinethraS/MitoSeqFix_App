# ============================================================
# MitoSeqFix — Inference & Deployment Pipeline
# (Chapter 9: Real-World Application / Appendix)
# ============================================================

# This script performs end-to-end inference on raw mitochondrial DNA (mtDNA)
# sequences using a trained Dual-Mode MitoSeqFix model.

# It supports:
#   • Sliding-window reconstruction of long sequences
#   • Per-base repair prediction
#   • Global damage classification
#   • Confidence estimation from gated attention layers


import sys
import json
import torch
import torch.nn as nn
import numpy as np


# ────────────────────────────────────────────────────────────
# Model Configuration (must match training exactly)
# ────────────────────────────────────────────────────────────

MAX_LEN            = 1024
EMBED_DIM          = 256
NUM_HEADS          = 8
NUM_ATTN_LAYERS    = 3
NUM_DAMAGE_CLASSES  = 4
VOCAB_SIZE         = 5

WINDOW_SIZE        = 1024
OVERLAP            = 512

CHECKPOINT_PATH    = r"D:\FYP\MitoSeqFix_App\curriculum_model\v2_stage4_consolidation_ep3.pt"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ────────────────────────────────────────────────────────────
# Biological Label Mapping (model output interpretation layer)
# ────────────────────────────────────────────────────────────

# Maps predicted class indices to biologically meaningful
# mitochondrial DNA damage categories.
DAMAGE_LABELS = {
    0: "Cytosine Deamination (C→T)",
    1: "Clustered Deletions",
    2: "Fragmentation / N-Gaps",
    3: "Low / No Damage",
    4: "Oxidative Damage (G→T / C→A)",
}


# ────────────────────────────────────────────────────────────
# Model Architecture (identical to training definition)
# ────────────────────────────────────────────────────────────

class LearnableConfidenceGate(nn.Module):
    """
    Input-dependent gating mechanism that learns whether
    each base position should be attended to or suppressed.

    This replaces fixed attention sparsity (e.g., Longformer)
    with learned, data-driven sparsity.
    """
    def __init__(self, embed_dim):
        super().__init__()
        self.gate = nn.Sequential(
            nn.Linear(embed_dim, embed_dim // 4),
            nn.ReLU(),
            nn.Linear(embed_dim // 4, 1),
            nn.Sigmoid()
        )
        self.threshold = nn.Parameter(torch.tensor(0.2))

    def forward(self, x):
        scores = self.gate(x)
        thr    = self.threshold.clamp(0.05, 0.95)
        mask   = (scores < thr).squeeze(-1)
        return scores, mask


class ConfidenceGatedAttentionLayer(nn.Module):
    """
    A single hierarchical attention layer with learnable sparsity gating.

    Each layer progressively refines:
      • Layer 1 → local damage detection
      • Layer 2 → regional structure consistency
      • Layer 3 → global sequence reliability
    """
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        self.norm      = nn.LayerNorm(embed_dim)
        self.conf_gate = LearnableConfidenceGate(embed_dim)

        self.attention = nn.MultiheadAttention(
            embed_dim, num_heads, batch_first=True
        )

        self.ff = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(embed_dim * 2, embed_dim),
        )

        self.ff_norm = nn.LayerNorm(embed_dim)

    def forward(self, x):
        normed       = self.norm(x)
        scores, mask = self.conf_gate(normed)

        # Safety constraint: ensure at least one token remains active
        all_masked   = mask.all(dim=1, keepdim=True)
        mask         = mask & ~all_masked

        attn_out, _  = self.attention(
            normed, normed, normed,
            key_padding_mask=mask
        )

        x = x + attn_out
        x = x + self.ff(self.ff_norm(x))
        return x, scores


class DualModeMitoModel(nn.Module):
    """
    Dual-task architecture:
      1. Token-level repair (base reconstruction)
      2. Sequence-level diagnosis (damage classification)

    This enables both fine-grained correction and global
    biological interpretation of mtDNA degradation.
    """
    def __init__(self, vocab_size=VOCAB_SIZE, embed_dim=EMBED_DIM,
                 num_heads=NUM_HEADS, num_attn_layers=NUM_ATTN_LAYERS,
                 num_damage_classes=NUM_DAMAGE_CLASSES):

        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embed_dim)

        # CNN captures local mutation motifs before attention
        self.cnn_backbone = nn.Sequential(
            nn.Conv1d(embed_dim, 128, kernel_size=7, padding=3, dilation=1),
            nn.GELU(),
            nn.Conv1d(128, 256, kernel_size=5, padding=4, dilation=2),
            nn.GELU(),
            nn.Conv1d(256, embed_dim, kernel_size=3, padding=4, dilation=4),
            nn.GELU(),
        )

        # Hierarchical gated attention stack
        self.gated_layers = nn.ModuleList([
            ConfidenceGatedAttentionLayer(embed_dim, num_heads)
            for _ in range(num_attn_layers)
        ])

        # Token-level reconstruction head
        self.repair_head = nn.Linear(embed_dim, vocab_size)

        # Global sequence classification head
        self.diag_head = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(embed_dim, 128),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(128, num_damage_classes)
        )

    def forward(self, x):
        x = self.embedding(x)
        x = x.permute(0, 2, 1)
        x = self.cnn_backbone(x)
        x = x.permute(0, 2, 1)

        conf_scores_all = []
        for layer in self.gated_layers:
            x, scores = layer(x)
            conf_scores_all.append(scores)

        repair_logits = self.repair_head(x)

        diag_input = x.permute(0, 2, 1)
        diag_logits = self.diag_head(diag_input)

        return repair_logits, diag_logits, conf_scores_all


# ────────────────────────────────────────────────────────────
# Model Loading Utility
# ────────────────────────────────────────────────────────────

def load_model():
    """
    Loads trained checkpoint into identical architecture.

    Ensures inference consistency with training pipeline.
    """
    model = DualModeMitoModel().to(device)
    ckpt  = torch.load(CHECKPOINT_PATH, map_location=device)

    state = ckpt.get("model_state_dict", ckpt)
    model.load_state_dict(state, strict=False)

    model.eval()
    return model


# ────────────────────────────────────────────────────────────
# Sliding Window Reconstruction (core inference method)
# ────────────────────────────────────────────────────────────

def reconstruct(model, damaged_seq):
    """
    Performs full-length reconstruction of mtDNA sequences
    using overlapping sliding windows.

    This is required because genomic sequences exceed model
    maximum context length (1024 bp).
    """

    encode_map = {"A": 0, "C": 1, "G": 2, "T": 3, "N": 4}
    base_map   = {0: "A", 1: "C", 2: "G", 3: "T", 4: "N"}

    seq = damaged_seq.upper()
    L   = len(seq)
    step = WINDOW_SIZE - OVERLAP

    all_logits = torch.zeros(L, VOCAB_SIZE)
    counts     = torch.zeros(L)

    all_gate_scores = []
    all_diag_logits = []

    with torch.no_grad():
        start = 0

        # Slide window across full genome
        while start < L:
            end   = min(start + WINDOW_SIZE, L)
            chunk = seq[start:end]

            encoded = [encode_map.get(b, 4) for b in chunk]
            encoded += [4] * (WINDOW_SIZE - len(encoded))

            x = torch.tensor(encoded).unsqueeze(0).to(device)

            rl, dl, conf_scores_all = model(x)

            # Aggregate overlapping predictions
            actual_len = end - start
            all_logits[start:end] += rl[0, :actual_len].cpu()
            counts[start:end]     += 1

            all_diag_logits.append(dl.cpu())

            # Average gate behaviour per window
            gate_mean = torch.stack(
                [s[0, :actual_len, 0] for s in conf_scores_all]
            ).mean(dim=0)

            all_gate_scores.append((start, end, gate_mean))

            if end == L:
                break
            start += step

    # ────────────────────────────────────────────────────────
    # Repair reconstruction
    # ────────────────────────────────────────────────────────

    avg_logits = all_logits / counts.unsqueeze(-1).clamp(min=1)
    probs      = torch.softmax(avg_logits, dim=-1)
    predicted  = torch.argmax(probs, dim=-1)

    repaired_seq = "".join(base_map[p.item()] for p in predicted)

    # Confidence derived from prediction certainty
    repair_confidence = float(probs.max(dim=-1).values.mean().item())

    # ────────────────────────────────────────────────────────
    # Diagnosis aggregation
    # ────────────────────────────────────────────────────────

    avg_diag   = torch.stack(all_diag_logits).mean(dim=0)
    diag_probs = torch.softmax(avg_diag, dim=-1)[0]

    damage_class = int(diag_probs.argmax())
    diag_conf    = float(diag_probs.max())

    damage_label = DAMAGE_LABELS.get(damage_class, "Unknown")

    # ────────────────────────────────────────────────────────
    # Biological sparsity estimate (from input damage)
    # ────────────────────────────────────────────────────────

    sparsity_score = seq.count("N") / L if L > 0 else 0.0

    # ────────────────────────────────────────────────────────
    # Gate-based confidence estimation (model interpretability)
    # ────────────────────────────────────────────────────────

    gate_full = torch.zeros(L, device=device)
    gate_cnt  = torch.zeros(L, device=device)

    for start, end, g in all_gate_scores:
        gate_full[start:end] += g
        gate_cnt[start:end]  += 1

    gate_avg = gate_full / gate_cnt.clamp(min=1)

    suppression_rate = float((gate_avg < 0.5).float().mean())

    # Final confidence combines gate activity + empirical scaling
    raw_conf = 1.0 - suppression_rate
    gate_conf = float(min(raw_conf, diag_conf - 0.01))
    gate_conf = max(gate_conf, 0.01)

    # ────────────────────────────────────────────────────────
    # Mutation count (edit distance approximation)
    # ────────────────────────────────────────────────────────

    changes = sum(a != b for a, b in zip(seq, repaired_seq))

    return {
        "success": True,
        "repairedSequence": repaired_seq,
        "inputLen": L,
        "outputLen": len(repaired_seq),
        "changes": changes,
        "confidence": round(gate_conf, 4),
        "damageType": damage_label,
        "sparsityScore": round(sparsity_score, 4),
        "diagConfidence": round(diag_conf, 4),
    }


# ────────────────────────────────────────────────────────────
# CLI Entry Point
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    dna = sys.stdin.read().strip()

    model = load_model()
    output = reconstruct(model, dna)

    print(json.dumps(output))