import json

def get_id():
    path = "data/cards_compiled.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    no = "PL!HS-bp1-003-R＋"
    for cid, c in data["member_db"].items():
        if c.get("card_no") == no:
            print(f"ID: {cid}")
            return

if __name__ == "__main__":
    get_id()
