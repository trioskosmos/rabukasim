import os

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\launcher\src\serialization.rs"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Cleanup PowerShell trash and duplicates
    if "use engine_rust::core::logic::*" in line:
        if "use engine_rust::core::logic::{ACTION_BASE_HAND" in line:
             continue # skip the double/corrupted line
        
        # Add a clean pair of imports
        new_lines.append("use engine_rust::core::logic::*;\n")
        new_lines.append("use engine_rust::core::logic::{ACTION_BASE_HAND, ACTION_BASE_HAND_CHOICE, ACTION_BASE_HAND_SELECT, ACTION_BASE_STAGE, ACTION_BASE_STAGE_CHOICE, ACTION_BASE_DISCARD_ACTIVATE, ACTION_BASE_CHOICE, ACTION_BASE_MODE, ACTION_BASE_LIVESET};\n")
    elif "use engine_rust::core::logic::{ACTION_BASE_HAND" in line:
        continue # skip
    else:
        new_lines.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
