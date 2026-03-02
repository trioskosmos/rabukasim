import torch
import numpy as np
import random
import time
import os
import json
import sys
from pathlib import Path
import collections
import concurrent.futures

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

# Robust path detection for the Rust engine
search_paths = [
    root_dir / "engine_rust_src" / "target" / "dev-release",
    root_dir / "engine_rust_src" / "target" / "debug",
    root_dir / "engine_rust_src" / "target" / "release",
]
for p in search_paths:
    if (p / "engine_rust.pyd").exists() or (p / "engine_rust.dll").exists():
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
            break

from alphazero.alphanet import AlphaNet
import torch.nn.functional as F
import engine_rust
from engine.game.deck_utils import UnifiedDeckParser

# ============================================================
# CONFIGURATION (v8 — Relational Transformer + Action Branching)
# ============================================================
NUM_ITERATIONS = 1000000

# --- Self-Play ---
GAMES_PER_ITER = 48         
SIMS_PER_MOVE = 128         
SRR = 8.0                   # Sample Reuse Ratio (How many times each move is seen)

# --- Training (The "Smarter Parallel" Mode) ---
TRAIN_STEPS_PER_ITER = 800  
BATCH_SIZE = 1024         
LR = 0.0003                 # Lowered for larger model stability
ENTROPY_LAMBDA = 1e-3       
DIRICHLET_ALPHA = 0.3       # For exploration noise
DIRICHLET_EPS = 0.25        

# --- Buffer ---
MAX_BUFFER_SIZE = 1000000   # 1,000,000 moves (Needs substantial RAM, ~6GB compressed)

# --- Global worker variables for parallel execution ---
db_engine_global = None

def init_worker(db_json_str):
    global db_engine_global
    import engine_rust
    db_engine_global = engine_rust.PyCardDatabase(db_json_str)

def load_tournament_decks(full_db):
    decks_dir = Path(__file__).resolve().parent.parent.parent / "ai" / "decks"
    parser = UnifiedDeckParser(full_db)
    loaded_decks = []
    
    # Pre-fetch generic energy as fallback
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

def play_one_game(d0, d1, sims_per_move, dirichlet_alpha, dirichlet_eps):
    """Worker function for parallel game generation."""
    import numpy as np
    import random
    import engine_rust
    
    state = engine_rust.PyGameState(db_engine_global)
    state.initialize_game(d0["members"]+d0["lives"], d1["members"]+d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = True
    
    game_history = []
    while not state.is_terminal() and state.turn < 100:
        legal_ids = state.get_legal_action_ids()
        if not legal_ids: 
            break
        
        eval_mode = engine_rust.EvalMode.TerminalOnly
        suggestions = state.get_mcts_suggestions(sims_per_move, 1.41, engine_rust.SearchHorizon.GameEnd(), eval_mode)
        
        policy_target = np.zeros(16384, dtype=np.float32)
        total_visits = sum(s[2] for s in suggestions)
        if total_visits > 0:
            # 1. Base Policy from MCTS
            p_mcts = np.zeros(16384, dtype=np.float32)
            for aid, q, v in suggestions:
                p_mcts[aid] = v / total_visits
            
            # 2. Add Dirichlet Noise to Root (Self-Play Exploration via Label Smoothing)
            noise = np.random.dirichlet([dirichlet_alpha] * len(suggestions))
            for idx, (aid, q, v) in enumerate(suggestions):
                policy_target[aid] = (1 - dirichlet_eps) * p_mcts[aid] + (dirichlet_eps * noise[idx])
        
        obs = state.to_alphazero_tensor()
        mask = np.zeros(16384, dtype=np.bool_)
        for aid in legal_ids:
            mask[aid] = True
            
        game_history.append({
            "obs": obs,
            "policy": policy_target,
            "player": state.current_player,
            "mask": mask
        })
        
        # Action selection (Temperature Schedule: Exploratory first 30 turns, then Greedy)
        vts = [s[2] for s in suggestions]
        acts = [s[0] for s in suggestions]
        
        try:
            if not acts or sum(vts) == 0:
                if not legal_ids: break
                action = random.choice(legal_ids)
            else:
                if state.turn < 3:
                    # Proportional sampling (Higher exploration in opening turns)
                    action = random.choices(acts, weights=vts, k=1)[0]
                else:
                    # Greedy sampling (Exploitative mid/late game for better data)
                    best_idx = np.argmax(vts)
                    action = acts[best_idx]
        except Exception:
            if not legal_ids: break
            action = random.choice(legal_ids)
        
        state.step(action)
        state.auto_step(db_engine_global)

    winner = state.get_winner()
    new_transitions = []
    
    p0 = state.get_player(0)
    p1 = state.get_player(1)
    p0_lives = len(p0.success_lives)
    p1_lives = len(p1.success_lives)
    
    for t in game_history:
        # 1. Base Win/Loss Reward (Pure Zero)
        win_reward = 1.0 if t["player"] == winner else -1.0 if winner != -1 else 0.0
        
        # 2. Intermediate Reward Shaping (Live Completion Delta)
        # Completing more lives than the opponent gives a positive signal even if the game was lost.
        # We use a 0.5 weight as requested.
        my_idx = t["player"]
        opp_idx = 1 - my_idx
        my_l = p0_lives if my_idx == 0 else p1_lives
        opp_l = p1_lives if my_idx == 0 else p0_lives
        
        live_reward = (my_l - opp_l) * 0.5
        
        # Final shaped outcome
        outcome = win_reward + live_reward
        
        # COMPRESSION: Sparse Policy
        policy = t["policy"]
        nz_indices = np.where(policy > 0)[0].astype(np.uint16)
        nz_values = policy[nz_indices].astype(np.float16)
        sparse_policy = (nz_indices, nz_values)

        # Observations (Card IDs) will overflow float16, keep as float32.
        obs_f32 = np.array(t["obs"]).astype(np.float32)
        
        # Legality Mask: Pack as bitmask
        packed_mask = np.packbits(t["mask"])
        
        new_transitions.append((obs_f32, sparse_policy, packed_mask, outcome))
        
    return new_transitions

def train_fixed_steps(model, buffer, optimizer, device, num_steps, batch_size):
    """Train for exactly `num_steps` gradient updates, sampling randomly from buffer."""
    model.train()
    
    buf_size = len(buffer)
    total_loss = 0
    total_vloss = 0
    total_ploss = 0
    total_accuracy = 0
    actual_steps = 0
    nan_count = 0
    
    for step in range(num_steps):
        if buf_size == 0:
            break
        indices = np.random.randint(0, buf_size, size=min(batch_size, buf_size))
        batch = [buffer[i] for i in indices]
        
        # obs: (Batch, 3910)
        obs_t = torch.from_numpy(np.stack([t[0] for t in batch])).float().to(device)
        
        # policy_targets: (Batch, 16384)
        pol_t = torch.zeros((len(batch), 16384), device=device)
        for i, sample in enumerate(batch):
            indices_nz, values_nz = sample[1]
            pol_t[i, indices_nz] = torch.from_numpy(values_nz).float().to(device)

        # mask: Unpack from bitmask (Batch, 16384)
        masks_raw = np.stack([np.unpackbits(t[2])[:16384] for t in batch])
        msk_t = torch.from_numpy(masks_raw.astype(np.bool_)).to(device)
        
        # value_targets: (Batch, 1)
        val_t = torch.from_numpy(np.array([t[3] for t in batch], dtype=np.float32)).unsqueeze(1).to(device)
        
        optimizer.zero_grad(set_to_none=True)
        policy_logits, value_preds = model(obs_t, mask=msk_t)
        
        # Losses
        value_loss = F.mse_loss(value_preds, val_t)
        
        log_probs = F.log_softmax(policy_logits, dim=1)
        policy_loss = F.kl_div(log_probs, pol_t, reduction='batchmean')
        
        # Entropy regularization (encourage exploration)
        probs = log_probs.exp()
        entropy = -(probs * log_probs).sum(dim=1).mean()
        
        loss = value_loss + policy_loss + (ENTROPY_LAMBDA * -entropy)
        
        if torch.isnan(loss):
            nan_count += 1
            continue
            
        # Calculate Policy Accuracy (Top-1 Match)
        correct = (torch.argmax(policy_logits, dim=1) == torch.argmax(pol_t, dim=1)).sum().item()
        total_accuracy += correct / len(batch)
            
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        total_loss += loss.item()
        total_vloss += value_loss.item()
        total_ploss += policy_loss.item()
        actual_steps += 1
    
    if actual_steps == 0:
        return {"loss": 0.0, "value": 0.0, "policy": 0.0, "accuracy": 0.0, "nan_detected": True}
        
    return {
        "loss": total_loss / actual_steps,
        "value": total_vloss / actual_steps,
        "policy": total_ploss / actual_steps,
        "accuracy": total_accuracy / actual_steps,
        "nan_detected": nan_count > 0
    }

def main():
    root_dir = Path(__file__).resolve().parent.parent.parent
    db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    
    # Needs to be a string to be passed easily to initialize workers
    db_json_str = json.dumps(full_db)
    tournament_decks = load_tournament_decks(full_db)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Device: {torch.cuda.get_device_name(0)}")
    model = AlphaNet().to(device)
    
    checkpoint_dir = Path(__file__).parent
    checkpoint_path = checkpoint_dir / "alphanet_latest.pt"
    if checkpoint_path.exists():
        print(f"Loading existing model: {checkpoint_path}")
        try:
            model.load_state_dict(torch.load(str(checkpoint_path), map_location=device), strict=False)
            print(f"Successfully loaded checkpoint: {checkpoint_path}")
        except Exception as e:
            print(f"Warning: Could not load checkpoint (architecture mismatch). Starting fresh. Error: {e}")
    
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=2e-4)
    
    # --- Buffer (O(1) Pop) ---
    master_buffer = collections.deque(maxlen=MAX_BUFFER_SIZE)
    
    print(f"--- PURE ZERO v8 (Relational Transformer) ---")
    print(f"MCTS Sims: {SIMS_PER_MOVE}")
    print(f"Train Steps/Iter: {TRAIN_STEPS_PER_ITER}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Buffer Capacity: {MAX_BUFFER_SIZE}")
    print(f"Stop Method: Press Ctrl+C to stop and save.")
    
    log_path = checkpoint_dir / "overnight_training_log.csv"
    log_exists = log_path.exists() and log_path.stat().st_size > 0
    log_file = open(str(log_path), "a", encoding="utf-8")
    
    if not log_exists:
        log_file.write("iter,loss,value_loss,policy_loss,accuracy,buffer_size,gen_time,train_time\n")
        start_it = 0
    else:
        # Detect last iteration from log
        try:
            with open(str(log_path), "r", encoding="utf-8") as rf:
                last_line = rf.readlines()[-1]
                start_it = int(last_line.split(',')[0]) + 1
            print(f"Resuming from iteration {start_it}")
        except:
            start_it = 0
            
    log_file.flush()

    try:
        # Process Pool for parallel game generation
        max_workers = max(1, os.cpu_count() - 2) if hasattr(os, 'cpu_count') and os.cpu_count() else 4
        print(f"Using {max_workers} worker processes for self-play.")
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers, initializer=init_worker, initargs=(db_json_str,)) as executor:
            for it in range(start_it, NUM_ITERATIONS):
                    
                # ========================================
                # 1. GENERATE GAMES (Self-Play)
                # ========================================
                gen_start = time.time()
                new_transitions = []
                
                futures = []
                for _ in range(GAMES_PER_ITER):
                    d0 = random.choice(tournament_decks)
                    d1 = random.choice(tournament_decks)
                    futures.append(executor.submit(play_one_game, d0, d1, SIMS_PER_MOVE, DIRICHLET_ALPHA, DIRICHLET_EPS))
                
                for future in concurrent.futures.as_completed(futures):
                    new_transitions.extend(future.result())
                
                gen_time = time.time() - gen_start
                
                # ========================================
                # 2. UPDATE BUFFER
                # ========================================
                master_buffer.extend(new_transitions)
                
                if not master_buffer: continue

                # ========================================
                # 3. TRAIN — Fixed Sample Reuse Ratio (SRR)
                # ========================================
                train_start = time.time()
                new_moves = len(new_transitions)
                target_steps = int((new_moves * SRR) / BATCH_SIZE)
                dynamic_steps = max(100, min(TRAIN_STEPS_PER_ITER, target_steps))
                
                stats = train_fixed_steps(
                    model, master_buffer, optimizer, device,
                    num_steps=dynamic_steps,
                    batch_size=BATCH_SIZE
                )
                train_time = time.time() - train_start
                
                # ========================================
                # 4. METRICS (Policy Accuracy)
                # ========================================
                pol_acc = stats['accuracy'] * 100
                
                # ========================================
                # 5. LOG & SAVE
                # ========================================
                total_time = gen_time + train_time
                print(f"It {it:3d} | Buf: {len(master_buffer):5d} (+{new_moves:4d}) | "
                      f"Acc: {pol_acc:5.1f}% | Loss: {stats['loss']:.4f} | "
                      f"V: {stats['value']:.3f} | Gen: {gen_time:.0f}s | Train: {train_time:.0f}s | "
                      f"Total: {total_time:.0f}s")
                log_file.write(f"{it},{stats['loss']},{stats['value']},{stats['policy']},{pol_acc},{len(master_buffer)},{gen_time:.1f},{train_time:.1f}\n")
                log_file.flush()
                
                if it % 5 == 0:
                    torch.save(model.state_dict(), str(checkpoint_path))
                if it % 20 == 0 and it > start_it:
                    torch.save(model.state_dict(), str(checkpoint_dir / f"alphanet_it{it}.pt"))
                
                # Periodically clear CUDA cache to prevent fragmentation
                if it % 10 == 0:
                    torch.cuda.empty_cache()

    except KeyboardInterrupt:
        print("\nCtrl+C detected. Saving model and exiting cleanly...")
    except Exception as e:
        print(f"Error during training: {e}")
        import traceback
        traceback.print_exc()
    finally:
        log_file.close()
        print("Finalizing...")
        torch.save(model.state_dict(), str(checkpoint_dir / "alphanet_final_session.pt"))
        print("Model saved. Training complete.")

if __name__ == "__main__":
    import multiprocessing
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()
