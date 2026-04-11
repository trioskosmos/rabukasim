#!/usr/bin/env python3
"""Find abilities missing frames or with minimal frames."""
import json

# Load ability frame source
with open('ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_source = json.load(f)

# Count abilities with frames vs without
with_frames = 0
without_frames = 0
minimal_frames = 0
no_frames_list = []

for i, ability in enumerate(frame_source.get('abilities', [])):
    frames = ability.get('frames', [])
    if not frames:
        without_frames += 1
        no_frames_list.append((i, ability))
    elif len(frames) <= 1:
        minimal_frames += 1
    else:
        with_frames += 1

print(f"Total abilities: {len(frame_source.get('abilities', []))}")
print(f"With frames (>1): {with_frames}")
print(f"No frames: {without_frames}")
print(f"Just 1 frame: {minimal_frames}")

# Show all abilities without frames
print(f"\n=== {without_frames} Abilities Without Frames ===\n")
for idx, (i, ability) in enumerate(no_frames_list, 1):
    trigger = ability.get('trigger', 'UNKNOWN')
    jp_text = ability.get('primary_text_jp', '')
    source_text = ability.get('source_ability_texts', [{}])[0].get('jp', jp_text)[:120]
    
    cards = []
    for text_obj in ability.get('source_ability_texts', []):
        cards.extend(text_obj.get('card_examples', []))
    
    print(f"{idx}. [{i}] Trigger: {trigger}")
    print(f"   JP Text: {source_text}...")
    print(f"   Cards: {', '.join(cards[:2])}")
    print()
