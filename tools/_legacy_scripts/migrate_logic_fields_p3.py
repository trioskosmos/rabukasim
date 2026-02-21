import re

logic_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\core\logic.rs"
bind_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\py_bindings.rs"

# --- logic.rs ---
with open(logic_path, "r", encoding="utf-8") as f:
    logic = f.read()

# 1. totals.iter().sum()
logic = logic.replace("totals.iter().sum()", "totals.to_array().iter().map(|&x| x as u32).sum()")

# 2. += on get_color_count
logic = re.sub(
    r"(\w+(?:\.players\[[^\]]+\])?\.heart_buffs\[[^\]]+\])\.get_color_count\(([^)]+)\)\s*\+=\s*([^;]+);",
    r"\1.add_to_color(\2, \3);",
    logic,
)

# 3. hearts (iterator)
logic = re.sub(r"for\s+(h|&h)\s+in\s+hearts\b", r"for \1 in hearts.to_array()", logic)

# 4. heart_req_reductions setters
logic = re.sub(
    r"(heart_req_reductions)\.set_color_count\(([^,]+),\s*\1\.get_color_count\(\2\)\s*\+\s*([^)]+)\)",
    r"\1.add_to_color(\2, \3)",
    logic,
)

# 5. Suitability checks with HeartBoard
# check_hearts_suitability(..., &req) where req is [u8; 7]
# But now req might be HeartBoard in some places?
# In check_live_success: req = live.required_hearts; (array)
# Change line 3406 manually or via regex:
logic = re.sub(
    r"req\.get_color_count\(i\)\s*=\s*(.+);",
    r"val = \1; req[i] = val;",  # This is risky, I'll do it manually.
    logic,
)

with open(logic_path, "w", encoding="utf-8") as f:
    f.write(logic)

# --- py_bindings.rs ---
with open(bind_path, "r", encoding="utf-8") as f:
    bind = f.read()

# tapped_members = val -> for i in 0..3 { .set_tapped(i, val[i]) }
bind = re.sub(
    r"fn set_tapped_members\(&mut self,\s*val:\s*\[bool;\s*3\]\)\s*\{\s*self\.inner\.tapped_members\s*=\s*val;\s*\}",
    r"fn set_tapped_members(&mut self, val: [bool; 3]) { for i in 0..3 { self.inner.set_tapped(i, val[i]); } }",
    bind,
)

bind = re.sub(
    r"fn set_moved_members_this_turn\(&mut self,\s*val:\s*\[bool;\s*3\]\)\s*\{\s*self\.inner\.moved_members_this_turn\s*=\s*val;\s*\}",
    r"fn set_moved_members_this_turn(&mut self, val: [bool; 3]) { for i in 0..3 { self.inner.set_moved(i, val[i]); } }",
    bind,
)

with open(bind_path, "w", encoding="utf-8") as f:
    f.write(bind)

print("Refactored logic.rs and py_bindings.rs (pass 3)")
