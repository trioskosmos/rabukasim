import json
import os
import sys

# Ensure we can import from local modules
sys.path.append(os.getcwd())

from tools.simplify_cards import generate_pseudocode


def main():
    compiled_path = "data/cards_compiled.json"
    raw_path = "engine/data/cards.json"
    batch1_path = "updates_batch_1.json"
    batch2_path = "updates_batch_2.json"
    output_path = "engine/data/cards.json"
    audit_path = "docs/card_logic_audit.md"

    if not os.path.exists(compiled_path):
        print(f"Error: {compiled_path} not found.")
        return
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found.")
        return

    # Load data
    with open(compiled_path, "r", encoding="utf-8") as f:
        compiled_data = json.load(f)
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_cards = json.load(f)

    overrides = {}
    if os.path.exists(batch1_path):
        with open(batch1_path, "r", encoding="utf-8") as f:
            overrides.update(json.load(f))
    if os.path.exists(batch2_path):
        with open(batch2_path, "r", encoding="utf-8") as f:
            overrides.update(json.load(f))

    # Audit data
    audit_entries = []

    # helper to process a database
    def process_db(db):
        for card_id, card_data in db.items():
            card_no = card_data.get("card_no")
            if not card_no:
                continue

            # Generate pseudocode blocks
            pcode_blocks = []
            bytecode_blocks = []

            if card_no in overrides:
                # If we have an override, we use it.
                # Note: overrides are usually a single string for all abilities
                pcode = overrides[card_no]
                pcode_blocks.append(pcode)
                # For audit, we'll just note it's overridden
                bytecode_blocks.append("OVERRIDDEN")
            else:
                abilities = card_data.get("abilities", [])
                for ab in abilities:
                    pcode = generate_pseudocode(ab)
                    pcode_blocks.append(pcode)
                    bytecode_blocks.append(str(ab.get("bytecode", [])))

            final_pcode = "\n\n".join(pcode_blocks)

            # Update raw card data with NEW field
            if card_no in raw_cards:
                raw_cards[card_no]["pseudocode"] = final_pcode

                # Add to audit
                audit_entries.append(
                    {
                        "card_no": card_no,
                        "name": raw_cards[card_no].get("name", "Unknown"),
                        "ability_jp": raw_cards[card_no].get("ability", ""),
                        "pseudocode": final_pcode,
                        "bytecodes": bytecode_blocks,
                    }
                )

    if "member_db" in compiled_data:
        process_db(compiled_data["member_db"])
    if "live_db" in compiled_data:
        process_db(compiled_data["live_db"])

    # Save updated cards.json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(raw_cards, f, ensure_ascii=False, indent=4)

    # Generate Audit Log
    with open(audit_path, "w", encoding="utf-8") as f:
        f.write("# Card Logic Audit Log\n\n")
        f.write(
            "This log documents the mapping between original Japanese card text, regenerated English pseudocode, and the resulting bytecode sequences.\n\n"
        )

        # Sort by card_no
        audit_entries.sort(key=lambda x: x["card_no"])

        for entry in audit_entries:
            f.write(f"## {entry['card_no']} - {entry['name']}\n\n")
            f.write("### Japanese Ability\n")
            f.write(f"```text\n{entry['ability_jp']}\n```\n\n")
            f.write("### Regenerated Pseudocode\n")
            f.write(f"```text\n{entry['pseudocode']}\n```\n\n")
            f.write("### Bytecode Sequences\n")
            for i, bc in enumerate(entry["bytecodes"]):
                f.write(f"- Ability {i + 1}: `{bc}`\n")
            f.write("\n---\n\n")

    print(f"Successfully updated {len(audit_entries)} cards in {output_path}")
    print(f"Audit log created at {audit_path}")


if __name__ == "__main__":
    main()
