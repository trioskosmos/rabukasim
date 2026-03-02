import collections
import json

with open("data/manual_translations_en.json", "r", encoding="utf-8") as f:
    data = json.load(f, object_pairs_hook=collections.OrderedDict)
new_data = collections.OrderedDict()
for k, v in data.items():
    new_v = v.replace("weight state", "wait state")
    new_data[k] = new_v
with open("data/manual_translations_en.json", "w", encoding="utf-8") as f:
    json.dump(new_data, f, indent=4, ensure_ascii=False)
print("Fix applied.")
