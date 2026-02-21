import os
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.ability import AbilityCostType, TriggerType
from game.data_loader import CardDataLoader


def check_cards():
    loader = CardDataLoader("data/cards.json")
    m_db, l_db = loader.load()

    print(f"Checking {len(m_db)} members for free activated abilities...")

    for cid, m in m_db.items():
        for ability in m.abilities:
            if ability.trigger == TriggerType.ACTIVATED:
                has_substantive_cost = False
                for cost in ability.costs:
                    if cost.type in (AbilityCostType.TAP_SELF, AbilityCostType.ENERGY, AbilityCostType.SACRIFICE_SELF):
                        has_substantive_cost = True

                if not has_substantive_cost:
                    print(f"Card {cid} ({m.name}): Infinite Activated Ability? Costs: {ability.costs}")
                    print(f"  Text: {m.ability_text}")


if __name__ == "__main__":
    check_cards()
