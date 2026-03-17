import json
import os


def create_interactive_viewer():
    # 1. Load the HTML template
    template_path = "interactive_deck_viewer.html"
    if not os.path.exists(template_path):
        print(f"Error: {template_path} not found")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 2. Load all cards
    json_path = "data/cards.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        cards_db = json.load(f)

    print(f"Loaded {len(cards_db)} cards from DB.")

    # 3. Embed JSON into HTML
    # We look for: let cardsDb = {};
    # And replace it with: const cardsDb = { ... JSON ... };

    json_str = json.dumps(cards_db, ensure_ascii=False)

    # Replacement logic
    target_str = "let cardsDb = {};"
    replacement_str = f"const cardsDb = {json_str};"

    if target_str not in html_content:
        print("Error: Could not find 'let cardsDb = {};' placeholder in HTML")
        return

    new_html = html_content.replace(target_str, replacement_str)

    # Remove the init() call since data is now embedded
    # It tries to fetch 'data/cards.json', which we don't want.
    # We can just comment it out or replace it.
    new_html = new_html.replace("init();", "// init(); Data is embedded.")

    # 4. Save new file
    output_path = "interactive_deck_viewer_embedded.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"Successfully created {output_path} with {len(cards_db)} cards embedded.")


if __name__ == "__main__":
    create_interactive_viewer()
