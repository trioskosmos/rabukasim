"""Compare abilities in backup frame source, semantic, and converted semantic."""

import json

# Load backup frame source
with open("launcher/static_content/data/ability_frame_source.json.backup", "r", encoding="utf-8") as f:
    backup_data = json.load(f)
backup_abilities = {ab["primary_text_jp"]: ab for ab in backup_data["abilities"]}

# Load semantic
with open("data/abilities_extracted_from_cards.json", "r", encoding="utf-8") as f:
    semantic_data = json.load(f)
semantic_abilities = {ab["full_text"]: ab for ab in semantic_data["unique_abilities"]}

# Load converted
with open("data/ability_frame_source.json", "r", encoding="utf-8") as f:
    converted_data = json.load(f)
converted_abilities = {ab["primary_text_jp"]: ab for ab in converted_data["abilities"]}

print(f"Backup abilities: {len(backup_abilities)}")
print(f"Semantic abilities: {len(semantic_abilities)}")
print(f"Converted abilities: {len(converted_abilities)}")

# Find matching abilities
common_texts = set(backup_abilities.keys()) & set(semantic_abilities.keys()) & set(converted_abilities.keys())
print(f"\nCommon abilities across all 3: {len(common_texts)}")

# Compare frame counts for common abilities
print("\n=== FRAME COUNT COMPARISON ===")
frame_count_diffs = []
for text in common_texts:
    backup_frames = len(backup_abilities[text].get("frames", []))
    converted_frames = len(converted_abilities[text].get("frames", []))
    if backup_frames != converted_frames:
        frame_count_diffs.append((text, backup_frames, converted_frames))

print(f"Abilities with different frame counts: {len(frame_count_diffs)}")
for text, backup_count, converted_count in sorted(frame_count_diffs, key=lambda x: x[1] - x[2], reverse=True)[:20]:
    print(f"Backup: {backup_count} | Converted: {converted_count} | {text[:80]}...")

# Analyze specific ability that might have improved
print("\n=== DETAILED COMPARISON FOR FIRST MATCHING ABILITY ===")
if common_texts:
    sample_text = list(common_texts)[0]
    print(f"\nText: {sample_text}")
    
    print("\n--- BACKUP FRAMES ---")
    for i, frame in enumerate(backup_abilities[sample_text].get("frames", [])[:5]):
        print(f"Frame {i}: {frame.get('op')} value={frame.get('value')}")
    
    print("\n--- CONVERTED FRAMES ---")
    for i, frame in enumerate(converted_abilities[sample_text].get("frames", [])[:5]):
        print(f"Frame {i}: {frame.get('op')} value={frame.get('value')}")
    
    print("\n--- SEMANTIC ACTIONS ---")
    for i, action in enumerate(semantic_abilities[sample_text].get("effect", {}).get("actions", [])[:5]):
        print(f"Action {i}: {action.get('action')} count={action.get('count')}")

# Find abilities that exist in backup but not in semantic
backup_only = set(backup_abilities.keys()) - set(semantic_abilities.keys())
print(f"\n\n=== ABILITIES ONLY IN BACKUP: {len(backup_only)} ===")
for text in list(backup_only)[:10]:
    print(f"- {text[:80]}...")

# Find abilities that exist in semantic but not in backup
semantic_only = set(semantic_abilities.keys()) - set(backup_abilities.keys())
print(f"\n=== ABILITIES ONLY IN SEMANTIC: {len(semantic_only)} ===")
for text in list(semantic_only)[:10]:
    print(f"- {text[:80]}...")
