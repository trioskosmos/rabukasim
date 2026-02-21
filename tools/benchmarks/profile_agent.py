import cProfile
import io
import os
import pstats
import sys

import numpy as np

# Add project root directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from ai.search_prob_agent import SearchProbAgent

from engine.game.enums import Phase as PhaseEnum
from engine.game.game_state import GameState
from engine.models.card import LiveCard, MemberCard


def profile_search():
    print("Setting up profile environment...")

    # Initialize GameState class variables
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
    state.players[0].hand = [1, 10, 1, 10, 1]  # 5 cards
    state.players[0].energy_zone = [200, 200, 200, 200]  # 4 energy
    state.players[0].stage = [1, -1, -1]  # One card on stage
    state.players[0].deck = [1] * 20  # Some deck

    # Set up agent with Numba enabled (default)
    agent = SearchProbAgent(depth=2)  # Higher depth to trigger more calls

    print("Starting profile...")
    pr = cProfile.Profile()
    pr.enable()

    # Run decision
    action = agent.choose_action(state, 0)

    pr.disable()
    print(f"Profile complete. Chose action: {action}")

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
    ps.print_stats(50)  # Top 50 by cumulative time
    print(s.getvalue())


if __name__ == "__main__":
    profile_search()
