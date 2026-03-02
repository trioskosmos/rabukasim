import json
import engine_rust
import os
import sys
import torch
import numpy as np
import random
from tqdm import tqdm
from pathlib import Path

# Add project root for engine imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from engine.game.deck_utils import UnifiedDeckParser
from engine.game.data_loader import CardDataLoader
from backend.rust_serializer import RustGameStateSerializer

# AlphaZero configuration
ACTION_SPACE = 16384

def load_tournament_decks(db_json):
    decks_dir = Path(__file__).parent.parent.parent / "ai" / "decks"
    # UnifiedDeckParser needs the raw dict DB
    parser = UnifiedDeckParser(db_json)
    
    loaded_decks = []
    
    # Standard energy if missing
    standard_energy_ids = []
    # Search in flattened DB (which we injected types into via parser)
    for cid, data in parser.normalized_db.items():
        if data.get("type") == "Energy" or cid.startswith("LL-E"):
            standard_energy_ids.append(data.get("card_id"))
            if len(standard_energy_ids) >= 12: break

    for deck_file in decks_dir.glob("*.txt"):
        with open(deck_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        results = parser.extract_from_content(content)
        if not results:
            continue
            
        d = results[0] # Take first deck
        
        members = []
        lives = []
        energy = []

        # Categorize cards using the parser's categorization
        # d['main'] and d['energy'] contain codes
        for code in d['main']:
            cdata = parser.resolve_card(code)
            if not cdata: continue
            
            ctype = cdata.get("type")
            if ctype == "Member":
                members.append(cdata["card_id"])
            elif ctype == "Live":
                lives.append(cdata["card_id"])
        
        for code in d['energy']:
            cdata = parser.resolve_card(code)
            if cdata:
                energy.append(cdata["card_id"])

        # Enforce 48 members, 12 lives, 12 energy
        if len(members) >= 48 and len(lives) >= 12:
            final_members = (members + members*4)[:48] # Fallback repetition if needed
            final_lives = (lives + lives*4)[:12]
            
            if len(energy) < 12:
                final_energy = (energy + standard_energy_ids * 12)[:12]
            else:
                final_energy = energy[:12]
            
            loaded_decks.append({
                "name": deck_file.stem,
                "members": final_members,
                "lives": final_lives,
                "energy": final_energy
            })
        else:
            print(f"Skipping {deck_file.name}: Members={len(members)}, Lives={len(lives)}")
            
    return loaded_decks

def generate_trajectories(num_games=10, sims_per_move=100, output_file="trajectories.json"):
    # Load raw card database for parser
    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    
    # Flatten the DB for UnifiedDeckParser
    flattened_db = {}
    for db_type in ["member_db", "live_db", "energy_db"]:
        if db_type in full_db:
            flattened_db.update(full_db[db_type])
    
    # Create engine DB
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))

    # Initialize Game State Serializer for detailed logging
    loader = CardDataLoader(db_path)
    m_db, l_db, e_db = loader.load()
    serializer = RustGameStateSerializer(m_db, l_db, e_db)

    # Load tournament decks (using the full DB which UnifiedDeckParser will flatten)
    tournament_decks = load_tournament_decks(full_db)
    
    # Fallback if nothing found
    if not tournament_decks:
        print("WARNING: No valid tournament decks found. Using 103/2001 fallback.")
        tournament_decks = [{
            "name": "Fallback_103",
            "members": [103] * 48,
            "lives": [2001] * 12,
            "energy": [1001] * 12 # LL-E-001 common
        }]
    
    print(f"Loaded {len(tournament_decks)} tournament decks: {[d['name'] for d in tournament_decks]}")

    dataset = []

    for g_idx in tqdm(range(num_games), desc="Self-Play Games"):
        d0 = random.choice(tournament_decks)
        d1 = random.choice(tournament_decks)
        
        # Launcher Pattern: Merge members and lives into main deck, pass empty initial success lives
        p0_main = d0["members"] + d0["lives"]
        p1_main = d1["members"] + d1["lives"]
        
        state = engine_rust.PyGameState(db_engine)
        state.initialize_game(
            p0_main, p1_main, 
            d0["energy"], d1["energy"], 
            [], [] # Initial success lives (empty for new game)
        )
        state.silent = True
        
        game_history = [] 
        log_file = None
        if g_idx == 0:
            log_file = open("alphazero_game_log.txt", "w", encoding="utf-8")
            log_file.write(f"Starting Game {g_idx} ({d0['name']} vs {d1['name']})\n")

        move_count = 0
        while not state.is_terminal() and state.turn < 100:
            legal_ids = state.get_legal_action_ids()
            if not legal_ids:
                break
            
            # Create legal mask
            legal_mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
            for aid in legal_ids:
                if 0 <= aid < ACTION_SPACE:
                    legal_mask[aid] = True
            
            # 1. Run MCTS
            suggestions = state.get_mcts_suggestions(sims_per_move, 1.41, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal)
            
            # Create policy target
            policy_target = np.zeros(ACTION_SPACE, dtype=np.float32)
            total_visits = sum(s[2] for s in suggestions)
            
            if total_visits > 0:
                for action_id, h_score, visits in suggestions:
                    if 0 <= action_id < ACTION_SPACE:
                        policy_target[action_id] = visits / total_visits
            
            # Record transition
            obs = state.to_alphazero_tensor()
            game_history.append({
                "obs": obs,
                "policy": policy_target.tolist(),
                "mask": legal_mask.tolist(), # Store as list for now, convert to array later
                "player": state.current_player
            })

            # 2. Pick action using temperature
            actions = [s[0] for s in suggestions]
            counts = [s[2] for s in suggestions]
            
            if not actions:
                action = random.choice(legal_ids)
            else:
                # AlphaZero: τ=1 (proportional) for early game, τ→0 (argmax) for late game
                # Using 30 turns (roughly 15 rounds) for exploration
                if state.turn < 30:
                    action = random.choices(actions, weights=counts, k=1)[0]
                else:
                    action = actions[np.argmax(counts)]
            
            move_count += 1            
            if log_file:
                p0 = state.get_player(0)
                p1 = state.get_player(1)
                ph = state.phase
                ph_names = ["MulliganP1", "MulliganP2", "Active", "Energy", "Draw", "Main", "LiveSet", "PerformanceP1", "PerformanceP2", "LiveResult", "Terminal", "Response", "Setup"]
                phase_name = ph_names[ph + 1] if -1 <= ph <= 11 else f"Phase_{ph}"
                
                # Get human-readable action label from engine
                action_label = state.get_action_label(action)
                
                def enrich(player_obj, lbl):
                    import re
                    card_cid = -1
                    match_hand = re.search(r"Hand(?: Index|\[)(\d+)", lbl)
                    if match_hand:
                        idx = int(match_hand.group(1))
                        if idx < len(player_obj.hand): card_cid = player_obj.hand[idx]
                        
                    match_stage = re.search(r"Member Slot (\d+)", lbl)
                    if match_stage:
                        idx = int(match_stage.group(1))
                        if idx < len(player_obj.stage): card_cid = player_obj.stage[idx]
                        
                    match_discard = re.search(r"Discard(?: Index)? (\d+)", lbl)
                    if match_discard:
                        idx = int(match_discard.group(1))
                        if idx < len(player_obj.discard): card_cid = player_obj.discard[idx]

                    if card_cid != -1:
                        info = flattened_db.get(str(card_cid), {})
                        return f"{lbl} -> [{info.get('card_id', card_cid)}] {info.get('name', 'Unknown')}"
                    return lbl

                active_p = p0 if state.current_player == 0 else p1
                action_label = enrich(active_p, action_label)
                
                # Format: [T1] [Main] P0 (S:0, L:0) -> Play Hand[1] to Slot 0
                stats = f"S:{p0.score}, L:{len(p0.success_lives)}" if state.current_player == 0 else f"S:{p1.score}, L:{len(p1.success_lives)}"
                
                # List all legal actions first
                log_file.write(f"\n[T{state.turn}] [{phase_name}] P{state.current_player} ({stats}) LEGAL ACTIONS:\n")
                for aid in legal_ids:
                    lbl = state.get_action_label(aid)
                    lbl = enrich(active_p, lbl)
                    # If this action was suggested by MCTS, show its visits and score
                    visits = 0
                    score = 0.0
                    for s_id, s_score, s_visits in suggestions:
                        if s_id == aid:
                            visits = s_visits
                            score = s_score
                            break
                    if visits > 0:
                        log_file.write(f"  - {lbl} [Visits: {visits}, Score: {score:.3f}]\n")
                    else:
                        log_file.write(f"  - {lbl}\n")
                        
                log_file.write(f"\n>> CHOSE: {action_label}\n")

            # 3. Step
            state.step(action)
            state.auto_step(db_engine)

        # 4. Game Outcome
        winner = state.get_winner()
        if log_file:
            log_file.write(f"\n=== GAME OVER ===\nWinner: {winner}\n\n")
            
            # Dump the rich frontend-style rule log straight from the engine
            log_file.write("=== FRONTEND-STYLE RULE LOG ===\n")
            engine_log = state.rule_log
            if engine_log:
                for entry in engine_log:
                    log_file.write(f"{entry}\n")
            else:
                log_file.write("No rule log entries generated by engine.\n")
                
            log_file.close()
        
        # Export full state dump for the first game (Bug Report level detail)
        if g_idx == 0:
            try:
                report = serializer.serialize_state(state)
                with open("lovecasim_report.json", "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                # Print to stdout so it shows up in the user's terminal summary
                print(f"\n[Dump] Exported full game report to lovecasim_report.json")
            except Exception as e:
                print(f"\n[Dump] Failed to export game report: {e}")
        
        for transition in game_history:
            outcome = 0.0
            if winner != -1:
                outcome = 1.0 if transition["player"] == winner else -1.0
            
            dataset.append({
                "obs": transition["obs"],
                "policy": transition["policy"],
                "mask": transition["mask"],
                "value": outcome
            })

    # Convert to numpy arrays for efficient storage
    obs_batch = np.array([t["obs"] for t in dataset], dtype=np.float32)
    policy_batch = np.array([t["policy"] for t in dataset], dtype=np.float32)
    mask_batch = np.array([t["mask"] for t in dataset], dtype=np.bool_)
    value_batch = np.array([t["value"] for t in dataset], dtype=np.float32)

    # Save dataset as Compressed NPZ
    output_path = output_file.replace(".json", ".npz")
    print(f"Saving {len(dataset)} transitions to {output_path}...")
    np.savez_compressed(output_path, 
                       obs=obs_batch, 
                       policy=policy_batch, 
                       mask=mask_batch, 
                       value=value_batch)

if __name__ == "__main__":
    generate_trajectories(num_games=20, sims_per_move=64)
