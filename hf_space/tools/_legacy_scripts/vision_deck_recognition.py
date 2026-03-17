import argparse
import json
import os
from pathlib import Path

# Try to import google-generativeai, but don't fail immediately so we can show a nice error
try:
    import google.generativeai as genai
except ImportError:
    genai = None


def load_card_db():
    """Load the card database for validation and matching."""
    db_path = Path("engine/data/cards.json")
    if not db_path.exists():
        # Fallback to current dir if run from tools/
        db_path = Path("../engine/data/cards.json")

    if not db_path.exists():
        print("Warning: engine/data/cards.json not found. Validation will be limited.")
        return {}

    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)


def recognize_deck(image_path, api_key=None):
    if genai is None:
        print("Error: 'google-generativeai' package not found.")
        print("Please install it using: pip install google-generativeai")
        return None

    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment or arguments.")
        return None

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-1.5-flash")

    # Read the image
    with open(image_path, "rb") as f:
        image_data = f.read()

    prompt = """
    This image shows a deck of cards for the "Love Live! School Idol Collection" TCG.
    Please identify each card in the image. For each card, find:
    1. The Card ID (e.g., PL!-sd1-001-SD, LL-E-001-SD). The ID is often printed in small text on the card, or I might need to match it based on the character and art.
    2. The Quantity. This is usually the large white number in the black box at the bottom right of each card slot.

    Output the list as a JSON array of objects with "card_id" and "quantity" fields.
    Example:
    [
      {"card_id": "PL!-sd1-001-SD", "quantity": 1},
      {"card_id": "PL!-sd1-002-SD", "quantity": 3}
    ]

    Only output the JSON.
    """

    # Image parts for Gemini API
    image_parts = [{"mime_type": "image/png", "data": image_data}]

    print("Analyzing image with Gemini 1.5 Flash...")
    response = model.generate_content(
        [prompt, image_parts[0]], generation_config={"response_mime_type": "application/json"}
    )

    try:
        data = json.loads(response.text)
        return data
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        print("Raw response:")
        print(response.text)
        return None


def main():
    parser = argparse.ArgumentParser(description="Recognize Love Live TCG deck from a photo.")
    parser.add_argument("image", help="Path to the image file.")
    parser.add_argument("--api-key", help="Google Cloud API Key.")
    parser.add_argument("--save", help="Path to save the deck JSON.", default="recognized_deck.json")

    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"Error: Image {args.image} not found.")
        return

    card_db = load_card_db()
    results = recognize_deck(args.image, args.api_key)

    if results:
        print(f"\nRecognized {len(results)} card types:")

        main_deck = []
        energy_deck = []

        for item in results:
            cid = item.get("card_id")
            qty = item.get("quantity", 1)

            # Basic validation/cleanup
            if cid not in card_db:
                # Try to find a fuzzy match or just report as unknown
                print(f"  [?] {cid} x{qty} (Not in DB)")
            else:
                card_name = card_db[cid].get("name", "Unknown")
                card_type = card_db[cid].get("type", "")
                print(f"  [OK] {cid} x{qty} ({card_name})")

                if "エネルギー" in card_type:
                    energy_deck.extend([cid] * qty)
                else:
                    main_deck.extend([cid] * qty)

        output_data = {"player": 0, "deck": main_deck, "energy_deck": energy_deck}

        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\nSaved deck to {args.save}")
        print(f"Total: {len(main_deck)} Main | {len(energy_deck)} Energy")


if __name__ == "__main__":
    main()
