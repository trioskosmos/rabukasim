import json
import os

from engine.models.bytecode_readable import decode_bytecode


TriggerType = {
    0: "NONE",
    1: "ON_PLAY",
    2: "ON_LIVE_START",
    3: "ON_LIVE_SUCCESS",
    4: "TURN_START",
    5: "TURN_END",
    6: "CONSTANT",
    7: "ON_ACTIVATE",
    8: "ON_LEAVES",
    9: "ON_REVEAL",
    10: "ON_POSITION_CHANGE",
}


def main():
    compiled_path = "data/cards_compiled.json"
    if not os.path.exists(compiled_path):
        print(f"Error: {compiled_path} not found.")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    # Cards to specifically trace (based on previous user context)
    target_card_nos = ["PL!-bp3-001-P", "PL!HS-bp1-004-P", "PL!N-bp1-002-P"]

    report_data = {"generated_at": "2026-01-31T12:00:00Z", "cards": []}

    print("Generating trace report...")
    for card_no in target_card_nos:
        # Find card in member_db
        card_data = None
        for cid, c in db.get("member_db", {}).items():
            if c.get("card_no") == card_no:
                card_data = c
                break

        if not card_data:
            print(f"Warning: Card {card_no} not found in DB.")
            continue

        print(f"Tracing {card_no}...")
        card_entry = {"card_no": card_no, "name": card_data.get("name", "Unknown"), "abilities": []}

        abilities = card_data.get("abilities", [])
        for idx, ability in enumerate(abilities):
            trigger_id = ability.get("trigger", 0)
            trigger_name = TriggerType.get(trigger_id, f"TRIG_{trigger_id}")
            bytecode = ability.get("bytecode", [])

            trace = decode_bytecode(bytecode)

            card_entry["abilities"].append(
                {
                    "index": idx,
                    "trigger_id": trigger_id,
                    "trigger_name": trigger_name,
                    "trace": trace.splitlines(),
                    "raw_bytecode": bytecode,
                    "semantic_form": ability.get("semantic_form", {}),
                }
            )

        report_data["cards"].append(card_entry)

    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)
    report_file = "reports/trace_report_latest.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"Report saved to {report_file}")


if __name__ == "__main__":
    main()
