import os

import numpy as np


def consolidate_data(files, output_file):
    all_states = []
    all_policies = []
    all_winners = []

    for f in files:
        if not os.path.exists(f):
            print(f"Skipping {f}, not found.")
            continue
        print(f"Loading {f}...")
        data = np.load(f)
        all_states.append(data["states"])
        all_policies.append(data["policies"])
        all_winners.append(data["winners"])

    if not all_states:
        print("No data to consolidate.")
        return

    np_states = np.concatenate(all_states, axis=0)
    np_policies = np.concatenate(all_policies, axis=0)
    np_winners = np.concatenate(all_winners, axis=0)

    np.savez_compressed(output_file, states=np_states, policies=np_policies, winners=np_winners)
    print(f"Consolidated {len(np_states)} samples to {output_file}")


if __name__ == "__main__":
    files = [
        "ai/data/data_poc_800.npz",
        "ai/data/data_batch_strat_1.npz",
        "ai/data/data_batch_0.npz",
        "ai/data/data_batch_strat_0.npz",
    ]
    consolidate_data(files, "ai/data/data_consolidated.npz")
