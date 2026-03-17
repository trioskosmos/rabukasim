import sys
import os
import torch
import numpy as np
import json
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import necessary modules from the codebase
from alphazero.training.overnight_vanilla import (
    engine_rust, 
    load_vanilla_database_json, 
    UnifiedDeckParser, 
    _resolve_deck_codes,
    HighFidelityAlphaNet,
    VanillaTransformerConfig,
    VANILLA_INPUT_DIM,
    VANILLA_GLOBAL_FEATURES,
    VANILLA_TOTAL_CARDS,
    VANILLA_CARD_FEATURES,
    ACTION_SPACE
)
from alphazero.training.vanilla_action_codec import policy_id_to_engine_action

def main():
    # 1. Configuration and Loading
    db_path = ROOT_DIR / "data" / "cards_vanilla.json"
    checkpoint_path = ROOT_DIR / "checkpoints" / "vanilla_overnight" / "best.pt"
    deck_path = ROOT_DIR / "ai" / "decks" / "muse_cup.txt"
    
    print(f"Loading database from {db_path}...")
    full_db, db_json_str = load_vanilla_database_json(db_path)
    rust_db = engine_rust.PyCardDatabase(db_json_str)
    
    print(f"Loading checkpoint from {checkpoint_path}...")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    
    # Initialize Model
    # Note: Diagnostic showed embed_dim=96, which is 'tiny'
    model_config = VanillaTransformerConfig.from_preset(
        "tiny",
        input_dim=VANILLA_INPUT_DIM,
        global_dim=VANILLA_GLOBAL_FEATURES,
        total_cards=VANILLA_TOTAL_CARDS,
        card_features=VANILLA_CARD_FEATURES,
        num_actions=ACTION_SPACE,
        value_dim=1
    )
    model = HighFidelityAlphaNet(config=model_config)
    model.load_state_dict(checkpoint["model"] if isinstance(checkpoint, dict) and "model" in checkpoint else checkpoint)
    model.eval()
    
    # 2. Setup Game
    print(f"Parsing deck from {deck_path}...")
    parser = UnifiedDeckParser(full_db)
    extracted_decks = parser.extract_from_content(deck_path.read_text(encoding="utf-8"))
    deck_data = _resolve_deck_codes(parser, extracted_decks[0])
    
    # Initialize Game State
    # Both players use the same deck for simplicity
    state = engine_rust.PyGameState(rust_db)
    state.initialize_game_with_seed(
        deck_data["initial_deck"], # p0_deck
        deck_data["initial_deck"], # p1_deck
        deck_data["energy"],       # p0_energy
        deck_data["energy"],       # p1_energy
        [],                        # p0_bonus
        [],                        # p1_bonus
        4242                       # seed
    )
    state.silent = True
    state.debug_mode = False
    
    # 3. Advance to Random State with Score
    # Continue until someone scores or a limit is reached
    max_steps = 100
    print(f"Advancing game until someone scores (max {max_steps} steps)...")
    steps_taken = 0
    while steps_taken < max_steps:
        if state.is_terminal():
            break
            
        # Check if score has been achieved
        state_json = json.loads(state.to_json())
        p0_score = state_json["players"][0]["score"]
        p1_score = state_json["players"][1]["score"]
        
        if p0_score > 0 or p1_score > 0:
            print(f"Goal reached! Score: P0={p0_score}, P1={p1_score}")
            break

        legal_actions = state.get_legal_action_ids()
        if not legal_actions:
            state.auto_step(rust_db)
            steps_taken += 1
            continue

        # Use model for slightly smarter advancement to hit score faster
        # Or just random if simple enough
        action = np.random.choice(list(legal_actions))
        state.step(int(action))
        state.auto_step(rust_db)
        steps_taken += 1
        
    print(f"\n--- Scored Game State Captured (Turn {state.turn}, Phase {state.phase}) ---")
    
    # 4. Extract Observation (Input)
    obs = state.to_vanilla_tensor()
    obs_array = np.asarray(obs, dtype=np.float32)
    
    print("\n[NN INPUT: Observation Vector (Detailed Breakdown)]")
    
    # --- Global Features (0-19) ---
    print("\n  [GLOBAL FEATURES]")
    # Based on vanilla_net.py forward() and phase_ids_from_scalar()
    # Phase is at index 0
    phase_val = obs_array[0]
    print(f"  Phase Scalar: {phase_val:.4f}")
    
    # Other indicators based on common global block patterns in this project
    # Indices 1-19 are various scalars
    
    # --- Card Features (20-799) ---
    print("\n  [CARD FEATURES SUMMARY]")
    ZONE_LABELS = ["Deck", "Hand", "Stage", "Energy", "Discard", "Success", "Yell", "Live"]
    
    cards_in_zones = {label: 0 for label in ZONE_LABELS}
    for deck_pos in range(VANILLA_TOTAL_CARDS):
        base = 20 + deck_pos * 13
        if base >= len(obs_array): break
        # Feature 0 is Zone ID normalized (likely by 10.0 based on _encode)
        zone_id = int(round(obs_array[base] * 10.0))
        if 0 <= zone_id < len(ZONE_LABELS):
            cards_in_zones[ZONE_LABELS[zone_id]] += 1
            
    for zone, count in cards_in_zones.items():
        if count > 0:
            print(f"    Cards in {zone:8}: {count}")

    # Show example card in hand/stage if exists
    for deck_pos in range(VANILLA_TOTAL_CARDS):
        base = 20 + deck_pos * 13
        if base >= len(obs_array): break
        zone_id = int(round(obs_array[base] * 10.0))
        if zone_id in [1, 2]: # Hand or Stage
            print(f"\n  Example Card (Deck Pos {deck_pos}, Zone {ZONE_LABELS[zone_id]}):")
            print(f"    Card Type ID             : {obs_array[base+1]:.0f}")
            print(f"    Main Value (Norm)        : {obs_array[base+2]:.4f}")
            print(f"    Hearts (Norm)            : {obs_array[base+3]:.4f}")
            # ... and so on
            break
    
    # 5. Model Inference (Output)
    print("\nRunning Model Inference...")
    
    # Get Legal Mask
    legal_engine_ids = state.get_legal_action_ids()
    from alphazero.training.vanilla_action_codec import build_legal_policy_mask
    legal_mask = build_legal_policy_mask(state, 0, deck_data["initial_deck"], state.phase, legal_engine_ids)
    legal_mask_t = torch.tensor(legal_mask).unsqueeze(0)
    
    obs_t = torch.tensor(obs_array).unsqueeze(0) # Batch dimension
    with torch.no_grad():
        # Pass mask to forward to suppress illegal actions (if the model code uses it)
        policy_logits, value_output = model(obs_t, mask=legal_mask_t)
        probs = torch.softmax(policy_logits, dim=1).squeeze(0).numpy()
        value = torch.tanh(value_output[0, 0]).item()
    
    # 6. Extract Actions (Output)
    print("\n[NN OUTPUT: Predicted Probabilities]")
    print(f"Estimated Win Margin/Value (Value Head): {value:.4f}")
    win_prob = (value + 1) / 2
    print(f"Rough Win Probability: {win_prob*100:.1f}%")
    
    # helper to name actions correctly
    def get_action_desc(pid):
        eng_id = policy_id_to_engine_action(state, 0, pid, state.phase, deck_data["initial_deck"])
        if eng_id is not None and eng_id in legal_engine_ids:
            return f"LEGAL: {state.get_action_label(eng_id)}"
        
        # Fallback manual decoding for illegal/unmapped
        if pid == 0: return "Pass"
        if 1 <= pid < 4: return f"RPS ({pid-1})"
        if 4 <= pid < 6: return f"Turn Order ({pid-4})"
        if 6 <= pid < 26: return f"Mulligan Slot {pid-6}"
        if 26 <= pid < 46: return f"Live Set Slot {pid-26}"
        if 46 <= pid < 106: 
            h = (pid-46)//3
            s = (pid-46)%3
            return f"Play Hand {h}, Stage {s}"
        return f"Policy ID {pid}"

    top_indices = np.argsort(probs)[::-1][:10]
    print("\nTop 10 Probabilities (After Masking):")
    for idx in top_indices:
        prob = probs[idx]
        if prob < 0.0001: continue
        print(f"  ID {idx:3}: {prob:.4f} - {get_action_desc(idx)}")

    # Also show what the raw probabilities WERE for the illegal ones if we didn't mask
    with torch.no_grad():
        raw_logits, _ = model(obs_t) # No mask
        raw_probs = torch.softmax(raw_logits, dim=1).squeeze(0).numpy()
    
    print("\nTop 5 RAW Probabilities (Unmasked - likely noisy residue):")
    raw_indices = np.argsort(raw_probs)[::-1][:5]
    for idx in raw_indices:
        print(f"  ID {idx:3}: {raw_probs[idx]:.4f} - {get_action_desc(idx)}")

if __name__ == "__main__":
    main()
