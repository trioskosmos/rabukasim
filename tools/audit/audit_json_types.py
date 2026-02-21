import json

path = "data/cards_compiled.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)


def audit(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "bytecode" and isinstance(v, list):
                for i, elem in enumerate(v):
                    if not isinstance(elem, int):
                        print(f"BAD BYTECODE at {path}.bytecode[{i}]: {repr(elem)} ({type(elem)})")
            elif k in ["trigger", "effect_type", "condition_type", "type"]:
                # 'type' is used for both Condition and Cost in JSON
                if not isinstance(v, int):
                    # But wait, 'params' often has 'type' which IS a string.
                    # We only care about 'type' if it's a direct child of Condition/Cost.
                    # Heuristic: if it's a sibling of 'params' or 'value', it's likely a struct field.
                    if "params" in obj or "value" in obj:
                        print(f"BAD ENUM TYPE at {path}.{k}: {repr(v)} ({type(v)})")
            audit(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            audit(v, f"{path}[{i}]")


audit(data)
