import json


def find_value(data, path=""):
    if isinstance(data, dict):
        for k, v in data.items():
            find_value(v, f"{path}.{k}")
    elif isinstance(data, list):
        for i, v in enumerate(data):
            find_value(v, f"{path}[{i}]")
    elif data == "card":
        print(f"Found 'card' at {path}")


if __name__ == "__main__":
    with open("data/cards_compiled.json", encoding="utf-8") as f:
        d = json.load(f)
    print("Searching for 'card'...")
    find_value(d)
