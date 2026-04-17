"""Check if missing abilities have different text format than expected."""

import json

with open("launcher/static_content/data/ability_frame_source.json.backup", "r", encoding="utf-8") as f:
    backup_data = json.load(f)
backup_abilities = {ab["primary_text_jp"]: ab for ab in backup_data["abilities"]}

with open("data/abilities_extracted_from_cards.json", "r", encoding="utf-8") as f:
    semantic_data = json.load(f)
semantic_texts = set(ab["full_text"] for ab in semantic_data["unique_abilities"])

backup_only = set(backup_abilities.keys()) - semantic_texts

print(f"=== SAMPLE MISSING ABILITIES FROM BACKUP ===\n")
for text in list(backup_only)[:10]:
    ability = backup_abilities[text]
    print(f"Trigger: {ability.get('trigger')}")
    print(f"Text: {text[:150]}...")
    print(f"Card count: {ability.get('card_refs', [{}])[0].get('card_no', 'N/A')}")
    print()

# Check if semantic has similar text but with different formatting
print(f"\n=== CHECKING FOR SIMILAR TEXT IN SEMANTIC ===\n")
for backup_text in list(backup_only)[:5]:
    backup_lower = backup_text.lower()
    
    # Look for semantic abilities with similar core text (without icons)
    backup_core = backup_text.replace("{{", "").replace("}}", "").replace(".png", "").replace("|", "")
    
    for semantic_ab in semantic_data["unique_abilities"]:
        semantic_text = semantic_ab["full_text"]
        semantic_core = semantic_text.replace("{{", "").replace("}}", "").replace(".png", "").replace("|", "")
        
        if len(backup_core) > 20 and backup_core[:30] in semantic_core:
            print(f"POSSIBLE MATCH:")
            print(f"  Backup:  {backup_text[:100]}...")
            print(f"  Semantic: {semantic_text[:100]}...")
            print()
            break
