import torch
import numpy as np
import json
import os
import sys

# Robust path detection for the Rust engine
base_dir = os.path.dirname(__file__)
search_paths = [
    os.path.join(base_dir, "..", "engine_rust_src", "target", "dev-release"),
    os.path.join(base_dir, "..", "engine_rust_src", "target", "debug"),
    os.path.join(base_dir, "..", "engine_rust_src", "target", "release"),
]
for p in search_paths:
    p_abs = os.path.abspath(p)
    if os.path.exists(os.path.join(p_abs, "engine_rust.pyd")) or os.path.exists(os.path.join(p_abs, "engine_rust.dll")):
        if p_abs not in sys.path:
            sys.path.insert(0, p_abs)
            break

import engine_rust
import random
import time
import argparse
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="AlphaZero v1 Benchmark & Stress Test")
    parser.add_argument("--checkpoint", type=str, default="alphazero/v1.pt", help="Path to model checkpoint")
    parser.add_argument("--stress", action="store_true", help="Run in stress test mode")
    parser.add_argument("--duration", type=int, default=60, help="Duration of stress test in seconds")
    parser.add_argument("--sims", type=int, default=128, help="MCTS simulations per move")
    return parser.parse_args()

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphazero.alphanet import AlphaNet, NUM_ACTIONS
# from alphazero.training.overnight_pure_zero import load_tournament_decks 
# Copied here to avoid import nightmare after reorganization
def load_tournament_decks(full_db):
    from engine.game.deck_utils import UnifiedDeckParser
    decks_dir = Path(__file__).parent.parent / "ai" / "decks"
    parser = UnifiedDeckParser(full_db)
    loaded_decks = []
    standard_energy_ids = [38, 39, 40, 41, 42] * 4 
    for deck_file in decks_dir.glob("*.txt"):
        with open(deck_file, "r", encoding="utf-8") as f:
            content = f.read()
        results = parser.extract_from_content(content)
        if not results: continue
        d = results[0]
        m, l, e = [], [], []
        for code in d['main']:
            cdata = parser.resolve_card(code)
            if not cdata: continue
            if cdata.get("type") == "Member": m.append(cdata["card_id"])
            elif cdata.get("type") == "Live": l.append(cdata["card_id"])
        for code in d['energy']:
            cdata = parser.resolve_card(code)
            if cdata: e.append(cdata["card_id"])
        if len(m) >= 30:
            loaded_decks.append({
                "name": deck_file.stem,
                "members": (m + m*4)[:48],
                "lives": (l + l*4)[:12],
                "energy": (e + standard_energy_ids*12)[:12]
            })
    return loaded_decks
import engine_rust

def get_player_move(player_type, state, db, model, device, sims=128):
    # print(f"    DEBUG: Entering get_player_move for {player_type}...", flush=True) # Too noisy
    legal_ids = state.get_legal_action_ids()
    if not legal_ids: 
        print(f"    DEBUG: No legal actions for {player_type}! Phase: {state.phase}", flush=True)
        # Deep diagnostic for the "No legal actions" bug
        pi = state.get_interaction()
        if pi:
            print(f"      [DEBUG] Interaction: type={pi.choice_type}, filter={pi.filter_attr}, ctx={pi.ctx}", flush=True)
            print(f"      [DEBUG] Pending Card: {state.pending_card_id}, AbIdx: {state.pending_ab_idx}", flush=True)
        return None

    if player_type == "Heuristic_Greedy":
        move = state.get_greedy_action(db, state.current_player, 0, None)
        # print(f"    DEBUG: Heuristic_Greedy chose {move}", flush=True)
        return move
    
    elif player_type == "Model_Greedy":
        obs_numpy = np.array(state.to_alphazero_tensor()).astype(np.float32)
        obs = torch.from_numpy(obs_numpy).unsqueeze(0).to(device)
        mask = torch.zeros((1, model.num_actions), dtype=torch.bool).to(device)
        for aid in legal_ids:
            if aid < model.num_actions:
                mask[0, aid] = True
        with torch.no_grad():
            policy_logits, _ = model(obs, mask=mask)
            policy = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]
        # Create a full-size policy array and fill it with very low values
        full_policy = np.full((NUM_ACTIONS,), -1.0, dtype=np.float32)
        full_policy[:model.num_actions] = policy
        move = int(np.argmax(full_policy))
        # print(f"    DEBUG: Model_Greedy chose {move}", flush=True)
        return move

    elif player_type == "Heuristic_MCTS":
        res = state.get_mcts_suggestions(sims, 0.0, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal)
        move = res[0][0] if res else random.choice(legal_ids)
        # print(f"    DEBUG: Heuristic_MCTS chose {move}", flush=True)
        return move

    elif player_type == "Model_MCTS":
        res = state.get_mcts_suggestions(sims, 0.0, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly)
        move = res[0][0] if res else random.choice(legal_ids)
        # print(f"    DEBUG: Model_MCTS chose {move}", flush=True)
        return move

def get_state_str(state):
    try:
        lines = []
        lines.append(f"--- Board State Snapshot ---")
        lines.append(f"Turn: {state.turn} | Phase: {state.phase} | Current Player: {state.current_player}")
        for i in range(2):
            p = state.get_player(i)
            # Use basic list conversion if these are numpy/special arrays
            hand = list(p.hand)
            stage = list(p.stage)
            energy = list(p.energy_zone)
            tapped_m = list(p.tapped_members)
            tapped_e = list(p.tapped_energy)
            
            lines.append(f"Player {i}: Score {p.score} | Success Lives {list(p.success_lives)}")
            lines.append(f"  Hand ({len(hand)}): {hand}")
            lines.append(f"  Stage: {stage} | Tapped: {tapped_m}")
            lines.append(f"  Energy Zone ({len(energy)}): {energy} | Tapped: {tapped_e}")
            lines.append(f"  Deck: {p.deck_count} | Energy Deck: {p.energy_deck_count}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error dumping state: {e}"

def play_match(p0_type, p1_type, decks, db_engine, model, device, sims=128):
    deck = random.choice(decks)
    d0 = deck
    d1 = deck
    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"]+d0["lives"], d1["members"]+d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = True
    
    action_history = []
    step_count = 0
    turn_steps = 0
    last_turn = state.turn
    
    while not state.is_terminal() and state.turn < 120 and step_count < 1000:
        if state.turn != last_turn:
            turn_steps = 0
            last_turn = state.turn
        
        p_type = p0_type if state.current_player == 0 else p1_type
        
        # Capture state before move
        legal_ids = state.get_legal_action_ids()
        current_phase = state.phase
        
        # Unsilence if this turn is taking too long
        if turn_steps >= 100:
            if state.silent:
                print(f"    [INFO] Turn {state.turn} reached 100 steps. Unsilencing engine for trace...", flush=True)
                state.silent = False
        
        move = get_player_move(p_type, state, db_engine, model, device, sims=sims)
        if move is None: 
            break
            
        action_label = state.get_verbose_label(move)
        legal_labels = [f"{aid}:{state.get_verbose_label(aid)}" for aid in legal_ids]
        
        phase_name = str(state.phase)
        if state.phase == 0: phase_name = "Main"
        elif state.phase == 1: phase_name = "Mulligan"
        elif state.phase == 2: phase_name = "LiveSet"
        elif state.phase == 3: phase_name = "SelectMode"
        elif state.phase == 4: phase_name = "SelectColor"
        elif state.phase == 5: phase_name = "SelectStageSlot"
        elif state.phase == 6: phase_name = "SelectMember"
        elif state.phase == 7: phase_name = "SelectChoice"
        
        action_history.append(f"Step {step_count} (T-Step {turn_steps}) | Turn {state.turn} | Phase {phase_name} ({state.phase}) | P{state.current_player} ({p_type}) | Move {move}: {action_label} | Legals: {legal_labels}")
        
        state.step(move)
        state.auto_step(db_engine)
        step_count += 1
        turn_steps += 1
        
        if step_count % 100 == 0:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    print(f"    DEBUG: Match finished. step_count={step_count}, turn_steps={turn_steps}, turn={state.turn}", flush=True)
    # Verbose logging for long turns or long games
    if step_count >= 1 or turn_steps >= 1:
        log_dir = Path("alphazero/logs/loops").resolve()
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        log_file = log_dir / f"loop_{p0_type}_vs_{p1_type}_t{state.turn}_{timestamp}.txt"
        print(f"    DEBUG: Attempting to write log to {log_file}", flush=True)
        
        state_snapshot = get_state_str(state)
        
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Long Game/Turn detected: {p0_type} vs {p1_type}\n")
            f.write(f"Total Steps: {step_count} | Turn Steps: {turn_steps} | Final Turn: {state.turn}\n")
            f.write("-" * 40 + "\n")
            f.write(state_snapshot + "\n")
            f.write("-" * 40 + "\n")
            f.write("ACTION HISTORY:\n")
            f.write("\n".join(action_history))
            f.write("\n\n" + "="*40 + "\n ENGINE RULE LOG \n" + "="*40 + "\n")
            f.write("\n".join(state.rule_log))
            f.write("\n\n" + "="*40 + "\n ENGINE TURN HISTORY \n" + "="*40 + "\n")
            f.write("\n".join(state.turn_history))
        print(f"    [LOGGED] Game written to {log_file}", flush=True)
        
    if step_count >= 1000:
        print(f"    WARNING: Match reached step limit (1000) at turn {state.turn}. Force terminating.")
    
    winner = state.get_winner()
    return winner, state.turn

def run_stress_test(db_engine, decks, model, device, duration_secs, sims):
    print(f"\n--- STRESS TEST STARTING (Duration: {duration_secs}s, MCTS Sims: {sims}) ---", flush=True)
    start_time = time.time()
    games_completed = 0
    stalls = 0
    scenarios = [
        ("Model_MCTS", "Heuristic_MCTS"),
        ("Heuristic_MCTS", "Model_MCTS"),
    ]
    
    while time.time() - start_time < duration_secs:
        p0, p1 = random.choice(scenarios)
        print(f"  Stress Game {games_completed+1}: {p0} vs {p1}...", flush=True)
        winner, turns = play_match(p0, p1, decks, db_engine, model, device, sims=sims)
        if winner == -1 and turns < 100: # -1 usually means softlock or terminal without winner? Actually engine uses -1 for draws/stalls
             stalls += 1
             print(f"    [ALERT] STALL DETECTED in game {games_completed+1}!", flush=True)
        games_completed += 1
        
    elapsed = time.time() - start_time
    print(f"\n--- STRESS TEST COMPLETED ---")
    print(f"Games Played: {games_completed}")
    print(f"Stalls Detected: {stalls}")
    print(f"Elapsed Time: {elapsed:.1f}s")
    if stalls == 0:
        print("RESULT: PASS - No stalls detected under high load.")
    else:
        print(f"RESULT: FAIL - {stalls} stalls detected.")

def run_benchmark(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Load Model using the robust helper
    from alphazero.alphanet import load_model
    checkpoint = args.checkpoint
    
    if not os.path.exists(checkpoint):
        print(f"ERROR: Checkpoint {checkpoint} not found!")
        return
            
    print(f"Loading model from {checkpoint}...")
    try:
        model = load_model(checkpoint, device=device)
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    print("Model loaded successfully.")

    # Load Data
    print("Loading cards_compiled.json...")
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        full_db = json.load(f)
    
    print("Initializing engine database...")
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    
    print("Loading tournament decks...")
    decks = load_tournament_decks(full_db)
    print(f"Loaded {len(decks)} decks.")

    if args.stress:
        run_stress_test(db_engine, decks, model, device, args.duration, args.sims)
        return

    # Scenarios per User Request
    scenarios = [
        ("GREEDY: Model vs Heuristic", "Model_Greedy", "Heuristic_Greedy"),
        ("GREEDY: Heuristic vs Model", "Heuristic_Greedy", "Model_Greedy"),
        ("MCTS 128: Model vs Heuristic", "Model_MCTS", "Heuristic_MCTS"),
        ("MCTS 128: Heuristic vs Model", "Heuristic_MCTS", "Model_MCTS"),
    ]

    games_per_scenario = 10
    print(f"\nStarting Tournament ({games_per_scenario} games per scenario)...")
    
    table_rows = []

    for s_idx, (label, p0_type, p1_type) in enumerate(scenarios):
        print(f"\n--- Scenario {s_idx+1}/{len(scenarios)}: {label} ---", flush=True)
        p0_wins = 0
        p1_wins = 0
        draws = 0
        turns_hist = []
        
        start_time = time.time()
        for i in range(games_per_scenario):
            print(f"  Starting Game {i+1}...", flush=True)
            try:
                winner, turns = play_match(p0_type, p1_type, decks, db_engine, model, device, sims=args.sims)
                if winner == 0: p0_wins += 1
                elif winner == 1: p1_wins += 1
                else: draws += 1
                turns_hist.append(turns)
                print(f"  Game {i+1}/{games_per_scenario} DONE. Result: {winner}, Turns: {turns}. Stats: ({p0_wins}-{p1_wins}-{draws})", flush=True)
            except Exception as e:
                print(f"\nFATAL ERROR in game {i+1}: {e}", flush=True)
                break
        
        elapsed = time.time() - start_time
        wr_p0 = (p0_wins / games_per_scenario) * 100
        wr_p1 = (p1_wins / games_per_scenario) * 100
        avg_turns = sum(turns_hist) / len(turns_hist) if turns_hist else 0
        speed = games_per_scenario/elapsed if elapsed > 0 else 0
        table_rows.append(f"| {label} | {avg_turns:.1f} | {wr_p0:.1f}% | {wr_p1:.1f}% | {speed:.2f} |")

    print("\n### Benchmark Results: v1.pt vs Original Heuristic")
    print("| Matchup | Avg Turns | P0 Win Rate | P1 Win Rate | Speed (g/s) |")
    print("|---|---|---|---|---|")
    for row in table_rows: print(row)

if __name__ == "__main__":
    args = parse_args()
    run_benchmark(args)
