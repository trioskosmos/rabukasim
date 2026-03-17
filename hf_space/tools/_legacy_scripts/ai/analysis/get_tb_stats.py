import json
import os

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


def extract_tb_summary(log_dir):
    event_acc = EventAccumulator(log_dir)
    event_acc.Reload()

    tags = event_acc.Tags().get("scalars", [])
    summary = {}

    for tag in tags:
        events = event_acc.Scalars(tag)
        if events:
            # Get last 5 values for averaging
            recent_values = [e.value for e in events[-5:]]
            avg_val = sum(recent_values) / len(recent_values)
            summary[tag] = {"last": events[-1].value, "avg_recent": avg_val, "count": len(events)}
    return summary


# Targets
log_dirs = [
    r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\logs\vector_tensorboard\ProgressPPO_0120_000139_1",
    r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\logs\vector_tensorboard\ProgressPPO_0119_234440_1",
]

results = {}
for d in log_dirs:
    if os.path.exists(d):
        print(f"Analyzing {d}...")
        results[os.path.basename(d)] = extract_tb_summary(d)
    else:
        print(f"Not found: {d}")

print(json.dumps(results, indent=2))
