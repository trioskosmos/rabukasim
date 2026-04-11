#!/usr/bin/env python3
"""
Identify incorrect frame operation replacements by comparing with semantic text
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_data = json.load(f)

# Load semantic dump for reference
with open('data/ability_semantic_dump.json', 'r', encoding='utf-8') as f:
    semantic_data = json.load(f)

# Create a mapping of ability_index to semantic data
semantic_map = {ability['ability_index']: ability for ability in semantic_data['abilities']}

# Abilities with likely incorrect replacements based on semantic analysis
incorrect_replacements = []

# Ability 594: Complex yell repeat logic that I oversimplified
frame_594 = frame_data['abilities'][594]
semantic_594 = semantic_map[594]
text_594 = semantic_594['primary_text_jp']
if "ブレードハートを失い" in text_594 and "もう一度エールを行う" in text_594:
    incorrect_replacements.append((594, "Missing LOSE_BLADE_HEARTS and REPEAT_YELL frames"))

# Ability 610: Two-part ability that needs proper separation
frame_610 = frame_data['abilities'][610]
semantic_610 = semantic_map[610]
text_610 = semantic_610['primary_text_jp']
if "コスト4以下" in text_610:
    incorrect_replacements.append((610, "Missing cost filter on opponent tap detection"))

# Ability 611: IS_TAPPED vs IS_SELF_TAP
frame_611 = frame_data['abilities'][611]
semantic_611 = semantic_map[611]
text_611 = semantic_611['primary_text_jp']
if "このメンバーが" in text_611 and "ウェイト状態になったとき" in text_611:
    incorrect_replacements.append((611, "IS_TAPPED should be IS_SELF_TAP for self-specific condition"))

# Ability 521: SUM_VALUE might not be right for yell score addition
frame_521 = frame_data['abilities'][521]
semantic_521 = semantic_map[521]
text_521 = semantic_521['primary_text_jp']
if "エールで出た" in text_521 and "スコア1つにつき" in text_521:
    incorrect_replacements.append((521, "SUM_VALUE might not correctly handle per-yell-score addition"))

print("Identified incorrect frame operation replacements:\n")
for ability_id, reason in incorrect_replacements:
    print(f"Ability {ability_id}: {reason}")
    semantic_ability = semantic_map[ability_id]
    print(f"  Text: {semantic_ability['primary_text_jp'][:100]}...")
    print()

print(f"Total incorrect replacements: {len(incorrect_replacements)}")
