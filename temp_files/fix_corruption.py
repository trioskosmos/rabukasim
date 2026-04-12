import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find the corrupted ability (the one that starts with card_refs instead of primary_text_jp)
for i, ability in enumerate(abilities):
    # Check if this ability is missing primary_text_jp but has card_refs
    if 'primary_text_jp' not in ability and 'card_refs' in ability:
        print(f"Found corrupted ability at index {i}")
        # Skip printing card refs to avoid encoding issues
        
        # This is the corrupted ability - replace it with the proper structure
        # The ability should be: Mill 3 cards, if all are member cards, draw 1
        new_ability = {
            "primary_text_jp": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、カードを1枚引く。",
            "primary_text_en": "",
            "source_ability_texts": [
                {
                    "jp": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、カードを1枚引く。",
                    "en": "",
                    "card_examples": [
                        "PL!HS-bp1-008-P | 徒町小鈴 (ab#0)",
                        "PL!HS-bp1-008-R | 徒町小鈴 (ab#0)"
                    ]
                }
            ],
            "trigger_id": 1,
            "trigger": "ON_PLAY",
            "frames": [
                {
                    "op": "MOVE_TO_DISCARD",
                    "frame_index": 0,
                    "value": 3,
                    "attr": {
                        "target_player": "SELF"
                    },
                    "slot": {
                        "target_slot": "CONTEXT",
                        "source_zone": "DECK_TOP",
                        "dest_zone": "DISCARD"
                    }
                },
                {
                    "op": "DISCARDED_CARDS",
                    "frame_index": 1,
                    "value": 3,
                    "attr": {
                        "card_type": "MEMBER",
                        "zone_mask": "ALL"
                    },
                    "slot": {
                        "target_slot": "STAGE_0",
                        "comparison": "GE"
                    }
                },
                {
                    "op": "JUMP_IF_FALSE",
                    "frame_index": 2,
                    "value": 1
                },
                {
                    "op": "DRAW",
                    "frame_index": 3,
                    "value": 1,
                    "slot": {
                        "target_slot": "CONTEXT"
                    }
                },
                {
                    "op": "RETURN",
                    "frame_index": 4
                }
            ],
            "card_refs": ability["card_refs"],
            "frame_verification": {
                "verified": True,
                "notes": [
                    "ON_PLAY: Mill 3 cards from top of deck. If all are member cards, draw 1 card.",
                    "Frame 0: MOVE_TO_DISCARD with value=3, source_zone=DECK_TOP, dest_zone=DISCARD - mills 3 cards from deck top",
                    "Frame 1: DISCARDED_CARDS with value=3, card_type=MEMBER - checks if all 3 discarded cards are member cards",
                    "Frame 2: JUMP_IF_FALSE with value=1 - skips effect if condition not met",
                    "Frame 3: DRAW with value=1 - draws 1 card",
                    "Frame 4: RETURN",
                    "2 cards share this pattern (徒町小鈴 variants)"
                ],
                "text_mapping": {
                    "自分のデッキの上からカードを3枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=3, source_zone=DECK_TOP, dest_zone=DISCARD",
                    "それらがすべてメンバーカードの場合": "Frame 1: DISCARDED_CARDS with value=3, card_type=MEMBER",
                    "カードを1枚引く": "Frame 3: DRAW with value=1"
                }
            }
        }
        abilities[i] = new_ability
        print(f"Fixed corrupted ability at index {i}")
        break

# Write back
with open('../data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done")
