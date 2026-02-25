import json
import os

def verify_images():
    json_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\cards_compiled.json"
    img_root = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\frontend\img"
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    member_db = data.get("member_db", {})
    live_db = data.get("live_db", {})
    
    missing_paths = []
    missing_ids = []
    
    def check_card(card_id, card_data):
        card_no = card_data.get("card_no", "Unknown")
        img_path = card_data.get("img_path")
        
        # Check img_path
        if img_path:
            full_img_path = os.path.join(img_root, img_path.replace("/", "\\"))
            if not os.path.exists(full_img_path):
                missing_paths.append((card_id, card_no, img_path))
        else:
            print(f"Warning: Card {card_id} ({card_no}) has no img_path.")

        # Check for card_id.webp as requested by user
        id_webp_path = os.path.join(img_root, "cards_webp", f"{card_id}.webp")
        if not os.path.exists(id_webp_path):
            missing_ids.append((card_id, card_no))

    print("Checking member_db...")
    for card_id, card_data in member_db.items():
        check_card(card_id, card_data)
    
    print("Checking live_db...")
    for card_id, card_data in live_db.items():
        check_card(card_id, card_data)

    print("\n--- RESULTS ---")
    if missing_paths:
        print(f"\nMissing img_paths ({len(missing_paths)}):")
        for cid, cno, path in missing_paths:
            print(f"  ID: {cid}, No: {cno}, Path: {path}")
    else:
        print("\nAll img_paths are present.")

    if missing_ids:
        print(f"\nMissing cardid.webp files ({len(missing_ids)}):")
        # Only print first 20 to avoid flood
        for cid, cno in missing_ids[:20]:
            print(f"  ID: {cid}, No: {cno} (expected {cid}.webp)")
        if len(missing_ids) > 20:
            print(f"  ... and {len(missing_ids) - 20} more.")
    else:
        print("\nAll cardid.webp files are present.")

if __name__ == "__main__":
    verify_images()
