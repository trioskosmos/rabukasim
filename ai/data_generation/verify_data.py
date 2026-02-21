import argparse
import os

import numpy as np


def verify(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    data = np.load(file_path)
    print(f"File: {file_path}")
    print(f"Keys: {list(data.keys())}")
    print(f"States shape: {data['states'].shape}")
    print(f"Policies shape: {data['policies'].shape}")
    print(f"Winners shape: {data['winners'].shape}")

    unique_winners = np.unique(data["winners"])
    print(f"Unique winners: {unique_winners}")
    if len(data["winners"]) > 0:
        print(f"Winner mean: {np.mean(data['winners'])}")
        print(f"Draw percentage: {np.mean(data['winners'] == 0) * 100:.1f}%")

    # Check sum of policy
    print(f"Sum of policy 0: {np.sum(data['policies'][0])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="ai/data/data_poc_800.npz")
    args = parser.parse_args()
    verify(args.file)
