#!/usr/bin/env python3
"""Check how many cards are in ability_frame_source."""
import json

# Load source
with open('ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_source = json.load(f)

# Get all (card_no, ab_idx) tuples
frames_by_card = {}
for ability in frame_source.get('abilities', []):
    primary_text_jp = ability.get('primary_text_jp', '')
    source_texts = ability.get('source_ability_texts', [])
    
    for src in source_texts:
        for card_ex in src.get('card_examples', []):
            # Parse "PL!S-bp2-004-P | 黒澤ダイヤ (ab#0)"
            parts = card_ex.split('|')
            if parts:
                card_no = parts[0].strip()
                # Extract ab_idx from "(ab#0)"
                rest = card_ex.split('(ab#')
                if len(rest) > 1:
                    ab_idx_str = rest[1].split(')')[0]
                    try:
                        ab_idx = int(ab_idx_str)
                        if card_no not in frames_by_card:
                            frames_by_card[card_no] = set()
                        frames_by_card[card_no].add(ab_idx)
                    except ValueError:
                        pass

print(f"Cards in ability_frame_source.json: {len(frames_by_card)}")

# Now check against cards.json
with open('cards.json', 'r', encoding='utf-8') as f:
    cards_json = json.load(f)

member_cards = {k: v for k, v in cards_json.items() if v.get('type') == 'メンバー'}
print(f"Member cards in cards.json: {len(member_cards)}")

# Check coverage
covered_members = 0
uncovered = []
for card_no in member_cards.keys():
    if card_no in frames_by_card:
        covered_members += 1
    else:
        uncovered.append(card_no)

print(f"Members with frames: {covered_members} / {len(member_cards)}")
print(f"Members without frames: {len(uncovered)} / {len(member_cards)}")
print(f"Coverage: {100 * covered_members / len(member_cards):.1f}%")

# Show some uncovered cards
print(f"\nFirst 20 uncovered member cards:")
for card_no in uncovered[:20]:
    card = member_cards[card_no]
    print(f"  {card_no}: {card.get('name')} (ability: {len(str(card.get('ability', ''))) > 0})")
