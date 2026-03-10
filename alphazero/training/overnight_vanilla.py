# ============================================================
# PRIMARY ENTRY POINT: AlphaZero Vanilla Training Loop
# Optimized for 4GB VRAM and High Performance Self-Play
# ============================================================
import os
# Reduce CUDA memory fragmentation (Recommended for 4GB cards)
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')

import torch
import numpy as np
import random
import time
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
    root_dir # Root/Current dir fallback
]
for p in search_paths:
    if (p / "engine_rust.pyd").exists() or (p / "engine_rust.dll").exists():
        p_str = str(p)
        if p_str in sys.path:
            sys.path.remove(p_str)
        sys.path.insert(0, p_str)
        print(f"[INIT] Prioritizing engine at {p_str}")
        break

from alphazero.vanilla_net import HighFidelityAlphaNet
import torch.nn.functional as F
import engine_rust
from engine.game.deck_utils import UnifiedDeckParser
from disk_buffer import PersistentBuffer
from alphazero.training.vanilla_utils import map_engine_to_vanilla, run_benchmark

# Also import the game loop helper from benchmark if needed
# For now, we'll modify play_one_game to match benchmark's logic

# ============================================================
# CONFIGURATION (Vanilla AlphaZero Loop)
# ============================================================
NUM_ITERATIONS = 1000000
ACTION_SPACE = 256
OBS_DIM = 800

# --- Self-Play & Parallelism ---
# Workers must use CPU: CUDA+multiprocessing+PyO3 causes silent evaluator failures
# GPU is reserved exclusively for the Trainer (training loop)
NUM_WORKERS = 4             # Reduced from 8: PyTorch workers ~400MB each, 8 exhausted RAM
GAMES_PER_ITER = 64        
SIMS_PER_MOVE = 64          # Increased: more sims = better policy targets for learning
SRR = 8.0                   # Sample Reuse Ratio
MIRROR = True               # Reduction of variance

# --- Training ---
TRAIN_STEPS_PER_ITER = 200  
BATCH_SIZE = 1024           # Back to 1024; GPU is no longer shared with workers
ACCUM_STEPS = 4             # Back to 4 (effective batch = 4096)
LR = 0.001                  
DIRICHLET_ALPHA = 0.3       
DIRICHLET_EPS = 0.25
DFS_SOFTMAX_TEMP = 0.5      # Warmer temp: alternatives get real probability mass for learning
EXPLORE_EPS = 0.05          # 5% of moves: play a random legal action for diversity
CURRICULUM_SWITCH_ITER = 25  # Reduced: model already has 100+ iter of knowledge. 25 is enough to re-tune.

# --- Buffer ---
MAX_BUFFER_SIZE = 2000000   # Increased to 2 million. Disk-backed (memmap), minimal RAM impact.
SPARSE_LIMIT = 256           # Matches Vanilla Action Space

# --- Global worker variables ---
db_engine_global = None
model_global = None
evaluator_global = None

def init_worker(db_json_str, model_path_str=None, device_str="cpu"):
    global db_engine_global, model_global
    import engine_rust, torch
    print(f"Worker process starting init... (PID: {os.getpid()})", flush=True)
    # Optimized: 2 threads allows Transformer to evaluate significantly faster on CPU
    torch.set_num_threads(2)
    from alphazero.vanilla_net import HighFidelityAlphaNet
    
    # Use the pre-stripped JSON string directly
    db_engine_global = engine_rust.PyCardDatabase(db_json_str)
    
    if model_path_str and Path(model_path_str).exists():
        # Standard FP32 model — PyTorch autocast handles mixed precision where needed
        model_global = HighFidelityAlphaNet(input_dim=800, num_actions=256).to(device_str)
        try:
            # Check if it's a weights-only file or a full checkpoint
            # Added mmap=True for faster loading on Windows
            ckpt = torch.load(model_path_str, map_location=device_str, weights_only=True, mmap=True)
            if isinstance(ckpt, dict) and 'model' in ckpt:
                model_global.load_state_dict(ckpt['model'])
            elif isinstance(ckpt, dict):
                # Probably a state_dict
                model_global.load_state_dict(ckpt)
            else:
                # Fallback for unexpected formats
                model_global.load_state_dict(ckpt)
            print(f"Worker loaded model: {model_path_str}")
        except Exception as e:
            print(f"Worker failed to load model: {e}")
        model_global.eval()

    # Initialize AlphaZero Evaluator for the worker
    global evaluator_global
    if model_global:
        evaluator_global = engine_rust.PyAlphaZeroEvaluator(
            model_global, 
            engine_rust.AlphaZeroTensorType.Vanilla
        )
    else:
        evaluator_global = None

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

# Removed redundant map_engine_to_vanilla (now in vanilla_utils.py)


def play_one_game(d0, d1, sims_per_move, mirror_seed=None, iteration=0):
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
                d0["members"]+d0["lives"], d1["members"]+d1["lives"], 
                d0["energy"], d1["energy"], [], [], mirror_seed
            )
        else:
            state.initialize_game(
                d0["members"]+d0["lives"], d1["members"]+d1["lives"], 
                d0["energy"], d1["energy"], [], []
            )
        
        initial_decks = [d0["members"] + d0["lives"], d1["members"] + d1["lives"]]
        game_history = []
        max_moves = 1000
        moves_taken = 0
        winner = None 
        
        # Stall detection
        last_state_hash = None
        stall_count = 0
        exit_reason = "Unknown"
        
        while not state.is_terminal() and state.turn < 40 and moves_taken < max_moves:
            # Hash-based stall detection
            current_state_str = f"{state.turn}_{state.current_player}_{state.phase}_{len(state.get_legal_action_ids())}"
            if current_state_str == last_state_hash:
                stall_count += 1
            else:
                stall_count = 0
                last_state_hash = current_state_str
            
            if stall_count >= 50: 
                break
            legal_ids = state.get_legal_action_ids()
            if not legal_ids:
                break
            
            state_json = json.loads(state.to_json())
            current_phase = state_json.get('phase', -4)
            curr_p_data = state_json['players'][state.current_player]
            
            # Move selection
            action_engine = None
            
            # FAST BYPASS FOR NON-LEARNING PHASES
            # Phase -4: Setup (Waiting for players)
            # Phase -3: RPS
            # Phase -2: Turn Choice
            if current_phase == -4: 
                if 0 in legal_ids: action_engine = 0
            elif current_phase in [-3, -2]:
                action_engine = random.choice(legal_ids)
            
            if action_engine is not None:
                state.step(action_engine)
                state.auto_step(db_engine_global)
                moves_taken += 1
                continue

            # MCTS / Neural Search for Interactive Phases
            # -1: Mulligan, 0: Energy, 4: Main, 5: LiveSet, 8: LiveResult, 10: Response
            interactive_phases = [-1, 0, 4, 5, 8, 10]
            
            # --- VANILLA OPTIMIZATION: Full-Turn Planning & Soft Policy ---
            # Curriculum: Use DFS teacher early, switch to neural MCTS later
            # This allows the model to learn the basics from DFS and then surpass it!
            use_dfs = (current_phase in [4, 5]) and (iteration < CURRICULUM_SWITCH_ITER)
            
            if use_dfs:
                evals, sequence = state.plan_full_turn(db_engine_global)
                if sequence:
                    # Execute ONLY the first action of the evaluation to keep states and evaluations perfectly paired
                    seq_action = sequence[0]
                    
                    # Record current state
                    obs_np = state.to_vanilla_tensor()
                    mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
                    legal_ids = state.get_legal_action_ids()
                    v_to_e = {}
                    for aid in legal_ids:
                        vid = map_engine_to_vanilla(curr_p_data, aid, initial_decks[state.current_player], current_phase)
                        if 0 <= vid < ACTION_SPACE:
                            mask[vid] = True
                            v_to_e[vid] = aid
                    
                    # Soft Policy from DFS evaluations
                    policy_target = np.zeros(ACTION_SPACE, dtype=np.float32)
                    
                    if evals:
                        valid_evs = []
                        vids = []
                        for aid, ev in evals:
                            vid = map_engine_to_vanilla(curr_p_data, aid, initial_decks[state.current_player], current_phase)
                            if 0 <= vid < ACTION_SPACE:
                                valid_evs.append(ev)
                                vids.append(vid)
                        
                        if valid_evs:
                            evs_arr = np.array(valid_evs)
                            # Warmer temperature (0.5) so alternatives get meaningful probability
                            exp_evs = np.exp((evs_arr - np.max(evs_arr)) / DFS_SOFTMAX_TEMP)
                            probs = exp_evs / np.sum(exp_evs)
                            for vid, p in zip(vids, probs):
                                policy_target[vid] = p
                        else:
                            target_vid = map_engine_to_vanilla(curr_p_data, seq_action, initial_decks[state.current_player], current_phase)
                            if 0 <= target_vid < ACTION_SPACE:
                                policy_target[target_vid] = 1.0
                    else:
                        target_vid = map_engine_to_vanilla(curr_p_data, seq_action, initial_decks[state.current_player], current_phase)
                        if 0 <= target_vid < ACTION_SPACE:
                            policy_target[target_vid] = 1.0

                    game_history.append({
                        "obs": obs_np,
                        "policy": policy_target,
                        "player": state.current_player,
                        "mask": mask,
                        "turn": state.turn
                    })
                    
                    # Exploration: occasionally deviate from the DFS pick.
                    # Because we re-plan EVERY step now, exploration is totally safe and won't break sequences.
                    if random.random() < EXPLORE_EPS and len(legal_ids) > 1:
                        actual_action = random.choice(legal_ids)
                    else:
                        actual_action = seq_action
                    
                    state.step(actual_action)
                    state.auto_step(db_engine_global)
                    moves_taken += 1
                    
                    # Refresh data for next game loop iteration
                    if not state.is_terminal():
                        state_json = json.loads(state.to_json())
                        curr_p_data = state_json['players'][state.current_player]

                    continue # Move to next game loop iteration

            if sims_per_move > 0 and current_phase in interactive_phases and evaluator_global:
                suggestions = state.search_mcts_alphazero(sims_per_move, evaluator_global, 64)
            elif sims_per_move > 0 and current_phase in interactive_phases:
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

            # Mapping diagnostics disabled during production training
            # (was causing disk I/O contention across workers)

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
                        
                        if moves_taken < 15:
                            action_vid = np.random.choice(vids, p=probs)
                        elif moves_taken < 30:
                            # Warm sampling: bias toward best but still explore
                            temp_probs = probs ** 2
                            temp_probs = temp_probs / temp_probs.sum()
                            action_vid = np.random.choice(vids, p=temp_probs)
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
            
            # Debug: Reduced per-step logging
            # if moves_taken % 50 == 0:
            #    state_json_after = json.loads(state.to_json())
            #    print(f"[DEBUG] Step: move={moves_taken}, phase={state_json_after.get('phase')}, turn={state_json_after.get('turn')}, player={state.current_player}, action={action_engine}")
            
            # Check for terminal state after each move (like benchmark)
            if state.is_terminal():
                winner = state.get_winner()
                exit_reason = "Terminal"
                break
            
            moves_taken += 1
        
        if moves_taken >= max_moves:
            exit_reason = "Max moves reached"
        elif state.turn >= 40:
            exit_reason = "Turn limit reached"
            
        if exit_reason != "Terminal" and state.turn == 0:
            print(f"[DEBUG] 0-Turn Game! Reason: {exit_reason}, Phase: {state.phase}, Legal: {len(state.get_legal_action_ids())}")
        
        # Debug: Check final state
        print(f"[DEBUG] Game ending - is_terminal: {state.is_terminal()}, turn: {state.turn}, winner: {state.get_winner()}")
        
        # Force terminal check
        if not state.is_terminal() and state.turn >= 40:
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
        # Reward Curve Tuning:
        # 1.0 until turn 5 (Elite Speed)
        # 0.5 by turn 10 (Mediocre/Bad for competitive play)
        # Exponential decay after turn 5: 0.87 per turn
        p0_final_lives = len(state.get_player(0).success_lives)
        p1_final_lives = len(state.get_player(1).success_lives)
        game_turns = max(state.turn, 1)
        
        if winner == -1: # Draw/Timeout logic handled separately in h-loop
            win_discount = 0.5 
        elif game_turns <= 5:
            win_discount = 1.0
        else:
            # 1.0 * (0.87 ^ (turns - 5)) => Turn 10 is exactly ~0.50
            win_discount = max(1.0 * (0.87 ** (game_turns - 5)), 0.1)
        
        new_transitions = []
        for h in game_history:
            if winner == h['player']:
                # Win: uses the speed-adjusted discount
                val = win_discount
            elif winner == 1 - h['player']:
                # Loss: surviving longer is slightly less bad, capped at 0.15
                val = min(0.005 * game_turns, 0.15)
            else:
                # Tie or Timeout: reward shaping based on live count diff
                my_lives = p0_final_lives if h['player'] == 0 else p1_final_lives
                opp_lives = p1_final_lives if h['player'] == 0 else p0_final_lives
                val = np.clip(0.5 + (my_lives - opp_lives) * 0.1, 0.0, 1.0)
            
            new_transitions.append((
                h['obs'],
                _dense_to_sparse(h['policy']),
                h['mask'],
                np.array([float(val)], dtype=np.float32)
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
        
    total_loss /= max(1, actual_steps)
    
    # Aggressive VRAM cleanup after training
    torch.cuda.empty_cache()
    
    return total_loss

def main():
    print("[DEBUG] Entered main()", flush=True)
    checkpoint_dir = Path(__file__).parent / "vanilla_checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    tournament_decks = load_tournament_decks(full_db)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # FP32 trainer — GradScaler + autocast handles mixed precision in training loop
    model = HighFidelityAlphaNet(input_dim=OBS_DIM, num_actions=ACTION_SPACE).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scaler = torch.amp.GradScaler('cuda' if device.type == 'cuda' else 'cpu')
    
    # Prepare stripped DB for main-process benchmarks (avoids redundant loads)
    stripped_db = json.loads(json.dumps(full_db))
    for cat in ["member_db", "live_db"]:
        for cid, data in stripped_db.get(cat, {}).items():
            data["abilities"] = []
            data["ability_flags"] = 0
            if "synergy_flags" in data:
                data["synergy_flags"] &= 1
    db_json_str_vanilla = json.dumps(stripped_db)
    db_engine_main = engine_rust.PyCardDatabase(db_json_str_vanilla)
    
    checkpoint_path = checkpoint_dir / "latest.pt"
    weights_path = checkpoint_dir / "weights_only.pt"
    start_it = 0
    if checkpoint_path.exists():
        print(f"Resuming: {checkpoint_path}")
        # Added mmap=True for faster loading on Windows
        ckpt = torch.load(str(checkpoint_path), map_location=device, weights_only=True, mmap=True)
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
    
    # Set env var for workers before creating executor
    os.environ["WORKER"] = "1"
    
    log_file = open(str(checkpoint_dir / "training_log.csv"), "a", encoding="utf-8")
    if start_it == 0:
        log_file.write("iter,loss,avg_turns,p0_wins,p1_wins,buffer_size,bench_turns,bench_score,gen_time,train_time\n")
        
    print(f"--- Vanilla Loop: Iter {start_it} onwards ---", flush=True)
    
    print(f"[DEBUG] Creating ProcessPoolExecutor with {NUM_WORKERS} workers...", flush=True)
    # Flush cache before starting workers
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    try:
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=NUM_WORKERS, 
            initializer=init_worker, 
            initargs=(db_json_str_vanilla, str(weights_path) if weights_path.exists() else (str(checkpoint_path) if checkpoint_path.exists() else None), "cpu")
        ) as executor:
            for it in range(start_it, NUM_ITERATIONS):
                print(f"\n=== Starting Iteration {it} ===", flush=True)
                gen_start = time.time()
                futures = []
                for i in range(GAMES_PER_ITER):
                    d0 = random.choice(tournament_decks)
                    d1 = random.choice(tournament_decks)
                    seed = random.getrandbits(64) if MIRROR else None
                    futures.append(executor.submit(play_one_game, d0, d1, SIMS_PER_MOVE, seed, it))
                
                game_stats = []
                new_transitions = []
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
                    # Pass existing model and db_engine to avoid redundant disk I/O
                    bench_turns, bench_score = run_benchmark(model=model, db=db_engine_main, sims=128)
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
                    # Save a lighter weights-only version for workers
                    torch.save(model.state_dict(), str(weights_path))
                    print(f"[CHECKPOINT] Saved to {checkpoint_path} and {weights_path}")
                    
    except KeyboardInterrupt:
        print("\n[STOP] KeyboardInterrupt detected. Saving progress...")
        torch.save({'model': model.state_dict(), 'optimizer': optimizer.state_dict(), 'it': it}, str(checkpoint_path))
        torch.save(model.state_dict(), str(weights_path))
        print(f"[CHECKPOINT] Saved to {checkpoint_path} and {weights_path}")
        buffer.flush()
        print("[BUFFER] Flushed to disk.")
    finally:
        log_file.close()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
