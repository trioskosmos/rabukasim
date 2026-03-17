import json
import os
import sys


def find_card_and_debug(card_no):
    log_file = "debug_trace.log"
    with open(log_file, "w", encoding="utf-8") as log:

        def log_print(*args):
            line = " ".join(map(str, args))
            log.write(line + "\n")
            print(line)

        cards_path = "engine/data/cards.json"
        with open(cards_path, "r", encoding="utf-8") as f:
            cards = json.load(f)

        card = cards.get(card_no)
        if not card:
            for k, v in cards.items():
                if v.get("card_no") == card_no:
                    card = v
                    break

        if not card:
            log_print(f"Card {card_no} not found.")
            return

        log_print(f"Card: {card.get('name')} ({card_no})")
        ability_text = card.get("ability", "No ability text")
        log_print(f"Ability Text: {ability_text}")
        log_print("-" * 40)

        sys.path.append(os.getcwd())
        # Instrument stdout for the parser prints
        original_stdout = sys.stdout
        sys.stdout = log

        from dataclasses import asdict

        from compiler.parser import AbilityParser

        try:
            abilities = AbilityParser.parse_ability_text(ability_text)
            for ab in abilities:
                try:
                    ab.bytecode = ab.compile()
                except Exception as e:
                    log_print(f"Compilation Error: {e}")
        finally:
            sys.stdout = original_stdout

        log_print(f"Parsed {len(abilities)} abilities:")
        for i, ab in enumerate(abilities):
            log_print(f"Ability {i}:")
            log_print(json.dumps(asdict(ab), indent=2, default=str))


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "PL!S-PR-020-PR"
    find_card_and_debug(target)
