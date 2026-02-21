import os

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\launcher\src\serialization.rs"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "use engine_rust::core::logic::*;" in line:
        new_lines.append("use engine_rust::core::logic::{ACTION_BASE_HAND, ACTION_BASE_HAND_CHOICE, ACTION_BASE_HAND_SELECT, ACTION_BASE_STAGE, ACTION_BASE_STAGE_CHOICE, ACTION_BASE_DISCARD_ACTIVATE, ACTION_BASE_CHOICE, ACTION_BASE_MODE, ACTION_BASE_LIVESET};\n")

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
