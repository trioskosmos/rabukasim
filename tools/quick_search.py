import json


def search():
    path = "data/cards.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    query = "HS-bp1-003"
    results = []
    for key, val in data.items():
        if query in key or query in str(val):
            results.append((key, val.get("name"), val.get("ability")))

    for key, name, ability in results:
        print(f"Key: {key}\nName: {name}\nAbility: {ability}\n---")


if __name__ == "__main__":
    search()
