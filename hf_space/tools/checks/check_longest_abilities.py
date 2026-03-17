import json

from game.ability import AbilityParser


def check_longest():
    print("Loading cards...")
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = list(data.values()) if isinstance(data, dict) else data

    # Filter out empty abilities
    cards = [c for c in cards if c.get("ability")]

    # Sort by ability text length
    cards.sort(key=lambda x: len(x.get("ability", "")), reverse=True)

    top_20 = cards[:20]

    parser = AbilityParser()

    print(f"Checking top {len(top_20)} longest abilities...\n")

    with open("longest_abilities_check.txt", "w", encoding="utf-8") as out:
        for i, card in enumerate(top_20, 1):
            card_name = card.get("name", "Unknown")
            # Try likely keys for ID
            card_id = card.get("id", card.get("cardNumber", card.get("card_no", "Unknown")))
            raw_text = card.get("ability", "")

            out.write(f"#{i} [{card_id}] {card_name} (Length: {len(raw_text)})\n")
            out.write("-" * 60 + "\n")
            out.write(f"RAW: {raw_text}\n")
            out.write("-" * 60 + "\n")

            try:
                abilities = parser.parse_ability_text(raw_text)
                for j, ability in enumerate(abilities, 1):
                    out.write(f"  Ability {j}:\n")
                    out.write(f"    Trigger: {ability.trigger}\n")
                    if ability.is_once_per_turn:
                        out.write("    [ONCE PER TURN]\n")

                    if ability.conditions:
                        out.write(f"    Conditions ({len(ability.conditions)}):\n")
                        for cond in ability.conditions:
                            out.write(
                                f"      - {cond.type} (Val: {cond.params.get('value', 'N/A')}, Neg: {cond.is_negated})\n"
                            )
                            if cond.params:
                                out.write(f"        Params: {cond.params}\n")

                    if ability.costs:
                        out.write(f"    Costs ({len(ability.costs)}):\n")
                        for cost in ability.costs:
                            out.write(f"      - {cost.type} (Val: {cost.value}, Opt: {cost.is_optional})\n")

                    if ability.effects:
                        out.write(f"    Effects ({len(ability.effects)}):\n")
                        for k, effect in enumerate(ability.effects, 1):
                            params = []
                            if effect.params:
                                params.append(f"Params={effect.params}")
                            if effect.value:
                                params.append(f"Value={effect.value}")
                            if effect.target:
                                params.append(f"Target={effect.target}")

                            out.write(f"      {k}. {effect.effect_type}\n")
                            if params:
                                out.write(f"         {' '.join(params)}\n")
                            if effect.is_optional:
                                out.write("         [OPTIONAL]\n")
                    else:
                        out.write("    Effects: (None)\n")

            except Exception as e:
                out.write(f"  ERROR PARSING: {e}\n")

            except Exception as e:
                out.write(f"  ERROR PARSING: {e}\n")

            out.write("=" * 80 + "\n\n")

    print("Check complete. See longest_abilities_check.txt")


if __name__ == "__main__":
    check_longest()
