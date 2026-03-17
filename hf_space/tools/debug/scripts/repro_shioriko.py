import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from engine.game.enums import Phase
from engine.game.game_state import GameState
from engine.models.ability import Ability, AbilityCostType, Cost, Effect, EffectType, TargetType
from engine.models.card import MemberCard


def test_shioriko_ability():
    # Setup card ID 264 (Shioriko PL!N-bp1-010-R)
    # raw_text: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る その中から1枚を手札に加え、残りを控え室に置く

    gs = GameState(verbose=True)
    p0 = gs.players[0]

    # 1. Setup deck and stage
    p0.main_deck = [1001, 1002, 1003, 1004, 1005]
    p0.energy_zone = [5001, 5002]  # Add real energy cards
    p0.hand = [264, 999]  # 999 is fodder for discard cost

    # Mock Shioriko card in DB
    shioriko_ability = Ability(
        trigger=1,  # ON_PLAY
        effects=[
            Effect(EffectType.LOOK_DECK, 3, TargetType.SELF),
            Effect(EffectType.LOOK_AND_CHOOSE, 1, TargetType.SELF, {"reason": "look_and_choose"}),
        ],
        costs=[Cost(type=AbilityCostType.DISCARD_HAND, value=1, is_optional=True)],
        raw_text="登場時手札を1枚控え室に置いてもよい：デッキの上から3枚見て1枚手札に加え、残りを控え室に置く",
    )

    shioriko = MemberCard(
        card_id=264,
        card_no="PL!N-bp1-010-R",
        name="三船栞子",
        cost=1,
        hearts=[1, 0, 0, 0, 0, 0, 0],
        blade_hearts=[0, 0, 0, 0, 0, 0],
        blades=1,
        abilities=[shioriko_ability],
    )

    GameState.member_db[264] = shioriko

    # 2. Play Shioriko
    gs.phase = Phase.MAIN
    gs.current_player = 0

    # Action 1: Play member from hand index 0 (Shioriko) to slot 0
    print(f"Starting Phase: {gs.phase.name} ({gs.phase.value})")
    gs = gs.step(1)  # Play Shioriko to slot 0 (1 + 0*3 + 0 = 1)

    print(f"End Phase: {gs.phase.name} ({gs.phase.value})")
    print(f"Pending Choices: {[{'type': pc[0], 'reason': pc[1].get('reason')} for pc in gs.pending_choices]}")

    # Check if discard choice is present
    if not gs.pending_choices or gs.pending_choices[0][0] != "TARGET_HAND":
        print("FAIL: No discard choice presented")
        return

    # Scenario A: Cancel cost
    gs_cancel = gs.copy()
    gs_cancel.step(0)  # Action 0 = Pass/Cancel optional cost

    print("\nScenario A: Cancel Cost")
    print(f"Pending Effects: {len(gs_cancel.pending_effects)}")
    print(f"Pending Choices: {len(gs_cancel.pending_choices)}")
    print(f"Deck Count: {len(gs_cancel.players[0].main_deck)}")

    if len(gs_cancel.pending_effects) == 0 and len(gs_cancel.players[0].main_deck) == 5:
        print("PASS: Ability aborted correctly")
    else:
        print("FAIL: Ability did not abort or deck was touched")

    # Scenario B: Pay cost
    gs_pay = gs.copy()
    # Action 501: Discard card at index 1 (999)
    # Hand is [264 (played but maybe still in list during step?), 999]
    # Actually hand.pop(0) happens in play_member. So hand is [999].
    gs_pay.step(500)  # Discard card 999

    print("\nScenario B: Pay Cost")
    print(f"Pending Choices: {len(gs_pay.pending_choices)}")
    if gs_pay.pending_choices and gs_pay.pending_choices[0][0] == "SELECT_FROM_LIST":
        print("PASS: SELECT_FROM_LIST presented")
    else:
        print(f"FAIL: Expected SELECT_FROM_LIST, got {gs_pay.pending_choices}")
        return

    # 3. Verify SELECT_FROM_LIST cards
    cards = gs_pay.pending_choices[0][1].get("cards", [])
    print(f"Looked Cards: {cards}")
    if cards == [1001, 1002, 1003]:
        print("PASS: Correct cards looked at")
    else:
        print("FAIL: Incorrect cards in list")

    # 4. Pick one (Action 601: index 1 -> 1002)
    gs_pay.step(601)

    print("\nResult of picking 1002")
    print(f"Hand: {gs_pay.players[0].hand}")
    print(f"Discard: {gs_pay.players[0].discard}")
    print(f"Deck Count: {len(gs_pay.players[0].main_deck)}")

    if 1002 in gs_pay.players[0].hand and 1001 in gs_pay.players[0].discard and 1003 in gs_pay.players[0].discard:
        print("PASS: Card added to hand and others discarded")
    else:
        print("FAIL: Card movement incorrect")

    # 5. Check Rule Log
    print("\nRule Log entries (last 5):")
    for entry in gs_pay.rule_log[-5:]:
        print(f"  {entry}")


if __name__ == "__main__":
    test_shioriko_ability()
