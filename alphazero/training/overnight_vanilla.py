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

from alphazero.vanilla_net import HighFidelityAlphaNet
import torch.nn.functional as F
import engine_rust
from engine.game.deck_utils import UnifiedDeckParser
from disk_buffer import PersistentBuffer
from alphazero.training.benchmark_vanilla import run_benchmark

# Also import the game loop helper from benchmark if needed
# For now, we'll modify play_one_game to match benchmark's logic

# ============================================================
# CONFIGURATION (Vanilla AlphaZero Loop)
# ============================================================
NUM_ITERATIONS = 1000000
ACTION_SPACE = 128
OBS_DIM = 800

# --- Self-Play ---
GAMES_PER_ITER = 16        
SIMS_PER_MOVE = 128         
SRR = 8.0                   # Sample Reuse Ratio
MIRROR = True               # Reduction of variance

# --- Training ---
TRAIN_STEPS_PER_ITER = 200  
BATCH_SIZE = 512            
ACCUM_STEPS = 4             
LR = 0.001                  
DIRICHLET_ALPHA = 0.3       
DIRICHLET_EPS = 0.25        

# --- Buffer ---
MAX_BUFFER_SIZE = 8000000    # ~16.1 GB on disk using uint8 indices
SPARSE_LIMIT = 128           # Matches Vanilla Action Space

# --- Global worker variables ---
db_engine_global = None
model_global = None

def init_worker(db_path_str, model_path_str=None, device_str="cpu", strip=True):
    global db_engine_global, model_global
    import engine_rust, json, torch
    from alphazero.vanilla_net import HighFidelityAlphaNet
    
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
        model_global = HighFidelityAlphaNet(input_dim=800, num_actions=128).to(device_str)
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

LOGIC_ID_MASK = 0x0FFF

def map_engine_to_vanilla(p_data, engine_id, initial_deck, current_phase=None):
    """Maps engine action ID to vanilla 128-dim action space.
    
    current_phase: helps distinguish context for multi-purpose IDs (like EID 0)
    """
    # 0 is "Pass" in Active phases (Main), but "Confirm" in setup/cleanup phases
    if engine_id == 0:
        # Phases: Mulligan(-1,0), LiveSet(5), LiveResult(8), Response(10)
        if current_phase in [-1, 0, 5, 8, 10]:
            return 7 # Confirm / Done
        return 0 # Pass (Active/Main phase)
    
    # Mulligan actions (300-305) -> Map to 1-6
    if 300 <= engine_id <= 305:
        return 1 + (engine_id - 300)
    
    # Confirm
    if engine_id == 11000:
        return 7
    
    # Play Member from hand (1000-1599)
    if 1000 <= engine_id < 1600:
        hand_idx = (engine_id - 1000) // 10
        if hand_idx < len(p_data['hand']):
            card_id = p_data['hand'][hand_idx]
            if initial_deck and card_id in initial_deck:
                try:
                    deck_idx = initial_deck.index(card_id)
                    if deck_idx < 60:
                        return 8 + deck_idx
                except ValueError:
                    pass
            if hand_idx < 60:
                return 8 + hand_idx
        return -1
    
    # Set Live (400-499)
    if 400 <= engine_id < 500:
        hand_idx = engine_id - 400
        if hand_idx < len(p_data['hand']):
            card_id = p_data['hand'][hand_idx]
            if initial_deck and card_id in initial_deck:
                try:
                    deck_idx = initial_deck.index(card_id)
                    if deck_idx < 60:
                        return 68 + deck_idx
                except ValueError:
                    pass
            if hand_idx < 60:
                return 68 + hand_idx
        return -1
    
    # Success Selection (600-602)
    if 600 <= engine_id <= 602:
        return 7 # Map to Confirm for now since it's "Done picking success"
    
    # RPS Actions (20000-20002)
    if 20000 <= engine_id <= 20002:
        return 125 + (engine_id - 20000) # 125, 126, 127
        
    # Turn Choice (5000-5001) - Use Dedicated Slot? 
    # Let's map to 7 (Confirm) or dedicate 124 for Turn Choice
    if engine_id in [5000, 5001]:
        return 124 # Dedicate 124
    
    # RPS P2 (21000-21002) - map to same as P1
    if 21000 <= engine_id <= 21002:
        return 125 + (engine_id - 21000)
    
    return -1


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
        winner = None  # Track winner like benchmark
        
        # Stall detection
        last_state_hash = None
        stall_count = 0
        
        # Debug: Check initial state
        initial_legal = state.get_legal_action_ids()
        print(f"[DEBUG] Game init - term:{state.is_terminal()} turn:{state.turn} player:{state.current_player} legal:{len(initial_legal)}")
        
        while not state.is_terminal() and state.turn < 25 and moves_taken < max_moves:
            # Hash-based stall detection
            current_state_str = f"{state.turn}_{state.current_player}_{state.phase}_{len(state.get_legal_action_ids())}"
            if current_state_str == last_state_hash:
                stall_count += 1
            else:
                stall_count = 0
                last_state_hash = current_state_str
            
            if stall_count >= 10:
                print(f"[WARNING] Game stalled at turn {state.turn}, phase {state.phase}. Terminating.")
                break
            legal_ids = state.get_legal_action_ids()
            if not legal_ids:
                print(f"[DEBUG] No legal actions! Turn: {state.turn}, is_terminal: {state.is_terminal()}")
                break
            
            # Debug: Check if loop is about to exit (only occasionally to reduce noise)
            if moves_taken >= 3 and moves_taken % 10 == 0:
                print(f"[DEBUG] Loop check: term={state.is_terminal()}, turn={state.turn}, moves={moves_taken}")
            
            # 1. Choose move source
            state_json = json.loads(state.to_json())
            current_phase = state_json.get('phase', -4)
            legal_ids = state.get_legal_action_ids()
            curr_p_data = state_json['players'][state.current_player]
            
            # FAST BYPASS FOR SETUP/INTERACTIVE PHASES
            # This ensures we get to the Main phase where the model actually learns
            action_engine = None
            
            if current_phase == -4: # Initial Setup
                if 0 in legal_ids: action_engine = 0
            elif current_phase == -3: # RPS
                action_engine = random.choice(legal_ids)
                print(f"[DEBUG] Random RPS: {action_engine}")
            elif current_phase == -2: # Turn Choice
                action_engine = random.choice(legal_ids)
                print(f"[DEBUG] Random Turn Choice: {action_engine}")
            
            # Mulligan, LiveSet, etc. will now use normal move selection below
            
            # FIXED: Use MCTS for phases -1 (Mulligan), 0 (Energy), 4 (Main), 5 (LiveSet)
            # Same as benchmark_vanilla.py
            if action_engine is not None:
                # Still record history if we want (though setup moves are low entropy)
                # But for simplicity, we just step
                state.step(action_engine)
                state.auto_step(db_engine_global)
                moves_taken += 1
                continue

            # FIXED: Use MCTS for multiple phases (not just Phase 4)
            if sims_per_move > 0 and current_phase in [4, 5, -1, 0]:
                # MCTS simulation
                suggestions = state.search_mcts(sims_per_move, 0.0, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal, None)
            else:
                suggestions = []
            
            # NORMAL MOVE SELECTION
            obs_np = state.to_vanilla_tensor()
            
            policy_target = np.zeros(ACTION_SPACE, dtype=np.float32)
            total_visits = sum(s[2] for s in suggestions)
            
            if total_visits > 0:
                for engine_id, q, visits in suggestions:
                    vid = map_engine_to_vanilla(curr_p_data, engine_id, initial_decks[state.current_player], current_phase)
                    if 0 <= vid < ACTION_SPACE:
                        policy_target[vid] += visits / total_visits
            
            mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
            v_to_e = {}
            for aid in legal_ids:
                vid = map_engine_to_vanilla(curr_p_data, aid, initial_decks[state.current_player], current_phase)
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
                        vid = map_engine_to_vanilla(p_data, aid, initial_decks[state.current_player])
                        label = state.get_verbose_label(aid)
                        f.write(f"  ID {aid} -> VID {vid}: {label}\n")
                    if policy_target.sum() < 1e-11:
                        f.write(f"CRITICAL: Zero-sum policy! Total suggestions: {len(suggestions)}\n")
                        for eid, q, v in suggestions:
                            vid = map_engine_to_vanilla(p_data, eid, initial_decks[state.current_player])
                            f.write(f"  Suggestion: EID {eid} -> VID {vid} (Visits: {v})\n")

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
                        action_vid = map_engine_to_vanilla(state_json['players'][state.current_player], action_engine, initial_decks[state.current_player])
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
                        action_vid = map_engine_to_vanilla(state_json['players'][state.current_player], action_engine, initial_decks[state.current_player])
                else:
                    print(f"DEBUG: MCTS visits yielded zero-sum policy. total_visits={total_visits}, suggestions={len(suggestions)}")
                    action_engine = random.choice(legal_ids)
                    action_vid = map_engine_to_vanilla(state_json['players'][state.current_player], action_engine, initial_decks[state.current_player])
            else:
                action_engine = random.choice(legal_ids)
                action_vid = map_engine_to_vanilla(state_json['players'][state.current_player], action_engine, initial_decks[state.current_player])

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
            state.auto_step(db_engine_global)
            
            # Debug: Show detailed step info (less verbose)
            if moves_taken % 10 == 0:
                state_json_after = json.loads(state.to_json())
                print(f"[DEBUG] Step: move={moves_taken}, phase={state_json_after.get('phase')}, turn={state_json_after.get('turn')}, player={state.current_player}, action={action_engine}")
            
            # Check for terminal state after each move (like benchmark)
            if state.is_terminal():
                winner = state.get_winner()
                print(f"[DEBUG] Game terminated at move {moves_taken}, turn {state.turn}, winner={winner}")
                break
            
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
            value_loss = F.mse_loss(value_preds.view_as(val_t[:, 0:1]), val_t[:, 0:1])
            
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
    model = HighFidelityAlphaNet(input_dim=OBS_DIM, num_actions=ACTION_SPACE).to(device)
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
                    bench_turns, bench_score = run_benchmark(str(checkpoint_path), sims=128)
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
