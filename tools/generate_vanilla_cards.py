import json
import os


def generate_vanilla_cards(input_path="data/cards_compiled.json", output_path="data/cards_vanilla.json"):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    print(f"Loading compiled cards from {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Strip all abilities from member and live databases
    for db_key in ["member_db", "live_db"]:
        if db_key in data:
            for cid, card in data[db_key].items():
                card["abilities"] = []
                card["ability_text"] = ""
                card["original_text"] = ""
                card["original_text_en"] = ""
                # Also strip ability-related flags for true vanilla
                card["ability_flags"] = 0
                card["semantic_flags"] = 0
                card["synergy_flags"] = 0
                if "cost_flags" in card:
                    card["cost_flags"] = 0

    print(f"Writing vanilla cards to {output_path}...")
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Done.")


if __name__ == "__main__":
    generate_vanilla_cards()
