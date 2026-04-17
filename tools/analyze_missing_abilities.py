"""Analyze abilities that exist in backup but not in semantic extraction."""

import json

with open("launcher/static_content/data/ability_frame_source.json.backup", "r", encoding="utf-8") as f:
    backup_data = json.load(f)
backup_abilities = {ab["primary_text_jp"]: ab for ab in backup_data["abilities"]}

with open("data/abilities_extracted_from_cards.json", "r", encoding="utf-8") as f:
    semantic_data = json.load(f)
semantic_abilities = {ab["full_text"]: ab for ab in semantic_data["unique_abilities"]}

backup_only = set(backup_abilities.keys()) - set(semantic_abilities.keys())

print(f"=== ABILITIES ONLY IN BACKUP ({len(backup_only)}) ===\n")

# Group by trigger
by_trigger = {}
for text in backup_only:
    ability = backup_abilities[text]
    trigger = ability.get("trigger", "UNKNOWN")
    if trigger not in by_trigger:
        by_trigger[trigger] = []
    by_trigger[trigger].append(text)

for trigger, texts in sorted(by_trigger.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n{trigger}: {len(texts)} abilities")
    for text in texts[:3]:
        print(f"  - {text[:100]}...")
    if len(texts) > 3:
        print(f"  ... and {len(texts) - 3} more")

# Analyze frame types in backup-only abilities
print(f"\n=== FRAME TYPES IN BACKUP-ONLY ABILITIES ===\n")
frame_types = {}
for text in backup_only:
    ability = backup_abilities[text]
    for frame in ability.get("frames", []):
        op = frame.get("op", "UNKNOWN")
        frame_types[op] = frame_types.get(op, 0) + 1

for op, count in sorted(frame_types.items(), key=lambda x: x[1], reverse=True):
    print(f"{op}: {count}")
