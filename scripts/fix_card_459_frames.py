import json

# Load generated frames
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find the ability for PL!S-bp3-025-L
for ability in data['abilities']:
    if isinstance(ability, dict) and 'card_refs' in ability:
        for ref in ability['card_refs']:
            if ref.get('card_no') == 'PL!S-bp3-025-L':
                print(f"Found PL!S-bp3-025-L, fixing frames...")
                # Fix the frames to match authored frames
                ability['frames'] = [
                    {
                        "op": "SELECT_MEMBER",
                        "frame_index": 0,
                        "value": 1,
                        "attr": {
                            "target_player": "SELF",
                            "group_enabled": 1,
                            "group_id": "AQOURS"
                        },
                        "slot": {
                            "target_slot": "CONTEXT",
                            "source_zone": "STAGE"
                        }
                    },
                    {
                        "op": "COUNT_BLADES",
                        "frame_index": 1,
                        "value": 6,
                        "attr": {
                            "target_player": "SELF"
                        },
                        "slot": {
                            "target_slot": "CONTEXT",
                            "comparison": "GE"
                        }
                    },
                    {
                        "op": "JUMP_IF_FALSE",
                        "frame_index": 2,
                        "value": 1
                    },
                    {
                        "op": "BOOST_SCORE",
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
                ]
                # Fix the db field
                ref['db'] = 'live_db'
                ref['card_id'] = 459
                print("Fixed frames and db field")
                break

# Save the fixed data
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write('\n')

print("Saved fixed frames")
