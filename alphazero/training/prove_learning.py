import torch
import torch.nn.functional as F
import numpy as np
import engine_rust
import json
import random
import time
import sys
from pathlib import Path

# Add project root to sys.path to find alphazero module
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from alphazero.alphanet import AlphaNet

def prove_learning():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # 1. Load DB
    db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)
    
    # 2. Load Model
    model = AlphaNet(num_layers=10, embed_dim=512).to(device)
    checkpoint_path = Path(__file__).parent / "alphanet_latest.pt"
    model.load_state_dict(torch.load(str(checkpoint_path), map_location=device), strict=False)
    model.eval()
    print(f"Loaded model: {checkpoint_path}")
    
    num_envs = 1
    p0_deck = [1] * 48 + [101] * 12
    p1_deck = [2] * 48 + [102] * 12
    energy = [38] * 40
    
    states = []
    for i in range(num_envs):
        s = engine_rust.PyGameState(db)
        s.initialize_game(p0_deck, p1_deck, energy, energy, [], [])
        s.auto_step(db)
        states.append(s)
        
    active_mask = [True] * num_envs
    turns = [0] * num_envs
    winners = [None] * num_envs
    
    print(f"Starting {num_envs} Parallel Self-Play Games...")
    
    # Pre-allocate numpy buffer for speed
    obs_buffer = np.zeros((num_envs, 20500), dtype=np.float32)
    
    step = 0
    while any(active_mask):
        step += 1
        active_indices = [i for i, a in enumerate(active_mask) if a]
        
        t0 = time.time()
        masks = torch.zeros((len(active_indices), model.num_actions), dtype=torch.bool, device=device)
        
        for i, idx in enumerate(active_indices):
            s = states[idx]
            obs_buffer[i] = s.to_alphazero_tensor()
            legal = s.get_legal_action_ids()
            valid = [a for a in legal if a < model.num_actions]
            masks[i, valid] = True
            
        t_obs = time.time() - t0
        
        # Inference
        obs_t = torch.from_numpy(obs_buffer[:len(active_indices)]).to(device)
        with torch.no_grad():
            logits, _ = model(obs_t, mask=masks)
            logits[~masks] = -1e4
            
            # Get Probabilities (Softmax over legal only)
            probs = torch.softmax(logits, dim=1)
            actions = torch.argmax(logits, dim=1).cpu().numpy()
            
        t_inf = time.time() - t0 - t_obs
        
        # Step
        for i, idx in enumerate(active_indices):
            s = states[idx]
            action = int(actions[i])
            conf = probs[i, action].item()
            
            if step <= 25:
                label = s.get_verbose_label(action)
                # Show top 3
                top_v, top_i = torch.topk(probs[i], k=3)
                top_moves = []
                for val, aid in zip(top_v, top_i):
                    if val > 0.001:
                        top_moves.append(f"{s.get_verbose_label(aid.item())[:15]} ({val:.1%})")
                
                print(f"S{step:2d} Ph:{s.phase:2d} P{s.current_player} | Act:{label[:25]} [Conf:{conf:.1%}]", flush=True)
                if len(top_moves) > 1:
                    print(f"   Alt: {', '.join(top_moves[1:])}", flush=True)
            
            s.step(action)
            s.auto_step(db)
            turns[idx] += 1
            if s.is_terminal() or turns[idx] > 500:
                active_mask[idx] = False
                winners[idx] = s.get_winner()
                
        t_step = time.time() - t0 - t_obs - t_inf
        
        if step % 20 == 0:
            print(f"Move {step}: Obs+Conv:{t_obs:.2f}s | Inf:{t_inf:.2f}s | Step:{t_step:.2f}s", flush=True)

    print("\n--- DONE ---")
    for i in range(num_envs):
        res_str = f"P{winners[i]}" if winners[i] >= 0 else "Draw"
        print(f"Game {i+1}: Winner: {res_str}, Turns: {turns[i]}")

if __name__ == "__main__":
    prove_learning()
