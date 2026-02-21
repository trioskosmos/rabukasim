import glob
import os

import numpy as np
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


def inspect_latest_log():
    log_dir = "./logs/vector_tensorboard/"
    # Find latest run
    all_runs = sorted(glob.glob(os.path.join(log_dir, "ProgressPPO_*")), key=os.path.getmtime, reverse=True)
    if not all_runs:
        # Fallback to any log
        all_runs = sorted(glob.glob(os.path.join(log_dir, "*")), key=os.path.getmtime, reverse=True)
        if not all_runs:
            print("No logs found.")
            return

    latest_run = all_runs[0]
    print(f"Inspecting run: {latest_run}")

    # Find event file
    event_files = glob.glob(os.path.join(latest_run, "events.out.tfevents.*"))
    if not event_files:
        print("No event file found in run dir.")
        return

    event_file = event_files[0]

    ea = EventAccumulator(event_file)
    ea.Reload()

    # List available tags
    tags = ea.Tags()["scalars"]
    print(f"Available Tags: {tags}")

    # Inspect Loss
    if "train/loss" in tags:
        events = ea.Scalars("train/loss")
        values = [e.value for e in events]
        print("\n--- Loss Analysis ---")
        print(f"Count: {len(values)}")
        print(f"Last 10 values: {values[-10:]}")
        diffs = np.diff(values)
        sign_changes = np.sum(np.diff(np.sign(diffs)) != 0)
        print(f"Sign Changes (Oscillations): {sign_changes} / {len(values)}")
        print(f"Mean: {np.mean(values):.4f}, Std: {np.std(values):.4f}")

    if "train/approx_kl" in tags:
        events = ea.Scalars("train/approx_kl")
        values = [e.value for e in events]
        print("\n--- Approx KL Analysis ---")
        print(f"Max: {np.max(values):.4f}, Mean: {np.mean(values):.4f}")

    if "train/entropy_loss" in tags:
        events = ea.Scalars("train/entropy_loss")
        values = [e.value for e in events]
        print("\n--- Entropy Analysis ---")
        if values:
            print(f"Start: {values[0]:.4f}, End: {values[-1]:.4f}")
            print(f"Trend: {'Decreasing' if values[-1] < values[0] else 'Increasing/Stable'}")


if __name__ == "__main__":
    inspect_latest_log()
