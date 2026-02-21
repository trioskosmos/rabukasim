import json
import os

def audit_filters():
    compiled_path = "data/cards_compiled.json"
    if not os.path.exists(compiled_path):
        print(f"Error: {compiled_path} not found.")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Issue trackers
    zero_filter_selects = []  # Cards with SELECT_MEMBER/PLAY_FROM_HAND with a=0
    
    # Opcode IDs
    O_SELECT_MEMBER = 65
    O_PLAY_MEMBER_FROM_HAND = 57
    O_PLAY_MEMBER_FROM_DISCARD = 63

    for db_name in ["member_db", "live_db"]:
        if db_name not in data:
            continue
        for cid_str, card in data[db_name].items():
            cid = int(cid_str)
            card_name = card.get("name", "???")
            card_no = card.get("card_no", "???")

            for ab_idx, ab in enumerate(card.get("abilities", [])):
                bc = ab.get("bytecode", [])
                raw_text = ab.get("original_text", "")
                
                # Parse bytecode
                for i in range(0, len(bc), 4):
                    if i + 3 >= len(bc):
                        break
                    op, v, a, s = bc[i], bc[i+1], bc[i+2], bc[i+3]

                    # Check zero-filter selects
                    if op in [O_SELECT_MEMBER, O_PLAY_MEMBER_FROM_HAND, O_PLAY_MEMBER_FROM_DISCARD]:
                        if a == 0:
                            zero_filter_selects.append(
                                f"ID={cid} [{card_no}] ({card_name}) ab#{ab_idx}\nText: {raw_text}\n"
                            )
                            break # don't add same card/ability twice

    print(f"Found {len(zero_filter_selects)} abilities with a=0")
    with open("reports/zero_filter_cards.txt", "w", encoding="utf-8") as f:
        for item in zero_filter_selects:
            f.write(item + "\n")

if __name__ == "__main__":
    audit_filters()
