"""Compare ability counts between backup and converted frame sources."""

import json

def load_backup():
    with open("launcher/static_content/data/ability_frame_source.json.backup", "r", encoding="utf-8") as f:
        return json.load(f)

def load_converted():
    with open("data/ability_frame_source.json", "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    backup_data = load_backup()
    converted_data = load_converted()
    
    backup_abilities = backup_data["abilities"]
    converted_abilities = converted_data["abilities"]
    
    backup_count = len(backup_abilities)
    converted_count = len(converted_abilities)
    
    print(f"=== ABILITY COUNT COMPARISON ===\n")
    print(f"Backup abilities: {backup_count}")
    print(f"Converted abilities: {converted_count}")
    print(f"Difference: {converted_count - backup_count}")
    
    # Get unique texts
    backup_texts = {ab["primary_text_jp"] for ab in backup_abilities}
    converted_texts = {ab["primary_text_jp"] for ab in converted_abilities}
    
    only_in_backup = backup_texts - converted_texts
    only_in_converted = converted_texts - backup_texts
    common = backup_texts & converted_texts
    
    print(f"\n=== UNIQUE ABILITY TEXTS ===\n")
    print(f"Only in backup: {len(only_in_backup)}")
    print(f"Only in converted: {len(only_in_converted)}")
    print(f"Common: {len(common)}")
    
    # Show some examples
    if only_in_backup:
        print(f"\n=== SAMPLE: ABILITIES ONLY IN BACKUP (first 10) ===")
        for i, text in enumerate(list(only_in_backup)[:10]):
            print(f"{i+1}. {text[:100]}...")
    
    if only_in_converted:
        print(f"\n=== SAMPLE: ABILITIES ONLY IN CONVERTED (first 10) ===")
        for i, text in enumerate(list(only_in_converted)[:10]):
            print(f"{i+1}. {text[:100]}...")
    
    # Compare frame counts for common abilities
    print(f"\n=== FRAME COUNT COMPARISON FOR COMMON ABILITIES ===\n")
    
    frame_diff_count = 0
    frame_diffs = []
    
    for text in common:
        backup_ab = next(ab for ab in backup_abilities if ab["primary_text_jp"] == text)
        converted_ab = next(ab for ab in converted_abilities if ab["primary_text_jp"] == text)
        
        backup_frames = len(backup_ab.get("frames", []))
        converted_frames = len(converted_ab.get("frames", []))
        
        if backup_frames != converted_frames:
            frame_diff_count += 1
            frame_diffs.append((text, backup_frames, converted_frames))
    
    print(f"Abilities with different frame counts: {frame_diff_count} / {len(common)}")
    
    if frame_diffs:
        print(f"\n=== SAMPLE: FRAME COUNT DIFFERENCES (first 20) ===")
        for i, (text, backup_frames, converted_frames) in enumerate(frame_diffs[:20]):
            print(f"{i+1}. Backup: {backup_frames} frames, Converted: {converted_frames} frames")
            print(f"   Text: {text[:80]}...")
            print()

if __name__ == "__main__":
    main()
