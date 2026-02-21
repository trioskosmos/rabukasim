import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from ai.arena_tournament import PPOAgent, create_mirror_deck, load_verified_pool

from engine.game.game_state import GameState, initialize_game

# Ensure project root is in path
sys.path.append(os.getcwd())


def debug_ppo():
    initialize_game(deck_type="random_verified")
    ppo = PPOAgent("checkpoints/lovelive_ppo_checkpoint_2320000_steps.zip")
    verified_members, verified_lives = load_verified_pool()

    state = GameState()
    deck = create_mirror_deck(verified_members, verified_lives, GameState.member_db, GameState.live_db)
    for p in state.players:
        p.main_deck = list(deck)
        p.hand = [p.main_deck.pop() for _ in range(5)]
        p.energy_zone = [p.energy_deck.pop() if p.energy_deck else 200 for _ in range(3)]

    print(f"Initial Phase: {state.phase}")
    print(f"Legal Actions: {sum(state.get_legal_actions())}")

    action = ppo.choose_action(state, 0)
    print(f"PPO Action: {action}")

    state = state.step(action)
    print(f"Next Phase: {state.phase}")


if __name__ == "__main__":
    debug_ppo()
