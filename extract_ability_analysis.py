#!/usr/bin/env python3
import json
from collections import defaultdict

# Load the cards compiled database
with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract ability types
operation_types = defaultdict(int)
trigger_types = defaultdict(int)
sample_abilities = []
ability_text_samples = defaultdict(list)

# Process member cards
member_db = data.get('member_db', {})
print(f"Total member cards: {len(member_db)}\n")

for card_id, card in member_db.items():
    card_name = card.get('name', 'Unknown')
    card_no = card.get('card_no', 'Unknown')
    
    for ability in card.get('abilities', []):
        raw_text = ability.get('raw_text', '')
        trigger = ability.get('trigger', -1)
        
        # Track trigger types
        trigger_types[trigger] += 1
        
        # Track operation types
        frame_prog = ability.get('frame_program', {})
        for frame in frame_prog.get('frames', []):
            op = frame.get('op', 'UNKNOWN')
            operation_types[op] += 1
        
        # Collect diverse ability samples
        if raw_text and len(sample_abilities) < 10:
            sample_abilities.append({
                'card_no': card_no,
                'card_name': card_name,
                'trigger': trigger,
                'raw_text': raw_text[:200] + '...' if len(raw_text) > 200 else raw_text,
                'ops': [f.get('op', 'UNKNOWN') for f in frame_prog.get('frames', [])],
            })

# Print results
print("=" * 80)
print("OPERATION TYPES FOUND IN ABILITIES:")
print("=" * 80)
for op_type, count in sorted(operation_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {op_type:25s}: {count:4d} occurrences")

print("\n" + "=" * 80)
print("TRIGGER TYPES:")
print("=" * 80)
trigger_map = {
    0: "PLAY/ENTRY",
    1: "MEMBER ENTRY",
    2: "LIVE START",
    3: "SCORE",
    4: "SUPPORT",
    5: "RECOVERY",
    6: "PASSIVE/CONSTANT",
    7: "ACTIVATE",
    8: "WAIT",
    9: "DRAW",
}
for trigger_id, count in sorted(trigger_types.items()):
    trigger_name = trigger_map.get(trigger_id, f"UNKNOWN({trigger_id})")
    print(f"  {trigger_name:25s}: {count:4d} abilities")

print("\n" + "=" * 80)
print("SAMPLE DIVERSE ABILITIES (First 10):")
print("=" * 80)
for i, ability in enumerate(sample_abilities, 1):
    trigger_name = trigger_map.get(ability['trigger'], f"UNKNOWN({ability['trigger']})")
    print(f"\n{i}. Card: {ability['card_no']} ({ability['card_name']})")
    print(f"   Trigger: {trigger_name}")
    print(f"   Operations: {', '.join(ability['ops'][:5])}" + ("..." if len(ability['ops']) > 5 else ""))
    print(f"   Text: {ability['raw_text']}")
