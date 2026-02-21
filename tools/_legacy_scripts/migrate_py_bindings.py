import re

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\py_bindings.rs"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. set_live_zone_revealed
content = re.sub(
    r"fn set_live_zone_revealed\(&mut self, val: \[bool; 3\]\) \{\s*self\.inner\.live_zone_revealed = val;\s*\}",
    r"fn set_live_zone_revealed(&mut self, val: [bool; 3]) { for i in 0..3 { self.inner.set_revealed(i, val[i]); } }",
    content,
)

# 2. set_heart_buffs
content = re.sub(
    r"self\.inner\.heart_buffs\[i\]\[j\] = heart;",
    r"self.inner.heart_buffs[i].set_color_count(j, heart.max(0).min(255) as u8);",
    content,
)

# 3. set_live_card
content = re.sub(
    r"self\.inner\.players\[p_idx\]\.live_zone_revealed\[slot_idx\] = revealed;",
    r"self.inner.players[p_idx].set_revealed(slot_idx, revealed);",
    content,
)

# 4. heart_buffs getter
content = re.sub(
    r"self\.inner\.heart_buffs\.iter\(\)\.map\(\|h\| h\.to_vec\(\)\)\.collect\(\)",
    r"self.inner.heart_buffs.iter().map(|h| h.to_array().iter().map(|&x| x as i32).collect()).collect()",
    content,
)

# 5. get_effective_hearts / get_total_hearts return types in bindings
content = re.sub(
    r"fn get_effective_hearts\(&self, p_idx: usize, slot_idx: usize\) -> \[u8; 7\] \{",
    r"fn get_effective_hearts(&self, p_idx: usize, slot_idx: usize) -> [u8; 7] {",
    content,
)
content = re.sub(
    r"self\.inner\.get_effective_hearts\(p_idx, slot_idx, &self\.db\.inner\)",
    r"self.inner.get_effective_hearts(p_idx, slot_idx, &self.db.inner).to_array()",
    content,
)

content = re.sub(
    r"fn get_total_hearts\(&self, p_idx: usize\) -> \[u32; 7\] \{",
    r"fn get_total_hearts(&self, p_idx: usize) -> [u32; 7] {",
    content,
)
content = re.sub(
    r"self\.inner\.get_total_hearts\(p_idx, &self\.db\.inner\)",
    r"self.inner.get_total_hearts(p_idx, &self.db.inner).to_array().map(|x| x as u32)",
    content,
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored py_bindings.rs")
