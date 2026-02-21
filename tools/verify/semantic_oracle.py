
import json
import re
import sys

# Force UTF-8 for Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

# Semantic Oracle Prototype
# Purpose: Parse Raw JP Text -> Semantic Expectations JSON

def parse_card_text(card_data):
    """
    Parses the raw Japanese text of a card and generates semantic expectations.
    """
    # Target Card
    card_id = "PL!HS-bp2-001-R"
    print(f"Processing Card: {card_id}")
    
    # Fetch Data
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)
        raw_text = cards.get(card_id, {}).get("ability", "")

    print(f"Raw Text: {raw_text}\n")

    scenarios = []

    # 1. Split by Triggers (Improved)
    # Use capturing group to keep delimiters
    # Expected format: "{{live_start...}}Effect..."
    abilities = []
    parts = re.split(r'(\{\{.*?\}\}|ライブ開始時|ライブ成功時|登場時|起動|自動)', raw_text)
    
    current_trigger = None
    current_text = ""
    
    for part in parts:
        if not part.strip(): continue
        
        # Check if part is a trigger
        is_trigger = False
        trigger_type = None
        
        if "ライブ開始時" in part or "live_start" in part:
            trigger_type = "ON_LIVE_START"
            is_trigger = True
        elif "ライブ成功時" in part or "live_success" in part:
             trigger_type = "ON_LIVE_SUCCESS"
             is_trigger = True
        elif "登場時" in part or "toujyou" in part or "on_play" in part:
             trigger_type = "ON_PLAY"
             is_trigger = True
        elif "起動" in part:
            trigger_type = "ACTIVATED"
            is_trigger = True
        elif "自動" in part:
            trigger_type = "AUTO"
            is_trigger = True
             
        if is_trigger:
            if current_trigger:
                abilities.append((current_trigger, current_text.strip()))
            current_trigger = trigger_type
            current_text = ""
        else:
            current_text += part
            
    if current_trigger:
        abilities.append((current_trigger, current_text.strip()))

    # Fallback: if no trigger found but text exists, treat as CONSTANT or Unknown
    if not abilities and raw_text.strip():
        print("Warning: No explicit trigger found. Treating as whole block.")
        # For now, we just skip or log.


    print(f"Found {len(abilities)} abilities.")

    
    # 2. Parse Each Ability
    for idx, (trigger, text) in enumerate(abilities):
        print(f"  Ability {idx+1}: Trigger={trigger}, Text='{text}'")
        
        # --- Logic for Cost Extraction ---
        energy_cost = text.count("icon_energy.png")  # Count E icons
        sacrifice_cost = "このメンバーをステージから控え室に置く" in text
        
        print(f"  [DEBUG] Cost Analysis: Energy={energy_cost}, Sacrifice={sacrifice_cost}")

        # Auto-detect Cost Mismatch (Prototype Feature)
        if energy_cost > 0:
             # Expect Pay Energy
             scenarios.append({
                 "name": f"Ab{idx}_CostCheck_Energy",
                 "trigger": trigger,
                 "setup": {},
                 "action": { "type": "ACTIVATE" },
                 "expect": { 
                     "energy_paid": energy_cost,
                     "notes": f"Must pay {energy_cost} Energy."
                 }
             })
        
        if sacrifice_cost:
             # Expect Sacrifice
             scenarios.append({
                 "name": f"Ab{idx}_CostCheck_Sacrifice",
                 "trigger": trigger,
                 "setup": {},
                 "action": { "type": "ACTIVATE" },
                 "expect": { 
                     "member_sacrificed": True,
                     "notes": "Must sacrifice self."
                 }
             })
        print(f"  Debug Repr: {repr(text)}")
        
        # --- Logic for Ability A (Live Start) ---
        if trigger == "ON_LIVE_START":
            # ACTUAL TEXT FOUND: "ライブ終了時まで、エールによって公開される自分のカードが持つ[桃ブレード]...は、すべて[青ブレード]になる。"
            
            # Logic: Color Change / Attribute Rewrite
            has_cond = "エールによって公開される" in text
            has_effect = "すべて[青ブレード]になる" in text

            if has_cond and has_effect:
                 # Scenario 1: Happy Path (Color Change)
                 scenarios.append({
                     "name": f"Ab{idx}_BladeColorChange_Blue",
                     "trigger": trigger,
                     "setup": { 
                         "deck_top": ["PINK_BLADE_CARD"],
                         "description": "Top card has Pink Blade"
                     },
                     "action": { "type": "START_LIVE" },
                     "expect": { 
                         "blade_color_delta": "BLUE",
                         "notes": "Revealed card's blade becomes Blue."
                     }
                 })
                 
                 # Scenario 2: Failure Path
                 scenarios.append({
                     "name": f"Ab{idx}_NoHeart_NoScoreUp",
                     "trigger": trigger,
                     "setup": { 
                         "stage_hearts": ["HEART_01"], # Different heart
                         "base_score": 1,
                         "description": "Card DOES NOT have Heart 06"
                     },
                     "action": { "type": "START_LIVE" },
                     "expect": { 
                         "score_delta": 0,
                         "notes": "Score should NOT increase."
                     }
                 })

        # --- Logic for Ability B (Live Success) ---
        elif trigger == "ON_LIVE_SUCCESS":
            # "エールにより公開された自分の『虹ヶ咲学園スクールアイドル同好会』のメンバーの場合、それを手札に加える。"
            # Relaxed matching
            # Note: The text is specific to "Nijigasaki Member", but for prototype we just check "Member" and "Add to Hand"
            has_cond = "公開された" in text and "メンバー" in text
            has_effect = "手札に加える" in text or "手札に加え" in text

            if has_cond and has_effect:
                # Scenario 1: Hit (Member)
                scenarios.append({
                    "name": f"Ab{idx}_RevealMember_AddHand",
                    "trigger": trigger,
                    "setup": {
                        "deck_top": ["MEMBER_CARD"],
                        "description": "Top of deck is a Member"
                    },
                    "action": { "type": "LIVE_SUCCESS" },
                    "expect": {
                        "hand_delta": 1,
                        "notes": "Revealed member is added to hand."
                    }
                })

                # Scenario 2: Miss (Non-Member)
                scenarios.append({
                    "name": f"Ab{idx}_RevealSpell_NoAdd",
                    "trigger": trigger,
                    "setup": {
                        "deck_top": ["SPELL_CARD"],
                        "description": "Top of deck is NOT a Member"
                    },
                    "action": { "type": "LIVE_SUCCESS" },
                    "expect": {
                        "hand_delta": 0,
                        "notes": "Revealed spell is NOT added to hand."
                    }
                })

    return {
        "card_no": card_id,
        "scenarios": scenarios
    }

if __name__ == "__main__":
    # Load Real Data
    try:
        with open("data/cards.json", "r", encoding="utf-8") as f:
            db = json.load(f)
    except FileNotFoundError:
        print("Error: data/cards.json not found.")
        sys.exit(1)

    # Target Card
    target_id = "PL!N-bp4-025-L"
    if target_id not in db:
        print(f"Card {target_id} not found in DB.")
        sys.exit(1)

    card_data = db[target_id]
    
    # Generate Semantic Expectations
    result = parse_card_text(card_data)
    
    # Output JSON
    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    print("\nGenerated Semantic Expectations (JSON):")
    print(output_json)
    
    # Save to file
    with open("tools/verify/semantic_demo_output.json", "w", encoding="utf-8") as f:
        f.write(output_json)
