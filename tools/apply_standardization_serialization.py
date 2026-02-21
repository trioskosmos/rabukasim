import os

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\launcher\src\serialization.rs"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Mulligan/Liveset IDs
content = content.replace('let action_id = 300 + i as i32;', 'let action_id = ACTION_BASE_MODE + i as i32;')
content = content.replace('let live_set_id = 400 + i as i32;', 'let live_set_id = ACTION_BASE_LIVESET + i as i32;')

# 2. Main phase IDs
content = content.replace('let aid = 1 + (i as i32 * 3) + slot;', 'let aid = ACTION_BASE_HAND + (i as i32 * 3) + slot;')
content = content.replace('// Also check for PlayMemberWithChoice (1000 - 1999)', '// Also check for PlayMemberWithChoice (1200 - 1999)')
content = content.replace('let aid = 1000 + i as i32 * 100 + slot as i32 * 10 + choice;', 'let aid = ACTION_BASE_HAND_CHOICE + i as i32 * 100 + slot as i32 * 10 + choice;')

# 3. Mask size
content = content.replace('let mut legal_mask = vec![false; 2000];', 'let mut legal_mask = vec![false; 12000];')
content = content.replace('if aid >= 0 && aid < 2000 {', 'if aid >= 0 && aid < 12000 {')

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
