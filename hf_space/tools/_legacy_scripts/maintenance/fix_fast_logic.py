import os

filepath = "engine/game/fast_logic.py"
if not os.path.exists(filepath):
    filepath = "c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine/game/fast_logic.py"

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip_until = -1
for i, line in enumerate(lines):
    if i <= skip_until:
        continue

    # 1. Play Block Fix
    if "f_ctx_batch[i, 7] = 1" in line and i > 1300 and i < 1340:
        new_lines.append("                             f_ctx_batch[i, 7] = 1\n")
        new_lines.append("                             f_ctx_batch[i, SID] = card_id\n")
        # Skip the next few messy lines until p_cp_slice
        for j in range(i + 1, i + 10):
            if "p_cp_slice = p_cp[i:i+1]" in lines[j]:
                skip_until = j - 1
                break
        continue

    # 2. Activation Block Fix
    if "f_ctx_batch[i, 7] = 1" in line and i >= 1340 and i < 1360:
        new_lines.append("                      f_ctx_batch[i, 7] = 1\n")
        new_lines.append("                      f_ctx_batch[i, SID] = card_id\n")
        continue

    new_lines.append(line)

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Successfully fixed fast_logic.py whitespace and SID tracking.")
