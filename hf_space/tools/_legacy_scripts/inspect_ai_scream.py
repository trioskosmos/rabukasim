import os
import sys

sys.path.append(os.getcwd())

from engine.game.data_loader import CardDataLoader


def inspect_card():
    loader = CardDataLoader("data/cards_compiled.json")
    members, lives, _ = loader.load()

    # Find LL-PR-004-PR
    card = next((x for x in lives.values() if x.card_no == "LL-PR-004-PR"), None)
    if not card:
        card = next((x for x in members.values() if x.card_no == "LL-PR-004-PR"), None)

    if not card:
        print("Card not found!")
        return

    print(f"Card: {card.name} ({card.card_no})")
    if hasattr(card, "abilities") and card.abilities:
        ab = card.abilities[0]
        print(f"Trigger: {ab.trigger}")
        for eff in ab.effects:
            print(f"Effect Type: {eff.effect_type} (Name: {eff.effect_type.name})")
            print(f"  Value: {eff.value}")
            print(f"  Target: {eff.target} (Name: {eff.target.name})")
            print(f"  Params: {eff.params}")
            print(f"  Modal Options: {len(eff.modal_options)}")

            h = abs(hash(eff.effect_type.name)) % 50
            print(f"  Hash(Name) % 50: {h}")

    else:
        print("No abilities.")


if __name__ == "__main__":
    inspect_card()
