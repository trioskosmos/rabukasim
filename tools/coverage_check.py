import os
import sys

# Context setup
sys.path.append(os.path.join(os.getcwd(), "game"))

from game.data_loader import CardDataLoader


def analyze_coverage():
    loader = CardDataLoader("game/../data/cards.json")
    try:
        members, lives, energy = loader.load()
    except Exception as e:
        print(f"Load failed: {e}")
        return

    total_abilities = 0
    parsed_effects = 0
    complex_unparsed = 0

    print(f"Analyzing {len(members)} members and {len(lives)} lives...")

    sample_unparsed = []

    for c in list(members.values()) + list(lives.values()):
        # Ability text is already parsed into Ability objects in loader
        # But we want to check if those objects actually HAVE effects
        # The loader uses AbilityParser.parse_ability_text(raw_text)

        # We need the RAW text to check if we missed something.
        # But data_loader doesn't store raw text anymore?
        # Wait, Ability object has `raw_text`.

        for ability in c.abilities:
            total_abilities += 1
            if ability.effects or ability.conditions or ability.costs:
                parsed_effects += 1
            else:
                complex_unparsed += 1
                sample_unparsed.append(ability.raw_text)

    print("\n--- Coverage Report ---")
    print(f"Total Ability Clauses: {total_abilities}")
    print(f"Successfully Parsed (Simple): {parsed_effects}")
    print(f"Unparsed (Complex): {complex_unparsed}")
    print(f"Coverage: {parsed_effects / total_abilities * 100:.1f}%")

    with open("unparsed.txt", "w", encoding="utf-8") as f:
        for s in sample_unparsed:
            f.write(f"- {s}\n")
    print("\nUnparsed texts saved to unparsed.txt")


if __name__ == "__main__":
    analyze_coverage()
