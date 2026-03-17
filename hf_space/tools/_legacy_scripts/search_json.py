import json
import os

path = "data/cards_compiled.json"
if not os.path.exists(path):
    print("File not found")
    exit(1)

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)


def find_paths(obj, target, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            find_paths(v, target, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_paths(v, target, f"{path}[{i}]")
    elif obj == target:
        print(f"FOUND at {path}")


find_paths(data, "YELL_REVEALED")
