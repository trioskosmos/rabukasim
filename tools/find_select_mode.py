"""Find SELECT_MODE occurrences in backup frame source."""

import json

with open("launcher/static_content/data/ability_frame_source.json.backup", "r", encoding="utf-8") as f:
    backup_data = json.load(f)

select_mode_abilities = []

for ability in backup_data["abilities"]:
    for frame in ability.get("frames", []):
        if frame.get("op") == "SELECT_MODE":
            select_mode_abilities.append({
                "text": ability.get("primary_text_jp"),
                "frames": ability.get("frames", [])
            })
            break

print(f"Found {len(select_mode_abilities)} abilities with SELECT_MODE\n")

for i, ab in enumerate(select_mode_abilities[:5]):
    print(f"=== Ability {i+1} ===")
    print(f"Text: {ab['text'][:150]}...")
    print(f"Frames:")
    for j, frame in enumerate(ab['frames'][:10]):
        print(f"  Frame {j}: {frame.get('op')} value={frame.get('value')}")
    print()
