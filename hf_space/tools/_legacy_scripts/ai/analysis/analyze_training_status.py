import datetime
import glob
import json
import os
import zipfile

# Try to import EventAccumulator
try:
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    HAS_TB = True
except ImportError:
    HAS_TB = False
    print("TensorBoard python package not found/importable. Will skip detailed log analysis.")


def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def get_latest_dir(pattern):
    dirs = glob.glob(pattern)
    dirs = [d for d in dirs if os.path.isdir(d)]
    if not dirs:
        return None
    return max(dirs, key=os.path.getmtime)


def main():
    report_lines = []

    def log(msg):
        print(msg)
        report_lines.append(msg)

    base_dir = os.getcwd()  # Run from root
    log(f"Running analysis from: {base_dir}")

    # --- Checkpoint Analysis ---
    checkpoint_pattern = os.path.join(base_dir, "checkpoints", "vector", "*.zip")
    log(f"\nLooking for checkpoints in: {checkpoint_pattern}")
    latest_checkpoint = get_latest_file(checkpoint_pattern)

    if latest_checkpoint:
        log("\n[Latest Checkpoint]")
        log(f"Path: {latest_checkpoint}")
        try:
            size_mb = os.path.getsize(latest_checkpoint) / (1024 * 1024)
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(latest_checkpoint))
            log(f"Size: {size_mb:.2f} MB")
            log(f"Modified: {mod_time}")

            with zipfile.ZipFile(latest_checkpoint, "r") as z:
                files_in_zip = len(z.namelist())
                log(f"Files in zip: {files_in_zip}")

                if "data" in z.namelist():
                    with z.open("data") as f:
                        try:
                            content = f.read().decode("utf-8")
                            data = json.loads(content)
                            log(f"Steps Trained: {data.get('num_timesteps', 'Unknown')}")
                            log(f"Obs Space: {data.get('observation_space', 'Unknown')}")
                            log(f"Action Space: {data.get('action_space', 'Unknown')}")

                            # Check for other interesting metadata if available
                            if "learning_rate" in data:
                                log(f"Learning Rate: {data['learning_rate']}")
                            if "n_steps" in data:
                                log(f"N Steps: {data['n_steps']}")
                            if "batch_size" in data:
                                log(f"Batch Size: {data['batch_size']}")

                        except Exception as e:
                            log(f"Error parsing metadata: {e}")
        except Exception as e:
            log(f"Error inspecting checkpoint: {e}")
    else:
        log("No checkpoints found.")

    # --- TensorBoard Analysis ---
    log_pattern = os.path.join(base_dir, "logs", "vector_tensorboard", "*")
    log(f"\nLooking for logs in: {log_pattern}")
    latest_log = get_latest_dir(log_pattern)

    if latest_log:
        log("\n[Latest TensorBoard Log]")
        log(f"Dir: {latest_log}")

        event_files = glob.glob(os.path.join(latest_log, "events.out.tfevents*"))
        if event_files:
            event_file = event_files[0]
            log(f"Event File: {os.path.basename(event_file)}")

            if HAS_TB:
                try:
                    log("Loading TensorBoard events (this may take 10-20s)...")
                    # Load only scalars to speed it up
                    ea = EventAccumulator(
                        event_file,
                        size_guidance={
                            "compressedHistograms": 0,
                            "images": 0,
                            "audio": 0,
                            "scalars": 1000,
                            "histograms": 0,
                        },
                    )
                    ea.Reload()

                    tags = ea.Tags().get("scalars", [])
                    log(f"Found {len(tags)} scalar metrics.")

                    interesting_keys = [
                        "rollout/ep_rew_mean",
                        "rollout/ep_len_mean",
                        "train/loss",
                        "train/entropy_loss",
                        "train/value_loss",
                        "train/learning_rate",
                        "train/approx_kl",
                        "train/clip_fraction",
                        "time/fps",
                    ]

                    for key in interesting_keys:
                        if key in tags:
                            events = ea.Scalars(key)
                            if events:
                                last_event = events[-1]
                                log(f"  {key:<25}: {last_event.value:.4f} (step {last_event.step})")
                        else:
                            # Try partial match
                            matches = [t for t in tags if key in t]
                            if matches:
                                for m in matches:
                                    events = ea.Scalars(m)
                                    if events:
                                        last_event = events[-1]
                                        log(f"  {m:<25}: {last_event.value:.4f} (step {last_event.step})")
                except Exception as e:
                    log(f"Error reading TensorBoard: {e}")
            else:
                log("TensorBoard library not installed, skipping log detailed analysis.")
        else:
            log("No event files found in log dir.")
    else:
        log("No TensorBoard logs found.")

    # Write report
    report_path = os.path.join(base_dir, "analysis_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\nReport written to: {report_path}")


if __name__ == "__main__":
    main()
