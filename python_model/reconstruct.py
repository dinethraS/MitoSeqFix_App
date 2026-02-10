import numpy as np
import torch

from python_model.model_architecture import DNARepairAutoencoder

# =========================
# CONFIG
# =========================
MODEL_PATH = r"D:\FYP\MitoSeqFix_App\python_model\best_model_transformer.pt"
VOCAB_SIZE = 5
EMBEDDING_DIM = 128
MAX_LEN = 1024
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =========================
# LOAD MODEL
# =========================

model = None

def load_model():
    global model

    model = DNARepairAutoencoder(
        vocab_size=VOCAB_SIZE,
        embedding_dim=EMBEDDING_DIM
    ).to(device)

    checkpoint = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])

    model.eval()
    return model


def repair_dna(damaged_seq, window_size=1024, overlap=256):
    if model is None:
        load_model()

    encoded = encode_sequence(damaged_seq)

    if len(encoded) <= window_size:
        padded = torch.tensor(encoded + [4] * (window_size - len(encoded))).unsqueeze(0).to(device)
        with torch.no_grad():
            output = model(padded)
            pred = torch.argmax(output, dim=-1).squeeze().cpu().numpy()
        return decode_sequence(pred)

    # Sliding window - PURE model predictions
    repaired_chunks = []
    for i in range(0, len(encoded), window_size - overlap):
        chunk = encoded[i:i + window_size]
        padded = torch.tensor(chunk + [4] * (window_size - len(chunk))).unsqueeze(0).to(device)
        with torch.no_grad():
            output = model(padded)
            pred = torch.argmax(output, dim=-1).squeeze().cpu().numpy()[:len(chunk)]
        repaired_chunks.append(pred)

    # Reconstruct
    final_seq = repaired_chunks[0].tolist()
    for chunk in repaired_chunks[1:]:
        final_seq.extend(chunk[window_size - overlap:].tolist())

    return decode_sequence(final_seq)

def has_damage(seq):
    seq_lower = seq.lower()
    damage_signals = ['c', 'n']  # lowercase + N bases
    return any(signal in seq_lower for signal in damage_signals)

# ================= ENCODING HELPER =================
def encode_sequence(seq):
    """Convert ACGTN string → [0,1,2,3,4] integers"""
    mapping = {'A':0, 'C':1, 'G':2, 'T':3, 'N':4}
    return [mapping.get(base.upper(), 4) for base in seq]

# ================= HELPERS =================
def decode_sequence(encoded):
    mapping = {0: 'A', 1: 'C', 2: 'G', 3: 'T', 4: 'N'}
    return ''.join(mapping[i] for i in encoded)


def calculate_accuracy(clean, repaired):
    min_len = min(len(clean), len(repaired))
    return np.mean([c == r for c, r in zip(clean[:min_len], repaired[:min_len])]) * 100