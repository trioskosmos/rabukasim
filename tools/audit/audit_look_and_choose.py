import json
import os


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("--- Auditing LOOK_AND_CHOOSE Remainder Logic ---")
    cards_raw = load_json("data/cards.json")
    cards_compiled = load_json("data/cards_compiled.json")

    issues = []

    # Text patterns indicating remainder to waiting room (discard)
    patterns = ["残りを控え室", "残りは控え室"]

    for no, raw in cards_raw.items():
        ability_text = raw.get("ability", "")
        if not any(p in ability_text for p in patterns):
            continue

        # Found a card that SHOULD discard remainder
        # Find compiled logic
        compiled = None
        for db in ["member_db", "live_db", "energy_db"]:
            for cid, c in cards_compiled.get(db, {}).items():
                if c.get("card_no") == no:
                    compiled = c
                    break
            if compiled:
                break

        if not compiled:
            print(f"[WARN] {no}: No compiled data found.")
            continue

        # Check bytecode
        for i, ab in enumerate(compiled.get("abilities", [])):
            bc = ab.get("bytecode", [])
            # Opcode 41 is O_LOOK_AND_CHOOSE.
            # Opcode 28 is O_ORDER_DECK (puts remainder on deck).

            # Simple check: Does it assume Order Deck logic?
            has_order_deck = False
            has_look_choose = False
            look_choose_s = -1

            idx = 0
            while idx < len(bc):
                op = bc[idx]
                if op == 28:  # O_ORDER_DECK
                    has_order_deck = True
                if op == 41:  # O_LOOK_AND_CHOOSE
                    has_look_choose = True
                    if idx + 3 < len(bc):
                        look_choose_s = bc[idx + 3]

                # Advance 4 ints
                idx += 4

            # Scan for "Remainder to Waiting Room" but using other opcodes
            if "残りを控え室" in ability_text or "remainder to waiting room" in ability_text.lower():
                # Check compiled opcodes
                opcodes = [bc[i] for i in range(0, len(bc), 4)]

                # Allowed opcodes that handle discard logic internally
                allowed = [41, 69, 58]  # LOOK_AND_CHOOSE, REVEAL_UNTIL, MOVE_TO_DISCARD

                # If no allowed opcode is present, flag it
                if not any(op in allowed for op in opcodes):
                    issues.append(
                        f"{no}: Text implies 'Remainder to Discard' but uses Opcodes {opcodes} (No known discard handler found)."
                    )

                # Specific check for REVEAL_UNTIL (69)
                # Does it handle discard?
                # interpreter.rs shows REVEAL_UNTIL usually adds to hand/stage and discards rest?
                # parsing logic in parser_v2 might not set it up right.

            if has_order_deck:
                issues.append(f"{no}: Uses O_ORDER_DECK (Op 28) but text says 'Remainder to Discard'.")
            elif has_look_choose:
                # Check if s param implies discard.
                # Decode s: Target (0-7) | Remainder (8-15)
                target = look_choose_s & 0xFF
                rem_dest = (look_choose_s >> 8) & 0xFF

                # We expect Remainder to be Discard (7)
                if rem_dest != 7:
                    issues.append(
                        f"{no}: Uses O_LOOK_AND_CHOOSE (Op 41) with s={look_choose_s} (Target={target}, Rem={rem_dest}), expected Rem={7} (Discard)."
                    )
            else:
                # Maybe complex logic?
                pass

    with open("reports/audit_look_and_choose.txt", "w", encoding="utf-8") as f:
        if issues:
            f.write(f"Found {len(issues)} issues:\n")
            for issue in issues:
                f.write(f"  - {issue}\n")
        else:
            f.write("No issues found (or heuristics missed them).\n")
    print("Report written to reports/audit_look_and_choose.txt")


if __name__ == "__main__":
    main()
