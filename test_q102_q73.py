import sys
import json
from pprint import pprint

with open("data/qa_data.json") as f:
    data = json.load(f)

for item in data:
    if item["id"] in ["Q102", "Q73"]:
        pprint(item)
