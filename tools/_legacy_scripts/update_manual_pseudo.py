import json
import os

path = "data/manual_pseudocode.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

data["LL-bp2-001-R＋"] = {
    "pseudocode": 'TRIGGER: CONSTANT\nEFFECT: REDUCE_COST(1) {PER_CARD="HAND_OTHER"}\n\nTRIGGER: CONSTANT\nEFFECT: PREVENT_BATON_TOUCH(1)\n\nTRIGGER: ON_LIVE_START\nCOST: DISCARD_HAND(X) {FILTER="You/Natsumi/Rurino"}\nEFFECT: ADD_BLADES(1) -> PLAYER {PER_CARD="DISCARDED"}'
}

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
