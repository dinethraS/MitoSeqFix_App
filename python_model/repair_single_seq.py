import sys

from python_model.reconstruct import repair_dna

# =========================
# BACKEND ENTRY POINT
# =========================

if __name__ == "__main__":

    damaged_input = sys.stdin.read().strip()

    if damaged_input:
        repaired = repair_dna(damaged_input)
        print(repaired)
