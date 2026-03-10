import os
import random
import time

import numpy as np
import torch

# Reduce CUDA memory fragmentation on 4GB GPUs
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
import concurrent.futures
import json
import sys
from pathlib import Path

from disk_buffer import PersistentBuffer

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

# Robust path detection for the Rust engine
search_paths = [
    root_dir / "engine_rust_src" / "target" / "release",
    root_dir / "engine_rust_src" / "target" / "dev-release",
    root_dir / "engine_rust_src" / "target" / "debug",
]
for p in search_paths:
    if (p / "engine_rust.pyd").exists() or (p / "engine_rust.dll").exists():
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
            break

import engine_rust
import torch.nn.functional as F

from alphazero.alphanet import AlphaNet
from engine.game.deck_utils import UnifiedDeckParser

# ============================================================
# CONFIGURATION (v8 — Relational Transformer + Action Branching)
# ============================================================
NUM_ITERATIONS = 1000000

# --- Self-Play ---
GAMES_PER_ITER = 8
SIMS_PER_MOVE = 128
SRR = 8.0  # Sample Reuse Ratio (How many times each move is seen)

# --- Training (The "Smarter Parallel" Mode) ---
TRAIN_STEPS_PER_ITER = 20
BATCH_SIZE = 256  # Physical batch: 256 is the stable peak for 4GB VRAM
ACCUM_STEPS = 4  # Effective batch = 256 * 4 = 1024
LR = 0.001  # Effective for batch 1024 (256 * 4)
ENTROPY_LAMBDA = 0.01
DIRICHLET_ALPHA = 0.3  # For exploration noise
DIRICHLET_EPS = 0.25

# --- Buffer ---
MAX_BUFFER_SIZE = (
    500000  # AlphaGo Zero scale enabled by disk_buffer.py using bfloat16 compression of observations on disk
)

# --- Global worker variables for parallel execution ---
db_engine_global = None


def init_worker(db_path_str):
    """Load DB from disk in each worker to avoid pickling the full JSON across process boundaries."""
    global db_engine_global
    with open(db_path_str, "r", encoding="utf-8") as f:
        db_json_str = f.read()
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
        if not results:
            continue

        d = results[0]
        m, l, e = [], [], []

        for code in d["main"]:
            cdata = parser.resolve_card(code)
            if not cdata:
                continue
            if cdata.get("type") == "Member":
                m.append(cdata["card_id"])
            elif cdata.get("type") == "Live":
                l.append(cdata["card_id"])

        for code in d["energy"]:
            cdata = parser.resolve_card(code)
            if cdata:
                e.append(cdata["card_id"])

        if len(m) >= 30:
            loaded_decks.append(
                {
                    "name": deck_file.stem,
                    "members": (m + m * 4)[:48],
                    "lives": (l + l * 4)[:12],
                    "energy": (e + standard_energy_ids * 12)[:12],
                }
            )
    return loaded_decks


def get_minimal_state(state):
    """Parses full engine JSON into the minimal UI-compatible format for debugging."""
    import json

    try:
        raw_json = state.to_json()
        data = json.loads(raw_json)

        def get_id(card):
            if card is None:
                return -1
            if isinstance(card, dict):
                return card.get("id", -1)
            return card

        return {
            "phase": data.get("phase"),
            "turn": data.get("turn"),
            "players": [
                {
                    "_label": f"Player {i + 1}",
                    "stage": [get_id(c) for c in (p.get("stage") or [])],
                    "live_zone": [get_id(c) for c in (p.get("live_zone") or [])],
                    "hand": [get_id(c) for c in (p.get("hand") or [])],
                    "success_lives": [get_id(c) for c in (p.get("success_lives") or [])],
                    "energy": [get_id(c) for c in (p.get("energy") or [])],
                    "discard": [get_id(c) for c in (p.get("discard") or [])],
                }
                for i, p in enumerate(data.get("players") or [])
            ],
        }
    except Exception as e:
        return {"error": str(e)}


def play_one_game(d0, d1, sims_per_move, dirichlet_alpha, dirichlet_eps):
    """Worker function for parallel game generation."""
    import random

    import engine_rust

    state = engine_rust.PyGameState(db_engine_global)
    state.initialize_game(d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = True
    state.debug_mode = False

    game_history = []
    action_trace = []
    max_moves = 1000  # Hard exit: state.turn may not advance every step (suspensions/triggers)
    moves_taken = 0
    while not state.is_terminal() and state.turn < 20 and moves_taken < max_moves:
        # Capture state BEFORE action selection
        board_snapshot = get_minimal_state(state)

        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            break

        eval_mode = engine_rust.EvalMode.Normal  # Use full OriginalHeuristic at leaf nodes (not random rollouts)
        suggestions = state.get_mcts_suggestions(sims_per_move, 1.41, engine_rust.SearchHorizon.GameEnd(), eval_mode)

        policy_target = np.zeros(22000, dtype=np.float32)
        total_visits = sum(s[2] for s in suggestions)
        if total_visits > 0:
            # 1. Base Policy from MCTS
            p_mcts = np.zeros(22000, dtype=np.float32)
            for aid, q, v in suggestions:
                p_mcts[aid] = v / total_visits

            # 2. Add Dirichlet Noise to Root (Self-Play Exploration via Label Smoothing)
            noise = np.random.dirichlet([dirichlet_alpha] * len(suggestions))
            for idx, (aid, q, v) in enumerate(suggestions):
                policy_target[aid] = (1 - dirichlet_eps) * p_mcts[aid] + (dirichlet_eps * noise[idx])

        obs = state.to_alphazero_tensor()
        mask = np.zeros(22000, dtype=np.bool_)
        for aid in legal_ids:
            mask[aid] = True

        game_history.append(
            {"obs": obs, "policy": policy_target, "player": state.current_player, "mask": mask, "turn": state.turn}
        )

        # Action selection (Temperature Schedule: Exploratory first 30 turns, then Greedy)
        vts = [s[2] for s in suggestions]
        acts = [s[0] for s in suggestions]

        try:
            if not acts or sum(vts) == 0:
                if not legal_ids:
                    break
                action = random.choice(legal_ids)
            else:
                if state.turn < 10:
                    # Proportional sampling (Higher exploration in opening/mid turns)
                    action = random.choices(acts, weights=vts, k=1)[0]
                else:
                    # Greedy sampling with random tie-breaking
                    max_v = np.max(vts)
                    best_indices = np.where(vts == max_v)[0]
                    best_idx = random.choice(best_indices)
                    action = acts[best_idx]
        except Exception:
            if not legal_ids:
                break
            action = random.choice(legal_ids)

        v_label = state.get_verbose_label(action)
        state.step(action)
        action_trace.append(
            {
                "p": int(state.current_player),
                "id": int(action),
                "label": v_label,
                "state": board_snapshot,  # Log state at the start of this move
            }
        )
        state.auto_step(db_engine_global)
        moves_taken += 1

    winner = state.get_winner()
    winner = state.get_winner()
    if state.is_terminal():
        reason = "Terminal"
    elif moves_taken >= max_moves:
        reason = "Loop"
    else:
        reason = "Turn"

    new_transitions = []

    p0 = state.get_player(0)
    p1 = state.get_player(1)
    p0_lives = len(p0.success_lives)
    p1_lives = len(p1.success_lives)
    for t in game_history:
        # ... [win_prob logic] ...
        win_prob = 1.0 if t["player"] == winner else 0.0 if winner in (0, 1) else 0.5

        my_idx = t["player"]
        opp_idx = 1 - my_idx
        my_l = p0_lives if my_idx == 0 else p1_lives
        opp_l = p1_lives if my_idx == 0 else p0_lives
        momentum = max(-1.0, min(1.0, (my_l - opp_l) / 5.0))

        # 3. Efficiency (Strategic Win Timing)
        tn = t["turn"]
        if tn <= 5:
            efficiency = 1.0
        else:
            efficiency = max(0.0, (15 - tn) / 10.0) ** 2

        target_v = np.array([win_prob, momentum, efficiency], dtype=np.float32)
        nz_indices = np.where(t["policy"] > 0)[0].astype(np.uint16)
        nz_values = t["policy"][nz_indices].astype(np.float16)
        obs_f32 = np.array(t["obs"], dtype=np.float32)
        obs_f32 = np.nan_to_num(obs_f32, nan=0.0, posinf=0.0, neginf=0.0)
        sparse_mask = np.where(t["mask"])[0].astype(np.uint16)
        new_transitions.append((obs_f32, (nz_indices, nz_values), sparse_mask, target_v))

    game_stats = {
        "turns": state.turn,
        "p0_lives": p0_lives,
        "p1_lives": p1_lives,
        "winner": winner,
        "reason": reason,
        "trace": action_trace,
        "d0_name": d0["name"],
        "d1_name": d1["name"],
        "d0_cards": d0["members"] + d0["lives"] + d0["energy"],
        "d1_cards": d1["members"] + d1["lives"] + d1["energy"],
    }

    return new_transitions, game_stats


def train_fixed_steps(model, buffer, optimizer, scaler, device, num_steps, batch_size):
    """Train for exactly `num_steps` gradient updates, sampling randomly from buffer."""
    model.train()
    train_start_time = time.time()
    total_loss = 0
    total_vloss = 0
    total_ploss = 0
    total_accuracy = 0
    total_rand_accuracy = 0
    actual_steps = 0
    buf_size = buffer.count
    nan_count = 0

    # Reset cumulative audit timers for this call
    train_fixed_steps._ts = 0
    train_fixed_steps._tt = 0
    train_fixed_steps._tf = 0
    train_fixed_steps._tb = 0

    # Precompute LUT indices once — constant across all steps
    lut_valid = (model.action_type_lut >= 0) & (model.action_type_lut < model.num_action_types)
    lut_t_idx = model.action_type_lut[lut_valid]  # (num_valid,)
    lut_s_idx = model.action_sub_lut[lut_valid]  # (num_valid,)
    # action_sub_lut in AlphaNet.__init__ stores raw unclamped aid-start values
    # (e.g. SelectChoice sub can be 4999) — clamp so flat_sub stays in [0, 1800)
    lut_s_clamped = lut_s_idx.clamp(max=model.max_sub_index - 1)
    lut_flat_sub = lut_t_idx * model.max_sub_index + lut_s_clamped  # (num_valid,)
    lut_t_exp = lut_t_idx.unsqueeze(0).expand(batch_size, -1)  # (B, num_valid)
    lut_fs_exp = lut_flat_sub.unsqueeze(0).expand(batch_size, -1)  # (B, num_valid)

    # Background fetcher to hide SSD read latency
    import concurrent.futures

    prefetch_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    next_batch_future = prefetch_executor.submit(buffer.sample, batch_size)

    for step in range(num_steps):
        if buf_size < batch_size:
            break

        # --- Phase 1: CPU data sampling (Prefetched) ---
        t0 = time.perf_counter()
        batch_data = next_batch_future.result()
        if batch_data is None:
            break

        obs_np, sparse_pol, msk_np, val_np = batch_data

        # Kick off the next disk read in the background immediately
        next_batch_future = prefetch_executor.submit(buffer.sample, batch_size)
        t1 = time.perf_counter()

        # --- Phase 2: CPU → GPU transfer + GPU Densification ---
        obs_t = torch.from_numpy(obs_np).to(device, non_blocking=True)
        obs_t = torch.nan_to_num(obs_t, nan=0.0, posinf=0.0, neginf=0.0)

        # Transfer only sparse policy parts and densify at VRAM speed natively
        row_v, col_v, val_v = sparse_pol
        gpu_row = torch.from_numpy(row_v).to(device, non_blocking=True).long()
        gpu_col = torch.from_numpy(col_v).to(device, non_blocking=True).long()
        gpu_val = torch.from_numpy(val_v).to(device, non_blocking=True)

        pol_t = torch.zeros(batch_size, model.num_actions, device=device)
        pol_t.index_put_((gpu_row, gpu_col), gpu_val)

        msk_t = torch.from_numpy(msk_np).to(device, non_blocking=True)
        val_t = torch.from_numpy(val_np).float().to(device, non_blocking=True)
        t2 = time.perf_counter()

        optimizer.zero_grad(set_to_none=True)

        # --- Phase 3: Forward + loss ---
        # amp_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        # Stick to float16 - often has smaller workspace requirements on laptop cards
        amp_dtype = torch.float16
        with torch.amp.autocast("cuda" if device.type == "cuda" else "cpu", dtype=amp_dtype):
            type_logits, sub_logits, value_preds = model.forward_heads(obs_t, mask=msk_t)
            value_loss = F.mse_loss(value_preds, val_t)

            # Policy loss compression (unchanged logic)
            pol_valid = pol_t[:, lut_valid]
            type_target = torch.zeros(batch_size, model.num_action_types, device=device)
            type_target.scatter_add_(1, lut_t_exp, pol_valid)
            sub_target = torch.zeros(batch_size, model.num_action_types * model.max_sub_index, device=device)
            sub_target.scatter_add_(1, lut_fs_exp, pol_valid)

            log_type = F.log_softmax(type_logits, dim=1).clamp(min=-100.0)
            type_loss = F.kl_div(log_type, type_target, reduction="batchmean")

            sub_logits_3d = sub_logits.view(batch_size, model.num_action_types, model.max_sub_index)
            sub_tgt_3d = sub_target.view(batch_size, model.num_action_types, model.max_sub_index)
            log_sub = F.log_softmax(sub_logits_3d, dim=2).clamp(min=-100.0)
            sub_loss = F.kl_div(
                log_sub.reshape(batch_size, -1), sub_tgt_3d.reshape(batch_size, -1), reduction="batchmean"
            )

            # Scale loss for gradient accumulation
            policy_loss = type_loss + sub_loss
            loss = (
                value_loss + policy_loss + (ENTROPY_LAMBDA * -log_type.exp().mul(log_type).sum(1).mean())
            ) / ACCUM_STEPS
        t3 = time.perf_counter()

        if torch.isnan(loss) or torch.isinf(loss):
            nan_count += 1
            if nan_count <= 3:
                print(f"  [WARN] NaN/Inf loss at step {step}: vl={value_loss.item():.4f} pl={policy_loss.item():.4f}")
            continue

        # Accuracy metrics (Model vs Random)
        with torch.no_grad():
            # 1. Model Prediction Accuracy (Masked Vectorized)
            masked_logits = type_logits.detach().clone()

            # Create a 1D mapping tensor from action_id -> type_id
            t_map = torch.full((model.num_actions,), -1, dtype=torch.long, device=device)
            t_map[lut_valid] = model.action_type_lut[lut_valid]

            # Broadcast mapping and extract only valid legal moves
            # msk_t is (B, num_actions)
            batch_indices = torch.arange(batch_size, device=device).unsqueeze(1).expand(-1, model.num_actions)
            b_val = batch_indices[msk_t]
            t_val = t_map.unsqueeze(0).expand(batch_size, -1)[msk_t]

            valid_mask = t_val >= 0
            type_mask = torch.zeros(batch_size, model.num_action_types, device=device, dtype=torch.bool)
            type_mask[b_val[valid_mask], t_val[valid_mask]] = True

            masked_logits[~type_mask] = -60000.0
            pred_type = torch.argmax(masked_logits, dim=1)  # (B,)
            true_type = model.action_type_lut[torch.argmax(pol_t, dim=1)]  # (B,)
            correct = (pred_type == true_type).sum().item()
            total_accuracy += correct / batch_size

            # 2. Random Baseline Accuracy (Picking any legal move at random) - Vectorized
            rand_indices = torch.multinomial(msk_t.float(), 1).squeeze(1)  # (B,)
            rand_type = model.action_type_lut[rand_indices]
            rand_correct = (rand_type == true_type).sum().item()
            total_rand_accuracy += rand_correct / batch_size

        # --- Phase 4: Backward (Accumulated) ---
        scaler.scale(loss).backward()

        # Only step the optimizer every ACCUM_STEPS
        if (step + 1) % ACCUM_STEPS == 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)

        t4 = time.perf_counter()

        # Report raw magnitude (unscaled by accum_steps) so metrics are intuitive
        total_loss += loss.item() * ACCUM_STEPS
        total_vloss += value_loss.item()
        total_ploss += policy_loss.item()
        actual_steps += 1

        # Accumulate phase timings
        time_sample = getattr(train_fixed_steps, "_ts", 0) + (t1 - t0)
        train_fixed_steps._ts = time_sample
        time_transfer = getattr(train_fixed_steps, "_tt", 0) + (t2 - t1)
        train_fixed_steps._tt = time_transfer
        time_forward = getattr(train_fixed_steps, "_tf", 0) + (t3 - t2)
        train_fixed_steps._tf = time_forward
        time_backward = getattr(train_fixed_steps, "_tb", 0) + (t4 - t3)
        train_fixed_steps._tb = time_backward

        # Audit log every 50 steps
        if actual_steps % 50 == 0:
            elapsed_so_far = time.time() - train_start_time
            sps = actual_steps / max(1e-6, elapsed_so_far)
            avg_l = total_loss / actual_steps
            avg_acc = (total_accuracy / actual_steps) * 100
            avg_rnd = (total_rand_accuracy / actual_steps) * 100
            n = actual_steps
            mem_str = ""
            if device.type == "cuda":
                alloc = torch.cuda.memory_allocated(device) / 1024**2
                reserv = torch.cuda.memory_reserved(device) / 1024**2
                mem_str = f" | alloc={alloc:.0f}MB pool={reserv:.0f}MB"
            print(
                f"  [Train {actual_steps:4d}/{num_steps}] {sps:.1f}s/s | Loss:{avg_l:.4f} | "
                f"Acc:{avg_acc:.1f}% (vs {avg_rnd:.1f}% random){mem_str}",
                flush=True,
            )

    # Cleanup prefetcher
    prefetch_executor.shutdown(wait=False, cancel_futures=True)

    elapsed = time.time() - train_start_time
    steps_per_sec = actual_steps / max(1e-6, elapsed)

    return {
        "loss": total_loss / actual_steps,
        "value": total_vloss / actual_steps,
        "policy": total_ploss / actual_steps,
        "accuracy": total_accuracy / actual_steps,
        "nan_detected": nan_count > 0,
        "steps_per_sec": steps_per_sec,
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
        # Enable TensorFloat-32 (TF32) for RTX Ampere cards (huge speedup for FP32 matmuls)
        torch.set_float32_matmul_precision("high")
        # Cap VRAM at 90% — Leave 10% for workers/Windows.
        # 256 batch is small enough that 90% is totally safe.
        torch.cuda.set_per_process_memory_fraction(0.90, device=0)
        # Let cuDNN benchmark and select the fastest kernel for fixed-shape Transformer inputs
        torch.backends.cudnn.benchmark = True
    model = AlphaNet().to(device)

    # torch.compile requires Triton which is Linux-only — skip on Windows.
    # On Linux this gives a meaningful speedup; on Windows it crashes on first inference.
    if hasattr(torch, "compile") and sys.platform != "win32":
        try:
            print("Compiling model with torch.compile...")
            model = torch.compile(model)
        except Exception as e:
            print(f"Could not compile model: {e}")

    # fused=True executes the optimizer step in a single highly optimized GPU kernel
    is_cuda = device.type == "cuda"
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=2e-4, fused=is_cuda)
    scaler = torch.amp.GradScaler("cuda" if is_cuda else "cpu")
    # StepLR cuts LR by half every 10 iterations to allow for fine-tuning
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    checkpoint_dir = Path(__file__).parent
    checkpoint_path = checkpoint_dir / "alphanet_latest.pt"

    start_it = 0
    if checkpoint_path.exists():
        print(f"Loading existing training state: {checkpoint_path}")
        try:
            ckpt = torch.load(str(checkpoint_path), map_location=device, weights_only=False)
            if "model" in ckpt:
                model_state = model.state_dict()
                compatible = {
                    k: v for k, v in ckpt["model"].items() if k in model_state and model_state[k].shape == v.shape
                }
                model.load_state_dict(compatible, strict=False)

                # Restore optimizer/scheduler states
                if "optimizer" in ckpt:
                    try:
                        optimizer.load_state_dict(ckpt["optimizer"])
                    except:
                        print("  Warning: Optimizer state mismatch, starting fresh.")
                if "scheduler" in ckpt:
                    try:
                        scheduler.load_state_dict(ckpt["scheduler"])
                    except:
                        print("  Warning: Scheduler state mismatch.")
                if "scaler" in ckpt:
                    try:
                        scaler.load_state_dict(ckpt["scaler"])
                    except:
                        pass

                # Recover iteration count
                if "it" in ckpt:
                    start_it = ckpt["it"] + 1
                    print(f"Successfully resumed training state (Iter {start_it})")
                else:
                    print("Successfully resumed training state (Iter ???)")
            else:
                # Legacy weight-only file
                model.load_state_dict(ckpt, strict=False)
                print("  Loaded legacy weights-only checkpoint.")
        except Exception as e:
            print(f"Warning: Could not load checkpoint. Starting fresh. Error: {e}")

    # --- Buffer (Disk-backed Scaling) ---
    buffer_dir = checkpoint_dir / "experience"
    master_buffer = PersistentBuffer(buffer_dir, max_size=MAX_BUFFER_SIZE, obs_dim=20500, num_actions=model.num_actions)

    print("--- PURE ZERO v8 (Relational Transformer) ---")
    print(f"MCTS Sims: {SIMS_PER_MOVE}")
    print(f"Train Steps/Iter: {TRAIN_STEPS_PER_ITER}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Buffer Capacity: {MAX_BUFFER_SIZE}")
    print(f"Buffer Current: {master_buffer.count}")
    print("Stop Method: Press Ctrl+C to stop and save.")

    log_path = checkpoint_dir / "overnight_training_log.csv"
    log_exists = log_path.exists() and log_path.stat().st_size > 0
    log_file = open(str(log_path), "a", encoding="utf-8")

    if not log_exists:
        log_file.write(
            "iter,loss,value_loss,policy_loss,accuracy,buffer_size,gen_time,train_time,avg_turns,p0_wins,p1_wins\n"
        )
        # start_it already 0 or from checkpoint
    else:
        # Detect last iteration from log if not already set from checkpoint
        if start_it == 0:
            try:
                with open(str(log_path), "r", encoding="utf-8") as rf:
                    lines = rf.readlines()
                    if len(lines) > 1:
                        last_line = lines[-1]
                        start_it = int(last_line.split(",")[0]) + 1
                        print(f"Resuming from iteration {start_it} (detected from CSV)")
            except Exception as e:
                print(f"  Warning: Could not recover iteration from log: {e}")

    log_file.flush()

    try:
        # 2 workers: safe for 4 GB GPU + 16 GB RAM on Windows.
        # 4 workers caused OOM: each worker holds up to ~8 MB of obs tensors
        # + Rust MCTS trees in RAM simultaneously during a long game.
        max_workers = 2
        print(f"Using {max_workers} worker processes for self-play.")

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=max_workers, initializer=init_worker, initargs=(str(db_path),)
        ) as executor:
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
                    futures.append(
                        executor.submit(play_one_game, d0, d1, SIMS_PER_MOVE, DIRICHLET_ALPHA, DIRICHLET_EPS)
                    )

                game_num = 0
                gen_game_stats = []
                loops_dir = checkpoint_dir / "loops"
                loops_dir.mkdir(exist_ok=True)

                try:
                    for future in concurrent.futures.as_completed(futures, timeout=600):
                        transitions, gstats = future.result()
                        new_transitions.extend(transitions)
                        gen_game_stats.append(gstats)
                        game_num += 1

                        w = gstats["winner"]
                        winner_str = f"P{w}" if w in (0, 1) else "Draw"

                        # LOG SUSPICIOUS GAMES (Loops or Timeouts)
                        if gstats["reason"] != "Terminal":
                            # We record both Loop and Turn hits to audit engine behavior
                            fname = f"trace_it{it}_g{game_num}_{gstats['reason']}.json"
                            trace_file = loops_dir / fname
                            with open(trace_file, "w", encoding="utf-8") as lf:
                                json.dump(gstats, lf, indent=2)
                            print(f"  [AUDIT] {gstats['reason']} detected! Trace: {fname}", flush=True)

                        print(
                            f"  [Game {game_num:2d}/{GAMES_PER_ITER}] {winner_str} | "
                            f"Turns: {gstats['turns']} | "
                            f"Lives: {gstats['p0_lives']}-{gstats['p1_lives']}",
                            flush=True,
                        )
                except concurrent.futures.TimeoutError:
                    print(
                        "  [WARN] Game timed out after 600s — skipping remaining futures for this iteration.",
                        flush=True,
                    )
                    for f in futures:
                        f.cancel()

                gen_time = time.time() - gen_start

                # ========================================
                # 2. UPDATE BUFFER
                # ========================================
                for t in new_transitions:
                    master_buffer.add(t[0], t[1], t[3], t[2])

                if not gen_game_stats:
                    print(f"  [WARN] All games timed out — skipping training for iteration {it}.", flush=True)
                    continue
                if master_buffer.count < BATCH_SIZE:
                    continue

                # ========================================
                # 3. TRAIN — Fixed Sample Reuse Ratio (SRR)
                # ========================================
                train_start = time.time()
                new_moves = len(new_transitions)
                target_steps = int((new_moves * SRR) / BATCH_SIZE)
                dynamic_steps = max(TRAIN_STEPS_PER_ITER, min(TRAIN_STEPS_PER_ITER * 5, target_steps))

                stats = train_fixed_steps(
                    model, master_buffer, optimizer, scaler, device, num_steps=dynamic_steps, batch_size=BATCH_SIZE
                )
                train_time = time.time() - train_start

                # ========================================
                # 4. METRICS (Policy Accuracy)
                # ========================================
                pol_acc = stats["accuracy"] * 100
                current_lr = optimizer.param_groups[0]["lr"]

                # Update scheduler after each iteration
                scheduler.step()

                # ========================================
                # 5. LOG & SAVE
                # ========================================
                winners = [s["winner"] for s in gen_game_stats]
                reasons = [s["reason"] for s in gen_game_stats]
                avg_turns = sum(s["turns"] for s in gen_game_stats) / len(gen_game_stats)
                p0_wins = winners.count(0)
                p1_wins = winners.count(1)

                # Detailed Draw Breakdown: [L]oop, [T]urn limit, [N]atural tie (Terminal)
                d_loop = reasons.count("Loop")
                d_turn = reasons.count("Turn")
                d_nat = reasons.count("Natural")
                draw_str = f"D:{d_nat + d_loop + d_turn}(L:{d_loop} T:{d_turn} N:{d_nat})"

                print(
                    f"It {it:3d} | Games: [P0:{p0_wins} P1:{p1_wins} {draw_str}] | AvgT: {avg_turns:.1f} | "
                    f"Buf: {master_buffer.count:5d} (+{new_moves:4d}) | "
                    f"Acc: {pol_acc:5.1f}% | Loss: {stats['loss']:.4f} | "
                    f"LR: {current_lr:.6f} | S/s: {stats['steps_per_sec']:.1f} | Gen: {gen_time:.0f}s | Train: {train_time:.0f}s"
                )

                log_file.write(
                    f"{it},{stats['loss']},{stats['value']},{stats['policy']},{pol_acc},{master_buffer.count},{gen_time:.1f},{train_time:.1f},{avg_turns:.1f},{p0_wins},{p1_wins}\n"
                )
                log_file.flush()

                if it % 10 == 0:
                    master_buffer.flush()
                    if device.type == "cuda":
                        torch.cuda.empty_cache()

                # Full state save (Model + Optimizer + Scheduler + Scaler)
                full_state = {
                    "model": model.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "scheduler": scheduler.state_dict(),
                    "scaler": scaler.state_dict(),
                    "it": it,
                }
                if it % 5 == 0:
                    torch.save(full_state, str(checkpoint_path))
                if it % 20 == 0 and it > start_it:
                    torch.save(full_state, str(checkpoint_dir / f"alphanet_it{it}.pt"))

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
