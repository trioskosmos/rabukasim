"""Analyze why ability texts differ between backup and semantic extraction."""

import json

def load_backup():
    with open("launcher/static_content/data/ability_frame_source.json.backup", "r", encoding="utf-8") as f:
        return json.load(f)

def load_semantic():
    with open("data/abilities_extracted_from_cards.json", "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_text(text):
    """Normalize text for comparison - remove formatting, whitespace."""
    import re
    # Remove image tags like {{icon_blade.png|ブレード}}
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def main():
    backup_data = load_backup()
    semantic_data = load_semantic()
    
    backup_abilities = backup_data["abilities"]
    semantic_abilities = semantic_data["unique_abilities"]
    
    # Build maps by normalized text
    backup_map = {}
    for ab in backup_abilities:
        norm_text = normalize_text(ab["primary_text_jp"])
        backup_map[norm_text] = ab
    
    semantic_map = {}
    for ab in semantic_abilities:
        norm_text = normalize_text(ab.get("full_text", ab.get("use_limitless_text", "")))
        semantic_map[norm_text] = ab
    
    backup_norm_texts = set(backup_map.keys())
    semantic_norm_texts = set(semantic_map.keys())
    
    only_in_backup = backup_norm_texts - semantic_norm_texts
    only_in_semantic = semantic_norm_texts - backup_norm_texts
    common = backup_norm_texts & semantic_norm_texts
    
    print(f"=== NORMALIZED TEXT COMPARISON (BACKUP vs SEMANTIC) ===\n")
    print(f"Backup abilities: {len(backup_abilities)}")
    print(f"Semantic abilities: {len(semantic_abilities)}")
    print(f"Only in backup (normalized): {len(only_in_backup)}")
    print(f"Only in semantic (normalized): {len(only_in_semantic)}")
    print(f"Common (normalized): {len(common)}")
    
    # Show examples of only in backup
    if only_in_backup:
        print(f"\n=== ABILITIES ONLY IN BACKUP (first 10) ===")
        for i, norm_text in enumerate(list(only_in_backup)[:10]):
            print(f"{i+1}. {norm_text[:100]}...")
            print(f"   Original: {backup_map[norm_text]['primary_text_jp'][:80]}...")
            print()
    
    # Show examples of only in semantic
    if only_in_semantic:
        print(f"\n=== ABILITIES ONLY IN SEMANTIC (first 10) ===")
        for i, norm_text in enumerate(list(only_in_semantic)[:10]):
            print(f"{i+1}. {norm_text[:100]}...")
            print(f"   Original: {semantic_map[norm_text].get('full_text', semantic_map[norm_text].get('use_limitless_text', ''))[:80]}...")
            print()

if __name__ == "__main__":
    main()
