import numpy as np


def debug_data(file_path):
    data = np.load(file_path)
    states = data["states"]
    policies = data["policies"]
    winners = data["winners"]

    print(f"File: {file_path}")
    print(f"Stats - States: min={np.min(states)}, max={np.max(states)}, has_nan={np.isnan(states).any()}")
    print(f"Stats - Policies: min={np.min(policies)}, max={np.max(policies)}, has_nan={np.isnan(policies).any()}")
    print(f"Stats - Winners: min={np.min(winners)}, max={np.max(winners)}, has_nan={np.isnan(winners).any()}")

    # Check policy sums
    p_sums = np.sum(policies, axis=1)
    print(f"Policy sums: min={np.min(p_sums)}, max={np.max(p_sums)}")

    # Check for negative policies
    if (policies < 0).any():
        print(f"WARNING: Found {np.sum(policies < 0)} negative policy entries!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="ai/data/data_consolidated.npz")
    args = parser.parse_args()
    debug_data(args.file)
