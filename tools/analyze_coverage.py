import json
import os


def analyze_comprehensiveness():
    scenario_path = "engine_rust_src/data/scenarios.json"
    compiled_path = "data/cards_compiled.json"

    if not os.path.exists(scenario_path) or not os.path.exists(compiled_path):
        print("Required data files not found.")
        return

    with open(scenario_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f).get("scenarios", [])

    with open(compiled_path, "r", encoding="utf-8") as f:
        compiled_data = json.load(f)
        member_db = compiled_data.get("member_db", {})

    # 1. Opcode Coverage in Scenarios
    used_opcodes = set()
    total_bytecode_size = 0
    for s in scenarios:
        # Note: Scenarios don't contain bytecode directly, but they match cards.
        # We need to find the card in the DB and see its opcodes.
        card_no = s.get("scenario_name", "").split(" ").pop(2) if " " in s.get("scenario_name", "") else ""
        # Finding by card_no is slow, let's use a lookup.
        # But we already have card_id in some scenarios? s['real_card_id']
        pass

    # Better way: Let's just look at the mapping of IDs we used.
    # Actually, we can just scan the compiled_db for all opcodes and see which cards have scenarios.

    cards_with_scenarios = {s["id"].split("_")[0] for s in scenarios}
    all_opcodes = set()
    covered_opcodes = set()

    for card_id_str, card in member_db.items():
        found_in_scenarios = any(card_id_str in cid for cid in cards_with_scenarios)
        for ab in card.get("abilities", []):
            bc = ab.get("bytecode", [])
            # Simplified opcode extraction (first byte of each instruction usually,
            # but instructions vary in length. Let's just collect all unique values below 255)
            # This is a rough heuristic but good for variety.
            for byte in bc:
                if 1 <= byte <= 250:  # Opcode range
                    all_opcodes.add(byte)
                    if found_in_scenarios:
                        covered_opcodes.add(byte)

    print(f"Total Scenarios: {len(scenarios)}")
    print(f"Unique Cards Covered: {len(cards_with_scenarios)}")
    print(f"Approx Unique Opcodes in Engine: {len(all_opcodes)}")
    print(f"Unique Opcodes covered by Scenarios: {len(covered_opcodes)}")
    print(f"Opcode Coverage: {(len(covered_opcodes) / max(1, len(all_opcodes))) * 100:.2f}%")


if __name__ == "__main__":
    analyze_comprehensiveness()
