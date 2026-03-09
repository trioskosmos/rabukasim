import sys
import json
from pprint import pprint

with open("data/cards_compiled.json") as f:
    data = json.load(f)

for category in data.values():
    if "4340" in category:
        pprint(category["4340"])
