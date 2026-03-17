import json
import os
import sys

# Ensure we can import from local modules
sys.path.append(os.getcwd())

from tools.decompile_bytecode import decompile


def main():
    compiled_path = "data/cards_compiled.json"
    audit_path = "docs/card_logic_audit.md"

    if not os.path.exists(compiled_path):
        print(f"Error: {compiled_path} not found.")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    audit_entries = []

    def process_db(db):
        for card_id, card_data in db.items():
            card_no = card_data.get("card_no", "Unknown")
            name = card_data.get("name", "Unknown")

            abilities = card_data.get("abilities", [])
            for i, ab in enumerate(abilities):
                raw_jp = ab.get("raw_text", "")
                bytecode = ab.get("bytecode", [])

                # Decompile bytecode to pseudocode
                pcode = decompile(bytecode)

                audit_entries.append(
                    {
                        "card_no": card_no,
                        "name": name,
                        "ability_no": i + 1,
                        "raw_jp": raw_jp,
                        "bytecode": bytecode,
                        "pseudocode": pcode,
                    }
                )

    process_db(data.get("member_db", {}))
    process_db(data.get("live_db", {}))

    # Sort by card_no
    audit_entries.sort(key=lambda x: (x["card_no"], x["ability_no"]))

    with open(audit_path, "w", encoding="utf-8") as f:
        f.write("# Card Logic Audit (Decompiled)\n\n")
        f.write(
            "This log shows the mapping from original Japanese text to engine bytecode and the resulting English pseudocode (automatically decompiled).\n\n"
        )

        last_card = None
        for entry in audit_entries:
            if entry["card_no"] != last_card:
                f.write(f"## {entry['card_no']} - {entry['name']}\n\n")
                last_card = entry["card_no"]

            f.write(f"### Ability {entry['ability_no']}\n")
            f.write(f"**Japanese:**\n```text\n{entry['raw_jp']}\n```\n")
            f.write(f"**Bytecode:**\n`{entry['bytecode']}`\n\n")
            f.write(f"**Decompiled Pseudocode:**\n```text\n{entry['pseudocode']}\n```\n\n")
            f.write("---\n\n")

    print(f"Generated audit log with {len(audit_entries)} entries at {audit_path}")


if __name__ == "__main__":
    main()
