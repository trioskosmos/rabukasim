import argparse
import contextlib
import io
import os
import random
import sys
import time

import numpy as np

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase
from headless_runner import RandomAgent, SmartHeuristicAgent, TrueRandomAgent


class EloRating:
    def __init__(self, k_factor=32):
        self.k_factor = k_factor
        self.ratings = {"TrueRandom": 1000, "Random": 1000, "Smart": 1000}
        self.matches = {"TrueRandom": 0, "Random": 0, "Smart": 0}
        self.wins = {"TrueRandom": 0, "Random": 0, "Smart": 0}
        self.true_wins = {"TrueRandom": 0, "Random": 0, "Smart": 0}
        self.draws = {"TrueRandom": 0, "Random": 0, "Smart": 0}
        self.total_turns = {"TrueRandom": 0, "Random": 0, "Smart": 0}

    def expected_score(self, rating_a, rating_b):
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update(self, agent_a, agent_b, score_a):
        """
        score_a: 1 for A win, 0 for B win, 0.5 for draw
        Uses K=64 for first 20 games (placement), then K=32
        """
        self.matches[agent_a] += 1
        self.matches[agent_b] += 1

        if score_a == 1:
            self.wins[agent_a] += 1
        elif score_a == 0:
            self.wins[agent_b] += 1

        # Variable K-factor: K=2*base_k for first 20 games, then base_k
        k_a = self.k_factor * 2 if self.matches[agent_a] <= 20 else self.k_factor
        k_b = self.k_factor * 2 if self.matches[agent_b] <= 20 else self.k_factor

        ra = self.ratings[agent_a]
        rb = self.ratings[agent_b]

        ea = self.expected_score(ra, rb)
        eb = self.expected_score(rb, ra)

        # Calculate new ratings with individual K-factors
        new_ra = ra + k_a * (score_a - ea)
        new_rb = rb + k_b * ((1 - score_a) - eb)

        self.ratings[agent_a] = new_ra
        self.ratings[agent_b] = new_rb

        # Update draws if applicable
        if score_a == 0.5:
            self.draws[agent_a] += 1
            self.draws[agent_b] += 1


def run_match(agent_a_name, agent_b_name, agents_map, num_games=10):
    """Run a set of games between two agents"""
    # Setup agents
    agent_a = agents_map[agent_a_name]
    agent_b = agents_map[agent_b_name]

    p0_wins = 0
    p1_wins = 0
    first_player_wins = 0
    score_a_total = 0

    # Load data once
    if not GameState.member_db:
        loader = CardDataLoader("data/cards.json")
        m, l, e = loader.load()
        GameState.member_db = m
        GameState.live_db = l

    for i in range(num_games):
        try:
            # Setup State
            state = GameState(verbose=False)

            # Setup Decks (Normal)
            for p in state.players:
                m_ids = list(GameState.member_db.keys())
                l_ids = list(GameState.live_db.keys())
                p.main_deck = [random.choice(m_ids) for _ in range(40)] + [random.choice(l_ids) for _ in range(10)]
                random.shuffle(p.main_deck)
                p.energy_deck = [200] * 12

                # Draw 5
                for _ in range(5):
                    if p.main_deck:
                        p.hand.append(p.main_deck.pop())

                # Energy 3
                for _ in range(3):
                    if p.energy_deck:
                        p.energy_zone.append(p.energy_deck.pop(0))

            # Decide who goes first
            first_player = i % 2  # Alternate
            state.first_player = first_player
            state.current_player = first_player
            state.phase = Phase.MULLIGAN_P1

            # Map logical P0/P1 to Agents
            # if first_player = 0, P0 starts. P0 is agent_a?
            # We want agent_a to be P0 in even games, P1 in odd games?
            # actually let's just assign:
            # Game: P0 vs P1
            # If i is even: P0=A, P1=B
            # If i is odd:  P0=B, P1=A

            p0_agent = agent_a if (i % 2 == 0) else agent_b
            p1_agent = agent_b if (i % 2 == 0) else agent_a

            # Run Game
            turn_count = 0
            # Suppress output
            with contextlib.redirect_stdout(io.StringIO()):
                while not state.is_terminal() and turn_count < 200:
                    pid = state.current_player
                    mask = state.get_legal_actions()
                    if not np.any(mask):
                        mask[0] = True

                    if pid == 0:
                        action = p0_agent.choose_action(state, pid)
                    else:
                        action = p1_agent.choose_action(state, pid)

                    state = state.step(action)
                    turn_count += 1

            # Result
            # Result
            winner = state.winner

            # Resolve Draws by Score (User Request)
            if winner == 2 or (not state.is_terminal()):
                s0 = len(state.players[0].success_lives)
                s1 = len(state.players[1].success_lives)
                if s0 > s1:
                    winner = 0
                elif s1 > s0:
                    winner = 1

            if winner == 0:
                p0_wins += 1
                if first_player == 0:
                    first_player_wins += 1
            elif winner == 1:
                p1_wins += 1
                if first_player == 1:
                    first_player_wins += 1

            # If i%2==0 (A is P0): Winner 0 -> A wins. Winner 1 -> B wins
            # If i%2==1 (A is P1): Winner 0 -> B wins. Winner 1 -> A wins

            game_score_a = 0.5  # Default draw
            if winner == 0:
                game_score_a = 1.0 if (i % 2 == 0) else 0.0
            elif winner == 1:
                game_score_a = 0.0 if (i % 2 == 0) else 1.0

            score_a_total += game_score_a

        except Exception:
            # Crash = Loss for engine? or Draw?
            # Treat as Draw
            score_a_total += 0.5

    # Print Bias Stats
    print(f"    [Bias Check] P0 Wins: {p0_wins}, P1 Wins: {p1_wins}, Start Wins: {first_player_wins}/{num_games}")

    return score_a_total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=300, help="Total games to simulate")
    args = parser.parse_args()

    print(f"Starting ELO Tournament ({args.games} random pairings)...")

    agents = {"TrueRandom": TrueRandomAgent(), "Random": RandomAgent(), "Smart": SmartHeuristicAgent()}

    agent_names = list(agents.keys())
    elo = EloRating()

    # Load cards once
    loader = CardDataLoader("data/cards.json")
    m, l, e = loader.load()
    GameState.member_db = m
    GameState.live_db = l

    start_time = time.time()

    # Random pairings
    crashes = 0
    for game_num in range(args.games):
        # Randomly select two different agents
        a, b = random.sample(agent_names, 2)

        # Run single game with suppressed output
        try:
            # Suppress all print statements during game
            with contextlib.redirect_stdout(io.StringIO()):
                state = GameState(verbose=False)

                # Setup decks
                for p in state.players:
                    m_ids = list(GameState.member_db.keys())
                    l_ids = list(GameState.live_db.keys())
                    # Energy IDs start at 2000
                    p.energy_deck = [2000] * 12

                    p.main_deck = [random.choice(m_ids) for _ in range(40)] + [random.choice(l_ids) for _ in range(10)]
                    random.shuffle(p.main_deck)

                    for _ in range(5):
                        if p.main_deck:
                            p.hand.append(p.main_deck.pop())
                    for _ in range(3):
                        if p.energy_deck:
                            p.energy_zone.append(p.energy_deck.pop(0))
                            # No need to append to tapped_energy, it's a fixed size array (50,)

                # Random first player
                first_player = random.randint(0, 1)
                state.first_player = first_player
                state.current_player = first_player
                state.phase = Phase.MULLIGAN_P1

                # Assign agents
                p0_agent = agents[a]
                p1_agent = agents[b]

                # Run game
                actions_this_game = []
                for turn in range(5000):
                    if state.game_over:
                        break

                    mask = state.get_legal_actions()
                    if not np.any(mask):
                        state.game_over = True
                        state.winner = 2
                        break

                    current_agent = p0_agent if state.current_player == 0 else p1_agent
                    action = current_agent.choose_action(state, state.current_player)
                    actions_this_game.append((state.current_player, state.phase, action))
                    state = state.step(action)

                    if turn > 4000:
                        # Potential loop detection: print last few actions if we likely will timeout
                        if turn == 4001:
                            print(
                                f"  [WARN] Game {game_num} ({a} vs {b}) likely infinite loop. Actions sample:",
                                file=sys.__stderr__,
                            )
                        if turn > 4990:
                            p_name = a if actions_this_game[-1][0] == 0 else b
                            print(
                                f"    Action {turn}: Player {p_name} ({actions_this_game[-1][0]}) in {actions_this_game[-1][1]} phase did {action}",
                                file=sys.__stderr__,
                            )

                # Determine winner
                is_true_win = state.game_over
                if not state.game_over:
                    # Timeout - use score lead
                    p0_score = len(state.players[0].success_lives)
                    p1_score = len(state.players[1].success_lives)
                    if p0_score > p1_score:
                        state.winner = 0
                    elif p1_score > p0_score:
                        state.winner = 1
                    else:
                        state.winner = 2

                # Update ELO and wins/draws centrally via elo.update
                if state.winner == 0:
                    score_a = 1.0
                elif state.winner == 1:
                    score_a = 0.0
                else:
                    score_a = 0.5

                # Track true wins separately
                if state.winner == 0 and is_true_win:
                    elo.true_wins[a] += 1
                elif state.winner == 1 and is_true_win:
                    elo.true_wins[b] += 1

                elo.update(a, b, score_a)

                # Track turns
                elo.total_turns[a] += state.turn_number
                elo.total_turns[b] += state.turn_number

            if (game_num + 1) % 100 == 0:
                print(f"  Completed {game_num + 1}/{args.games} games...")

        except Exception as e:
            crashes += 1
            # Fallback print to sys.__stderr__ to see it during redirect
            print(f"  [DEBUG] Game {game_num} ({a} vs {b}) crashed: {e}", file=sys.__stderr__)
            continue

    # Final Results
    print("\n" + "=" * 40)
    print("TOURNAMENT RESULTS")
    print("=" * 40)
    print(f"{'Agent':<15} | {'ELO':<6} | {'Games':<5} | {'Win Rate':<12} | {'Avg Turns'}")
    print("-" * 65)

    for agent_name in sorted(elo.ratings.keys(), key=lambda x: elo.ratings[x], reverse=True):
        elo_score = int(elo.ratings[agent_name])
        games = elo.matches[agent_name]
        win_rate = f"{elo.wins[agent_name]}/{games}" if games > 0 else "N/A"
        avg_turns = f"{elo.total_turns[agent_name] / games:.1f}" if games > 0 else "N/A"
        print(f"{agent_name:<15} | {elo_score:<6} | {games:<5} | {win_rate:<12} | {avg_turns}")

    print("=" * 40)
    elapsed = time.time() - start_time
    print(f"Total Time: {elapsed:.2f}s")

    with open("final_stats.txt", "w") as f:
        f.write(
            f"{'Agent':<15} | {'ELO':<6} | {'Games':<5} | {'Win Rate':<12} | {'True Wins':<10} | {'Draws':<6} | {'Avg Turns'}\n"
        )
        f.write("-" * 95 + "\n")
        for agent_name in sorted(elo.ratings.keys(), key=lambda x: elo.ratings[x], reverse=True):
            elo_score = int(elo.ratings[agent_name])
            games = elo.matches[agent_name]
            win_rate = f"{elo.wins[agent_name]}/{games}" if games > 0 else "N/A"
            true_wins = f"{elo.true_wins[agent_name]}/{games}" if games > 0 else "N/A"
            draws = elo.draws[agent_name]
            avg_turns = f"{elo.total_turns[agent_name] / games:.1f}" if games > 0 else "N/A"
            f.write(
                f"{agent_name:<15} | {elo_score:<6} | {games:<5} | {win_rate:<12} | {true_wins:<10} | {draws:<6} | {avg_turns}\n"
            )
        f.write("=" * 40 + "\n")
        f.write(f"Total Time: {elapsed:.2f}s\n")


if __name__ == "__main__":
    main()
