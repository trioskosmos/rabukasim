import re

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\core\logic.rs"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Helper for PlayerState access
# self.players[p_idx].tapped_members[idx] = val -> self.players[p_idx].set_tapped(idx, val)
content = re.sub(
    r"(\w+(?:\.players\[[^\]]+\])?)\.tapped_members\[([^\]]+)\]\s*=\s*([^;]+);", r"\1.set_tapped(\2, \3);", content
)
# self.players[p_idx].tapped_members[idx] -> self.players[p_idx].is_tapped(idx)
content = re.sub(r"(\w+(?:\.players\[[^\]]+\])?)\.tapped_members\[([^\]]+)\]", r"\1.is_tapped(\2)", content)

# moved_members_this_turn
content = re.sub(
    r"(\w+(?:\.players\[[^\]]+\])?)\.moved_members_this_turn\[([^\]]+)\]\s*=\s*([^;]+);",
    r"\1.set_moved(\2, \3);",
    content,
)
content = re.sub(r"(\w+(?:\.players\[[^\]]+\])?)\.moved_members_this_turn\[([^\]]+)\]", r"\1.is_moved(\2)", content)

# live_zone_revealed
content = re.sub(
    r"(\w+(?:\.players\[[^\]]+\])?)\.live_zone_revealed\[([^\]]+)\]\s*=\s*([^;]+);",
    r"\1.set_revealed(\2, \3);",
    content,
)
content = re.sub(r"(\w+(?:\.players\[[^\]]+\])?)\.live_zone_revealed\[([^\]]+)\]", r"\1.is_revealed(\2)", content)

# cannot_live, has_immunity, deck_refreshed_this_turn
flags_map = {
    "cannot_live": "FLAG_CANNOT_LIVE",
    "has_immunity": "FLAG_IMMUNITY",
    "deck_refreshed_this_turn": "FLAG_DECK_REFRESHED",
}
for old, flag in flags_map.items():
    # Assignment
    content = re.sub(
        r"(\w+(?:\.players\[[^\]]+\])?)\.{}\s*=\s*([^;]+);".format(old),
        r"\1.set_flag(PlayerState::{}, \2);".format(flag),
        content,
    )
    # Access
    content = re.sub(
        r"(\w+(?:\.players\[[^\]]+\])?)\.{}".format(old), r"\1.get_flag(PlayerState::{})".format(flag), content
    )

# HeartBoard indexing
# .heart_req_reductions[i] -> .heart_req_reductions.get_color_count(i)
content = re.sub(r"(\.heart_req_reductions)\[([^\]]+)\]", r"\1.get_color_count(\2)", content)
# .heart_buffs[i][j] -> .heart_buffs[i].get_color_count(j)
content = re.sub(r"(\.heart_buffs\[[^\]]+\])\[([^\]]+)\]", r"\1.get_color_count(\2)", content)

# Swap calls
# .tapped_members.swap(i, j) -> .swap_tapped(i, j)
content = re.sub(r"\.tapped_members\.swap\(([^,]+),\s*([^\)]+)\)", r".swap_tapped(\1, \2)", content)
content = re.sub(r"\.moved_members_this_turn\.swap\(([^,]+),\s*([^\)]+)\)", r".swap_moved(\1, \2)", content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored logic.rs")
