path = r"c:\Users\trios\/.gemini\antigravity\vscode\loveca-copy\engine\game\fast_logic.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Line 1328 is index 1327
# 1324:                          if map_idx >= 0:
# 1325:                              code_seq = b_map[map_idx]
# 1326:                              f_ctx_batch[i, 7] = 1
# 1327:                              f_ctx_batch[i, SID] = card_id
# 1328:                                    p_cp_slice = p_cp[i:i+1]
# 1329:                              out_bonus_slice = batch_delta_bonus[i:i+1]

target_line = lines[1327]
print(f"Old line: {repr(target_line)}")
if "p_cp_slice = p_cp[i:i+1]" in target_line:
    # Match indentation of previous line
    prev_line = lines[1326]
    indent = prev_line[: len(prev_line) - len(prev_line.lstrip())]
    lines[1327] = indent + "p_cp_slice = p_cp[i:i+1]\n"
    print(f"New line: {repr(lines[1327])}")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Fix applied.")
else:
    print("Target line not found at expected index.")
