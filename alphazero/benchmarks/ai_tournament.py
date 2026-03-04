import argparse
import json
import os
import random
import sys
import time
from multiprocessing import Pool, cpu_count
from typing import Dict, List, Tuple

import numpy as np

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Robust path detection for the Rust engine
base_dir = os.path.dirname(os.path.abspath(__file__))
search_paths = [
    os.path.join(base_dir, "..", "..", "engine_rust_src", "target", "dev-release"),
    os.path.join(base_dir, "..", "..", "engine_rust_src", "target", "debug"),
    os.path.join(base_dir, "..", "..", "engine_rust_src", "target", "release"),
    os.path.join(base_dir, "..", "..", ".venv", "Lib", "site-packages", "engine_rust"),
]
for p in search_paths:
    p_abs = os.path.abspath(p)
    if os.path.exists(os.path.join(p_abs, "engine_rust.pyd")) or os.path.exists(os.path.join(p_abs, "engine_rust.dll")):
        if p_abs not in sys.path:
            sys.path.insert(0, p_abs)
            break

try:
    import engine_rust
except ImportError:
    # Try one more location (site-packages root)
    try:
        import engine_rust
    except ImportError:
        print("Error: engine_rust not found. Please ensure the Rust engine is compiled and in your path.")
        sys.exit(1)


class EloRating:
    def __init__(self, k_factor=32):
        self.k_factor = k_factor
        self.ratings = {}
        self.matches = {}
        self.wins = {}
        self.draws = {}

    def init_agent(self, name):
        if name not in self.ratings:
            self.ratings[name] = 1000
            self.matches[name] = 0
            self.wins[name] = 0
            self.draws[name] = 0

    def update(self, agent_a, agent_b, score_a):
        self.init_agent(agent_a)
        self.init_agent(agent_b)
        self.matches[agent_a] += 1
        self.matches[agent_b] += 1
        
        if score_a == 1.0:
            self.wins[agent_a] += 1
        elif score_a == 0.0:
            self.wins[agent_b] += 1
        else:
            self.draws[agent_a] += 1
            self.draws[agent_b] += 1

        ra, rb = self.ratings[agent_a], self.ratings[agent_b]
        ea = 1 / (1 + 10 ** ((rb - ra) / 400))
        eb = 1 - ea
        
        k = self.k_factor * 2 if self.matches[agent_a] <= 20 else self.k_factor
        self.ratings[agent_a] = ra + k * (score_a - ea)
        self.ratings[agent_b] = rb + k * ((1 - score_a) - eb)


# Global storage for worker processes to avoid re-loading DB
G_DB = None


def init_worker(db_json_str):
    global G_DB
    G_DB = engine_rust.PyCardDatabase(db_json_str)


def parse_deck(path: str, card_map: Dict[str, int]) -> Dict[str, List[int]]:
    """Parses a deck file and returns member, energy, and live lists."""
    deck_members = []
    deck_energy = []
    deck_lives = []
    
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("x")
            card_no = parts[0].strip()
            count = 1
            if len(parts) > 1:
                try: count = int(parts[1].strip())
                except: pass
            
            if card_no in card_map:
                cid, ctype = card_map[card_no]
                if ctype == "energy": deck_energy.extend([cid] * count)
                elif ctype == "live": deck_lives.extend([cid] * count)
                else: deck_members.extend([cid] * count)
                
    return {"members": deck_members, "energy": deck_energy, "lives": deck_lives}


def run_single_match(args):
    """Worker function to run a single match."""
    p0_name, p1_name, p0_sims, p1_sims, p0_h_id, p1_h_id, deck_pair, seed, debug = args
    
    global G_DB
    state = engine_rust.PyGameState(G_DB)
    state.silent = not debug
    
    d0, d1 = deck_pair
    state.initialize_game_with_seed(
        d0["members"], d1["members"],
        d0["energy"], d1["energy"],
        d0["lives"], d1["lives"],
        seed
    )
    
    # Phase Constants (Match engine_rust/src/core/enums.rs)
    PHASE_RPS = -3
    PHASE_TURN_CHOICE = -2
    PHASE_MULLIGAN_P1 = -1
    PHASE_MULLIGAN_P2 = 0
    ACTION_PASS = 0
    ACTION_TURN_CHOICE_FIRST = 5000
    ACTION_RPS_ROCK_P1 = 20000 
    ACTION_RPS_SCISSORS_P2 = 21002
    
    turns = 0
    # 1. Advance through Setup/Rps/TurnChoice/Mulligan
    # These phases are not suitable for MCTS benchmarking as they are setup logic.
    # We automate them to get to the actual gameplay.
    while state.phase < 1 and turns < 200:
        if state.phase == PHASE_RPS:
            # P0 chose, now P1 needs to choose if not already done
            if state.rps_choices[0] == -1:
                state.step(ACTION_RPS_ROCK_P1)
            elif state.rps_choices[1] == -1:
                state.step(ACTION_RPS_SCISSORS_P2)
        elif state.phase == PHASE_TURN_CHOICE:
            state.step(ACTION_TURN_CHOICE_FIRST)
        elif state.phase in [PHASE_MULLIGAN_P1, PHASE_MULLIGAN_P2]:
            state.step(ACTION_PASS) # No mulligan for simplicity in benchmark
        else:
            # Advance (Energy/Draw/Active logic)
            state.step(ACTION_PASS)
        turns += 1

    # Run full match
    if p0_name == "random" or p1_name == "random":
        # Manual match loop for true random support
        while state.phase != 9 and turns < 2000: # Phase::Terminal = 9
            acting_p = state.acting_player
            legal = state.get_legal_action_ids()
            if not legal: break
            
            if debug:
                print(f"[DEBUG] Turn {state.turn}, Phase {state.phase}, Acting P{acting_p}")
                print(f"  Hand: P0={len(state.get_player(0).hand)}, P1={len(state.get_player(1).hand)}")
                print(f"  Score: P0={len(state.get_player(0).success_lives)}, P1={len(state.get_player(1).success_lives)}")

            if (acting_p == 0 and p0_name == "random") or (acting_p == 1 and p1_name == "random"):
                # Pick a random legal action
                action = random.choice(legal)
                if debug:
                    print(f"  Random Action: {action} ({state.get_action_label(action)})")
                state.step(action)
            else:
                # MCTS/Heuristic for the other player
                acting_sims = p0_sims if acting_p == 0 else p1_sims
                acting_h_id = p0_h_id if acting_p == 0 else p1_h_id
                
                if acting_sims > 0:
                    # Use MCTS
                    h_type = "original" if acting_h_id == 0 else "legacy"
                    results = state.search_mcts(num_sims=acting_sims, heuristic_type=h_type)
                    if not results:
                        action = legal[0]
                    else:
                        action = results[0][0]
                        if debug:
                            print(f"  MCTS Results (All Legal):")
                            # Map action_id to results for easy lookup
                            res_map = {r[0]: (r[1], r[2]) for r in results}
                            for la in legal:
                                label = state.get_action_label(la)
                                score, visits = res_map.get(la, (0.5, 0))
                                print(f"    - Action {la:<5} ({label:<40}): Score={score:.4f}, Visits={visits}")
                    state.step(action)
                else:
                    # Use greedy
                    action = state.get_greedy_action(G_DB, acting_p, acting_h_id)
                    if debug:
                        print(f"  Greedy Results (All Legal):")
                        evals = state.get_greedy_evaluations(G_DB, acting_p, acting_h_id)
                        # evals is Vec<(i32, f32)>
                        eval_map = {e[0]: e[1] for e in evals}
                        for la in legal:
                            label = state.get_action_label(la)
                            score = eval_map.get(la, 0.5)
                            print(f"    - Action {la:<5} ({label:<40}): Score={score:.4f}")
                        print(f"  Greedy Choice: {action} ({state.get_action_label(action)})")
                    state.step(action)
            turns += 1
        winner = state.get_winner()
        match_turns = state.turn
    else:
        # Fast native loop
        winner, match_turns = state.play_asymmetric_match(
            p0_sims, p1_sims,
            p0_h_id, p1_h_id,
            engine_rust.SearchHorizon.GameEnd(),
            True, True # enable_rollout for both
        )
    
    # Map winner to result (1.0 for P0 win, 0.0 for P1 win, 0.5 for draw)
    if winner == 0: result = 1.0
    elif winner == 1: result = 0.0
    else: result = 0.5
    
    return result, match_turns


def main():
    parser = argparse.ArgumentParser(description="RabukaSim AI Tournament Runner (Native Rust Engine)")
    parser.add_argument("--sims", type=int, default=128, help="MCTS simulations per move")
    parser.add_argument("--games_per_pair", type=int, default=10, help="Games per deck/agent matchup")
    parser.add_argument("--p0_type", type=str, default="original", choices=["original", "legacy", "simple", "random"], help="Heuristic for P0")
    parser.add_argument("--p1_type", type=str, default="original", choices=["original", "legacy", "simple", "random"], help="Heuristic for P1")
    parser.add_argument("--decks", type=str, nargs="*", help="Specific deck files to use (recursive search in ai/decks if omitted)")
    parser.add_argument("--workers", type=int, default=0, help="Number of worker processes (0=auto)")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--debug", action="store_true", help="Print debug info per action")
    parser.add_argument("--duration", type=float, default=0, help="Tournament duration in seconds (0=limit by games)")
    args = parser.parse_args()

    # 1. Load Data
    db_path = "data/cards_compiled.json"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found. Run compiler first.")
        sys.exit(1)
        
    with open(db_path, "r", encoding="utf-8") as f:
        db_content = f.read()
        db_json = json.loads(db_content)

    # 2. Build Card Map for deck parsing
    card_map = {}
    # Use the keys from the DB as the source of truth for IDs
    for cid, data in db_json.get("member_db", {}).items():
        card_map[data["card_no"]] = (int(cid), "member")
    for cid, data in db_json.get("live_db", {}).items():
        card_map[data["card_no"]] = (int(cid), "live")
    for cid, data in db_json.get("energy_db", {}).items():
        card_map[data["card_no"]] = (int(cid), "energy")

    # 3. Load Decks
    deck_files = []
    if args.decks:
        deck_files = args.decks
    else:
        decks_dir = "ai/decks"
        if os.path.exists(decks_dir):
            for root, _, files in os.walk(decks_dir):
                for f in files:
                    if f.endswith(".txt"):
                        deck_files.append(os.path.join(root, f))
    
    parsed_decks = []
    for i, df in enumerate(deck_files):
        p = parse_deck(df, card_map)
        if p and len(p["members"]) >= 40:
            parsed_decks.append(p)
            if i == 0:
                print(f"Sample Deck ({df}): Members={len(p['members'])}, Energy={len(p['energy'])}, Lives={len(p['lives'])}")
    
    if not parsed_decks:
        print("Error: No valid decks found.")
        sys.exit(1)
        
    print(f"Loaded {len(parsed_decks)} decks.")

    # 4. Map heuristics to IDs (Matches py_bindings.rs)
    h_map = {"original": 0, "legacy": 1, "simple": 2, "random": -1}
    p0_h = h_map[args.p0_type]
    p1_h = h_map[args.p1_type]

    # 5. Build Tasks
    tasks = []
    for i in range(len(parsed_decks)):
        # Every deck vs itself or vs others? 
        # User requested "ai\decks decks", suggesting a tournament over available decks.
        # We'll run mirror matches (Agent A vs Agent B on same decks)
        d = parsed_decks[i]
        
        # If duration is set, we ensure we have a massive pool of tasks to pull from
        count = args.games_per_pair
        if args.duration > 0:
            count = max(count, 10000) # Arbitrary large number
            
        for g in range(count):
            seed = args.seed + i * 100000 + g # Larger seed spacing
            tasks.append((
                args.p0_type, args.p1_type, 
                args.sims, args.sims, 
                p0_h, p1_h, 
                (d, d), seed, args.debug
            ))

    # 6. Run Tournament
    num_workers = args.workers if args.workers > 0 else max(1, cpu_count() - 1)
    print(f"Starting Tournament: {len(tasks)} matches using {num_workers} workers...")
    print(f"Matchup: {args.p0_type} ({args.sims} MCTS) vs {args.p1_type} ({args.sims} MCTS)")
    
    start_time = time.time()
    elo = EloRating()
    elo.init_agent(args.p0_type)
    elo.init_agent(args.p1_type)
    
    p0_wins = 0
    p1_wins = 0
    draws = 0
    turns_history = []

    with Pool(processes=num_workers, initializer=init_worker, initargs=(db_content,)) as pool:
        results = []
        for res, t in pool.imap(run_single_match, tasks, chunksize=1):
            results.append((res, t))
            turns_history.append(t)
            if res == 1.0: p0_wins += 1
            elif res == 0.0: p1_wins += 1
            else: draws += 1
            
            # Since it's a mirror match of agents, we update Elo based on P0 vs P1
            elo.update(args.p0_type, args.p1_type, res)
            
            # Print individual game result
            winner_str = args.p0_type if res == 1.0 else args.p1_type if res == 0.0 else "Draw"
            if not args.duration: # Only print per-game if not in high-speed duration mode
                print(f"Game {len(results)}: Winner={winner_str}, Turns={t}")
            elif len(results) % 100 == 0:
                print(f"Completed {len(results)} games...")

            if args.duration > 0 and time.time() - start_time >= args.duration:
                print(f"\nDuration limit ({args.duration}s) reached. Stopping...")
                break

    elapsed = time.time() - start_time
    
    # 7. Results
    print("\n" + "="*50)
    print("TOURNAMENT RESULTS")
    print("="*50)
    print(f"Total Matches:  {len(results)}")
    print(f"Total Time:     {elapsed:.2f}s ({elapsed/max(1, len(results)):.3f}s/game)")
    print(f"Avg Turns:      {np.mean(turns_history):.1f}")
    
    # Turn Distribution
    print("-" * 50)
    print("TURN DISTRIBUTION:")
    counts = {}
    for t in turns_history:
        counts[t] = counts.get(t, 0) + 1
    for t in sorted(counts.keys()):
        percentage = (counts[t] / len(results) * 100)
        bar = "#" * int(percentage / 2) # Simple visual bar
        print(f"  {t:>2} turns: {counts[t]:>5} games ({percentage:>5.1f}%) {bar}")
    print("-" * 50)
    
    print(f"P0 ({args.p0_type}) Wins: {p0_wins} ({p0_wins/max(1, len(results))*100:.1f}%)")
    print(f"P1 ({args.p1_type}) Wins: {p1_wins} ({p1_wins/max(1, len(results))*100:.1f}%)")
    print(f"Draws:               {draws} ({draws/max(1, len(results))*100:.1f}%)")
    print("-" * 50)
    
    print("\nELO RATINGS:")
    for name in sorted(elo.ratings, key=lambda x: elo.ratings[x], reverse=True):
        print(f"  {name:<12}: {int(elo.ratings[name])}")
    print("=" * 50)


if __name__ == "__main__":
    main()
