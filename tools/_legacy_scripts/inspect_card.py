from engine.game.game_state import initialize_game
from engine.models.ability import EffectType


def inspect_card():
    game = initialize_game()
    card_no = "PL!S-pb1-013-N"

    found_cid = None
    for cid, card in game.member_db.items():
        if card.card_no == card_no:
            found_cid = cid
            print(f"Found {card_no} as ID {cid}")
            print(f"Name: {card.name}")
            for ab in card.abilities:
                print(f"Ability: {ab.raw_text}")
                if ab.costs:
                    print(f"  Costs: {ab.costs}")
                for i, eff in enumerate(ab.effects):
                    print(f"  Effect [{i}]: Type {eff.effect_type} ({EffectType(eff.effect_type).name})")
                    print(f"    Params: {eff.params}")
                    print(f"    Target: {eff.target}")
                    print(f"    Value: {eff.value}")
            break


if __name__ == "__main__":
    inspect_card()
