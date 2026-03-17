import re

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\core\hardcoded.rs"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. heart_buffs[slot][color] += val
# Matches: state.players[p_idx].heart_buffs[1 as usize][0] += 2;
content = re.sub(
    r"state\.players\[p_idx\]\.heart_buffs\[(\d+)\s+as\s+usize\]\[(\d+)\]\s+([+-]=)\s+(\d+);",
    r"state.players[p_idx].heart_buffs[\1 as usize].add_to_color(\2, \4);",
    content,
)

# 2. heart_req_reductions[color] += val
content = re.sub(
    r"state\.players\[p_idx\]\.heart_req_reductions\[(\d+)\]\s+([+-]=)\s+(\d+);",
    r"state.players[p_idx].heart_req_reductions.add_to_color(\1, \3);",
    content,
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored hardcoded.rs")
