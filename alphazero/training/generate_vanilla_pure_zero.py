import json
import engine_rust
import os
import sys
import torch
import numpy as np
import random
import time
from tqdm import tqdm
from pathlib import Path

# Add project root for engine imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from engine.game.deck_utils import UnifiedDeckParser

# AlphaZero configuration
ACTION_SPACE = 128

def load_tournament_decks(db_json):
    decks_dir = Path(__file__).parent.parent.parent / "ai" / "decks"
    parser = UnifiedDeckParser(db_json)
    loaded_decks = []
    
    standard_energy_ids = []
    for cid, data in parser.normalized_db.items():
        if data.get("type") == "Energy" or cid.startswith("LL-E"):
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

def map_engine_to_vanilla(state_json, engine_id):
    """
    Maps engine action ID to 128-dim vanilla space.
    0: Pass
    1-6: Mulligan
    7: Confirm
    8-67: Play Member #N (Deck Index)
    68-127: Set Live #N (Deck Index)
    """
    if engine_id == 0: return 0
    if 300 <= engine_id < 306: return 1 + (engine_id - 300)
    if engine_id == 11000: return 7
    
    p_idx = state_json['current_player']
    p_data = state_json['players'][p_idx]
    initial_deck = p_data['initial_deck']
    
    # Play Member (Hand)
    if 1000 <= engine_id < 1012:
        hand_idx = engine_id - 1000
        if hand_idx < len(p_data['hand']):
            card_id = p_data['hand'][hand_idx]
            try:
                deck_idx = initial_deck.index(card_id)
                return 8 + deck_idx
            except ValueError:
                return -1
                
    # Set Live (Selection/Slot)
    # Note: In vanilla training, we simplify 'Set Live' to 'Execute Live Synergies'
    if 400 <= engine_id < 403:
        for cid in p_data['hand']:
            if cid > 10000: # Typical ID range for Lives
                 try:
                    deck_idx = initial_deck.index(cid)
                    return 68 + deck_idx
                 except ValueError:
                    continue
        return 68 

    # Select Success Live (Pick which succeeding card moves to success pile)
    # Mapping to 0 (Pass/Done) as requested for minimal action space.
    # Safe because Action 0 is HIDDEN by the engine during mandatory selection.
    if 600 <= engine_id < 603:
        return 0

    return -1

def strip_abilities(db_json):
    """
    Strips all abilities to create a 'Vanilla' environment.
    This ensures that automatic triggers don't happen in the engine,
    preventing state changes that the AI can't explain.
    """
    for cat in ["member_db", "live_db"]:
        for cid, data in db_json.get(cat, {}).items():
            # 1. Clear all abilities (Robustly silences all effects)
            data["abilities"] = []
            
            # 2. Clear Ability Flags (AI heuristic awareness)
            data["ability_flags"] = 0
            
            # 3. Simplify Synergy Flags
            # We keep only CENTER flag (bit 0) if present
            if "synergy_flags" in data:
                data["synergy_flags"] &= 1
                
    return db_json

import argparse

# ... (imports stay same, but I'll add argparse logic to the end)

def generate_vanilla_trajectories(num_games=10, sims_per_move=128, output_file="vanilla_trajectories.npz", mirror=False, verbose=False):
    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    
    # Apply robust stripping
    stripped_db = strip_abilities(full_db)
    db_engine = engine_rust.PyCardDatabase(json.dumps(stripped_db))
    tournament_decks = load_tournament_decks(stripped_db)
    
    dataset = []

    start_generation = time.time()
    for g_idx in tqdm(range(num_games), desc="Vanilla Self-Play", disable=verbose):
        # Mirror match logic
        if mirror:
            d0 = d1 = random.choice(tournament_decks)
            seed = random.getrandbits(64)
            state = engine_rust.PyGameState(db_engine)
            state.silent = True
            state.initialize_game_with_seed(
                d0["members"] + d0["lives"], d1["members"] + d1["lives"], 
                d0["energy"], d1["energy"], 
                [], [], seed
            )
        else:
            d0 = random.choice(tournament_decks)
            d1 = random.choice(tournament_decks)
            state = engine_rust.PyGameState(db_engine)
            state.silent = True
            state.initialize_game(
                d0["members"] + d0["lives"], d1["members"] + d1["lives"], 
                d0["energy"], d1["energy"], 
                [], []
            )
        
        game_history = [] 

        while not state.is_terminal() and state.turn < 100:
            legal_ids = state.get_legal_action_ids()
            if not legal_ids: break
            
            suggestions = state.get_mcts_suggestions(sims_per_move, 1.41, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly)
            
            policy_target = np.zeros(ACTION_SPACE, dtype=np.float32)
            total_visits = sum(s[2] for s in suggestions)
            
            state_json = json.loads(state.to_json())
            
            if total_visits > 0:
                for engine_id, h_score, visits in suggestions:
                    vanilla_id = map_engine_to_vanilla(state_json, engine_id)
                    if 0 <= vanilla_id < ACTION_SPACE:
                        policy_target[vanilla_id] += visits / total_visits
            
            p_sum = policy_target.sum()
            if p_sum > 0: policy_target /= p_sum

            obs = state.to_vanilla_tensor()
            
            mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
            for aid in legal_ids:
                vid = map_engine_to_vanilla(state_json, aid)
                if 0 <= vid < ACTION_SPACE:
                    mask[vid] = True

            game_history.append({
                "obs": obs,
                "policy": policy_target.copy(),
                "player": state.current_player,
                "mask": mask
            })

            actions = [s[0] for s in suggestions]
            counts = [s[2] for s in suggestions]
            
            if not actions:
                action = random.choice(legal_ids)
            else:
                action = random.choices(actions, weights=counts, k=1)[0]
            
            state.step(action)
            state.auto_step(db_engine)

        winner = state.get_winner()
        
        if verbose:
            p0 = state.get_player(0)
            p1 = state.get_player(1)
            perf_history = json.loads(state.performance_history)
            
            # Group judgements by turn and track running scores
            judgements_by_turn = {}
            running_scores = {0: 0, 1: 0}
            
            for entry in perf_history:
                t_num = entry.get('turn', 0)
                if t_num not in judgements_by_turn:
                    judgements_by_turn[t_num] = []
                
                p_id = entry.get('player_id')
                lives = entry.get('lives', [])
                
                card_results = []
                turn_points = 0
                for l in lives:
                    name = l.get('name', 'Unknown')
                    is_passed = l.get('passed', False)
                    passed_str = "OK" if is_passed else "FAIL"
                    required = sum(l.get('required', []))
                    filled = sum(l.get('filled', []))
                    card_results.append(f"[{name}: {filled}/{required} {passed_str}]")
                    if is_passed:
                        turn_points += 1
                
                running_scores[p_id] += turn_points
                
                if card_results:
                    judgements_by_turn[t_num].append({
                        "p_id": p_id,
                        "text": f"P{p_id}: {' '.join(card_results)}",
                        "score_after": f"P0:{running_scores[0]} P1:{running_scores[1]}"
                    })

            print(f"Game {g_idx+1:3d} | Winner: P{winner} | Final Turn: {state.turn:2d} | Final Scores: P0:{p0.score} P1:{p1.score}", flush=True)
            for t_num in sorted(judgements_by_turn.keys()):
                for item in judgements_by_turn[t_num]:
                    print(f"  Turn {t_num:2d} | {item['text']} | Score: {item['score_after']}", flush=True)

        for transition in game_history:
            outcome = 0.5
            if winner != -1:
                outcome = 1.0 if transition["player"] == winner else 0.0
            
            dataset.append({
                "obs": transition["obs"],
                "policy": transition["policy"],
                "mask": transition["mask"],
                "value": outcome
            })

    end_generation = time.time()
    total_time = end_generation - start_generation
    games_per_sec = num_games / total_time if total_time > 0 else 0
    print(f"Generation throughput: {games_per_sec:.2f} games/sec", flush=True)

    # Save
    obs_batch = np.array([t["obs"] for t in dataset], dtype=np.float32)
    policy_batch = np.array([t["policy"] for t in dataset], dtype=np.float32)
    mask_batch = np.array([t["mask"] for t in dataset], dtype=np.bool_)
    value_batch = np.array([t["value"] for t in dataset], dtype=np.float32)

    print(f"Saving {len(dataset)} Vanilla transitions to {output_file}...")
    np.savez_compressed(output_file, obs=obs_batch, policy=policy_batch, mask=mask_batch, value=value_batch)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_games", type=int, default=10)
    parser.add_argument("--sims_per_move", type=int, default=128)
    parser.add_argument("--output_file", type=str, default="vanilla_trajectories.npz")
    parser.add_argument("--mirror", action="store_true", help="Force identical decks and shuffles")
    parser.add_argument("--verbose", action="store_true", help="Print game summaries")
    args = parser.parse_args()
    
    generate_vanilla_trajectories(
        num_games=args.num_games, 
        sims_per_move=args.sims_per_move, 
        output_file=args.output_file,
        mirror=args.mirror,
        verbose=args.verbose
    )
