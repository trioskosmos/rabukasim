import json
import os

path = os.path.join("data", "metadata.json")
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Change to bit 25
data["extra_constants"]["FLAG_BATON_SLOT_ONLY"] = 33554432
# Add it to bytecode_layout so it packs correctly using slot_params["is_baton_slot"] = True
data["bytecode_layout"]["S"]["standard"]["is_baton_slot"] = [25, 25]

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)
