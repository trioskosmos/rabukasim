import json
import os
import sys


def analyze_card(input_id):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    cards_path = os.path.join(project_root, "data", "cards.json")
    pseudocode_path = os.path.join(project_root, "data", "manual_pseudocode.json")
    compiled_path = os.path.join(project_root, "data", "cards_compiled.json")

    results = {
        "input_id": input_id,
        "card_no": None,
        "sequential_id": None,
        "source_data": None,
        "manual_pseudocode": None,
        "compiled_data": None,
    }

    # Helper to check if input is sequential ID
    is_seq = False
    try:
        if str(input_id).isdigit():
            is_seq = True
            results["sequential_id"] = int(input_id)
        else:
            results["card_no"] = str(input_id)
    except:
        results["card_no"] = str(input_id)

    # 1. Load from cards_compiled.json (to map seq_id <-> card_no)
    try:
        with open(compiled_path, "r", encoding="utf-8") as f:
            compiled_json = json.load(f)
            member_db = compiled_json.get("member_db", {})
            live_db = compiled_json.get("live_db", {})

            target = None
            if is_seq:
                target = member_db.get(str(input_id)) or live_db.get(str(input_id))
            else:
                for db in [member_db, live_db]:
                    for sid, item in db.items():
                        if item.get("card_no") == results["card_no"]:
                            target = item
                            results["sequential_id"] = int(sid)
                            break
                    if target:
                        break

            if target:
                results["compiled_data"] = target
                results["card_no"] = target.get("card_no")
                results["sequential_id"] = int(target.get("card_id", results["sequential_id"]))
    except Exception as e:
        print(f"Error reading cards_compiled.json: {e}")

    # 2. Load from cards.json (Master Data)
    try:
        with open(cards_path, "r", encoding="utf-8") as f:
            cards_data = json.load(f)
            if results["card_no"] in cards_data:
                results["source_data"] = cards_data[results["card_no"]]
            else:
                # Try search by card_no in values if input_id was card_no but not found in keys
                for key, val in cards_data.items():
                    if val.get("card_no") == results["card_no"]:
                        results["source_data"] = val
                        results["card_no"] = key
                        break
    except Exception as e:
        print(f"Error reading cards.json: {e}")

    # 3. Load from manual_pseudocode.json
    try:
        with open(pseudocode_path, "r", encoding="utf-8") as f:
            pseudo_data = json.load(f)
            if results["card_no"] in pseudo_data:
                results["manual_pseudocode"] = pseudo_data[results["card_no"]]
    except Exception:
        pass  # Optional

    return results


def format_output(results):
    if not results["source_data"] and not results["compiled_data"]:
        print(f"Card '{results['input_id']}' not found in database.")
        return

    src = results["source_data"] or {}
    pseudo = results["manual_pseudocode"] or {}
    compiled = results["compiled_data"] or {}

    print("================================================")
    print(f" CARD ANALYSIS: {results['card_no']} (ID: {results['sequential_id']})")
    print("================================================")
    print(f"Name:   {src.get('name', 'N/A')}")
    print(f"Type:   {src.get('type', 'N/A')}")
    print(f"Rare:   {src.get('rare', 'N/A')}")
    print(f"Cost:   {src.get('cost', compiled.get('cost', 'N/A'))}")
    print(f"Unit:   {src.get('unit', 'N/A')}")

    print("\n--- RAW ABILITY TEXT ---")
    print(src.get("ability", "No raw ability text found."))

    print("\n--- MANUAL PSEUDOCODE ---")
    print(pseudo.get("pseudocode", "No manual pseudocode found."))

    if compiled:
        print(f"\n--- COMPILED DATA (Sequential ID: {results['sequential_id']}) ---")

        # Show detailed abilities
        abilities = compiled.get("abilities", [])
        if abilities:
            for i, ab in enumerate(abilities):
                print(f"\n[Ability {i}]")
                print(f"  Trigger: {ab.get('trigger_type')} ({ab.get('trigger')})")
                print(f"  Once per turn: {ab.get('is_once_per_turn', False)}")

                # Conditions
                conds = ab.get("conditions", [])
                if conds:
                    print(f"  Conditions ({len(conds)}):")
                    for c in conds:
                        print(f"    - Type {c.get('type')} (Val: {c.get('value')}, Attr: {c.get('attr')})")
                        if c.get("params"):
                            print(f"      Params: {c.get('params')}")

                # Costs
                costs = ab.get("costs", [])
                if costs:
                    print(f"  Costs ({len(costs)}):")
                    for c in costs:
                        print(f"    - Type {c.get('type')} (Val: {c.get('value')})")

                # Bytecode
                bytecode = ab.get("bytecode", [])
                if bytecode:
                    print(f"  Bytecode: {bytecode}")

                # Translation hints
                print(f"  Source Text: {ab.get('raw_text')}")
        else:
            print("  No compiled abilities found.")

    print("\n================================================")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python card_analyzer.py <card_no_or_sequential_id>")
        sys.exit(1)

    val = sys.argv[1]
    results = analyze_card(val)
    format_output(results)
