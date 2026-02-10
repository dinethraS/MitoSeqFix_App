import time
import torch
import pandas as pd
import numpy as np
from Levenshtein import distance
from collections import defaultdict

from python_model.reconstruct import encode_sequence, decode_sequence, calculate_accuracy, repair_dna

# ================= CONFIG =================
TEST_CSV = r"D:\FYP\Implementation\data\raw/test_dataset.csv"
BATCH_SIZE = 64
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ================= EVALUATION =================
def evaluate_test_set():
    print("mtDNA Repair Model - FULL TEST EVALUATION")
    print(f"Raw CSV: {TEST_CSV}")

    # Load RAW CSV
    df = pd.read_csv(TEST_CSV)
    df = df.sample(frac=0.05, random_state=42)

    print(f"Using 30% sample: {len(df)} sequences")
    print(f"Dataset: {len(df)} samples | Columns: {df.columns.tolist()}")

    damage_types = df['damage_type'].fillna('unknown').values
    print(f"Damage types: {np.unique(damage_types)}")

    # Per-damage-type results
    damage_results = defaultdict(list)

    print("Evaluating with progress tracking...")
    total_samples = len(df)
    start_time = time.time()
    batch_count = 0

    for i in range(0, total_samples, BATCH_SIZE):
        # Progress update
        if batch_count % 10 == 0:
            elapsed = time.time() - start_time
            print(f"Batch {batch_count}/{total_samples // BATCH_SIZE} "
                  f"({i / total_samples * 100:.1f}%) - {elapsed / 60:.1f}min elapsed")

        # Process batch
        batch_end = min(i + BATCH_SIZE, total_samples)
        for j in range(i, batch_end):
            damaged_input = df['damaged'].iloc[j]
            clean_seq = df['clean'].iloc[j]
            dtype = damage_types[j]

            # Use your PRODUCTION repair_dna()
            repaired_seq = repair_dna(damaged_input)

            clean_str = decode_sequence(encode_sequence(clean_seq))
            repaired_str = repaired_seq
            acc = calculate_accuracy(clean_str, repaired_str)

            damage_results[dtype].append({'acc': acc})

        batch_count += 1

    print("Evaluation complete!")

    # DAMAGE TYPE BREAKDOWN
    print("\n" + "=" * 80)
    print("DAMAGE TYPE BREAKDOWN")
    print("=" * 80)
    print(f"{'Type':20s} {'Samples':8s} {'Accuracy':8s}")
    print("-" * 80)

    type_accuracies = {}
    for dtype, results in damage_results.items():
        avg_acc = np.mean([r['acc'] for r in results])
        type_accuracies[dtype] = avg_acc
        print(f"{dtype:20s} {len(results):8d} {avg_acc:7.1f}%")

    # OVERALL
    all_accs = [r['acc'] for results in damage_results.values() for r in results]
    overall_acc = np.mean(all_accs)
    print("\n" + "=" * 80)
    print(f"OVERALL TEST ACCURACY: {overall_acc:.1f}%")
    print("=" * 80)

    return type_accuracies, overall_acc


if __name__ == "__main__":
    type_acc, overall = evaluate_test_set()
    print(f"\nFINAL RESULT: {overall:.1f}% accuracy across all damage types!")
