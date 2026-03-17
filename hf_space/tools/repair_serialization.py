path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\launcher\src\serialization.rs"

with open(path, "rb") as f:
    raw_data = f.read()

# Since the file might be a mix of encodings now, let's just find the start of a known good line
# and replace everything before it with a clean header.
# "pub fn get_group_name" is a good anchor.

trigger = b"pub fn get_group_name"
idx = raw_data.find(trigger)

if idx != -1:
    header = """use serde_json::{json, Value};
use engine_rust::core::models::{GameState, PlayerState, CardDatabase};
use engine_rust::core::logic::*;
use engine_rust::core::logic::{ACTION_BASE_HAND, ACTION_BASE_HAND_CHOICE, ACTION_BASE_HAND_SELECT, ACTION_BASE_STAGE, ACTION_BASE_STAGE_CHOICE, ACTION_BASE_DISCARD_ACTIVATE, ACTION_BASE_CHOICE, ACTION_BASE_MODE, ACTION_BASE_LIVESET};
use std::collections::HashMap;

"""
    new_data = header.encode("utf-8") + raw_data[idx:]
    with open(path, "wb") as f:
        f.write(new_data)
else:
    print("Could not find anchor!")
