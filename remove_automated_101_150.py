import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Removing automated frame_verification for abilities 101-150...")

# Remove frame_verification from abilities 101-150
for i in range(101, 151):
    if 'frame_verification' in data['abilities'][i]:
        del data['abilities'][i]['frame_verification']
        print(f"Removed frame_verification from ability {i}")

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Removed automated frame_verification for abilities 101-150")
print("Saved file")
