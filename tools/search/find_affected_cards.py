import json
import re

try:
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        cards = json.load(f)
except FileNotFoundError:
    print("Could not find data/cards_compiled.json")
    exit(1)

affected_cards = []

print(f"Loaded {len(cards)} cards")
print(f"Sample keys: {list(cards.keys())[:5]}")

# Relaxed pattern: Look for "Draw" (引) and "Hand...Place/Discard" (手札...置/捨)
# We don't enforce order heavily, just presence in the same ability block
# But we exclude blocks that HAVE a colon, as those likely legitimately have costs.
pattern_colon = re.compile(r"[:：]")

# Collect all cards from member_db and live_db
all_cards = {}
if "member_db" in cards:
    all_cards.update(cards["member_db"])
if "live_db" in cards:
    all_cards.update(cards["live_db"])

print(f"Total cards to check: {len(all_cards)}")

for card_id, card in all_cards.items():
    if card_id in ["441", "444"]:
        print(f"Checking ID {card_id}: {card.get('card_no')}")

    if not isinstance(card, dict) or "abilities" not in card:
        continue

    for ab in card.get("abilities", []):
        text = ab.get("raw_text", "")

        # We explicitly want to find cards like Shioriko:
        # "{{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く"

        has_draw = "引" in text
        has_discard_phrase = "手札を" in text and ("置" in text or "捨" in text)
        has_colon = pattern_colon.search(text)

        if card.get("card_no") in ["PL!N-sd1-010-SD", "PL!N-sd1-013-SD"]:
            print(f"DEBUG {card.get('card_no')}: {text}")
            print(f"  Draw: {'引' in text} ({text.find('引')})")
            print(f"  Hand: {'手札を' in text}")
            print(f"  Discard: {'置' in text or '捨' in text}")
            print(f"  Colon: {pattern_colon.search(text)}")

        if has_draw and has_discard_phrase and not has_colon:
            affected_cards.append({"id": card.get("card_no", card_id), "name": card.get("name"), "text": text})

with open("affected_list_utf8.txt", "w", encoding="utf-8") as f:
    f.write(f"Found {len(affected_cards)} potentially affected cards:\n")
    for c in affected_cards:
        f.write(f"- {c['id']} {c['name']}: {c['text']}\n")

print(f"Written {len(affected_cards)} cards to affected_list_utf8.txt")
