import torch
import numpy as np
import random
import time
import os
import json
import sys
import collections
import concurrent.futures
from pathlib import Path

# Reduce CUDA memory fragmentation (Disabled: crashes on Windows)
# os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')

# Add project root for imports
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

# Robust path detection for the Rust engine
search_paths = [
    root_dir / "engine_rust_src" / "target" / "release",
    root_dir / "engine_rust_src" / "target" / "debug",
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
from disk_buffer import PersistentBuffer
def run_benchmark(x):
    return 0, 0

# ============================================================
# CONFIGURATION (Vanilla AlphaZero Loop)
# ============================================================
NUM_ITERATIONS = 1000000
ACTION_SPACE = 22000
OBS_DIM = 20500

# --- Self-Play ---
GAMES_PER_ITER = 16        
SIMS_PER_MOVE = 128         
SRR = 8.0                   # Sample Reuse Ratio
MIRROR = True               # Reduction of variance

# --- Training ---
TRAIN_STEPS_PER_ITER = 20  
BATCH_SIZE = 256            
ACCUM_STEPS = 4             
LR = 0.001                  
DIRICHLET_ALPHA = 0.3       
DIRICHLET_EPS = 0.25        

# --- Buffer ---
MAX_BUFFER_SIZE = 8000000    # ~16.1 GB on disk using uint8 indices
SPARSE_LIMIT = 256           # Matches Vanilla Action Space

# --- Global worker variables ---
db_engine_global = None

def init_worker(db_path_str, strip=False):
    global db_engine_global
    import engine_rust, json
    with open(db_path_str, "r", encoding="utf-8") as f:
        db_json = json.load(f)
    
    if strip:
        # Strip all abilities to create a pure 'Vanilla' environment
        for cat in ["member_db", "live_db"]:
            for cid, data in db_json.get(cat, {}).items():
                data["abilities"] = []
                data["ability_flags"] = 0
                if "synergy_flags" in data:
                    data["synergy_flags"] &= 1
                    
    db_json_str = json.dumps(db_json)
    db_engine_global = engine_rust.PyCardDatabase(db_json_str)

def load_tournament_decks(full_db):
    decks_dir = Path(__file__).resolve().parent.parent.parent / "ai" / "decks"
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


    
    # Set Live (400-499)
    # Engine uses: 400 + hand_index
    if 400 <= engine_id < 500:
        hand_idx = engine_id - 400
        if hand_idx < 60:
            return 68 + hand_idx  # 68-127 (60 slots)
        return -1
    
    # Select Success Live (600-602) - no abilities in vanilla, map to Pass
    if 600 <= engine_id <= 602:
        return 0
    
    # Turn Choice (5000-5001) - no abilities in vanilla, map to Pass
    if engine_id in [5000, 5001]:
        return 0
    
    # RPS (20000-21002) - no abilities in vanilla, map to Pass
    if 20000 <= engine_id <= 20002 or 21000 <= engine_id <= 21002:
        return 0
    
    return -1

# --- Global worker variables ---
db_engine_global = None
model_global = None

def init_worker(db_path_str, model_path_str=None, device_str="cpu", strip=False):
    global db_engine_global, model_global
    import engine_rust, json, torch
    from alphazero.alphanet import AlphaNet
    
    with open(db_path_str, "r", encoding="utf-8") as f:
        db_json = json.load(f)
    
    if strip:
        # Strip all abilities to create a pure 'Vanilla' environment
        for cat in ["member_db", "live_db"]:
            for cid, data in db_json.get(cat, {}).items():
                data["abilities"] = []
                data["ability_flags"] = 0
                if "synergy_flags" in data:
                    data["synergy_flags"] &= 1
                    
    db_json_str = json.dumps(db_json)
    db_engine_global = engine_rust.PyCardDatabase(db_json_str)
    
    if model_path_str and Path(model_path_str).exists():
        model_global = AlphaNet(input_dim=800, num_actions=128).to(device_str)
        try:
            ckpt = torch.load(model_path_str, map_location=device_str, weights_only=True)
            if isinstance(ckpt, dict) and 'model' in ckpt:
                model_global.load_state_dict(ckpt['model'])
            else:
                model_global.load_state_dict(ckpt)
            print(f"Worker loaded model: {model_path_str}")
        except Exception as e:
            print(f"Worker failed to load model: {e}")
        model_global.eval()

def play_one_game(d0, d1, sims_per_move, mirror_seed=None):
    global db_engine_global, model_global
    import engine_rust, json, torch, random, traceback
    import numpy as np
    import torch.nn.functional as F
    
    def _dense_to_sparse(dense_policy):
        """Convert dense policy array to sparse (indices, values) tuple."""
        indices = np.where(dense_policy > 0)[0]
        values = dense_policy[indices]
        return (indices, values)
    
    try:
        state = engine_rust.PyGameState(db_engine_global)
        state.silent = True
        
        if mirror_seed:
            state.initialize_game_with_seed(
                d0["members"]+d0["lives"], d0["members"]+d0["lives"], 
                d0["energy"], d0["energy"], [], [], mirror_seed
            )
        else:
            state.initialize_game(
                d0["members"]+d0["lives"], d1["members"]+d1["lives"], 
                d0["energy"], d1["energy"], [], []
            )
        
        initial_decks = [state.get_player(0).initial_deck, state.get_player(1).initial_deck]
        game_history = []
        max_moves = 1000
        moves_taken = 0
        
        # Debug: Check initial state
        initial_legal = state.get_legal_action_ids()
        print(f"[DEBUG] Game init - term:{state.is_terminal()} turn:{state.turn} player:{state.current_player} legal:{len(initial_legal)}")
        
        while not state.is_terminal() and state.turn < 25 and moves_taken < max_moves:
            legal_ids = state.get_legal_action_ids()
            if not legal_ids:
                print(f"[DEBUG] No legal actions! Turn: {state.turn}, is_terminal: {state.is_terminal()}")
                break
            
            # Debug: Check if loop is about to exit
            if moves_taken >= 3:
                print(f"[DEBUG] Loop check: term={state.is_terminal()}, turn={state.turn}, moves={moves_taken}")
            
            # 1. Neural Network Prior (if available)
            policy_final = np.zeros(ACTION_SPACE, dtype=np.float32)
            obs_np = state.to_tensor()
            
            # MCTS simulation
            suggestions = state.get_mcts_suggestions(sims_per_move, 0.0, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly)
            
            state_json = json.loads(state.to_json())
            current_phase = state_json.get('phase', 0)
            
            legal_ids = state.get_legal_action_ids()
            
            # Debug: Show legal actions and their vanilla mapping
            if moves_taken <= 10:
                mapping_info = []
                for aid in legal_ids[:8]:
                    mapping_info.append(str(aid))
                print(f"[DEBUG] Phase {current_phase}, Move {moves_taken}: Legal ({len(legal_ids)}): {mapping_info}")
            
            policy_target = np.zeros(ACTION_SPACE, dtype=np.float32)
            total_visits = sum(s[2] for s in suggestions)
            
            mapping_failures = 0
            if total_visits > 0:
                for engine_id, q, visits in suggestions:
                    vid = engine_id
                    if 0 <= vid < ACTION_SPACE:
                        policy_target[vid] += visits / total_visits
                    else:
                        mapping_failures += 1

            mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
            v_to_e = {}
            for aid in legal_ids:
                vid = aid
                if 0 <= vid < ACTION_SPACE:
                    mask[vid] = True
                    v_to_e[vid] = aid

            # Log legal actions and mapping status to file (User Request)
            p_label = "P1" if state.current_player == 0 else "P2"
            p_data = state_json['players'][state.current_player]
            log_path = "reports/mapping_diag.txt"
            with open(log_path, "a", encoding="utf-8") as f:
                if total_visits > 0 and (policy_target.sum() < 1e-11 or random.random() < 0.005):
                    f.write(f"\n--- DEBUG [{p_label}, Turn {state.turn}, Phase {state_json['phase']}] ---\n")
                    f.write(f"Hand: {p_data['hand']}\n")
                    f.write(f"Initial Deck: {initial_decks[state.current_player]}\n")
                    f.write(f"Legal Actions (First 20):\n")
                    for aid in legal_ids[:20]:
                        vid = aid
                        label = state.get_verbose_label(aid)
                        f.write(f"  ID {aid} -> VID {vid}: {label}
")
                    if policy_target.sum() < 1e-11:
                        f.write(f"CRITICAL: Zero-sum policy! Total suggestions: {len(suggestions)}
")
                        for eid, q, v in suggestions:
                            vid = eid
                            f.write(f"  Suggestion: EID {eid} -> VID {vid} (Visits: {v})
")

            # Move selection: Model-guided or MCTS-weighted?
            if model_global:
                with torch.no_grad():
                    # Correctly placement on worker device
                    net_device = next(model_global.parameters()).device
                    # Convert list to numpy array if needed
                    if isinstance(obs_np, list):
                        obs_np = np.array(obs_np, dtype=np.float32)
                    obs_t = torch.from_numpy(obs_np).float().unsqueeze(0).to(net_device)
                    mask_t = torch.from_numpy(mask).unsqueeze(0).to(net_device)
                    policy_logits, _ = model_global(obs_t, mask_t)
                    # Apply mask to logits
                    policy_logits.masked_fill_(~mask_t, -1e9)
                    probs = F.softmax(policy_logits, dim=1).cpu().numpy()[0]
                    
                    # NaN validation
                    if np.isnan(probs).any():
                        print(f"CRITICAL: NaNs in policy probabilities! Resetting to uniform mask.")
                        probs = np.zeros(ACTION_SPACE, dtype=np.float32)
                        m_np = mask_t.cpu().numpy()[0]
                        if m_np.sum() > 0:
                            probs[m_np] = 1.0 / m_np.sum()
                        else:
                            probs.fill(0) # Should not happen
                    
                    # Sample from model policy with some exploration early on
                    vids = np.arange(ACTION_SPACE)
                    try:
                        p_sum = probs.sum()
                        if p_sum > 0:
                            probs = probs / p_sum
                        else:
                            probs = np.zeros(ACTION_SPACE, dtype=np.float32)
                            probs[mask] = 1.0 / mask.sum() if mask.any() else 0
                            if probs.sum() == 0: probs[0] = 1.0 # Absolute fallback
                        
                        if moves_taken < 10:
                            action_vid = np.random.choice(vids, p=probs)
                        else:
                            action_vid = np.argmax(probs)
                    except Exception as e:
                        print(f"Sampling Error (Model): {e}. Fallback to random.")
                        action_engine = random.choice(legal_ids)
                        action_vid = action_engine
                    else:
                        action_engine = v_to_e.get(action_vid, random.choice(legal_ids))
            elif total_visits > 0:
                # Fallback to MCTS visits if no model loaded yet
                vids = np.arange(ACTION_SPACE)
                p_sum = policy_target.sum()
                if p_sum > 1e-11:
                    p_mcts = policy_target / p_sum
                    try:
                        action_vid = np.random.choice(vids, p=p_mcts)
                        action_engine = v_to_e.get(action_vid, random.choice(legal_ids))
                    except Exception as e:
                        print(f"Sampling Error (MCTS): {e}. Fallback to random.")
                        action_engine = random.choice(legal_ids)
                        action_vid = action_engine
                else:
                    print(f"DEBUG: MCTS visits yielded zero-sum policy. total_visits={total_visits}, suggestions={len(suggestions)}")
                    action_engine = random.choice(legal_ids)
                    action_vid = action_engine
            else:
                action_engine = random.choice(legal_ids)
                action_vid = action_engine

            if np.isnan(policy_target).any():
                print(f"CRITICAL: Policy target contain NaN during game! total_visits={total_visits}")
                policy_target = np.nan_to_num(policy_target)

            game_history.append({
                "obs": obs_np,
                "policy": policy_target,
                "player": state.current_player,
                "mask": mask,
                "turn": state.turn
            })
            
            state.step(action_engine)
            
            # Debug: Show detailed step info
            state_json = json.loads(state.to_json())
            print(f"[DEBUG] Step: move={moves_taken}, phase={state_json.get('phase')}, turn={state.turn}, player={state.current_player}, action={action_engine}")
            
            state.auto_step(db_engine_global)
            
            # Debug after auto_step
            state_json_after = json.loads(state.to_json())
            if moves_taken <= 5:
                print(f"[DEBUG] AutoStep: move={moves_taken}, phase={state_json_after.get('phase')}, turn={state_json_after.get('turn')}")
            
            moves_taken += 1
        
        print(f"[DEBUG] While loop exited - term:{state.is_terminal()}, turn:{state.turn}, moves:{moves_taken}")
        
        # Debug: Check final state
        print(f"[DEBUG] Game ending - is_terminal: {state.is_terminal()}, turn: {state.turn}, winner: {state.get_winner()}")
        
        # Force terminal check
        if not state.is_terminal() and state.turn >= 25:
            print("[DEBUG] Game ended by turn limit, checking winner...")
            # Calculate winner based on success lives (score)
            p0_score = len(state.get_player(0).success_lives)
            p1_score = len(state.get_player(1).success_lives)
            print(f"[DEBUG] Score: P0={p0_score}, P1={p1_score}")
            if p0_score > p1_score:
                winner = 0
            elif p1_score > p0_score:
                winner = 1
            else:
                winner = 2  # Tie
            print(f"[DEBUG] Determined winner: {winner}")
        else:
            winner = state.get_winner()
        new_transitions = []
        for h in game_history:
            # Value is 1 if that player won, 0 if lost, 0.5 if tie
            val = 0.5
            if winner == h['player']: val = 1.0
            elif winner == 1 - h['player']: val = 0.0
            
            new_transitions.append((
                h['obs'],
                _dense_to_sparse(h['policy']),
                h['mask'],
                np.array([val], dtype=np.float32)
            ))
            
        stats = {
            "turns": state.turn,
            "p0_lives": len(state.get_player(0).success_lives),
            "p1_lives": len(state.get_player(1).success_lives),
            "winner": winner
        }
        return new_transitions, stats
    except Exception:
        print("CRITICAL ERROR IN WORKER:")
        traceback.print_exc()
        raise

def train_fixed_steps(model, buffer, optimizer, scaler, device, num_steps, batch_size):
    model.train()
    total_loss = 0
    actual_steps = 0
    
    for _ in range(num_steps):
        batch = buffer.sample(batch_size)
        if batch is None: break
        
        obs_np, sparse_pol, msk_np, val_np = batch
        
        obs_t = torch.from_numpy(obs_np).to(device)
        # Densify sparse policy
        pol_t = torch.zeros(batch_size, ACTION_SPACE, device=device)
        row_v, col_v, val_v = sparse_pol
        pol_t[torch.from_numpy(row_v).long().to(device), torch.from_numpy(col_v).long().to(device)] = torch.from_numpy(val_v).float().to(device)
        
        msk_t = torch.from_numpy(msk_np).to(device)
        val_t = torch.from_numpy(val_np).float().to(device)
        
        optimizer.zero_grad()
        
        # Fix device selection for autocast
        with torch.autocast(device_type=device.type, dtype=torch.float16 if device.type == 'cuda' else torch.bfloat16):
            policy_logits, value_preds = model(obs_t, mask=msk_t)
            
            # Policy loss: we only care about the win_prob part of the value_preds (first col)
            # though model(obs) returns a single scalar for value in VanillaNet usually
            value_loss = F.mse_loss(value_preds[:, 0:1], val_t[:, 0:1])
            
            log_probs = F.log_softmax(policy_logits, dim=1)
            policy_loss = F.kl_div(log_probs, pol_t, reduction='batchmean')
            
            loss = (value_loss + policy_loss) / ACCUM_STEPS
            
        scaler.scale(loss).backward()
        
        if (actual_steps + 1) % ACCUM_STEPS == 0:
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
            
        total_loss += loss.item() * ACCUM_STEPS
        actual_steps += 1
        
    return total_loss / max(1, actual_steps)

def main():
    checkpoint_dir = Path(__file__).parent / "vanilla_checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    tournament_decks = load_tournament_decks(full_db)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AlphaNet(input_dim=OBS_DIM, num_actions=ACTION_SPACE).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scaler = torch.amp.GradScaler(device.type if device.type == 'cuda' else 'cpu')
    
    checkpoint_path = checkpoint_dir / "latest.pt"
    start_it = 0
    if checkpoint_path.exists():
        print(f"Resuming: {checkpoint_path}")
        ckpt = torch.load(str(checkpoint_path), map_location=device, weights_only=True)
        model.load_state_dict(ckpt['model'])
        optimizer.load_state_dict(ckpt['optimizer'])
        start_it = ckpt['it'] + 1
        
    buffer_dir = checkpoint_dir / "experience"
    buffer = PersistentBuffer(
        buffer_dir, 
        max_size=MAX_BUFFER_SIZE, 
        obs_dim=OBS_DIM, 
        num_actions=ACTION_SPACE,
        sparse_limit=SPARSE_LIMIT,
        index_dtype=np.uint8
    )
    
    log_file = open(str(checkpoint_dir / "training_log.csv"), "a", encoding="utf-8")
    if start_it == 0:
        log_file.write("iter,loss,avg_turns,p0_wins,p1_wins,buffer_size,bench_turns,bench_score,gen_time,train_time\n")
        
    print(f"--- Vanilla Loop: Iter {start_it} onwards ---")
    
    try:
        # Use 1 worker to avoid GPU contention between workers
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=1, 
            initializer=init_worker, 
            initargs=(str(db_path), str(checkpoint_path) if checkpoint_path.exists() else None, device.type, True)
        ) as executor:
            for it in range(start_it, NUM_ITERATIONS):
                print(f"\n=== Starting Iteration {it} ===")
                gen_start = time.time()
                futures = []
                for _ in range(GAMES_PER_ITER):
                    d0 = random.choice(tournament_decks)
                    d1 = random.choice(tournament_decks)
                    seed = random.getrandbits(64) if MIRROR else None
                    futures.append(executor.submit(play_one_game, d0, d1, SIMS_PER_MOVE, seed))
                
                new_transitions = []
                game_stats = []
                for future in concurrent.futures.as_completed(futures):
                    transitions, stat = future.result()
                    new_transitions.extend(transitions)
                    game_stats.append(stat)
                    print(f"  [Game done] Winner: {stat['winner']}, Turns: {stat['turns']}, P0 Lives: {stat['p0_lives']}, P1 Lives: {stat['p1_lives']}")
                
                for t in new_transitions:
                    buffer.add(t[0], t[1], t[3], t[2])
                
                gen_time = time.time() - gen_start
                
                if buffer.count >= BATCH_SIZE:
                    train_start = time.time()
                    print(f"[TRAIN] It {it:3d} | Training on {buffer.count} samples...")
                    loss = train_fixed_steps(model, buffer, optimizer, scaler, device, TRAIN_STEPS_PER_ITER, BATCH_SIZE)
                    train_time = time.time() - train_start
                    print(f"[TRAIN] It {it:3d} | Loss: {loss:.4f} | Train Time: {train_time:.1f}s")
                else:
                    loss, train_time = 0, 0
                    print(f"[WAIT] It {it:3d} | Buffer too small: {buffer.count}/{BATCH_SIZE}")
                
                wins = [s["winner"] for s in game_stats]
                avg_turns = sum(s["turns"] for s in game_stats) / len(game_stats) if game_stats else 0
                
                # Detailed game stats
                p0_lives = sum(s["p0_lives"] for s in game_stats)
                p1_lives = sum(s["p1_lives"] for s in game_stats)
                ties = wins.count(2) if 2 in wins else 0
                print(f"[SUMMARY] It {it:3d} | Loss: {loss:.4f} | Gen: {gen_time:.1f}s | P0 Wins: {wins.count(0)} | P1 Wins: {wins.count(1)} | Ties: {ties} | Avg Lives - P0: {p0_lives/len(game_stats):.1f} P1: {p1_lives/len(game_stats):.1f} | Avg Turns: {avg_turns:.1f}")
                
                # Periodic Benchmark (Greedy/No MCTS)
                bench_turns, bench_score = 0, 0
                if it % 10 == 0:
                    model.eval()
                    print(f"[BENCHMARK] Running benchmark...")
                    bench_turns, bench_score = run_benchmark(str(checkpoint_path))
                    model.train()
                    print(f"[BENCHMARK] Turns: {bench_turns:.1f}, Score: {bench_score:.1f}")

                log_file.write(f"{it},{loss:.4f},{avg_turns:.1f},{wins.count(0)},{wins.count(1)},{buffer.count},{bench_turns:.1f},{bench_score:.1f},{gen_time:.1f},{train_time:.1f}\n")
                log_file.flush()
                
                # Print GPU memory if available
                if torch.cuda.is_available():
                    mem_allocated = torch.cuda.memory_allocated(device) / 1024**3
                    mem_reserved = torch.cuda.memory_reserved(device) / 1024**3
                    print(f"[GPU] Memory: {mem_allocated:.2f}GB allocated, {mem_reserved:.2f}GB reserved")
                
                if it % 5 == 0:
                    torch.save({'model': model.state_dict(), 'optimizer': optimizer.state_dict(), 'it': it}, str(checkpoint_path))
                    print(f"[CHECKPOINT] Saved to {checkpoint_path}")
                    
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        log_file.close()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
