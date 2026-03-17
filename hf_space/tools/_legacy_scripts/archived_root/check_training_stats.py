import glob
import os

import torch

files = glob.glob("ai/models/alphanet_epoch_*.pt")
metric_log = []

for f in sorted(files, key=lambda x: int(os.path.basename(x).split("_")[-1].split(".")[0])):
    try:
        ckpt = torch.load(f, map_location="cpu")
        epoch = ckpt.get("epoch", -1) + 1
        val_loss = ckpt.get("val_loss", 0.0)
        metric_log.append((epoch, val_loss))
    except Exception as e:
        print(f"Error loading {f}: {e}")

print(f"{'Epoch':<10} | {'Val Loss':<10} | {'Change'}")
print("-" * 35)

last_loss = None
for epoch, loss in metric_log:
    change = ""
    if last_loss is not None:
        diff = loss - last_loss
        pct = (diff / last_loss) * 100
        change = f"{diff:+.4f} ({pct:+.1f}%)"

    print(f"{epoch:<10} | {loss:<10.4f} | {change}")
    last_loss = loss
