import logging
import os
import sys

import numpy as np

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase
from headless_runner import RandomAgent, TrueRandomAgent


def run_debug_game():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    loader = CardDataLoader("data/cards.json")
    m_db, l_db, e_db = loader.load()
    GameState.member_db = m_db
    GameState.live_db = l_db

    # Try multiple seeds
    for seed in range(43, 100):
        print(f"Checking Seed {seed}...", end="\r")
        np.random.seed(seed)

        # Verbose false for speed
        state = GameState(verbose=False)
        # Setup similar to before
        for p in state.players:
            m_ids = list(m_db.keys())
            l_ids = list(l_db.keys())
            p.main_deck = [np.random.choice(m_ids) for _ in range(40)] + [np.random.choice(l_ids) for _ in range(10)]
            np.random.shuffle(p.main_deck)
            p.energy_deck = [2000] * 12
            for _ in range(5):
                if p.main_deck:
                    p.hand.append(p.main_deck.pop())
            for _ in range(3):
                if p.energy_deck:
                    p.energy_zone.append(p.energy_deck.pop(0))
                    p.tapped_energy[len(p.energy_zone) - 1] = False

        state.first_player = 0
        state.current_player = 0
        state.phase = Phase.MULLIGAN_P1

        agents = [RandomAgent(), TrueRandomAgent()]

        consecutive_phase_7 = 0

        # Check for loop
        for action_num in range(4001):
            if state.game_over:
                break

            p_idx = state.current_player
            mask = state.get_legal_actions()
            if not np.any(mask):
                break

            action = agents[p_idx].choose_action(state, p_idx)
            state = state.step(action)

            if state.phase == Phase.PERFORMANCE_P2:
                consecutive_phase_7 += 1
            else:
                consecutive_phase_7 = 0

            if consecutive_phase_7 > 50:
                print(f"\n!!! FOUND PHASE 7 LOOP IN SEED {seed} !!!")
                print("Re-running with verbose log to tools/game_log.txt...")

                # Re-run exactly same setup with verbose
                np.random.seed(seed)
                state = GameState(verbose=True)
                for p in state.players:
                    p.main_deck = [np.random.choice(m_ids) for _ in range(40)] + [
                        np.random.choice(l_ids) for _ in range(10)
                    ]
                    np.random.shuffle(p.main_deck)
                    p.energy_deck = [2000] * 12
                    for _ in range(5):
                        if p.main_deck:
                            p.hand.append(p.main_deck.pop())
                    for _ in range(3):
                        if p.energy_deck:
                            p.energy_zone.append(p.energy_deck.pop(0))
                            p.tapped_energy[len(p.energy_zone) - 1] = False
                state.first_player = 0
                state.current_player = 0
                state.phase = Phase.MULLIGAN_P1
                state.verbose = True  # Ensure verbose

                with open("tools/game_log.txt", "w", encoding="utf-8") as f:
                    for replay_action in range(action_num + 20):
                        if state.game_over:
                            break
                        p_idx = state.current_player
                        mask = state.get_legal_actions()
                        if not np.any(mask):
                            break
                        action = agents[p_idx].choose_action(state, p_idx)

                        phase_name = state.phase.name
                        log_msg = f"Action {replay_action}: P{p_idx} ({phase_name}) -> CHOICE {action}"
                        f.write(log_msg + "\n")
                        state = state.step(action)
                        if state.phase == Phase.PERFORMANCE_P2 and replay_action > action_num:
                            f.write("--- STUCK IN LOOP ---\n")
                return


if __name__ == "__main__":
    run_debug_game()
