import json
import sys

def dump_compiled_cards():
    target_ids = {294, 384, 430, 258, 261}
    
    try:
        with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    found = {}
    
    # Check both member_db and live_db
    databases = ['member_db', 'live_db']
    
    for db_name in databases:
        if db_name in data:
            db = data[db_name]
            for card_id_str, card_data in db.items():
                try:
                    cid = int(card_id_str)
                    if cid in target_ids:
                        found[cid] = card_data
                except ValueError:
                    continue

    # Write to file
    with open('compiled_cards_dump.json', 'w', encoding='utf-8') as f:
        json.dump(found, f, indent=2, ensure_ascii=False)
    print(f"Dumped {len(found)} cards to compiled_cards_dump.json")

if __name__ == "__main__":
    dump_compiled_cards()
