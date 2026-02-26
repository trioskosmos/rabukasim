import json

def precision_clean():
    # Source of truth for Japanese abilities
    with open('reports/bp5_deep_audit_raw.json', 'r', encoding='utf-8') as f:
        audit_data = json.load(f)
    
    # Target file
    target_file = 'data/manual_pseudocode.json'
    with open(target_file, 'r', encoding='utf-8') as f:
        manual_data = json.load(f)
    
    modified_count = 0
    removed_ids = []
    
    for card_id, manual_entry in list(manual_data.items()):
        if "-bp5-" not in card_id:
            continue
            
        # Check against audit data
        if card_id not in audit_data:
            # If not in audit, it might be a missing card or a differently formatted ID
            # For now, if we don't have source text, we should be cautious.
            continue
            
        source_text = audit_data[card_id].get('ability')
        
        # If Japanese ability is null or empty
        if not source_text:
            # Check if it's an "E" card (Special)
            is_e_card = "-E" in card_id
            
            # Current pseudocode
            current_p = manual_entry.get('pseudocode', "")
            
            if not is_e_card:
                # Normal card with no ability text should have NO triggered effects
                if "TRIGGER: ON_" in current_p or "TRIGGER: ACTIVATED" in current_p:
                    # It has an ability it shouldn't have.
                    # We should probably remove the triggered parts.
                    # If it has a CONSTANT heart (e.g. PR cards), we keep it.
                    lines = current_p.split('\n')
                    new_lines = [l for l in lines if "TRIGGER: CONSTANT" in l or "EFFECT: ADD_HEARTS" in l or "EFFECT: ADD_BLADES" in l]
                    # If after cleaning it's just empty or only has constant hearts, that's better.
                    # But most skill-less N cards don't even have ADD_HEARTS in pseudocode (it's in raw data).
                    
                    if not any("EFFECT: ADD_" in l for l in new_lines):
                        # It's completely skill-less.
                        print(f"Cleaning Skill-less card: {card_id}")
                        manual_data[card_id]["pseudocode"] = "" # Or remove it? Let's clear it.
                    else:
                        manual_data[card_id]["pseudocode"] = "\n".join(new_lines).strip()
                    
                    modified_count += 1
            else:
                # E-cards should ONLY have CONSTANT hearts/blades.
                lines = current_p.split('\n')
                new_lines = [l for l in lines if "TRIGGER: CONSTANT" in l or "EFFECT: ADD_HEARTS" in l or "EFFECT: ADD_BLADES" in l or "EFFECT: BOOST_SCORE" in l]
                manual_data[card_id]["pseudocode"] = "\n".join(new_lines).strip()
                modified_count += 1

    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(manual_data, f, indent=4, ensure_ascii=False)
    
    print(f"Precision Clean complete. Modified {modified_count} cards.")

if __name__ == "__main__":
    precision_clean()
