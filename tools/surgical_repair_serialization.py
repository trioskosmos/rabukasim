import os

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\launcher\src\serialization.rs"

with open(path, "rb") as f:
    raw_data = f.read()

# We know the file starts with "use serde_json" after my previous partial repair,
# or it might still have PowerShell trash.
# Let's rebuild the entire file by segments if possible, or just fix the known corrupted functions.

# The first 50 lines contain the group and unit names.
# The ability summary starts around line 75.

header = """use serde_json::{json, Value};
use engine_rust::core::models::{GameState, PlayerState, CardDatabase};
use engine_rust::core::logic::*;
use engine_rust::core::logic::{ACTION_BASE_HAND, ACTION_BASE_HAND_CHOICE, ACTION_BASE_HAND_SELECT, ACTION_BASE_STAGE, ACTION_BASE_STAGE_CHOICE, ACTION_BASE_DISCARD_ACTIVATE, ACTION_BASE_CHOICE, ACTION_BASE_MODE, ACTION_BASE_LIVESET};
use std::collections::HashMap;

pub fn get_group_name(id: u8, lang: &str) -> &'static str {
    if lang == "jp" {
        match id {
            0 => "μ's",
            1 => "Aqours",
            2 => "虹ヶ咲",
            3 => "Liella!",
            4 => "蓮ノ空",
            _ => "他"
        }
    } else {
        match id {
            0 => "μ's",
            1 => "Aqours",
            2 => "Nijigasaki",
            3 => "Liella!",
            4 => "Hasunosora",
            _ => "Other"
        }
    }
}

pub fn get_unit_name(id: u8, lang: &str) -> &'static str {
    if lang == "jp" {
        match id {
            0 => "Printemps", 1 => "lily white", 2 => "BiBi",
            3 => "CYaRon!", 4 => "AZALEA", 5 => "Guilty Kiss",
            6 => "DiverDiva", 7 => "A・ZU・NA", 8 => "QU4RTZ", 9 => "R3BIRTH",
            10 => "CatChu!", 11 => "Kaleidoscore", 12 => "5yncri5e!",
            13 => "スリーズブーケ", 14 => "DOLLCHESTRA", 15 => "みらくらぱーく",
            16 => "edel Poké",
            _ => "ユニット"
        }
    } else {
        match id {
            0 => "Printemps", 1 => "lily white", 2 => "BiBi",
            3 => "CYaRon!", 4 => "AZALEA", 5 => "Guilty Kiss",
            6 => "DiverDiva", 7 => "A・ZU・NA", 8 => "QU4RTZ", 9 => "R3BIRTH",
            10 => "CatChu!", 11 => "Kaleidoscore", 12 => "5yncri5e!",
            13 => "Cerise Bouquet", 14 => "DOLLCHESTRA", 15 => "Mira-Cra-Park",
            16 => "Edel Poke",
            _ => "Unit"
        }
    }
}
"""

# Now find where "pub fn resolve_card_name" starts to preserve the middle part.
anchor = b"pub fn resolve_card_name"
idx = raw_data.find(anchor)

if idx != -1:
    middle_segment = raw_data[idx:]
    
    # We need to fix the ability summary within the middle segment.
    # It has mojibake for triggers.
    
    jp_trigger_map = 'let t_map = ["", "登場時", "ライブ進行時", "ライブ成功時", "ターン開始時", "ターン終了時", "常時", "起動"];'
    jp_trigger_fmt = 'if !t_desc.is_empty() { format!("【{}】", t_desc) } else { "".to_string() }'

    # Convert to bytes for replacement if needed, but let's try string replacement on the decoded content.
    # Since it's mojibake, we might need regex or just find the line starts.
    
    try:
        content_str = middle_segment.decode("utf-8", errors="replace")
        
        # Repair the Trigger Map Mojibake
        import re
        content_str = re.sub(r'let t_map = \["", ".*", ".*", ".*", ".*", ".*", ".*", ".*"\];', jp_trigger_map, content_str)
        content_str = re.sub(r'if !t_desc\.is_empty\(\) \{ format!\(".*\{\}.*", t_desc\) \}', jp_trigger_fmt, content_str)
        
        # Final full file assembly
        with open(path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n")
            f.write(content_str)
            
        print("Repair complete.")
    except Exception as e:
        print(f"Repair failed: {e}")
else:
    print("Could not find middle anchor!")
