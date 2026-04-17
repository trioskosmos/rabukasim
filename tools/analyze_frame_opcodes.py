"""Analyze all frame opcodes in ability_frame_source.json.backup."""

import json
from collections import Counter

with open("launcher/static_content/data/ability_frame_source.json.backup", "r", encoding="utf-8") as f:
    data = json.load(f)

opcode_counter = Counter()

for ability in data["abilities"]:
    for frame in ability.get("frames", []):
        op = frame.get("op", "unknown")
        opcode_counter[op] += 1

print("=== FRAME OPCODES ===")
for opcode, count in opcode_counter.most_common():
    print(f"{opcode}: {count}")
