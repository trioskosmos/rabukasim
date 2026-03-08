import sys, os
import time
from pathlib import Path

# Add project root to sys.path first!
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

print("Step 0: sys.path updated")
import torch
import numpy as np
import engine_rust
import json
import random
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

# Add alphazero/training to path for disk_buffer
training_dir = Path(__file__).resolve().parent
if str(training_dir) not in sys.path:
    sys.path.insert(0, str(training_dir))

print("Step 1: Imports done")

from alphazero.vanilla_net import HighFidelityAlphaNet
from engine.game.deck_utils import UnifiedDeckParser
from disk_buffer import PersistentBuffer
import torch.nn.functional as F

# Configuration
FIXED_SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010]
NUM_ACTIONS = 128
OBS_DIM = 800

# Training configuration with enhancements
NUM_WORKERS = 4  # Number of parallel game workers
TEMP_START = 1.0  # Initial temperature
TEMP_END = 0.1  # Final temperature (decays over iterations)
TEMP_DECAY_ITERS = 5000  # Iterations to decay temperature
DIRICHLET_ALPHA = 0.3  # Dirichlet noise parameter
DIRICHLET_EPSILON = 0.25  # Fraction of exploration noise
LR_WARMUP_ITERS = 100  # Learning rate warmup iterations
LR_START = 1e-5  # Starting learning rate during warmup
LR_MAX = 0.001  # Maximum learning rate after warmup
LR_MIN = 1e-5  # Minimum learning rate for decay
PRIORITY_ALPHA = 0.6  # Priority exponent for PER
PRIORITY_BETA_START = 0.4  # Initial importance sampling exponent
PRIORITY_BETA_END = 1.0  # Final importance sampling exponent


def play_training_game_parallel(args):
    """
    Parallel version of play_training_game for ProcessPoolExecutor.
    Must be at module level for pickling.
    
    Args:
        args: tuple of (deck, seed, sims, db_json_str, temperature)
    
    Returns:
        (transitions, stats)
    """
    deck, seed, sims, db_json_str, temperature = args
    
    # Recreate database and model in this process
    db = engine_rust.PyCardDatabase(db_json_str)
    
    state = engine_rust.PyGameState(db)
    state.silent = True
    state.initialize_game_with_seed(deck["m"], deck["m"], [38]*12, [38]*12, deck["l"], deck["l"], seed)
    
    initial_decks = [state.get_player(0).initial_deck, state.get_player(1).initial_deck]
    game_history = []
    moves = 0
    winner = None
    
    while not state.is_terminal() and state.turn < 25 and moves < 500:
        legal = state.get_legal_action_ids()
        if not legal:
            state.auto_step(db)
            legal = state.get_legal_action_ids()
            if not legal: break
        
        pj = json.loads(state.to_json())
        cp = pj.get('phase', -4)
        curr_p = state.current_player
        
        # Setup/RPS/TurnChoice bypass
        if cp == -4:
            if 0 in legal:
                state.step(0); state.auto_step(db); moves += 1; continue
        if cp == -3:
            action = random.choice(legal)
            state.step(action); state.auto_step(db); moves += 1; continue
        if cp == -2:
            action = random.choice(legal)
            state.step(action); state.auto_step(db); moves += 1; continue
        
        # Get legal vanilla indices
        mask = np.zeros(NUM_ACTIONS, dtype=np.bool_)
        legal_vanilla_indices = []
        v_to_e = {}
        for aid in legal:
            vid = map_engine_to_vanilla(pj['players'][curr_p], aid, initial_decks[curr_p], cp)
            if 0 <= vid < NUM_ACTIONS:
                mask[vid] = True
                legal_vanilla_indices.append(vid)
                v_to_e[vid] = aid
        
        # MCTS for decision phases
        action = -1
        policy_target = np.zeros(NUM_ACTIONS, dtype=np.float32)
        
        if sims > 0 and cp in [4, 5, -1, 0]:
            sugg = state.search_mcts(sims, 0.0, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal, None)
            if sugg:
                total_visits = sum(s[2] for s in sugg)
                if total_visits > 0:
                    for engine_id, q, visits in sugg:
                        vid = map_engine_to_vanilla(pj['players'][curr_p], engine_id, initial_decks[curr_p], cp)
                        if 0 <= vid < NUM_ACTIONS:
                            policy_target[vid] += visits / total_visits
        
        # Apply Dirichlet noise
        if policy_target.sum() > 0:
            policy_target = apply_dirichlet_noise(policy_target, legal_vanilla_indices, DIRICHLET_ALPHA, DIRICHLET_EPSILON)
        
        # Select action using temperature
        if len(legal_vanilla_indices) > 0 and policy_target[legal_vanilla_indices].sum() > 0:
            selected_vid = select_action_with_temperature(policy_target, legal_vanilla_indices, temperature)
            action = v_to_e.get(selected_vid, legal[0])
        else:
            action = v_to_e.get(legal_vanilla_indices[0], legal[0]) if legal_vanilla_indices else legal[0]
        
        # Record transition (only for decision phases)
        if sims > 0 and cp in [4, 5, -1, 0]:
            obs_np = state.to_vanilla_tensor()
            mask = np.zeros(NUM_ACTIONS, dtype=np.bool_)
            for aid in legal:
                vid = map_engine_to_vanilla(pj['players'][curr_p], aid, initial_decks[curr_p], cp)
                if 0 <= vid < NUM_ACTIONS: mask[vid] = True
            
            game_history.append({
                "obs": obs_np,
                "policy": policy_target,
                "player": curr_p,
                "mask": mask
            })
        
        state.step(action)
        state.auto_step(db)
        moves += 1
        
        if state.is_terminal():
            winner = state.get_winner()
            break
    
    # Compute values
    new_transitions = []
    for h in game_history:
        val = 0.5
        if winner == h['player']: val = 1.0
        elif winner == 1 - h['player']: val = 0.0
        
        indices = np.where(h['policy'] > 0)[0]
        values = h['policy'][indices]
        new_transitions.append((h['obs'], (indices, values), h['mask'], np.array([val], dtype=np.float32)))
    
    stats = {
        "turns": state.turn,
        "p0_lives": len(state.get_player(0).success_lives),
        "p1_lives": len(state.get_player(1).success_lives),
        "winner": winner
    }
    return new_transitions, stats

def get_random_seeds(count=10):
    """Generate random seeds for overnight benchmark"""
    return [random.getrandbits(64) for _ in range(count)]

def map_engine_to_vanilla(p_data, engine_id, initial_deck, current_phase=None):
    """Maps engine action ID to vanilla 128-dim action space."""
    if engine_id == 0:
        if current_phase in [-1, 0, 5, 8, 10]: return 7 # Confirm
        return 0 # Pass
    if 300 <= engine_id <= 305: return 1 + (engine_id - 300)
    if engine_id == 11000: return 7
    if 1000 <= engine_id < 1600:
        hand_idx = (engine_id - 1000) // 10
        if hand_idx < len(p_data['hand']):
            card_id = p_data['hand'][hand_idx]
            if initial_deck and card_id in initial_deck:
                try:
                    idx = initial_deck.index(card_id)
                    if idx < 60: return 8 + idx
                except: pass
            if hand_idx < 60: return 8 + hand_idx
    if 400 <= engine_id < 500:
        hand_idx = engine_id - 400
        if hand_idx < len(p_data['hand']):
            card_id = p_data['hand'][hand_idx]
            if initial_deck and card_id in initial_deck:
                try:
                    idx = initial_deck.index(card_id)
                    if idx < 60: return 68 + idx
                except: pass
            if hand_idx < 60: return 68 + hand_idx
    if 20000 <= engine_id <= 20002: return 125 + (engine_id - 20000)
    if 5000 <= engine_id <= 5001: return 123 + (engine_id - 5000)
    if 600 <= engine_id <= 602: return 7
    return -1


def get_lr(it, warmup_iters, max_iters, lr_start, lr_max, lr_min):
    """
    Compute learning rate with warmup and cosine decay.
    """
    if it < warmup_iters:
        # Linear warmup
        return lr_start + (lr_max - lr_start) * it / warmup_iters
    else:
        # Cosine decay
        progress = (it - warmup_iters) / max(warmup_iters, max_iters - warmup_iters)
        progress = min(1.0, progress)
        return lr_min + (lr_max - lr_min) * 0.5 * (1 + math.cos(math.pi * progress))


def get_temperature(it, temp_start, temp_end, decay_iters):
    """
    Compute temperature with exponential decay.
    Higher temperature = more exploration (softer policy)
    Lower temperature = more exploitation (greedy)
    """
    if it >= decay_iters:
        return temp_end
    # Exponential decay from temp_start to temp_end
    decay_rate = math.log(temp_end / temp_start) / decay_iters
    return temp_start * math.exp(decay_rate * it)


def apply_dirichlet_noise(policy, legal_indices, alpha=0.3, epsilon=0.25):
    """
    Apply Dirichlet noise to policy for exploration.
    
    Args:
        policy: numpy array of policy probabilities
        legal_indices: indices of legal actions
        alpha: Dirichlet concentration parameter
        epsilon: fraction of noise to mix in
    
    Returns:
        Modified policy with Dirichlet noise
    """
    if len(legal_indices) == 0:
        return policy
    
    # Generate Dirichlet noise over legal actions
    legal_count = len(legal_indices)
    dirichlet_noise = np.random.dirichlet([alpha] * legal_count)
    
    # Mix noise with original policy
    noisy_policy = policy.copy()
    for i, idx in enumerate(legal_indices):
        noisy_policy[idx] = (1 - epsilon) * policy[idx] + epsilon * dirichlet_noise[i]
    
    # Renormalize
    noisy_policy /= noisy_policy.sum()
    return noisy_policy


def select_action_with_temperature(policy, legal_indices, temperature=1.0):
    """
    Select action using temperature-scaled policy.
    
    Args:
        policy: numpy array of policy probabilities
        legal_indices: indices of legal actions
        temperature: temperature parameter (higher = more random)
    
    Returns:
        Selected action index
    """
    if temperature <= 0.01 or len(legal_indices) == 0:
        # Greedy selection
        return legal_indices[np.argmax(policy[legal_indices])]
    
    # Apply temperature scaling
    scaled_logits = policy[legal_indices] ** (1.0 / temperature)
    scaled_probs = scaled_logits / scaled_logits.sum()
    
    # Sample from distribution
    return legal_indices[np.random.choice(len(legal_indices), p=scaled_probs)]

def run_benchmark(model_path=None, sims=50):
    print(f"Benchmark Init (Sims: {sims})")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    db_path = root_dir / "data" / "cards_vanilla.json"
    if not db_path.exists(): db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f: db_json = json.load(f)
    
    # Strip all abilities to create a pure 'Vanilla' environment (same as overnight_vanilla.py)
    for cat in ["member_db", "live_db"]:
        for cid, data in db_json.get(cat, {}).items():
            data["abilities"] = []
            data["ability_flags"] = 0
            if "synergy_flags" in data:
                data["synergy_flags"] &= 1
    
    db_json_str = json.dumps(db_json)
    db = engine_rust.PyCardDatabase(db_json_str)
    parser = UnifiedDeckParser(db_json)
    
    model = HighFidelityAlphaNet(input_dim=800, num_actions=128).to(device)
    if model_path and Path(model_path).exists():
        ckpt = torch.load(model_path, map_location=device, weights_only=True)
        model.load_state_dict(ckpt['model'] if isinstance(ckpt, dict) and 'model' in ckpt else ckpt)
    model.eval()
    
    decks_dir = root_dir / "ai" / "decks"
    all_decks = []
    for df in list(decks_dir.glob("*.txt"))[:2]:
        with open(df, "r", encoding="utf-8") as f:
            ext = parser.extract_from_content(f.read())
            if ext:
                m, l = [], []
                for c in ext[0]['main']:
                    cd = parser.resolve_card(c)
                    if cd and cd.get("type") == "Member": m.append(cd["card_id"])
                    elif cd and cd.get("type") == "Live": l.append(cd["card_id"])
                if m and l: all_decks.append({"name": df.stem, "m": (m*5)[:48], "l": (l*5)[:12]})

    results = []
    for deck in all_decks:  # Run all available decks
        for seed in FIXED_SEEDS:  # Run all seeds for each deck
            print(f"\n--- START: Deck {deck['name']}, Seed {seed} ---")
            state = engine_rust.PyGameState(db)
            state.initialize_game_with_seed(deck["m"], deck["m"], [38]*12, [38]*12, deck["l"], deck["l"], seed)
            
            p0 = state.get_player(0)
            if len(p0.deck) == 0:
                print(f"!!! CRITICAL: Deck P0 is empty for {deck['name']} seed {seed}!")
                continue

            initial_decks = [state.get_player(0).initial_deck, state.get_player(1).initial_deck]
            moves = 0
            winner = None
            while not state.is_terminal() and state.turn < 25 and moves < 500:
                legal = state.get_legal_action_ids()
                pj = json.loads(state.to_json())
                cp = pj.get('phase', -4)
                curr_p = state.current_player
                
                if not legal:
                    state.auto_step(db)
                    legal = state.get_legal_action_ids()
                    if not legal:
                        break
                
                # Setup / RPS / TurnChoice Bypass
                if cp == -4: # Setup (Internal engine transition)
                    if 0 in legal:
                        state.step(0); state.auto_step(db); moves += 1; continue
                
                if cp == -3: # RPS
                    action = random.choice(legal)
                    state.step(action); state.auto_step(db); moves += 1; continue
                
                if cp == -2: # Turn Choice
                    action = random.choice(legal)
                    state.step(action); state.auto_step(db); moves += 1; continue

                # Use MCTS for decision phases
                action = -1
                if sims > 0 and cp in [4, 5, -1, 0]:
                    sugg = state.search_mcts(sims, 0.0, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal, None)
                    if sugg: action = sugg[0][0]
                
                if action == -1:
                    mask = torch.zeros((1, 128), dtype=torch.bool, device=device)
                    v_to_e = {}
                    for aid in legal:
                        vid = map_engine_to_vanilla(pj['players'][curr_p], aid, initial_decks[curr_p], cp)
                        if 0 <= vid < 128: mask[0, vid] = True; v_to_e[vid] = aid
                    
                    if mask.any():
                        obs = torch.from_numpy(np.array(state.to_vanilla_tensor(), dtype=np.float32)).unsqueeze(0).to(device)
                        with torch.no_grad():
                            lgt, _ = model(obs, mask=mask)
                            action = v_to_e.get(torch.argmax(lgt).item(), legal[0])
                    else:
                        action = legal[0]

                state.step(action)
                state.auto_step(db)
                moves += 1
                
                # Check for winner
                if state.is_terminal():
                    winner = state.get_winner()
            
            p0s = len(state.get_player(0).success_lives)
            p1s = len(state.get_player(1).success_lives)
            total_score = p0s + p1s
            results.append({"turns": state.turn, "score": total_score, "winner": winner})
            print(f"[{deck['name']}] S{seed} | Turns: {state.turn} | Score: {p0s}-{p1s} | Winner: {['P0','P1','Draw'][winner] if winner is not None else 'N/A'}")
            
    if results:
        avg_turns = sum(r['turns'] for r in results) / len(results)
        avg_score = sum(r['score'] for r in results) / len(results)
        print(f"Results: Avg Turns {avg_turns:.1f}, Avg Score {avg_score:.1f} ({len(results)} games)")
        return avg_turns, avg_score
    return 0.0, 0.0  # Default fallback if no results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="alphazero/training/vanilla_checkpoints/latest.pt")
    parser.add_argument("--sims", type=int, default=128)
    parser.add_argument("--loop", action="store_true", help="Run in loop mode for overnight training data collection")
    parser.add_argument("--iters", type=int, default=1000000, help="Number of iterations for loop mode")
    args = parser.parse_args()
    
    if args.loop:
        # Run in loop mode for overnight training (AlphaZero-like with GPU)
        print("=== Running in LOOP mode for overnight training ===")
        
        # Load database for loop mode
        db_path = root_dir / "data" / "cards_vanilla.json"
        if not db_path.exists(): db_path = root_dir / "data" / "cards_compiled.json"
        with open(db_path, "r", encoding="utf-8") as f: db_json = json.load(f)
        
        # Strip abilities for vanilla
        for cat in ["member_db", "live_db"]:
            for cid, data in db_json.get(cat, {}).items():
                data["abilities"] = []
                data["ability_flags"] = 0
                if "synergy_flags" in data:
                    data["synergy_flags"] &= 1
        
        db_json_str = json.dumps(db_json)
        
        # Training config (simpler version without PER for Windows compatibility)
        ACTION_SPACE = 128
        OBS_DIM = 800
        GAMES_PER_ITER = 16
        TRAIN_STEPS_PER_ITER = 50
        BATCH_SIZE = 512  # Increased from 256 for better GPU utilization
        ACCUM_STEPS = 4
        MAX_BUFFER_SIZE = 8000000
        SPARSE_LIMIT = 128
        
        # Learning rate scheduling
        LR_WARMUP_ITERS = 100  # Warmup iterations
        LR_START = 1e-5  # Starting LR during warmup
        LR_MAX = 0.001  # Max LR after warmup
        LR_MIN = 1e-5  # Minimum LR for decay
        LR_DECAY_ITERS = 5000  # Iterations for LR decay
        
        # Temperature for self-play
        TEMP_START = 1.0  # Initial temperature
        TEMP_END = 0.1  # Final temperature
        TEMP_DECAY_ITERS = 5000  # Iterations to decay temperature
        
        # Dirichlet noise for exploration
        DIRICHLET_ALPHA = 0.3
        DIRICHLET_EPSILON = 0.25
        
        # Parallel workers
        NUM_WORKERS = min(4, mp.cpu_count() - 1)
        
        checkpoint_dir = Path(__file__).parent / "vanilla_checkpoints"
        checkpoint_dir.mkdir(exist_ok=True)
        checkpoint_path = checkpoint_dir / "latest.pt"
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {device}")
        
        model = HighFidelityAlphaNet(input_dim=OBS_DIM, num_actions=ACTION_SPACE).to(device)
        
        # Enable gradient checkpointing for memory efficiency
        if hasattr(model, 'gradient_checkpointing_enable'):
            model.gradient_checkpointing_enable()
        
        # Start with low LR for warmup
        optimizer = torch.optim.AdamW(model.parameters(), lr=LR_START, weight_decay=1e-4)
        scaler = torch.amp.GradScaler(device.type if device.type == 'cuda' else 'cpu')
        
        # Load checkpoint if exists
        start_it = 0
        if checkpoint_path.exists():
            print(f"Resuming from: {checkpoint_path}")
            ckpt = torch.load(str(checkpoint_path), map_location=device, weights_only=True)
            model.load_state_dict(ckpt['model'])
            optimizer.load_state_dict(ckpt['optimizer'])
            start_it = ckpt.get('it', 0) + 1
        
        # Buffer for experience - use regular buffer (PER has Windows file I/O issues)
        buffer_dir = checkpoint_dir / "experience"
        buffer = PersistentBuffer(
            buffer_dir,
            max_size=MAX_BUFFER_SIZE,
            obs_dim=OBS_DIM,
            num_actions=ACTION_SPACE,
            sparse_limit=SPARSE_LIMIT,
            index_dtype=np.uint8
        )
        
        # Setup logging
        log_file = open(str(checkpoint_dir / "training_log.csv"), "a", encoding="utf-8")
        if start_it == 0:
            log_file.write("iter,loss,avg_turns,p0_wins,p1_wins,buffer_size,bench_turns,bench_score,gen_time,train_time,value_loss,policy_loss,lr,temperature\n")
        
        # Load decks
        decks_dir = root_dir / "ai" / "decks"
        all_decks = []
        parser = UnifiedDeckParser(db_json)
        for df in list(decks_dir.glob("*.txt")):
            with open(df, "r", encoding="utf-8") as f:
                ext = parser.extract_from_content(f.read())
                if ext:
                    m, l = [], []
                    for c in ext[0]['main']:
                        cd = parser.resolve_card(c)
                        if cd and cd.get("type") == "Member": m.append(cd["card_id"])
                        elif cd and cd.get("type") == "Live": l.append(cd["card_id"])
                    if m and l: all_decks.append({"name": df.stem, "m": (m*5)[:48], "l": (l*5)[:12]})
        
        print(f"Loaded {len(all_decks)} decks for training")
        
        # Import game logic functions from this module
        # We'll use the existing run_benchmark logic but adapted for training
        import concurrent.futures
        from functools import partial
        
        def play_training_game(deck, seed, sims, db, model, device, temperature=1.0, use_dirichlet=True):
            """Play a single game for training with MCTS, temperature, and Dirichlet noise"""
            state = engine_rust.PyGameState(db)
            state.silent = True
            state.initialize_game_with_seed(deck["m"], deck["m"], [38]*12, [38]*12, deck["l"], deck["l"], seed)
            
            initial_decks = [state.get_player(0).initial_deck, state.get_player(1).initial_deck]
            game_history = []
            moves = 0
            winner = None
            
            while not state.is_terminal() and state.turn < 25 and moves < 500:
                legal = state.get_legal_action_ids()
                if not legal:
                    state.auto_step(db)
                    legal = state.get_legal_action_ids()
                    if not legal: break
                
                pj = json.loads(state.to_json())
                cp = pj.get('phase', -4)
                curr_p = state.current_player
                
                # Setup/RPS/TurnChoice bypass
                if cp == -4:
                    if 0 in legal:
                        state.step(0); state.auto_step(db); moves += 1; continue
                if cp == -3:
                    action = random.choice(legal)
                    state.step(action); state.auto_step(db); moves += 1; continue
                if cp == -2:
                    action = random.choice(legal)
                    state.step(action); state.auto_step(db); moves += 1; continue
                
                # Get legal vanilla indices for this position
                mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
                legal_vanilla_indices = []
                v_to_e = {}
                for aid in legal:
                    vid = map_engine_to_vanilla(pj['players'][curr_p], aid, initial_decks[curr_p], cp)
                    if 0 <= vid < ACTION_SPACE:
                        mask[vid] = True
                        legal_vanilla_indices.append(vid)
                        v_to_e[vid] = aid
                
                # MCTS for decision phases
                action = -1
                policy_target = np.zeros(ACTION_SPACE, dtype=np.float32)
                
                if sims > 0 and cp in [4, 5, -1, 0]:
                    sugg = state.search_mcts(sims, 0.0, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal, None)
                    if sugg:
                        # Build policy from MCTS visits
                        total_visits = sum(s[2] for s in sugg)
                        if total_visits > 0:
                            for engine_id, q, visits in sugg:
                                vid = map_engine_to_vanilla(pj['players'][curr_p], engine_id, initial_decks[curr_p], cp)
                                if 0 <= vid < ACTION_SPACE:
                                    policy_target[vid] += visits / total_visits
                
                # If no MCTS policy, use model
                if policy_target.sum() == 0 and mask.any():
                    obs = torch.from_numpy(np.array(state.to_vanilla_tensor(), dtype=np.float32)).unsqueeze(0).to(device)
                    with torch.no_grad():
                        lgt, _ = model(obs, mask=torch.from_numpy(mask).unsqueeze(0).to(device))
                        policy_target = torch.softmax(lgt, dim=1).cpu().numpy()[0]
                
                # Apply Dirichlet noise for exploration (especially early in training)
                if use_dirichlet and policy_target.sum() > 0:
                    policy_target = apply_dirichlet_noise(
                        policy_target, 
                        legal_vanilla_indices, 
                        alpha=DIRICHLET_ALPHA, 
                        epsilon=DIRICHLET_EPSILON
                    )
                
                # Select action using temperature
                if len(legal_vanilla_indices) > 0 and policy_target[legal_vanilla_indices].sum() > 0:
                    selected_vid = select_action_with_temperature(
                        policy_target, 
                        legal_vanilla_indices, 
                        temperature=temperature
                    )
                    action = v_to_e.get(selected_vid, legal[0])
                else:
                    action = v_to_e.get(legal_vanilla_indices[0], legal[0]) if legal_vanilla_indices else legal[0]
                
                # Record transition (only for decision phases with MCTS)
                if sims > 0 and cp in [4, 5, -1, 0]:
                    obs_np = state.to_vanilla_tensor()
                    
                    # Get proper mask
                    mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
                    for aid in legal:
                        vid = map_engine_to_vanilla(pj['players'][curr_p], aid, initial_decks[curr_p], cp)
                        if 0 <= vid < ACTION_SPACE: mask[vid] = True
                    
                    game_history.append({
                        "obs": obs_np,
                        "policy": policy_target,
                        "player": curr_p,
                        "mask": mask
                    })
                
                state.step(action)
                state.auto_step(db)
                moves += 1
                
                if state.is_terminal():
                    winner = state.get_winner()
                    break
            
            # Compute values
            new_transitions = []
            for h in game_history:
                val = 0.5
                if winner == h['player']: val = 1.0
                elif winner == 1 - h['player']: val = 0.0
                
                indices = np.where(h['policy'] > 0)[0]
                values = h['policy'][indices]
                new_transitions.append((h['obs'], (indices, values), h['mask'], np.array([val], dtype=np.float32)))
            
            stats = {
                "turns": state.turn,
                "p0_lives": len(state.get_player(0).success_lives),
                "p1_lives": len(state.get_player(1).success_lives),
                "winner": winner
            }
            return new_transitions, stats
        
        def train_step(model, buffer, optimizer, scaler, device, steps, batch_size, beta=1.0):
            """Training step with priority experience replay support"""
            model.train()
            total_loss = 0
            total_value_loss = 0
            total_policy_loss = 0
            actual_steps = 0
            td_errors = []  # For priority updates
            
            for _ in range(steps):
                # Sample from buffer
                batch = buffer.sample(batch_size)
                if batch is None: break
                obs_np, sparse_pol, msk_np, val_np = batch
                weights_np = np.ones(batch_size, dtype=np.float32)
                
                obs_t = torch.from_numpy(obs_np).to(device)
                pol_t = torch.zeros(batch_size, ACTION_SPACE, device=device)
                row_v, col_v, val_v = sparse_pol
                pol_t[torch.from_numpy(row_v).long().to(device), torch.from_numpy(col_v).long().to(device)] = torch.from_numpy(val_v).float().to(device)
                msk_t = torch.from_numpy(msk_np).to(device)
                val_t = torch.from_numpy(val_np).float().to(device)
                weights_t = torch.from_numpy(weights_np).to(device)
                
                optimizer.zero_grad()
                
                with torch.autocast(device_type=device.type, dtype=torch.float16 if device.type == 'cuda' else torch.bfloat16):
                    policy_logits, value_preds = model(obs_t, mask=msk_t)
                    value_loss = F.mse_loss(value_preds.view_as(val_t[:, 0:1]), val_t[:, 0:1])
                    log_probs = F.log_softmax(policy_logits, dim=1)
                    policy_loss = F.kl_div(log_probs, pol_t, reduction='batchmean')
                    
                    # Apply importance sampling weights to loss
                    loss = ((value_loss + policy_loss) * weights_t.mean()) / ACCUM_STEPS
                
                scaler.scale(loss).backward()
                
                if (actual_steps + 1) % ACCUM_STEPS == 0:
                    scaler.step(optimizer)
                    scaler.update()
                    optimizer.zero_grad()
                
                total_loss += loss.item() * ACCUM_STEPS
                total_value_loss += value_loss.item()
                total_policy_loss += policy_loss.item()
                actual_steps += 1
            
            # Calculate accuracy
            avg_value_loss = total_value_loss / max(1, actual_steps)
            avg_policy_loss = total_policy_loss / max(1, actual_steps)
            avg_loss = total_loss / max(1, actual_steps)
            
            # Accuracy not meaningful for this setup - showing policy loss instead
            accuracy = 0.0  # Removed placeholder
            
            return avg_loss, avg_value_loss, avg_policy_loss, accuracy
        
        # Main training loop
        db = engine_rust.PyCardDatabase(db_json_str)  # Already loaded in run_benchmark
        
        try:
            for it in range(start_it, args.iters):
                print(f"\n=== Starting Iteration {it} ===")
                gen_start = time.time()
                
                # Compute learning rate with warmup and decay
                current_lr = get_lr(it, LR_WARMUP_ITERS, LR_DECAY_ITERS, LR_START, LR_MAX, LR_MIN)
                for param_group in optimizer.param_groups:
                    param_group['lr'] = current_lr
                
                # Compute temperature for self-play (higher early = more exploration)
                current_temp = get_temperature(it, TEMP_START, TEMP_END, TEMP_DECAY_ITERS)
                
                # Beta is not used (PER disabled for Windows)
                current_beta = 0.0
                
                print(f"[SCHEDULE] LR: {current_lr:.6f} | Temp: {current_temp:.4f}")
                
                # Play games with random decks and random seeds
                new_transitions = []
                game_stats = []
                decks_used = []
                
                # Use parallel game execution with ProcessPoolExecutor
                if NUM_WORKERS > 1:
                    # Prepare game parameters
                    game_params = []
                    for _ in range(GAMES_PER_ITER):
                        deck = random.choice(all_decks)
                        decks_used.append(deck)
                        seed = random.getrandbits(64)
                        game_params.append((deck, seed, args.sims, db_json_str, current_temp))
                    
                    # Execute games in parallel
                    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
                        futures = [executor.submit(play_training_game_parallel, params) for params in game_params]
                        for future in as_completed(futures):
                            try:
                                transitions, stats = future.result()
                                new_transitions.extend(transitions)
                                game_stats.append(stats)
                            except Exception as e:
                                print(f"[ERROR] Game failed: {e}")
                else:
                    # Sequential execution (fallback)
                    for _ in range(GAMES_PER_ITER):
                        deck = random.choice(all_decks)
                        decks_used.append(deck)
                        seed = random.getrandbits(64)
                        transitions, stats = play_training_game(deck, seed, args.sims, db, model, device, 
                                                             temperature=current_temp, use_dirichlet=True)
                        new_transitions.extend(transitions)
                        game_stats.append(stats)
                
                for deck, stats in zip(decks_used, game_stats):
                    print(f"  [Game] {deck['name']} | Winner: {['P0','P1','Draw'][stats['winner']] if stats['winner'] is not None else 'N/A'} | Turns: {stats['turns']} | Lives: P0={stats['p0_lives']} P1={stats['p1_lives']}")
                
                # Add to buffer
                for t in new_transitions:
                    buffer.add(t[0], t[1], t[3], t[2])
                
                gen_time = time.time() - gen_start
                
                # Training
                if buffer.count >= BATCH_SIZE:
                    train_start = time.time()
                    print(f"[TRAIN] It {it:3d} | Training on {buffer.count} samples...")
                    loss, value_loss, policy_loss, accuracy = train_step(model, buffer, optimizer, scaler, device, TRAIN_STEPS_PER_ITER, BATCH_SIZE)
                    train_time = time.time() - train_start
                    print(f"[TRAIN] It {it:3d} | Loss: {loss:.4f} (Value: {value_loss:.4f}, Policy: {policy_loss:.4f}) | Train Time: {train_time:.1f}s")
                else:
                    loss, value_loss, policy_loss, accuracy = 0, 0, 0, 0
                    train_time = 0
                    print(f"[WAIT] It {it:3d} | Buffer too small: {buffer.count}/{BATCH_SIZE}")
                
                # Stats
                wins = [s["winner"] for s in game_stats]
                avg_turns = sum(s["turns"] for s in game_stats) / len(game_stats) if game_stats else 0
                p0_lives = sum(s["p0_lives"] for s in game_stats)
                p1_lives = sum(s["p1_lives"] for s in game_stats)
                ties = wins.count(2) if 2 in wins else 0
                
                print(f"\n=== ITERATION {it} SUMMARY ===")
                print(f"  Games: {len(game_stats)} | P0 Wins: {wins.count(0)} | P1 Wins: {wins.count(1)} | Ties: {ties}")
                print(f"  Avg Turns: {avg_turns:.1f} | Avg Lives: P0={p0_lives/len(game_stats):.1f} P1={p1_lives/len(game_stats):.1f}")
                print(f"  Gen Time: {gen_time:.1f}s | Train Time: {train_time:.1f}s | Loss: {loss:.4f}")
                print(f"  Buffer: {buffer.count} samples | LR: {current_lr:.6f}")
                print(f"========================\n")
                
                # Periodic benchmark
                bench_turns, bench_score = 0, 0
                if it % 10 == 0:
                    model.eval()
                    print(f"[BENCHMARK] Running benchmark...")
                    bench_turns, bench_score = run_benchmark(str(checkpoint_path), sims=128)
                    model.train()
                    print(f"[BENCHMARK] Turns: {bench_turns:.1f}, Score: {bench_score:.1f}")
                
                log_file.write(f"{it},{loss:.4f},{avg_turns:.1f},{wins.count(0)},{wins.count(1)},{buffer.count},{bench_turns:.1f},{bench_score:.1f},{gen_time:.1f},{train_time:.1f},{value_loss:.4f},{policy_loss:.4f},{current_lr:.6f},{current_temp:.4f}\n")
                log_file.flush()
                
                # GPU memory
                if torch.cuda.is_available():
                    mem_allocated = torch.cuda.memory_allocated(device) / 1024**3
                    mem_reserved = torch.cuda.memory_reserved(device) / 1024**3
                    print(f"[GPU] Memory: {mem_allocated:.2f}GB allocated, {mem_reserved:.2f}GB reserved")
                
                # Save checkpoint
                if it % 5 == 0:
                    # Save regular checkpoint
                    torch.save({
                        'model': model.state_dict(),
                        'optimizer': optimizer.state_dict(),
                        'it': it,
                        'loss': loss,
                        'value_loss': value_loss,
                        'policy_loss': policy_loss,
                        'timestamp': time.time()
                    }, str(checkpoint_path))
                    print(f"[CHECKPOINT] Saved to {checkpoint_path}")
                    
                    # Save best model
                    if loss < best_loss:
                        best_loss = loss
                        best_path = checkpoint_dir / "best.pt"
                        torch.save({
                            'model': model.state_dict(),
                            'optimizer': optimizer.state_dict(),
                            'it': it,
                            'loss': loss
                        }, str(best_path))
                        print(f"[BEST] New best model! Loss: {best_loss:.4f}")
                    
                    # Save periodic backup
                    if it % 50 == 0:
                        backup_path = checkpoint_dir / f"checkpoint_it{it}.pt"
                        torch.save({
                            'model': model.state_dict(),
                            'optimizer': optimizer.state_dict(),
                            'it': it,
                            'loss': loss
                        }, str(backup_path))
                        print(f"[BACKUP] Saved to {backup_path}")
                    
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            log_file.close()
            
    else:
        run_benchmark(args.model, args.sims)
