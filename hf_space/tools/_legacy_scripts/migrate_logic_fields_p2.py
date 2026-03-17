import re

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\core\logic.rs"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern for h[c] where h is a HeartBoard or similar
# Matches: h[c], req[h], etc.
# But we need to be careful not to match arrays.
# In logic.rs, HeartBoard variables are often: h, req, reductions, board, total, total_hearts, red
hb_vars = ["h", "req", "reductions", "board", "total", "total_hearts", "red", "needed_board", "pool_board", "req_board"]

for v in hb_vars:
    content = re.sub(r"\b{}\[([^\]]+)\]".format(v), r"{}.get_color_count(\1)".format(v), content)

# Fix the specific loop in encode_gamestate
# for c in 0..7 { p0_stage_hearts[c] += h.get_color_count(c) as u32; }
# This is actually fine now if h is HeartBoard.

# Also fix cases where we set color count
# req[h] = (...) -> req.set_color_count(h, ...)
content = re.sub(r"\b(req|red|total|board)\[([^\]]+)\]\s*=\s*([^;]+);", r"\1.set_color_count(\2, \3);", content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored logic.rs (pass 2)")
