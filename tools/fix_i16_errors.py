import os
import re

LOG_FILE = r"engine_rust_src/check_output_3.txt"
RS_FILE = r"engine_rust_src/src/core/logic.rs"

# Ensure paths are correct relative to workspace root if needed,
# but assuming running from workspace root or tools dir.
# Adjusting to absolute paths based on user environment just in case,
# or assuming valid CWD.
BASE_DIR = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy"
LOG_FILE = os.path.join(BASE_DIR, LOG_FILE)
RS_FILE = os.path.join(BASE_DIR, RS_FILE)

print(f"Reading log from {LOG_FILE}")
with open(LOG_FILE, "r", encoding="utf-8") as f:
    log_content = f.read()

# Extract line numbers
# Pattern: --> src\core\logic.rs:(\d+):
line_indices = []
for match in re.finditer(r"src\\core\\logic\.rs:(\d+):", log_content):
    line_indices.append(int(match.group(1)) - 1)

line_indices = sorted(list(set(line_indices)))

print(f"Found {len(line_indices)} unique lines to fix.")

with open(RS_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in line_indices:
    if idx >= len(lines):
        continue

    line = lines[idx]
    original = line
    modified = False

    # 1. Simple 'as i16' replacement
    if "as i16" in line:
        line = line.replace("as i16", "as i32")
        modified = True

    # 2. Variable specific fixes if no cast is present but needed
    # ctx.choice_index is i16 but needs to be i32 in these contexts
    if "ctx.choice_index" in line and "as i32" not in line and "as i16" not in line:
        # Avoid double casting if it was "ctx.choice_index as i16" which became "as i32" above
        # But here we target bare usage
        line = line.replace("ctx.choice_index", "ctx.choice_index as i32")
        modified = True

    if modified:
        lines[idx] = line
        print(f"Fixed line {idx + 1}:\n  Old: {original.strip()}\n  New: {line.strip()}")
    else:
        print(f"Line {idx + 1} matched but no obvious fix found: {original.strip()}")

print("Writing changes...")
with open(RS_FILE, "w", encoding="utf-8") as f:
    f.writelines(lines)
print("Done.")
