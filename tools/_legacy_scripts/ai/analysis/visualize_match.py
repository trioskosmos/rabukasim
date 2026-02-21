import os
import sys

# Setup paths
sys.path.append(os.getcwd())

import random

from ai.arena_tournament_parallel import PPOAgent, SmartHeuristicAgent, create_mirror_deck, load_verified_pool

from engine.game.game_state import GameState, Phase, initialize_game


def print_state(state):
    p0 = state.players[0]
    p1 = state.players[1]
    print(f"\n--- Turn {state.turn_number} [Phase: {state.phase}] Player {state.current_player} ---")
    print(
        f"P0 (PPO)   | Score: {len(p0.success_lives)} | Lives: {len(p0.live_zone)} | Hand: {len(p0.hand)} | Energy: {p0.energy_count} | Stage: {p0.stage}"
    )
    print(
        f"P1 (Smart) | Score: {len(p1.success_lives)} | Lives: {len(p1.live_zone)} | Hand: {len(p1.hand)} | Energy: {p1.energy_count} | Stage: {p1.stage}"
    )


def main():
    print("Initializing Match: PPO vs SmartHeuristic...")

    # 1. Load Data
    verified_members, verified_lives = load_verified_pool()
    initialize_game(deck_type="random_verified")

    # 2. Setup Agents
    # Find latest model
    import glob

    list_of_files = glob.glob("checkpoints/vector/*.zip")
    latest_model = max(list_of_files, key=os.path.getctime)
    print(f"Loading Model: {latest_model}")

    ppo = PPOAgent(latest_model, device="cpu")
    smart = SmartHeuristicAgent()

    # 3. Setup Game
    state = GameState()
    mirror_deck = create_mirror_deck(verified_members, verified_lives, GameState.member_db, GameState.live_db)

    for p in state.players:
        p.main_deck = list(mirror_deck)
        p.energy_deck = [200] * 12
        p.hand = [p.main_deck.pop() for _ in range(5)]
        p.energy_zone = [p.energy_deck.pop() for _ in range(3)]
        random.shuffle(p.main_deck)

    state.first_player = 0  # PPO goes first
    state.current_player = 0
    state.phase = Phase.MULLIGAN_P1

    agents = [ppo, smart]

    # 4. Loop
    while not state.game_over and state.turn_number <= 50:  # Limit length
        print_state(state)

        current_agent = agents[state.current_player]
        action = current_agent.choose_action(state, state.current_player)

        print(f"Action: {action}")

        state = state.step(action)
        state.check_win_condition()

        # time.sleep(0.5)

    print("\n=== GAME OVER ===")
    print(f"Winner: {state.winner}")
    print(f"Final Score: PPO {len(state.players[0].success_lives)} - {len(state.players[1].success_lives)} Smart")


if __name__ == "__main__":
    main()
