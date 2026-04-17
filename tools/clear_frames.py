"""Clear all frames from ability_frame_source.json to establish baseline."""

import json

input_path = "launcher/static_content/data/ability_frame_source.json"
output_path = "launcher/static_content/data/ability_frame_source.json"

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Clear all frames
for ability in data.get("abilities", []):
    ability["frames"] = []

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"Cleared frames from {len(data.get('abilities', []))} abilities")
