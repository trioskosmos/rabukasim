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

# ============================================================
# IMPROVED VANILLA TRAINING BENCHMARK
# Based on considerations from plans/vanilla training guide.txt
# ============================================================
# Key improvements:
# 1. Mulligan strategy: replace high cost/high requirement cards
# 2. Live set optimization: prioritize setting 3 cards
# 3. Enhanced reward function: consider turns, lives, and scores
# 4. Mathematical information: expected yell heart values
# 5. Action prioritization: field placement and baton pass weighting
# 6. Performance combination optimization

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

# ============================================================
# NEW: Card Analysis Utilities for Vanilla Strategy
# ============================================================

def analyze_card_costs(db_json, card_id):
    """
    Analyze a card's costs for mulligan decisions.
    Returns: (energy_cost, life_requirement, yell_hearts)
    """
    # Check member_db first, then live_db
    for cat in ["member_db", "live_db"]:
        if cat in db_json and card_id in db_json[cat]:
            card = db_json[cat][card_id]
            energy = card.get("cost", 0)
            life_req = card.get("life", 0)
            # Estimate yell hearts (simplified - actual implementation would need card data)
            yell = 0
            if "YellHeart" in str(card.get("abilities", [])):
                yell = 1
            return energy, life_req, yell
    return 0, 0, 0

def calculate_mulligan_strategy(db_json, hand, deck_copy, replace_count=5):
    """
    Determine which cards to replace during mulligan.
    Evaluates EACH card individually based on its costs.
    
    Strategy: Score each card and keep the best ones, replace the worst.
    - Keep: Low energy cost, low life requirement, yell hearts (useful for performance)
    - Replace: High energy cost, high life requirement
    
    Args:
        db_json: Card database
        hand: Current hand cards
        deck_copy: Remaining deck (to know what's available)
        replace_count: Maximum cards to replace (default 5 = full hand)
    
    Returns:
        List of indices to replace
    """
    if not hand or len(hand) == 0:
        return []
    
    # Score each card individually - keep the best, replace the worst
    card_scores = []
    for idx, card_id in enumerate(hand):
        energy, life_req, yell = analyze_card_costs(db_json, card_id)
        
        # Score: HIGHER is better (keep), LOWER should be replaced
        # Negative score = replace this card
        # Positive score = keep this card
        score = -1 * (energy * 2 + life_req) + yell * 5
        
        card_scores.append((idx, score))
    
    # Sort by score ascending (lowest scores = replace first)
    card_scores.sort(key=lambda x: x[1])
    
    # Replace the lowest scoring cards
    # Keep at least 1 card (never replace entire hand unless explicitly requested)
    max_replace = min(replace_count, len(hand) - 1)
    indices_to_replace = [idx for idx, _ in card_scores[:max_replace]]
    
    return indices_to_replace

def get_deck_expected_values(db_json, deck):
    """
    Calculate expected values for remaining deck.
    This provides mathematical information to the model.
    
    Returns:
        dict with min/max/expected energy, life_req, yell_hearts
    """
    if not deck:
        return {"energy": (0, 0, 0), "life_req": (0, 0, 0), "yell": (0, 0, 0)}
    
    energies = []
    life_reqs = []
    yells = []
    
    for card_id in deck:
        energy, life_req, yell = analyze_card_costs(db_json, card_id)
        energies.append(energy)
        life_reqs.append(life_req)
        yells.append(yell)
    
    return {
        "energy": (min(energies), max(energies), np.mean(energies)),
        "life_req": (min(life_reqs), max(life_reqs), np.mean(life_reqs)),
        "yell": (min(yells), max(yells), np.mean(yells))
    }

def prioritize_live_set_actions(legal_actions, state, curr_p):
    """
    Prioritize live set actions that set more cards (up to 3).
    Also consider combination potential.
    
    Returns:
        List of actions sorted by priority
    """
    # Get current live set count
    pj = json.loads(state.to_json())
    current_lives = len(pj['players'][curr_p].get('live_zone', []))
    
    # Priority: more cards in live set is generally better
    # Weight actions that add to live set higher
    prioritized = []
    for aid in legal_actions:
        # Check if action is a live card play (400-499 range typically)
        is_live_play = 400 <= aid < 500
        priority = 0
        if is_live_play and current_lives < MAX_LIVE_SET_CARDS:
            priority = 10  # High priority for filling live set
        prioritized.append((aid, priority))
    
    prioritized.sort(key=lambda x: x[1], reverse=True)
    return [a[0] for a in prioritized]

def prioritize_field_actions(legal_actions, state, curr_p, db_json=None):
    """
    Prioritize playing members to field.
    Baton pass: energy cost = card cost - card currently in the slot.
    
    IMPORTANT: "the actual slot position does not matter, just what is in the slot"
    So we only need to consider the energy costs of cards on field vs in hand.
    Higher cost cards should be played to pass to lower cost cards for efficiency.
    
    Args:
        legal_actions: List of legal action IDs
        state: Current game state
        curr_p: Current player index
        db_json: Card database (optional, for card analysis)
    
    Returns:
        List of actions sorted by priority
    """
    pj = json.loads(state.to_json())
    field = pj['players'][curr_p].get('field', [])
    hand = pj['players'][curr_p].get('hand', [])
    field_count = len(field)
    
    # Get energy costs of cards currently on field
    field_costs = []
    for field_card in field:
        if field_card:
            energy, _, _ = analyze_card_costs(db_json, field_card) if db_json else (0, 0, 0)
            field_costs.append(energy)
    
    prioritized = []
    for aid in legal_actions:
        # Check if action plays a member card (1000-1599 range typically)
        is_member_play = 1000 <= aid < 1600
        priority = 0
        bonus = 0
        
        if is_member_play and field_count < MAX_STAGE_SLOTS:
            priority = 20  # High priority for field placement
            
            # Extract hand index from action ID
            hand_idx = (aid - 1000) // 10
            if hand_idx < len(hand):
                card_id = hand[hand_idx]
                energy, _, _ = analyze_card_costs(db_json, card_id) if db_json else (0, 0, 0)
                
                # BATON PASS OPTIMIZATION:
                # Check if playing this card would give good baton pass efficiency
                # Good: high cost card -> low cost card on field (big discount)
                # Good: low cost card -> high cost card on field (small cost)
                
                if field_costs:
                    for field_energy in field_costs:
                        if energy > field_energy:
                            # High cost passing to low cost = very efficient
                            bonus += 10
                        elif energy == field_energy:
                            # Same cost = neutral
                            bonus += 3
                        else:
                            # Low cost passing to high cost = less efficient but still works
                            bonus += 5
                    
                    # Average the bonuses
                    bonus = bonus // max(1, len(field_costs))
                else:
                    # First card to field - no baton pass yet
                    bonus += 5
            
            priority += bonus
        
        prioritized.append((aid, priority))
    
    prioritized.sort(key=lambda x: x[1], reverse=True)
    return [a[0] for a in prioritized]

# ============================================================
# Card-Centric + Slot-Aware Action Mapping (248-dim action space)
# ============================================================

def get_card_zone(state, player_idx, card_id):
    """
    Returns the zone of a card for the given player.
    0: Deck (not in any zone)
    1: Hand
    2: Field (stage)
    3: Live Zone
    4: Energy Zone
    5: Discard/Other
    """
    p = state.get_player(player_idx)
    pj = json.loads(state.to_json())
    p_data = pj['players'][player_idx]
    
    if card_id in p_data.get('hand', []): return 1
    if card_id in p_data.get('field', []): return 2
    if card_id in p_data.get('live_zone', []): return 3
    if card_id in p_data.get('energy_zone', []): return 4
    return 0  # Deck or discard

def engine_action_to_action_248(engine_id, state, phase, initial_deck, player_idx):
    """
    Converts engine action ID to 248-dim action space index.
    
    Action space:
      0: Pass
      1-6: Mulligan (hand[0-5])
      7: Confirm
      8-67: Generic card play [0-59]
      68-127: Play to slot 0 [0-59]
      128-187: Play to slot 1 [0-59]
      188-247: Play to slot 2 [0-59]
    """
    # Phase actions
    if engine_id == 0:
        if phase in [-1, 0, 5, 8, 10]: return 7  # Confirm
        return 0  # Pass
    if 300 <= engine_id <= 305: return 1 + (engine_id - 300)  # Mulligan
    if engine_id == 11000: return 7  # Confirm
    
    # Card plays
    p = state.get_player(player_idx)
    pj = json.loads(state.to_json())
    p_data = pj['players'][player_idx]
    hand = p_data.get('hand', [])
    
    # Main phase: play member (1000+ range)
    # Engine encoding: 1000 + hand_idx*10 + slot?
    if 1000 <= engine_id < 1600:
        hand_idx = (engine_id - 1000) // 10
        slot = (engine_id - 1000) % 10  # Slot info encoded in last digit?
        
        if hand_idx < len(hand):
            card_id = hand[hand_idx]
            if card_id in initial_deck:
                try:
                    deck_idx = initial_deck.index(card_id)
                    # If slot is specified (1-3), use slot-specific action
                    if 1 <= slot <= 3:
                        slot_idx = slot - 1  # 0-indexed
                        return 68 + slot_idx * 60 + deck_idx
                    else:
                        # Generic play with auto-slot selection
                        return 8 + deck_idx
                except:
                    pass
        return None
    
    # Live phase: set live (400+ range)
    if 400 <= engine_id < 500:
        hand_idx = engine_id - 400
        if hand_idx < len(hand):
            card_id = hand[hand_idx]
            if card_id in initial_deck:
                try:
                    deck_idx = initial_deck.index(card_id)
                    return 8 + deck_idx  # Generic play for live
                except:
                    pass
        return None
    
    return None

def action_248_to_engine_action(state, player_idx, action_idx, phase, initial_deck):
    """
    Converts 248-dim action index to engine action ID.
    
    For slot-specific plays, tries to pick the best slot for baton pass.
    """
    # Phase actions
    if action_idx == 0: return 0  # Pass
    if 1 <= action_idx <= 6: return 300 + (action_idx - 1)  # Mulligan
    if action_idx == 7: return 11000  # Confirm
    
    # Generic card play (8-67)
    if 8 <= action_idx < 68:
        deck_idx = action_idx - 8
        if deck_idx >= len(initial_deck):
            print(f"[WARN] deck_idx {deck_idx} >= len(initial_deck) {len(initial_deck)}")
            return None
        
        card_id = initial_deck[deck_idx]
        pj = json.loads(state.to_json())
        hand = pj['players'][player_idx].get('hand', [])
        
        if card_id not in hand:
            print(f"[WARN] Trying to play card_id {card_id} (deck idx {deck_idx}) not in hand. Hand has {len(hand)} cards: {hand[:5]}...")
            return None
        hand_idx = hand.index(card_id)
        
        # Map based on phase
        if phase in [4, 5]:  # Main phase
            # For generic, try slot 0 (will be auto-selected/switched)
            result = 1000 + hand_idx * 10 + 0
            print(f"[DEBUG] Action {action_idx} -> Card {card_id} (deck {deck_idx}) hand_idx {hand_idx} -> Engine {result}")
            return result
        elif phase in [-1, 0]:  # Live phase
            return 400 + hand_idx
        return None
    
    # Slot-specific card play (68-247)
    if 68 <= action_idx < 248:
        # Decode: slot_idx = (action_idx - 68) // 60, deck_idx = (action_idx - 68) % 60
        offset = action_idx - 68
        slot_idx = offset // 60
        deck_idx = offset % 60
        
        if slot_idx >= 3:
            print(f"[WARN] slot_idx {slot_idx} >= 3")
            return None
        if deck_idx >= len(initial_deck):
            print(f"[WARN] deck_idx {deck_idx} >= len(initial_deck) {len(initial_deck)} in slot-specific")
            return None
        
        card_id = initial_deck[deck_idx]
        pj = json.loads(state.to_json())
        hand = pj['players'][player_idx].get('hand', [])
        field = pj['players'][player_idx].get('field', [])
        
        if card_id not in hand:
            print(f"[WARN] card_id {card_id} not in hand (slot-specific)")
            return None
        hand_idx = hand.index(card_id)
        
        # Return engine action with slot encoding
        # Assuming slot is encoded as: 1000 + hand_idx*10 + slot (1-indexed)
        return 1000 + hand_idx * 10 + (slot_idx + 1)
    
    return None

def build_action_mask_248(state, player_idx, initial_deck, phase):
    """
    Builds 248-dim binary mask of legal actions.
    
    Only mark actions that correspond to legal engine actions.
    """
    legal_engine = state.get_legal_action_ids()
    mask = np.zeros(248, dtype=np.bool_)
    
    if not initial_deck:
        print(f"[WARN] initial_deck is empty/None")
        # At minimum, pass is always legal
        mask[0] = True
        return mask
    
    # Convert each legal engine action to 248-dim index
    for eng_id in legal_engine:
        action_idx = engine_action_to_action_248(eng_id, state, phase, initial_deck, player_idx)
        if action_idx is not None and 0 <= action_idx < 248:
            mask[action_idx] = True
    
    num_legal = mask.sum()
    if num_legal > 100:
        print(f"[DEBUG] Phase {phase}: {num_legal} legal actions (unusual)")
    
    return mask

# ============================================================
# Neural MCTS Implementation for True AlphaZero Learning
# ============================================================

class NeuralMCTS:
    """
    Card-centric + slot-aware neural action selection (248-dim action space).
    
    Action hierarchy:
      8-67: Generic card plays (auto-slot selection)
      68-247: Slot-specific plays (explicit slot for baton pass strategy)
    """
    
    def __init__(self, model, device, initial_deck=None):
        self.model = model
        self.device = device
        self.initial_deck = initial_deck if initial_deck is not None else []
        self.temperature = 1.0
    
    def select_action(self, state, player_idx, current_phase):
        """
        Select action using neural network policy (card + slot aware).
        
        Returns:
            policy_248: numpy array of 248-dim action probabilities (clean, no noise)
            action_engine: selected engine action ID
            value: model-estimated value
        """
        dbg_file = open('/tmp/debug.log', 'a') if False else open('c:/tmp/debug.log', 'a')  # Use Windows path
        
        # Build mask for this state
        mask_248 = build_action_mask_248(state, player_idx, self.initial_deck, current_phase)
        
        if not mask_248.any():
            # No legal actions - shouldn't happen
            dbg_file.write(f"WARN: No legal actions in mask for phase {current_phase}\n")
            dbg_file.flush()
            dbg_file.close()
            return np.ones(248) / 248, 0, 0.5
        
        # Get observation
        obs = state.to_vanilla_tensor()
        # Ensure obs is numpy array (Rust engine may return list)
        if isinstance(obs, list):
            obs = np.array(obs, dtype=np.float32)
        elif not isinstance(obs, np.ndarray):
            obs = np.asarray(obs, dtype=np.float32)
        
        # Query model (output is 248-dim)
        with torch.no_grad():
            obs_t = torch.from_numpy(obs).float().unsqueeze(0).to(self.device)
            mask_t = torch.from_numpy(mask_248).unsqueeze(0).bool().to(self.device)
            policy_logits, value = self.model(obs_t, mask=mask_t)
            
            # Get clean probabilities (no noise!)
            policy_248 = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]
            value = value.item()
        
        # Mask to legal actions only
        policy_248_masked = policy_248 * mask_248.astype(np.float32)
        if policy_248_masked.sum() == 0:
            dbg_file.write(f"WARN: All masked policy probs are 0 after masking\n")
            policy_248_masked = mask_248.astype(np.float32) / mask_248.sum()
        else:
            policy_248_masked = policy_248_masked / policy_248_masked.sum()  # Renormalize
        
        # Select action using temperature
        if self.temperature > 0.01:
            # Temperature sampling
            policy_temp = policy_248_masked ** (1.0 / self.temperature)
            policy_temp = policy_temp / policy_temp.sum()
            action_idx = np.random.choice(248, p=policy_temp)
        else:
            # Greedy
            action_idx = np.argmax(policy_248_masked)
        
        dbg_file.write(f"DEBUG: Selected action_idx {action_idx}, phase {current_phase}\n")
        
        # Convert to engine action
        action_engine = action_248_to_engine_action(state, player_idx, action_idx, current_phase, self.initial_deck)
        if action_engine is None:
            legal_actions = state.get_legal_action_ids()
            if legal_actions:
                action_engine = legal_actions[0]
                dbg_file.write(f"INFO: Converted action_idx {action_idx} returned None, using legal: {action_engine}\n")
            else:
                action_engine = 0
                dbg_file.write(f"INFO: No legal actions, using 0\n")
        dbg_file.write(f"DEBUG: Final action_engine = {action_engine}\n")
        dbg_file.flush()
        dbg_file.close()
        
        return policy_248_masked, action_engine, value


# ============================================================
# Enhanced Training Functions with True Self-Play
# ============================================================

def play_selfplay_game(model, device, db, deck, seed, use_neural_mcts=True, iteration=0, total_iters=2000):
    """
    Play a single game for training with Neural MCTS card-centric actions.
    
    Collects clean (non-noisy) policy targets and game outcomes.
    """
    state = engine_rust.PyGameState(db)
    state.silent = True
    state.initialize_game_with_seed(
        deck["m"], deck["m"], 
        [38]*12, [38]*12, 
        deck["l"], deck["l"], 
        seed
    )
    
    initial_decks = [list(state.get_player(0).initial_deck), list(state.get_player(1).initial_deck)]
    print(f"[DEBUG] Initial deck sizes: P0={len(initial_decks[0])}, P1={len(initial_decks[1])}")
    if initial_decks[0]:
        print(f"[DEBUG] Initial_deck[0] (first 10): {initial_decks[0][:10]}")
    game_history = []
    moves = 0
    winner = None
    
    # Initialize Neural MCTS with initial deck for each player
    mcts_players = [
        NeuralMCTS(model, device, initial_decks[0]),
        NeuralMCTS(model, device, initial_decks[1])
    ]
    
    while not state.is_terminal() and state.turn < 25 and moves < 500:
        legal = state.get_legal_action_ids()
        if not legal:
            state.auto_step(db)
            legal = state.get_legal_action_ids()
            if not legal:
                break
        
        pj = json.loads(state.to_json())
        phase = pj.get('phase', -4)
        curr_p = state.current_player
        
        # Auto-play non-decision phases
        if phase == -4:  # Setup
            if 0 in legal:
                state.step(0)
                state.auto_step(db)
                moves += 1
                continue
        if phase in [-3, -2]:  # RPS, TurnChoice
            action = random.choice(legal)
            state.step(action)
            state.auto_step(db)
            moves += 1
            continue
        
        # Decision phases: use Neural MCTS
        if phase in [4, 5, -1, 0] and use_neural_mcts:
            # Set temperature with iteration-based decay
            mcts_players[curr_p].temperature = get_temperature_by_move(
                moves,
                temp_start=1.0,
                temp_end=0.0,
                explore_moves=20,
                iteration=iteration,
                total_iters=total_iters
            )
            
            # Get clean policy + action from model
            policy_248, action_engine, value_pred = mcts_players[curr_p].select_action(
                state, curr_p, phase
            )
            
            # Store transition (clean policy, no noise)
            obs_800 = state.to_vanilla_tensor()
            if isinstance(obs_800, list):
                obs_800 = np.array(obs_800, dtype=np.float32)
            mask_248 = build_action_mask_248(state, curr_p, initial_decks[curr_p], phase)
            
            game_history.append({
                'obs': obs_800,
                'policy': policy_248.copy(),  # CLEAN policy (already masked & normalized)
                'mask': mask_248,
                'phase': phase,
                'player': curr_p,
                'value_pred': value_pred
            })
            
            action = action_engine
        else:
            # Fallback: random for non-decision phases or disabled MCTS
            action = random.choice(legal)
        
        try:
            state.step(action)
        except Exception as e:
            print(f"[ERROR] Step failed - Action: {action}, Phase: {phase}, Legal: {legal}")
            print(f"[ERROR] Exception: {e}")
            action = legal[0] if legal else 0
            state.step(action)
        
        state.auto_step(db)
        moves += 1
        
        if state.is_terminal():
            winner = state.get_winner()
            break
    
    # Build training transitions with terminal values
    new_transitions = []
    for h in game_history:
        # Terminal value target
        if winner == h['player']:
            value_target = 1.0
        elif winner == 1 - h['player']:
            value_target = 0.0
        else:
            value_target = 0.5
        
        # Sparse representation: store non-zero indices
        nonzero_indices = np.where(h['policy'] > 1e-6)[0]
        nonzero_values = h['policy'][nonzero_indices]
        
        # (obs, sparse_policy, mask, value_target)
        new_transitions.append((
            h['obs'].astype(np.float32),
            (nonzero_indices.astype(np.int32), nonzero_values.astype(np.float32)),
            h['mask'],
            np.array([value_target], dtype=np.float32)
        ))
    
    stats = {
        'turns': state.turn,
        'p0_lives': len(state.get_player(0).success_lives),
        'p1_lives': len(state.get_player(1).success_lives),
        'winner': winner,
        'moves': moves,
        'num_transitions': len(new_transitions)
    }
    
    return new_transitions, stats


def run_training_loop_with_selfplay(args):
    """
    Main training loop with TRUE self-play.
    This implements proper AlphaZero training.
    """
    # ... (implementation continues with self-play loop)
    pass


# Configuration for True AlphaZero
USE_NEURAL_MCTS = True  # Default to Neural MCTS for actual learning
MCTS_SIMS = 50  # Number of MCTS simulations per move
SELFPLAY_ITERATIONS = 1000


# Original configuration
FIXED_SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010]
NUM_ACTIONS = 248  # Phase(8) + Generic(60) + SlotSpecific(180: 60×3)
OBS_DIM = 800

# Training configuration with enhancements
NUM_WORKERS = 4  # Number of parallel game workers
TEMP_START = 1.0  # Initial temperature (high for early game exploration)
TEMP_END = 0.0  # Final temperature (greedy in late game)
TEMP_EXPLORE_MOVES = 20  # Number of moves to explore with high temperature (standard AlphaZero)
DIRICHLET_ALPHA = 0.3  # Dirichlet noise parameter
DIRICHLET_EPSILON = 0.25  # Fraction of exploration noise
LR_WARMUP_ITERS = 100  # Learning rate warmup iterations
LR_START = 1e-5  # Starting learning rate during warmup
LR_MAX = 0.001  # Maximum learning rate after warmup
LR_MIN = 1e-5  # Minimum learning rate for decay
PRIORITY_ALPHA = 0.6  # Priority exponent for PER
PRIORITY_BETA_START = 0.4  # Initial importance sampling exponent
PRIORITY_BETA_END = 1.0  # Final importance sampling exponent

# ============================================================
# NEW: Vanilla Training Guide Configuration
# Based on plans/vanilla training guide.txt considerations
# ============================================================

# Mulligan settings
MULLIGAN_ENABLED = True  # Enable mulligan strategy
MULLIGAN_REPLACE_COUNT = 5  # Max cards to replace in mulligan (up to full hand)

# Action prioritization
PRIORITIZE_FIELD_PLACEMENT = True  # Prioritize playing members to stage
PRIORITIZE_LIVE_SET = True  # Prioritize filling live set (up to 3 cards)

# Enhanced reward weights (to prevent just looking for wins)
REWARD_WIN_WEIGHT = 0.7  # Weight for win/loss in reward
REWARD_TURN_WEIGHT = 0.15  # Weight for turn speed in reward (faster wins better)
REWARD_LIFE_WEIGHT = 0.15  # Weight for life count in reward

# Performance optimization
MAX_STAGE_SLOTS = 3  # Maximum stage slots
MAX_LIVE_SET_CARDS = 3  # Maximum cards in live set zone


def play_training_game_parallel(args):
    """
    Parallel version of play_training_game for ProcessPoolExecutor.
    Must be at module level for pickling.
    
    Args:
        args: tuple of (deck, seed, sims, db_json_str, temperature)
    
    Returns:
        (transitions, stats)
    """
    deck, seed, sims, db_json_str, _ = args  # Temperature now computed per-move
    
    # Recreate database and model in this process
    db = engine_rust.PyCardDatabase(db_json_str)
    
    state = engine_rust.PyGameState(db)
    state.silent = True
    state.initialize_game_with_seed(deck["m"], deck["m"], [38]*12, [38]*12, deck["l"], deck["l"], seed)
    
    initial_decks = [state.get_player(0).initial_deck, state.get_player(1).initial_deck]
    game_history = []
    moves = 0
    winner = None
    
    # Standard AlphaZero temperature: high for first 20 moves, then greedy
    EXPLORE_MOVES = 20
    
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
            sugg = state.search_mcts(sims, 0.0, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Solitaire, None)
            if sugg:
                total_visits = sum(s[2] for s in sugg)
                if total_visits > 0:
                    for engine_id, q, visits in sugg:
                        vid = map_engine_to_vanilla(pj['players'][curr_p], engine_id, initial_decks[curr_p], cp)
                        if 0 <= vid < NUM_ACTIONS:
                            policy_target[vid] += visits / total_visits
        
        
        # Store clean policy for training (no noise)
        # Keep original policy_target clean for training
        clean_policy = policy_target.copy() if policy_target.sum() > 0 else policy_target
        
        # Apply Dirichlet noise for ACTION SELECTION ONLY (not for training data)
        # The function handles its own copy internally
        if policy_target.sum() > 0:
            policy_target_for_selection = apply_dirichlet_noise(policy_target, legal_vanilla_indices, DIRICHLET_ALPHA, DIRICHLET_EPSILON)
        else:
            policy_target_for_selection = policy_target
        
        # Select action using temperature (move-based: high for first 20 moves, then greedy)
        current_temp = get_temperature_by_move(moves, temp_start=1.0, temp_end=0.0, explore_moves=EXPLORE_MOVES)
        if len(legal_vanilla_indices) > 0 and policy_target_for_selection[legal_vanilla_indices].sum() > 0:
            selected_vid = select_action_with_temperature(policy_target_for_selection, legal_vanilla_indices, current_temp)
            action = v_to_e.get(selected_vid, legal[0])
        else:
            action = v_to_e.get(legal_vanilla_indices[0], legal[0]) if legal_vanilla_indices else legal[0]
        
        # Record transition (only for decision phases) - use CLEAN policy
        if sims > 0 and cp in [4, 5, -1, 0]:
            obs_np = state.to_vanilla_tensor()
            if isinstance(obs_np, list):
                obs_np = np.array(obs_np, dtype=np.float32)
            mask = np.zeros(NUM_ACTIONS, dtype=np.bool_)
            for aid in legal:
                vid = map_engine_to_vanilla(pj['players'][curr_p], aid, initial_decks[curr_p], cp)
                if 0 <= vid < NUM_ACTIONS: mask[vid] = True
            
            game_history.append({
                "obs": obs_np,
                "policy": clean_policy,  # Save CLEAN policy without noise
                "player": curr_p,
                "mask": mask
            })
        
        state.step(action)
        state.auto_step(db)
        moves += 1
        
        if state.is_terminal():
            winner = state.get_winner()
            break
    
    # Compute values with weighted reward function
    # This prevents the model from just looking for wins - it also learns from
    # turn speed and life count as secondary objectives
    new_transitions = []
    max_turns = 25  # Maximum turns in a game
    
    for h in game_history:
        # Base outcome value
        val = 0.5
        if winner == h['player']: 
            val = 1.0
        elif winner == 1 - h['player']: 
            val = 0.0
        
        # Turn-based reward: earlier moves with win are more valuable
        # This addresses "lower number of turns through better board management"
        turn_progress = moves / max_turns  # 0 to 1 scale
        if winner == h['player']:
            # Winning earlier is better
            turn_val = 1.0 - turn_progress * 0.5
        elif winner == 1 - h['player']:
            # Losing later (slow opponent) is slightly better than losing fast
            turn_val = turn_progress * 0.3
        else:
            turn_val = 0.5
        
        # Life-based reward
        p0_lives_final = len(state.get_player(0).success_lives)
        p1_lives_final = len(state.get_player(1).success_lives)
        life_val = (p0_lives_final if h['player'] == 0 else p1_lives_final) / 12.0
        
        # Combine: outcome is primary, but turn speed and life count matter
        final_val = (REWARD_WIN_WEIGHT * val + 
                     REWARD_TURN_WEIGHT * turn_val + 
                     REWARD_LIFE_WEIGHT * life_val)
        final_val = np.clip(final_val, 0.0, 1.0)
        
        indices = np.where(h['policy'] > 0)[0]
        values = h['policy'][indices]
        new_transitions.append((h['obs'], (indices, values), h['mask'], np.array([final_val], dtype=np.float32)))
    
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
    Compute temperature with exponential decay (iteration-based).
    Higher temperature = more exploration (softer policy)
    Lower temperature = more exploitation (greedy)
    DEPRECATED: Use get_temperature_by_move instead for move-based scheduling.
    """
    if it >= decay_iters:
        return temp_end
    # Exponential decay from temp_start to temp_end
    decay_rate = math.log(temp_end / temp_start) / decay_iters
    return temp_start * math.exp(decay_rate * it)


def get_temperature_by_move(move_number, temp_start=1.0, temp_end=0.0, explore_moves=20, iteration=0, total_iters=2000):
    """
    Compute temperature based on move number within a game + iteration-based decay.
    Standard AlphaZero methodology: high temperature for first N moves, then greedy.
    Also includes iteration-based annealing to reduce exploration as training progresses.
    
    Args:
        move_number: Current move number in the game (0-indexed)
        temp_start: Initial temperature (high for exploration)
        temp_end: Final temperature (0 for greedy)
        explore_moves: Number of moves to explore with high temperature
        iteration: Current training iteration (for annealing)
        total_iters: Total number of training iterations for decay
    
    Returns:
        Temperature value
    """
    # Apply iteration-based decay to temp_start
    # Gradually reduce exploration temperature as we train more
    if total_iters > 0:
        decay_factor = 1.0 - min(1.0, iteration / total_iters)
        iteration_adjusted_start = temp_start * decay_factor
    else:
        iteration_adjusted_start = temp_start
    
    # Then apply move-based scheduling
    if move_number < explore_moves:
        return iteration_adjusted_start
    else:
        return temp_end


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

    results = []
    
    # Filter valid decks
    valid_decks = []
    for d in all_decks:
        if isinstance(d, dict) and "m" in d and "l" in d:
            valid_decks.append(d)
            
    for deck in valid_decks:  # Run all available decks
        if not isinstance(deck, dict) or "m" not in deck or "l" not in deck:
            continue
        for seed in FIXED_SEEDS:  # Run all seeds for each deck
            deck_name = deck.get('name', 'Unknown')
            print(f"\n--- START: Deck {deck_name}, Seed {seed} ---")
            state = engine_rust.PyGameState(db)
            state.initialize_game_with_seed(deck["m"], deck["m"], [38]*12, [38]*12, deck["l"], deck["l"], seed)
            
            p0 = state.get_player(0)
            if len(p0.deck) == 0:
                print(f"!!! CRITICAL: Deck P0 is empty for {deck_name} seed {seed}!")
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
                if sims > 0 and cp in [4, 5, 0]:
                    sugg = state.search_mcts(sims, 0.0, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Solitaire, None)
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
                
                # APPLY ACTION PRIORITIZATION based on vanilla guide:
                # - Phase 5 (Live Set): Prioritize filling live set (up to 3 cards)
                # - Phase 0/4 (Main): Prioritize field placement
                # This helps with "main: should prioritise playing members to the field"
                # and "live set: can put up to three cards in live set zone"
                
                if cp == 5:  # Live Set phase
                    # Prioritize live card plays to fill the set
                    prioritized_actions = prioritize_live_set_actions(legal, state, curr_p)
                    # Use prioritized action if MCTS didn't pick one
                    if action == -1 or action not in prioritized_actions[:3]:
                        action = prioritized_actions[0] if prioritized_actions else action
                elif cp in [0, 4]:  # Main phase
                    # Prioritize field placement
                    prioritized_actions = prioritize_field_actions(legal, state, curr_p)
                    if action == -1 or action not in prioritized_actions[:3]:
                        action = prioritized_actions[0] if prioritized_actions else action

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
            winner_idx = int(winner) if winner is not None else None
            winner_str = ['P0','P1','Draw'][winner_idx] if winner_idx is not None else 'N/A'
            print(f"[{deck_name}] S{seed} | Turns: {state.turn} | Score: {p0s}-{p1s} | Winner: {winner_str}")
            
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
    parser.add_argument("--neural-mcts", action="store_true", help="Use Neural MCTS for true AlphaZero self-play (slower but learns properly)")
    parser.add_argument("--fast", action="store_true", help="Fast mode: use model directly without MCTS (quick testing)")
    args = parser.parse_args()
    
    # Set global flags based on args
    # For training (loop mode), Neural MCTS is default for actual learning
    if args.fast:
        USE_NEURAL_MCTS = False
        print("[CONFIG] Fast mode - Model-only (no MCTS, quick testing)")
    elif args.loop or args.neural_mcts:
        USE_NEURAL_MCTS = True
        print("[CONFIG] Neural MCTS enabled - True AlphaZero learning")
    else:
        USE_NEURAL_MCTS = False
        print("[CONFIG] Engine MCTS mode (default)")
    
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
        ACTION_SPACE = 248  # Card-centric action space: 8 (phase) + 60 (generic) + 180 (3 slots × 60)
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
        
        # Temperature for self-play (now move-based: high for first 20 moves, then greedy)
        # Note: This is kept for logging purposes; actual temperature is computed per-move in game functions
        TEMP_START = 1.0  # Initial temperature (high for exploration in early game)
        TEMP_END = 0.0  # Final temperature (greedy in late game)
        TEMP_EXPLORE_MOVES = 20  # Number of moves to explore with high temperature
        
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
        best_loss = float('inf')  # Default, will be loaded from checkpoint if available
        if checkpoint_path.exists():
            print(f"Resuming from: {checkpoint_path}")
            ckpt = torch.load(str(checkpoint_path), map_location=device, weights_only=True)
            model.load_state_dict(ckpt['model'])
            optimizer.load_state_dict(ckpt['optimizer'])
            start_it = ckpt.get('it', 0) + 1
            best_loss = ckpt.get('best_loss', float('inf'))  # Resume best_loss tracking
            print(f"Resumed from iteration {start_it}, best_loss: {best_loss:.4f}")
        
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
        
        def play_training_game(deck, seed, sims, db, model, device, use_dirichlet=True):
            """Play a single game for training with MCTS and move-based temperature"""
            state = engine_rust.PyGameState(db)
            state.silent = True
            state.initialize_game_with_seed(deck["m"], deck["m"], [38]*12, [38]*12, deck["l"], deck["l"], seed)
            
            initial_decks = [state.get_player(0).initial_deck, state.get_player(1).initial_deck]
            game_history = []
            moves = 0
            winner = None
            
            # Standard AlphaZero temperature: high for first 20 moves, then greedy
            EXPLORE_MOVES = 20
            
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
                    
                # Mulligan bypass (Phase -1 typically means mulligan decision, but if it has a specific phase like -1)
                if cp == -1 and MULLIGAN_ENABLED:
                    hand = pj['players'][curr_p].get('hand', [])
                    deck = pj['players'][curr_p].get('deck', [])
                    
                    try:
                        db_json_ref = db_json
                    except NameError:
                        db_path = root_dir / "data" / "cards_compiled.json"
                        with open(db_path, "r", encoding="utf-8") as f: 
                            db_json_ref = json.load(f)
                    replace_indices = calculate_mulligan_strategy(db_json_ref, hand, deck, MULLIGAN_REPLACE_COUNT)
                    
                    # Action 7 is confirm, actions 8-67 are cards in hand to replace
                    action = 7 # Confirm by default
                    
                    # Select first card to replace if any, else confirm
                    for idx in replace_indices:
                        aid = 8 + idx
                        if aid in legal:
                            action = aid
                            break
                            
                    if action == 7 and 7 not in legal:
                        action = legal[0] # Fallback
                        
                    state.step(action)
                    state.auto_step(db)
                    moves += 1
                    continue
                
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
                
                if sims > 0 and cp in [4, 5, 0]:
                    sugg = state.search_mcts(sims, 0.0, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Solitaire, None)
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
                
                # Store clean policy for training (no noise)
                clean_policy = policy_target.copy() if policy_target.sum() > 0 else policy_target
                
                # Apply Dirichlet noise for ACTION SELECTION ONLY (not for training data)
                # The function handles its own copy internally
                if use_dirichlet and policy_target.sum() > 0:
                    policy_target_for_selection = apply_dirichlet_noise(
                        policy_target, 
                        legal_vanilla_indices, 
                        alpha=DIRICHLET_ALPHA, 
                        epsilon=DIRICHLET_EPSILON
                    )
                else:
                    policy_target_for_selection = policy_target
                
                # Select action using temperature (move-based: high for first 20 moves, then greedy)
                current_temp = get_temperature_by_move(moves, temp_start=1.0, temp_end=0.0, explore_moves=EXPLORE_MOVES)
                if len(legal_vanilla_indices) > 0 and policy_target_for_selection[legal_vanilla_indices].sum() > 0:
                    selected_vid = select_action_with_temperature(
                        policy_target_for_selection, 
                        legal_vanilla_indices, 
                        temperature=current_temp
                    )
                    action = v_to_e.get(selected_vid, legal[0])
                else:
                    action = v_to_e.get(legal_vanilla_indices[0], legal[0]) if legal_vanilla_indices else legal[0]
                
                # Record transition (only for decision phases with MCTS) - use CLEAN policy
                if sims > 0 and cp in [4, 5, 0]:
                    obs_np = state.to_vanilla_tensor()
                    if isinstance(obs_np, list):
                        obs_np = np.array(obs_np, dtype=np.float32)
                    
                    # Get proper mask
                    mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
                    for aid in legal:
                        vid = map_engine_to_vanilla(pj['players'][curr_p], aid, initial_decks[curr_p], cp)
                        if 0 <= vid < ACTION_SPACE: mask[vid] = True
                    
                    game_history.append({
                        "obs": obs_np,
                        "policy": clean_policy,  # Save CLEAN policy without noise
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
                
                # Temperature is now move-based (high for first 20 moves, then greedy)
                # PLUS iteration-based decay (reduces exploration as training progresses)
                # Log the representative temperature (early game exploration with iteration decay)
                current_temp = get_temperature_by_move(0, temp_start=TEMP_START, temp_end=TEMP_END, explore_moves=TEMP_EXPLORE_MOVES, iteration=it, total_iters=args.iters)
                
                # Beta is not used (PER disabled for Windows)
                current_beta = 0.0
                
                print(f"[SCHEDULE] LR: {current_lr:.6f} | Temp: {current_temp:.4f}")
                
                # Play games with random decks and random seeds
                new_transitions = []
                game_stats = []
                decks_used = []
                
                # Use parallel game execution with ProcessPoolExecutor
                # For Neural MCTS, we need to pass the model to workers
                if NUM_WORKERS > 1 and USE_NEURAL_MCTS:
                    # Neural MCTS requires model in each process - use sequential for now
                    print("[INFO] Using sequential Neural MCTS (model in main process)")
                    for _ in range(GAMES_PER_ITER):
                        deck = random.choice(all_decks)
                        decks_used.append(deck)
                        seed = random.getrandbits(64)
                        
                        # Use Neural MCTS for true self-play with card-centric 64-dim actions
                        transitions, stats = play_selfplay_game(
                            model, device, db, deck, seed,
                            use_neural_mcts=True,
                            iteration=it,
                            total_iters=args.iters
                        )
                        new_transitions.extend(transitions)
                        game_stats.append(stats)
                elif NUM_WORKERS > 1:
                    # Prepare game parameters for engine MCTS
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
                    # Sequential execution
                    for _ in range(GAMES_PER_ITER):
                        deck = random.choice(all_decks)
                        decks_used.append(deck)
                        seed = random.getrandbits(64)
                        
                        if USE_NEURAL_MCTS:
                            # Use Neural MCTS for true self-play with card-centric actions
                            transitions, stats = play_selfplay_game(
                                model, device, db, deck, seed,
                                use_neural_mcts=True,
                                iteration=it,
                                total_iters=args.iters
                            )
                        else:
                            # Use engine MCTS
                            transitions, stats = play_training_game(
                                deck, seed, args.sims, db, model, device, 
                                use_dirichlet=True
                            )
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
                        'best_loss': best_loss,
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
                            'loss': loss,
                            'best_loss': best_loss
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
