import os
import sys

import numpy as np

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.search_prob_agent import SearchProbAgent, YellOddsCalculator
from engine.game.enums import Phase as PhaseEnum
from engine.game.game_state import GameState
from engine.models.card import LiveCard, MemberCard


def test_odds_calculator():
    print("Testing YellOddsCalculator...")
    # Mock databases
    member_db = {
        1: MemberCard(
            card_id=1,
            card_no="M1",
            name="Red Girl",
            cost=1,
            hearts=np.array([1, 0, 0, 0, 0, 0, 0]),
            blade_hearts=np.array([1, 0, 0, 0, 0, 0, 0]),
            blades=1,
        ),
        2: MemberCard(
            card_id=2,
            card_no="M2",
            name="Blue Girl",
            cost=1,
            hearts=np.array([0, 0, 0, 0, 0, 1, 0]),
            blade_hearts=np.array([0, 0, 0, 0, 0, 1, 0]),
            blades=1,
        ),
    }
    live_db = {
        100: LiveCard(
            card_id=100, card_no="L1", name="Red Live", score=2, required_hearts=np.array([2, 0, 0, 0, 0, 0, 0])
        ),  # Needs 2 Red
    }

    calc = YellOddsCalculator(member_db, live_db)

    # Situation: 1 Red on stage, 1 Red in deck, 1 Yell remaining.
    stage_hearts = np.array([1, 0, 0, 0, 0, 0, 0])
    deck = [1, 2, 2, 2]  # 1 Red, 3 Blue

    # 1 Yell: Odds should be 1/4 = 0.25
    odds = calc.calculate_odds(deck, stage_hearts, [100], num_yells=1, samples=1000)
    print(f"Odds with 1 yell: {odds:.3f} (Expected ~0.25)")

    # 2 Yells: Odds should be higher.
    # Combinations of 2 from 4: (1,B), (1,B), (1,B), (B,B), (B,B), (B,B) -> 3/6 = 0.5
    odds = calc.calculate_odds(deck, stage_hearts, [100], num_yells=2, samples=1000)
    print(f"Odds with 2 yells: {odds:.3f} (Expected ~0.50)")

    # Needs ANY
    live_db[101] = LiveCard(
        card_id=101, card_no="L2", name="Any Live", score=1, required_hearts=np.array([0, 0, 0, 0, 0, 0, 2])
    )
    odds = calc.calculate_odds(deck, stage_hearts, [101], num_yells=1, samples=1000)
    print(
        f"Any Odds with 1 yell (Stage has 1, needs 2 total): {odds:.3f} (Expected ~1.0 because staging 1 counts as any if no specific color? Wait.)"
    )
    # Actually engine check_meet for ANY:
    # staging [1,0,0,0,0,0,0] -> 1 Red.
    # L101 needs 2 ANY.
    # Red heart CAN be used as ANY.
    # So we have 1 'available any'. We need 2.
    # If Yell gives 1 Blue, we have 2 hearts total -> Successful.
    # Since every card in deck has 1 heart, any yell card makes it successful.


def test_search_agent():
    print("\nTesting SearchProbAgent...")
    # Clear and set class-level databases (REQUIRED by game engine)
    GameState.member_db = {
        1: MemberCard(
            card_id=1,
            card_no="M1",
            name="Cheap",
            cost=1,
            hearts=np.array([1, 0, 0, 0, 0, 0, 0]),
            blade_hearts=np.array([1, 0, 0, 0, 0, 0, 0]),
            blades=1,
        ),
        10: MemberCard(
            card_id=10,
            card_no="M10",
            name="Expensive",
            cost=5,
            hearts=np.array([1, 1, 1, 1, 1, 1, 1]),
            blade_hearts=np.array([1, 1, 1, 1, 1, 1, 1]),
            blades=3,
        ),
    }
    GameState.live_db = {
        100: LiveCard(
            card_id=100, card_no="L1", name="Easy Live", score=2, required_hearts=np.array([0, 0, 0, 0, 0, 0, 1])
        ),
    }

    state = GameState()
    state.phase = PhaseEnum.MAIN
    state.current_player = 0
    state.players[0].hand = [1, 10]
    state.players[0].energy_zone = [200, 200]  # 2 energy

    legal_mask = state.get_legal_actions()
    legal_indices = np.where(legal_mask)[0]
    print(f"Legal actions: {legal_indices}")

    # Debug: Manually test step() to see if it works
    print(f"\n[DEBUG] Before step: Stage = {list(state.players[0].stage)}, Hand = {state.players[0].hand}")

    for action in legal_indices[:4]:
        ns = state.copy()
        ns = ns.step(action)
        print(f"  Action {action}: Stage = {list(ns.players[0].stage)}, Hand = {ns.players[0].hand}")

    agent = SearchProbAgent(depth=1)
    action = agent.choose_action(state, 0)
    print(f"\nChosen action: {action}")
    # Expected: Should play card 1 (id 1) because it can afford it (cost 1 < 2).
    # Card 10 (id 10) costs 5, which is too much.
    # Action 1 (index 0 in hand to slot 0) or similar.


if __name__ == "__main__":
    test_odds_calculator()
    test_search_agent()
