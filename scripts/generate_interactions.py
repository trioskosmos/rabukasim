import json
import os

import engine_rust
from tqdm import tqdm


def generate_interactions():
    db_path = "engine/data/cards_compiled.json"
    if not os.path.exists(db_path):
        db_path = "data/cards_compiled.json"
    
    with open(db_path, "r", encoding="utf-8") as f:
        db_json_raw = f.read()
        db_data = json.loads(db_json_raw)
    
    db = engine_rust.PyCardDatabase(db_json_raw)
    
    member_ids = [int(k) for k in db_data["member_db"].keys()]
    live_ids = [int(k) for k in db_data["live_db"].keys()]
    energy_ids = [int(k) for k in db_data["energy_db"].keys()]
    
    # Create a saturated state
    p0_deck = (member_ids[:20] if len(member_ids) >= 20 else member_ids * 5)[:20]
    p1_deck = p0_deck.copy()
    p0_energy = (energy_ids[:10] if len(energy_ids) >= 10 else energy_ids * 5)[:10]
    p1_energy = p0_energy.copy()
    p0_lives = (live_ids[:3] if len(live_ids) >= 3 else live_ids * 3)[:3]
    p1_lives = p0_lives.copy()
    
    results = []
    
    print(f"Analyzing {len(member_ids)} member cards...")
    
    for mid in tqdm(member_ids):
        card_data = db_data["member_db"][str(mid)]
        card_name = card_data.get("name", "Unknown")
        card_no = card_data.get("card_no", "???")
        
        abilities = card_data.get("abilities", [])
        for ab_idx, ab in enumerate(abilities):
            bytecode = ab.get("bytecode", [])
            if not bytecode:
                continue
            
            # Create a fresh game state for each ability
            gs = engine_rust.PyGameState(db)
            gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)
            
            # Setup card on stage for player 0
            # Use properties instead of methods for current_player
            gs.current_player = 0
            
            # To modify player state, we need to sync it back
            state_json = json.loads(gs.to_json())
            # Put the card in the first stage slot of player 0
            state_json["players"][0]["stage"][0] = mid
            # Also put some cards in hand and discard for better selection triggers
            state_json["players"][0]["hand"] = p0_deck[5:10]
            state_json["players"][0]["discard"] = p0_deck[10:15]
            
            gs.apply_state_json(json.dumps(state_json))
            
            # Execute bytecode
            try:
                gs.debug_execute_bytecode(
                    bytecode, 
                    player_id=0, 
                    area_idx=0, 
                    source_card_id=mid, 
                    target_slot=0, 
                    choice_index=-1, 
                    selected_color=0
                )
            except Exception:
                continue
            
            # Check interaction stack
            interaction = gs.get_interaction()
            if interaction:
                # We hit a suspension point!
                labels = []
                action_ids = gs.get_legal_action_ids()
                for aid in action_ids:
                    try:
                        label = gs.get_verbose_label(aid)
                        labels.append({"action_id": aid, "label": label})
                    except:
                        labels.append({"action_id": aid, "label": f"Action {aid}"})
                
                results.append({
                    "card_id": mid,
                    "card_no": card_no,
                    "card_name": card_name,
                    "ability_index": ab_idx,
                    "ability_text": ab.get("raw_text", ""),
                    "choice_type": interaction.choice_type,
                    "choice_text": gs.pending_choice_text,
                    "action_labels": labels
                })

    # Same for lives
    print(f"Analyzing {len(live_ids)} live cards...")
    for lid in tqdm(live_ids):
        card_data = db_data["live_db"][str(lid)]
        abilities = card_data.get("abilities", [])
        for ab_idx, ab in enumerate(abilities):
            bytecode = ab.get("bytecode", [])
            if not bytecode:
                continue
            
            gs = engine_rust.PyGameState(db)
            gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)
            
            try:
                gs.debug_execute_bytecode(
                    bytecode, 
                    player_id=0, 
                    area_idx=0, 
                    source_card_id=lid, 
                    target_slot=0, 
                    choice_index=-1, 
                    selected_color=0
                )
            except:
                continue
                
            interaction = gs.get_interaction()
            if interaction:
                labels = []
                for aid in gs.get_legal_action_ids():
                    labels.append({"action_id": aid, "label": gs.get_verbose_label(aid)})
                
                results.append({
                    "card_id": lid,
                    "card_no": card_data.get("card_no", "???"),
                    "card_name": card_data.get("name", "Unknown"),
                    "ability_index": ab_idx,
                    "ability_text": ab.get("raw_text", ""),
                    "choice_type": interaction.choice_type,
                    "choice_text": gs.pending_choice_text,
                    "action_labels": labels
                })

    output_path = "qa/interactions_analysis.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Generated interactions for {len(results)} card abilities.")

if __name__ == "__main__":
    generate_interactions()
