import os
import sys
import json
import torch
import numpy as np
import random

# Ensure engine_rust is importable
pwd = os.getcwd()
if pwd not in sys.path:
    sys.path.append(pwd)

import engine_rust
from alphazero.vanilla_net import HighFidelityAlphaNet, VanillaTransformerConfig
from alphazero.training.vanilla_action_codec import (
    ACTION_SPACE, 
    policy_id_to_engine_action, 
    build_legal_policy_mask
)

def load_deck_txt(path, db):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    m_list = []
    e_list = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"): continue
        if " x " in line:
            parts = line.split(" x ")
            card_no = parts[0].strip()
            qty = int(parts[1].strip())
            cid = db.id_by_no(card_no)
            if cid is None: continue
            if cid >= 10000: e_list.extend([cid] * qty)
            else: m_list.extend([cid] * qty)
    return {"initial_deck": m_list, "energy": e_list}

def main():
    root = os.getcwd()
    db_path = os.path.join(root, "data", "cards_vanilla.json")
    ckpt_path = os.path.join(root, "checkpoints", "vanilla_overnight", "best.pt")
    deck_path = os.path.join(root, "ai/decks/muse_cup.txt")

    print(f"Loading DB...")
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    rust_db = engine_rust.PyCardDatabase(db_json)
    deck_data = load_deck_txt(deck_path, rust_db)

    print(f"Loading model (preset: tiny)...")
    config = VanillaTransformerConfig.from_preset("tiny")
    model = HighFidelityAlphaNet(config)
    checkpoint = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    num_games = 50
    model_wins = 0
    draws = 0
    total_turns = 0

    print(f"Starting comparison: Model vs Random ({num_games} games)...")

    for i in range(num_games):
        if i % 10 == 0:
            print(f"  Playing game {i}...")
        # Initialize Game
        state = engine_rust.PyGameState(rust_db)
        seed = 42 + i
        state.initialize_game_with_seed(
            deck_data["initial_deck"], deck_data["initial_deck"],
            deck_data["energy"], deck_data["energy"],
            [], [], seed
        )
        state.silent = True
        
        # Determine roles
        # Game 0-24: P0 is Model, P1 is Random
        # Game 25-49: P0 is Random, P1 is Model
        model_player = 0 if i < (num_games // 2) else 1
        
        while not state.is_terminal() and state.turn < 25:
            legal_engine_ids = state.get_legal_action_ids()
            if not legal_engine_ids:
                state.auto_step(rust_db)
                continue
            
            curr_player = state.current_player
            if curr_player == model_player:
                # Model Turn
                obs = state.to_vanilla_tensor()
                obs_t = torch.from_numpy(obs).unsqueeze(0)
                mask = build_legal_policy_mask(state, curr_player, deck_data["initial_deck"], state.phase, legal_engine_ids)
                mask_t = torch.from_numpy(mask).unsqueeze(0)
                
                with torch.no_grad():
                    logits, _ = model(obs_t, mask=mask_t)
                    probs = torch.softmax(logits, dim=1).squeeze(0).numpy()
                
                # Filter strictly by legal engine actions mapping
                legal_probs = []
                legal_actions = []
                for pid in np.where(mask > 0)[0]:
                    eng_id = policy_id_to_engine_action(state, curr_player, pid, state.phase, deck_data["initial_deck"])
                    if eng_id is not None and eng_id in legal_engine_ids:
                        legal_probs.append(probs[pid])
                        legal_actions.append(eng_id)
                
                if not legal_actions:
                    action = random.choice(list(legal_engine_ids))
                else:
                    action = legal_actions[np.argmax(legal_probs)]
            else:
                # Random Turn
                action = random.choice(list(legal_engine_ids))
            
            state.step(int(action))
            state.auto_step(rust_db)
            
        total_turns += state.turn
        winner = state.get_winner()
        if winner == model_player:
            model_wins += 1
        elif winner == -1:
            draws += 1 # Or handle as tie/loss

    print(f"\nResults over {num_games} games:")
    print(f"  Model Wins : {model_wins} ({model_wins/num_games*100:.1f}%)")
    print(f"  Random Wins: {num_games - model_wins - draws}")
    print(f"  Draws      : {draws}")
    print(f"  Avg Turns  : {total_turns/num_games:.1f}")

if __name__ == "__main__":
    main()
