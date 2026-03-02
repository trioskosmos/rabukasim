import json
import engine_rust
import os
import sys
import time
import re
import random
import numpy as np
from pathlib import Path

# Add project root for engine imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from engine.game.deck_utils import UnifiedDeckParser

def enrich_label(lbl, player_obj, flattened_db):
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
        base_id = card_cid & 0xFFFFF
        info = flattened_db.get(str(base_id), {})
        return f"{lbl} -> [{info.get('card_id', base_id)}] {info.get('name', 'Unknown')}"
    return lbl

def load_tournament_decks(full_db):
    decks_dir = Path(__file__).parent.parent.parent / "ai" / "decks"
    parser = UnifiedDeckParser(full_db)
    loaded_decks = []
    
    standard_energy_ids = []
    for cid, data in parser.normalized_db.items():
        if data.get("type") == "Energy" or str(cid).startswith("LL-E"):
            standard_energy_ids.append(data.get("card_id"))
            if len(standard_energy_ids) >= 12: break

    for deck_file in decks_dir.glob("*.txt"):
        with open(deck_file, "r", encoding="utf-8") as f:
            content = f.read()
        results = parser.extract_from_content(content)
        if not results: continue
        d = results[0]
        members, lives, energy = [], [], []
        for code in d['main']:
            cdata = parser.resolve_card(code)
            if not cdata: continue
            if cdata.get("type") == "Member": members.append(cdata["card_id"])
            elif cdata.get("type") == "Live": lives.append(cdata["card_id"])
        for code in d['energy']:
            cdata = parser.resolve_card(code)
            if cdata: energy.append(cdata["card_id"])
        
        if len(members) >= 48 and len(lives) >= 12:
            loaded_decks.append({
                "name": deck_file.stem,
                "members": (members + members*4)[:48],
                "lives": (lives + lives*4)[:12],
                "energy": (energy + standard_energy_ids*12)[:12]
            })
    return loaded_decks

def run_audit():
    print("--- MCTS 10s Stability Audit (TERMINAL REWARDS ONLY) ---")
    results = []
    
    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    
    flattened_db = {}
    for db_type in ["member_db", "live_db", "energy_db"]:
        if db_type in full_db:
            flattened_db.update(full_db[db_type])
            
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    tournament_decks = load_tournament_decks(full_db)
    
    d0 = tournament_decks[0] # Using fixed sequence for slightly better repro
    d1 = tournament_decks[1]
    print(f"Using Decks: {d0['name']} vs {d1['name']}")

    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = True

    print("Advancing game to after first Live success, looking for a valid Main Phase choice...")
    max_turns = 100
    while not state.is_terminal() and state.turn < max_turns:
        legal_ids = state.get_legal_action_ids()
        if not legal_ids: 
            state.auto_step(db_engine)
            continue
            
        # Stop condition: After first live success AND specifically in a Main Phase with multiple choices
        p0 = state.get_player(0)
        p1 = state.get_player(1)
        has_success = len(p0.success_lives) > 0 or len(p1.success_lives) > 0
        
        if has_success and state.phase == 5 and len(legal_ids) > 1: # 5 = Main
            print(f"Moment reached at Turn {state.turn}, Phase Main!")
            break
        
        # Quick MCTS to move the game along
        sugg = state.get_mcts_suggestions(32, 0.0, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal)
        action = sugg[0][0] if sugg else legal_ids[0]
        state.step(action)
        state.auto_step(db_engine)

    ph_names = ["MulliganP1", "MulliganP2", "Active", "Energy", "Draw", "Main", "LiveSet", "PerformanceP1", "PerformanceP2", "LiveResult", "Terminal", "Response", "Setup"]
    phase_name = ph_names[state.phase + 1] if -1 <= state.phase <= 11 else f"Phase_{state.phase}"
    print(f"\n--- AUDIT POINT: Turn {state.turn}, Phase {phase_name}, Player {state.current_player} ---")
    results.append(f"Audit at T{state.turn} {phase_name} for Player {state.current_player} (PURE MCTS MODE)")
    
    legal_ids = state.get_legal_action_ids()
    active_player_obj = state.get_player(state.current_player)
    
    results.append("\nLEGAL ACTIONS:")
    for aid in legal_ids:
        lbl = f"({aid}) {enrich_label(state.get_action_label(aid), active_player_obj, flattened_db)}"
        results.append(f"  - {lbl}")

    print(f"\nMonitoring best move stability for 10 seconds (TERMINAL_ONLY REWARDS)...")
    results.append("\nMonitoring best move stability for 10 seconds (TERMINAL_ONLY REWARDS)...")
    
    start_time = time.time()
    current_best_id = -1
    sims = 200 # Faster starting ramp for pure rollouts
    
    try:
        terminal_mode = engine_rust.EvalMode.TerminalOnly
    except AttributeError:
        print("Error: TerminalOnly mode not found in engine_rust. Rebuild might have failed.")
        return

    while time.time() - start_time < 10:
        # PURE ROLLOUT SEARCH
        sugg = state.get_mcts_suggestions(sims, 0.0, engine_rust.SearchHorizon.GameEnd(), terminal_mode)
        if not sugg: 
            sims += 200
            continue
            
        top_move = sugg[0]
        top_id = top_move[0]
        top_score = top_move[1]
        top_visits = top_move[2]
        
        if top_id != current_best_id:
            raw_lbl = state.get_action_label(top_id)
            new_lbl = enrich_label(raw_lbl, active_player_obj, flattened_db)
            msg = f"[{time.time()-start_time:.2f}s] NEW BEST: {new_lbl} (Visits: {top_visits}, Score: {top_score:.3f}, TotalSims: {sims})"
            print(msg)
            results.append(msg)
            current_best_id = top_id
        
        sims = int(sims * 1.3) + 200
        time.sleep(0.1)

    print("\nAudit Complete.")
    with open("mcts_audit_terminal_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    run_audit()
