import os

filepath = "engine/game/fast_logic.py"
if not os.path.exists(filepath):
    filepath = "c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine/game/fast_logic.py"

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip_until = -1


# Helper to remove leading spaces and re-indent
def reindent(line, depth):
    return " " * depth + line.strip() + "\n"


for i, line in enumerate(lines):
    if i <= skip_until:
        continue

    # Standardize play block
    if i == 1322 and "if card_id < b_idx.shape[0]:" in line:
        new_lines.append(reindent("if card_id < b_idx.shape[0]:", 22))
        new_lines.append(reindent("map_idx = b_idx[card_id, 0]", 26))
        new_lines.append(reindent("if map_idx >= 0:", 26))
        new_lines.append(reindent("code_seq = b_map[map_idx]", 30))
        new_lines.append(reindent("f_ctx_batch[i, 7] = 1", 30))
        new_lines.append(reindent("f_ctx_batch[i, SID] = card_id", 30))
        new_lines.append(reindent("p_cp_slice = p_cp[i:i+1]", 30))
        new_lines.append(reindent("out_bonus_slice = batch_delta_bonus[i:i+1]", 30))
        new_lines.append(reindent("out_bonus_slice[0] = 0", 30))
        new_lines.append(
            reindent(
                "resolve_bytecode(code_seq, f_ctx_batch[i], g_ctx_batch[i], pid, p_h[i], p_d[i], p_stg[i], p_ev[i], p_ec[i], p_cv[i], p_cp_slice, p_tap[i], p_lr[i], o_tap[i], p_tr[i], b_map, b_idx, out_bonus_slice, card_stats, o_tap[i])",
                30,
            )
        )
        new_lines.append(reindent("p_sb[i] += out_bonus_slice[0]", 30))
        new_lines.append(reindent("f_ctx_batch[i, 7] = 0", 30))
        skip_until = 1334
        continue

    # Standardize activation block
    if i == 1342 and "if map_idx >= 0:" in line:
        new_lines.append(reindent("if map_idx >= 0:", 18))
        new_lines.append(reindent("code_seq = b_map[map_idx]", 22))
        new_lines.append(reindent("f_ctx_batch[i, 7] = 1", 22))
        new_lines.append(reindent("f_ctx_batch[i, SID] = card_id", 22))
        new_lines.append(reindent("p_cp_slice = p_cp[i:i+1]", 22))
        new_lines.append(reindent("out_bonus_slice = batch_delta_bonus[i:i+1]", 22))
        new_lines.append(reindent("out_bonus_slice[0] = 0", 22))
        new_lines.append(
            reindent(
                "resolve_bytecode(code_seq, f_ctx_batch[i], g_ctx_batch[i], pid, p_h[i], p_d[i], p_stg[i], p_ev[i], p_ec[i], p_cv[i], p_cp_slice, p_tap[i], p_lr[i], o_tap[i], p_tr[i], b_map, b_idx, out_bonus_slice, card_stats, o_tap[i])",
                22,
            )
        )
        new_lines.append(reindent("p_sb[i] += out_bonus_slice[0]", 22))
        new_lines.append(reindent("f_ctx_batch[i, 7] = 0", 22))
        skip_until = 1350
        continue

    new_lines.append(line)

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
