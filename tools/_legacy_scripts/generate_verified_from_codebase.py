import json
import os
import re


def generate_verified_pool():
    cards_json_path = "engine/data/cards.json"
    compiled_json_path = "engine/data/cards_compiled.json"
    strict_test_path = "engine/tests/cards/batches/test_auto_generated_strict.py"
    output_path = (
        "engine/data/verified_card_pool.json"  # Writing to engine/data as per user context usually, or root data?
    )
    # The previous script wrote to data/verified_card_pool.json. Let's check where it is used.
    # The artifact says verified_card_pool.json matches existing. The file list showed it in root? No, `data/` dir in root.
    # Wait, `ls` showed `verified_card_pool.json` in the root directory `c:\Users\trios\.gemini\antigravity\vscode\loveca-copy`.
    # But `update_verified_pool.py` wrote to `data/verified_card_pool.json`.
    # Let's write to `verified_card_pool.json` in root to be safe/consistent with what seems to be used,
    # OR follow the project structure. The user previously mentioned `data/` source.
    # I'll write to `verified_card_pool.json` in the ROOT, and maybe `engine/data` if needed.
    # Let's align with the existing file location. The previous `list_dir` showed `verified_card_pool.json` in root.

    target_path = "verified_card_pool.json"

    print(f"Loading {cards_json_path}...")
    with open(cards_json_path, "r", encoding="utf-8") as f:
        cards_db = json.load(f)

    print(f"Loading {compiled_json_path}...")
    with open(compiled_json_path, "r", encoding="utf-8") as f:
        compiled_db = json.load(f)
        compiled_members = compiled_db.get("member_db", {})
        compiled_lives = compiled_db.get("live_db", {})

    print(f"Scanning test batches in {os.path.dirname(strict_test_path)}...")
    tested_cards = set()
    batch_dir = os.path.dirname(strict_test_path)
    for filename in os.listdir(batch_dir):
        if filename.startswith("test_") and filename.endswith(".py"):
            full_path = os.path.join(batch_dir, filename)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "cno =" in line:
                            match = re.search(r'cno = ["\'](.*?)["\']', line)
                            if match:
                                tested_cards.add(match.group(1))
            except Exception as e:
                print(f"Error reading {full_path}: {e}")

    print(f"Found {len(tested_cards)} cards with strict tests.")

    verified_abilities = []
    vanilla_members = []
    vanilla_lives = []

    for cid, card_data in cards_db.items():
        cno = card_data.get("card_no")

        # Check if compiled
        # Compiled DB keys are usually stringified integers of card_id? Or just card_id?
        # Let's iterate compiled to find match or use ID if keys match.
        # attributes in cards.json: "id": 1, ...
        # attributes in compiled: "0": { "card_id": 0 ... }
        # So we can look up by ID.

        # Determine if Vanilla
        abilities = card_data.get("ability", "")
        # In cards.json it's a string. If empty or just newlines, it's vanilla.
        # But wait, some have abilities but they are just keywords?
        # Let's assume empty string or "None"?
        # Actually proper Vanilla check: `abilities` list is empty in compiled JSON.

        compiled_entry = None
        # compiled keys are string indices
        # We need to find the entry in compiled_db corresponding to valid card_no
        # It seems compiled_members is a dict of "0": {...}, "1": {...}
        # We can map cno -> entry

        # Optimization: Build cno map for compiled
        # We'll do it on the fly or pre-build.

        # Let's just loop all cards in cards.json.

        is_vanilla = False
        has_bytecode = False

        # Find in compiled
        # This is O(N*M) if naive. Let's rely on card_id if possible.
        # But cards.json keys are weird sometimes.
        # Let's assume we can match by card_no.

        # Let's pre-index compiled by card_no
        if "compiled_index" not in locals():
            compiled_index = {}
            for k, v in compiled_members.items():
                compiled_index[v["card_no"]] = v
            for k, v in compiled_lives.items():
                compiled_index[v["card_no"]] = v

        comp_card = compiled_index.get(cno)

        if comp_card:
            # Check for bytecode
            # "bytecode": [...] in abilities
            # If any ability has bytecode, or if vanilla (no abilities).

            comp_abilities = comp_card.get("abilities", [])
            if not comp_abilities:
                is_vanilla = True
                has_bytecode = True  # Trivially true for vanilla
            else:
                # Check if ALL abilities have bytecode
                all_have_bytecode = True
                for ab in comp_abilities:
                    if not ab.get("bytecode"):
                        all_have_bytecode = False
                        break
                if all_have_bytecode:
                    has_bytecode = True

        # Categorize
        if is_vanilla:
            if "-L" in cno:
                vanilla_lives.append(cno)
            else:
                vanilla_members.append(cno)
        else:
            if has_bytecode and cno in tested_cards:
                verified_abilities.append(cno)

    # Sort
    verified_abilities.sort()
    vanilla_members.sort()
    vanilla_lives.sort()

    print(f"Verified Abilities: {len(verified_abilities)}")
    print(f"Vanilla Members: {len(vanilla_members)}")
    print(f"Vanilla Lives: {len(vanilla_lives)}")

    output_data = {
        "verified_abilities": verified_abilities,
        "vanilla_members": vanilla_members,
        "vanilla_lives": vanilla_lives,
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Written to {target_path}")


if __name__ == "__main__":
    generate_verified_pool()
