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
        # Single chunk case
        padded = torch.tensor(encoded + [4] * (window_size - len(encoded))).unsqueeze(0).to(device)
        with torch.no_grad():
            output = model(padded)
            pred = torch.argmax(output, dim=-1).squeeze().cpu().numpy()
        return decode_sequence(pred[:len(encoded)])  # Trim padding!

    # FIXED Sliding window
    repaired_chunks = []
    step_size = window_size - overlap  # 768

    for i in range(0, len(encoded), step_size):
        chunk = encoded[i:i + window_size]
        padded_chunk = chunk + [4] * (window_size - len(chunk))
        padded = torch.tensor(padded_chunk).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(padded)
            pred = torch.argmax(output, dim=-1).squeeze().cpu().numpy()
            repaired_chunk = pred[:len(chunk)]  # Original chunk length

        repaired_chunks.append(repaired_chunk)

    # FIXED RECONSTRUCTION - Full sequence!
    final_seq = repaired_chunks[0]
    for i in range(1, len(repaired_chunks)):
        # Overlap region: take from previous chunk (more stable)
        overlap_start = len(final_seq) - overlap
        overlap_end = overlap_start + overlap
        new_chunk_start = len(repaired_chunks[i]) - (len(encoded) - i)

        if not isinstance(final_seq, np.ndarray):
            final_seq = np.array(final_seq)

        chunk_part = repaired_chunks[i][overlap:]
        if isinstance(chunk_part, list):
            chunk_part = np.array(chunk_part)

        final_seq = np.concatenate([final_seq, chunk_part])

    return decode_sequence(final_seq[:len(encoded)])

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