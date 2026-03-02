import os
import sys

fn = "engine_rust_src/final_final_check.log"
if not os.path.exists(fn):
    print("Log not found")
    sys.exit(0)

with open(fn, "rb") as f:
    data = f.read()

if b"\xff\xfe" in data:
    text = data.decode("utf-16le", errors="ignore")
else:
    text = data.decode("utf-8", errors="ignore")

lines = text.splitlines()
for i, line in enumerate(lines):
    if "error:" in line or "error[" in line:
        print("\n".join(lines[max(0, i - 2) : i + 10]))
        print("-" * 50)
