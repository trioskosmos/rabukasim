import os
from PIL import Image
import json

def convert_and_move():
    src_dir = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\frontend\img\downloaded_temp"
    dest_dir = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\frontend\img\cards_webp"
    json_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\cards_compiled.json"

    if not os.path.exists(src_dir):
        print("Source directory not found.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Map card_no to card_id for potential naming alignment (though card_no is fine per user)
    # However, user mentioned card number is fine. But we need to match the img_path in JSON.
    all_cards = {**data.get("member_db", {}), **data.get("live_db", {})}
    
    # Map card_no (normalized) to the expected filename in img_path
    no_to_meta_path = {}
    for card_id, card_data in all_cards.items():
        card_no = card_data.get("card_no")
        img_path = card_data.get("img_path")
        if card_no and img_path:
            filename = os.path.basename(img_path)
            no_to_meta_path[card_no] = filename
            # Add normalization variants
            no_to_meta_path[card_no.replace("＋", "+")] = filename
            no_to_meta_path[card_no.replace("!", "_").replace("+", "_")] = filename

    count = 0
    for filename in os.listdir(src_dir):
        if filename.endswith(".png"):
            basename = os.path.splitext(filename)[0]
            
            # Find the target filename from metadata
            # Source filename was safe_name = card_no.replace("!", "_").replace("+", "_") + ".png"
            # Reverse lookup or direct match
            target_filename = None
            
            # Try to match the basename back to a card_no
            potential_no = basename.replace("_", "!") # Partial reversal
            # This is tricky because we replaced both ! and + with _
            
            # Better: iterate through all cards and see if one matches this basename
            for card_no, meta_filename in no_to_meta_path.items():
                safe_no = card_no.replace("!", "_").replace("+", "_").replace("＋", "_")
                if safe_no == basename:
                    target_filename = meta_filename
                    break
            
            if not target_filename:
                # Fallback to the basename as webp if not found in metadata
                target_filename = basename + ".webp"
                print(f"Warning: No metadata found for {basename}, using {target_filename}")

            src_file = os.path.join(src_dir, filename)
            dest_file = os.path.join(dest_dir, target_filename)

            try:
                with Image.open(src_file) as img:
                    img.save(dest_file, "WEBP")
                print(f"Converted {filename} -> {target_filename}")
                count += 1
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

    print(f"Total converted: {count}")

if __name__ == "__main__":
    convert_and_move()
