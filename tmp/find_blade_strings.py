import json

def search_blades():
    with open("data/consolidated_abilities.json", "r", encoding="utf-8") as f:
        consol = json.load(f)

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        compiled = json.load(f)

    blade_cards = []
    
    for jp_text, data in consol.items():
        if "ブレード" in jp_text or "blade" in jp_text.lower():
            cards = data.get("cards", [])
            for c in cards:
                blade_cards.append((c, jp_text, data.get("pseudocode", "")))

    print(f"Found {len(blade_cards)} cards mentioning 'ブレード':")
    for cno, text, pseudo in blade_cards:
        # Find in compiled db
        comp_card = None
        for db_name in ["member_db", "live_db"]:
            for cid, cdata in compiled.get(db_name, {}).items():
                if cdata.get("card_no") == cno:
                    comp_card = cdata
                    break
        
        if comp_card:
            opcodes = []
            for ab in comp_card.get("abilities", []):
                bc = ab.get("bytecode", [])
                for i in range(0, len(bc), 5):
                    opcodes.append(bc[i])
            ops_str = ", ".join(map(str, sorted(set(opcodes))))
            print(f"- {cno}: Opcodes {ops_str}")
        else:
            print(f"- {cno}: Not found in compiled db")

if __name__ == "__main__":
    search_blades()
