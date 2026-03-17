from game.data_loader import CardDataLoader
from game.game_state import TriggerType


def find_infinite_abilities():
    loader = CardDataLoader("data/cards.json")
    members, lives, energy = loader.load()

    print("Checking members for infinite activated abilities...")
    for mid, m in members.items():
        for abi_idx, ab in enumerate(m.abilities):
            if ab.trigger == TriggerType.ACTIVATED:
                # Infinite if no cost and not once per turn
                has_cost = len(ab.costs) > 0
                is_limited = ab.is_once_per_turn

                if not has_cost and not is_limited:
                    print("INFINITE ABILITY FOUND!")
                    print(f"  Card: {m.name} (ID: {mid}, NO: {m.card_id})")
                    print(f"  Ability Text: {m.ability_text}")
                    print(f"  Parsed Costs: {ab.costs}")
                    print(f"  Is Once Per Turn: {ab.is_once_per_turn}")
                    print("-" * 20)


if __name__ == "__main__":
    find_infinite_abilities()
