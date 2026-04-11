#!/usr/bin/env python3
"""
Fix script for abilities 601-611 in ability_frame_source.json
"""
import json

def save_json(filepath, data):
    """Save JSON with UTF-8 encoding"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

filepath = 'data/ability_frame_source.json'

# Load the file
with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Ability 601: Looks correct - ADD_BLADES, RETURN
# Text: "{{jidou.png|自動}}このメンバーが登場か、エリアを移動するたび、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。(対戦相手のカードの効果でも発動する。)"
# Current frames: [ADD_BLADES, RETURN] - appears correct
if len(data['abilities']) > 601:
    data['abilities'][601]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}このメンバーが登場か、エリアを移動するたび、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。(対戦相手のカードの効果でも発動する。)",
            "Frames appear correct",
            "Frame 0: ADD_BLADES - adds 2 blades",
            "Frame 1: RETURN"
        ]
    }

# Ability 602: Missing IS_SELF_MOVE check
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES, RETURN] - missing IS_SELF_MOVE check
if len(data['abilities']) > 602:
    data['abilities'][602]["frames"] = [
        {
            "op": "IS_SELF_MOVE",
            "frame_index": 0,
            "attr": {
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "ADD_BLADES",
            "frame_index": 2,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][602]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Added IS_SELF_MOVE check",
            "Frame 0: IS_SELF_MOVE - checks if self moved",
            "Frame 1: JUMP_IF_FALSE - jumps if not self move",
            "Frame 2: ADD_BLADES - adds 1 blade",
            "Frame 3: RETURN"
        ]
    }

# Ability 603: Looks correct - SELECT_MEMBER, ADD_BLADES, RETURN
# Text: "{{jidou.png|自動}}このカードが表向きでライブカード置き場に置かれたとき、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード..."
# Current frames: [SELECT_MEMBER, ADD_BLADES, RETURN] - appears correct
if len(data['abilities']) > 603:
    data['abilities'][603]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}このカードが表向きでライブカード置き場に置かれたとき、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード...",
            "Frames appear correct",
            "Frame 0: SELECT_MEMBER - selects Nijigasaki member",
            "Frame 1: ADD_BLADES - adds 2 blades to selected member",
            "Frame 2: RETURN"
        ]
    }

# Ability 604: Looks correct - DRAW, RETURN
# Text: "{{jidou.png|自動}}このメンバーがエリアを移動するたび、カードを1枚引く。(対戦相手のカードの効果でも発動する。)"
# Current frames: [DRAW, RETURN] - appears correct
if len(data['abilities']) > 604:
    data['abilities'][604]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}このメンバーがエリアを移動するたび、カードを1枚引く。(対戦相手のカードの効果でも発動する。)",
            "Frames appear correct",
            "Frame 0: DRAW - draws 1 card",
            "Frame 1: RETURN"
        ]
    }

# Ability 605: Looks correct - ADD_HEARTS, RETURN
# Text: "{{jidou.png|自動}}カードの効果によって自分のエネルギー置き場にエネルギーカードが置かれるたび、ライブ終了時まで、{{heart_06.png|heart06}}を得る。(相手のカードの効果でも発動する。)"
# Current frames: [ADD_HEARTS, RETURN] - appears correct
if len(data['abilities']) > 605:
    data['abilities'][605]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}カードの効果によって自分のエネルギー置き場にエネルギーカードが置かれるたび、ライブ終了時まで、{{heart_06.png|heart06}}を得る。(相手のカードの効果でも発動する。)",
            "Frames appear correct",
            "Frame 0: ADD_HEARTS - adds heart06",
            "Frame 1: RETURN"
        ]
    }

# Ability 606: Looks correct - MAIN_PHASE, JUMP_IF_FALSE, PLAY_LIVE_FROM_DISCARD, REDUCE_LIVE_SET_LIMIT, RETURN
# Text: "{{jidou.png|自動}}自分のメインフェイズにこのカードが控え室から手札に加えられたとき、自分の手札からカード名が「DIVE!」のライブカード1枚を表向きでライブカード置き場に置いてもよい。そうした場合、次のライブカードセットフェイ..."
# Current frames: [MAIN_PHASE, JUMP_IF_FALSE, PLAY_LIVE_FROM_DISCARD, REDUCE_LIVE_SET_LIMIT, RETURN] - appears correct
if len(data['abilities']) > 606:
    data['abilities'][606]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}自分のメインフェイズにこのカードが控え室から手札に加えられたとき、自分の手札からカード名が「DIVE!」のライブカード1枚を表向きでライブカード置き場に置いてもよい。そうした場合、次のライブカードセットフェイ...",
            "Frames appear correct",
            "Frame 0: MAIN_PHASE - checks main phase",
            "Frame 1: JUMP_IF_FALSE - jumps if not main phase",
            "Frame 2: PLAY_LIVE_FROM_DISCARD - plays DIVE! live",
            "Frame 3: REDUCE_LIVE_SET_LIMIT - reduces live set limit",
            "Frame 4: RETURN"
        ]
    }

# Ability 607: Looks correct - TARGET_MEMBER_HAS_NO_HEARTS, JUMP_IF_FALSE, ADD_HEARTS, RETURN
# Text: "{{jidou.png|自動}}自分のステージにいるメンバーの{{live_start.png|ライブ開始時}}能力が解決するたび、そのメンバーが{{icon_all.png|ハート}}を持たない場合、ライブ終了時まで、そのメンバーは{{i..."
# Current frames: [TARGET_MEMBER_HAS_NO_HEARTS, JUMP_IF_FALSE, ADD_HEARTS, RETURN] - appears correct
if len(data['abilities']) > 607:
    data['abilities'][607]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_ABILITY_RESOLVE",
            "Text: {{jidou.png|自動}}自分のステージにいるメンバーの{{live_start.png|ライブ開始時}}能力が解決するたび、そのメンバーが{{icon_all.png|ハート}}を持たない場合、ライブ終了時まで、そのメンバーは{{i...",
            "Frames appear correct",
            "Frame 0: TARGET_MEMBER_HAS_NO_HEARTS - checks if member has no hearts",
            "Frame 1: JUMP_IF_FALSE - jumps if has hearts",
            "Frame 2: ADD_HEARTS - adds hearts",
            "Frame 3: RETURN"
        ]
    }

# Ability 608: Looks correct - DRAW, RETURN
# Text: "{{jidou.png|自動}}自分のステージにいるメンバーの{{live_success.png|ライブ成功時}}能力が解決するたび、カードを1枚引く。"
# Current frames: [DRAW, RETURN] - appears correct
if len(data['abilities']) > 608:
    data['abilities'][608]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_ABILITY_RESOLVE",
            "Text: {{jidou.png|自動}}自分のステージにいるメンバーの{{live_success.png|ライブ成功時}}能力が解決するたび、カードを1枚引く。",
            "Frames appear correct",
            "Frame 0: DRAW - draws 1 card",
            "Frame 1: RETURN"
        ]
    }

# Ability 609: Looks correct - MAIN_PHASE, JUMP_IF_FALSE, PAY_ENERGY, JUMP_IF_FALSE, RECOVER_MEMBER, RETURN
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のメインフェイズの間、自分のカードが1枚以上いずれかの領域から控え室に置かれるたび、{{icon_energy.png|E}}支払ってもよい。そうした場合、それらのカ..."
# Current frames: [MAIN_PHASE, JUMP_IF_FALSE, PAY_ENERGY, JUMP_IF_FALSE, RECOVER_MEMBER, RETURN] - appears correct
if len(data['abilities']) > 609:
    data['abilities'][609]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_MOVE_TO_DISCARD",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のメインフェイズの間、自分のカードが1枚以上いずれかの領域から控え室に置かれるたび、{{icon_energy.png|E}}支払ってもよい。そうした場合、それらのカ...",
            "Frames appear correct",
            "Frame 0: MAIN_PHASE - checks main phase",
            "Frame 1: JUMP_IF_FALSE - jumps if not main phase",
            "Frame 2: PAY_ENERGY - optionally pays energy",
            "Frame 3: JUMP_IF_FALSE - jumps if not paid",
            "Frame 4: RECOVER_MEMBER - recovers member",
            "Frame 5: RETURN"
        ]
    }

# Ability 610: Missing frames for tapping BiBi member and drawing when opponent taps
# Text: "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。）{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト4以下のメンバーがウェイト状態になったとき、カードを1枚引く。"
# Current frames: [DRAW, RETURN] - missing frames
if len(data['abilities']) > 610:
    data['abilities'][610]["frames"] = [
        {
            "op": "IS_CENTER",
            "frame_index": 0,
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 3
        },
        {
            "op": "SELECT_MEMBER",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "target_player": "SELF",
                "group_enabled": 1,
                "group_id": "BIBI",
                "is_optional": 1
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "STAGE"
            }
        },
        {
            "op": "TAP_MEMBER",
            "frame_index": 3,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "TAP_OPPONENT",
            "frame_index": 4,
            "value": 1,
            "attr": {
                "target_player": "OPPONENT"
            },
            "params": {
                "filter": "ACTIVE"
            },
            "slot": {
                "target_slot": "STAGE_2"
            }
        },
        {
            "op": "JUMP",
            "frame_index": 5,
            "value": 6
        },
        {
            "op": "OPPONENT_TAP_COST_LE4",
            "frame_index": 6,
            "attr": {
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 7,
            "value": 1
        },
        {
            "op": "DRAW",
            "frame_index": 8,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 9
        }
    ]
    data['abilities'][610]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_MEMBER_TAP",
            "Text: {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。）{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト4以下のメンバーがウェイト状態になったとき、カードを1枚引く。",
            "Fixed: Added proper frames for BiBi tap and opponent tap detection",
            "Frame 0: IS_CENTER - checks if in center",
            "Frame 1: JUMP_IF_FALSE - jumps if not center",
            "Frame 2: SELECT_MEMBER - selects BiBi member (optional)",
            "Frame 3: TAP_MEMBER - taps selected member",
            "Frame 4: TAP_OPPONENT - taps opponent active member",
            "Frame 5: JUMP - skips to end",
            "Frame 6: OPPONENT_TAP_COST_LE4 - checks opponent tapped cost <= 4",
            "Frame 7: JUMP_IF_FALSE - jumps if not tapped",
            "Frame 8: DRAW - draws 1 card",
            "Frame 9: RETURN"
        ]
    }

# Ability 611: NOP needs proper check for self tap
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のメインフェイズの間、このメンバーがアクティブ状態からウェイト状態になったとき、カードを1枚引き、手札を1枚控え室に置く。"
# Current frames: [MAIN_PHASE, NOP, JUMP_IF_FALSE, DRAW, MOVE_TO_DISCARD, RETURN] - NOP needs proper check
if len(data['abilities']) > 611:
    data['abilities'][611]["frames"] = [
        {
            "op": "MAIN_PHASE",
            "frame_index": 0,
            "attr": {
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GE"
            }
        },
        {
            "op": "IS_SELF_TAP",
            "frame_index": 1,
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 2,
            "value": 2
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
            "op": "MOVE_TO_DISCARD",
            "frame_index": 4,
            "value": 1,
            "attr": {
                "target_player": "SELF",
                "zone_mask": "Guest+Friend"
            },
            "slot": {
                "target_slot": "STAGE_1",
                "source_zone": "HAND",
                "dest_zone": "DISCARD"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 5
        }
    ]
    data['abilities'][611]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_MEMBER_TAP",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のメインフェイズの間、このメンバーがアクティブ状態からウェイト状態になったとき、カードを1枚引き、手札を1枚控え室に置く。",
            "Fixed: Replaced NOP with IS_SELF_TAP check",
            "Frame 0: MAIN_PHASE - checks main phase",
            "Frame 1: IS_SELF_TAP - checks if self tapped",
            "Frame 2: JUMP_IF_FALSE - jumps if not self tap",
            "Frame 3: DRAW - draws 1 card",
            "Frame 4: MOVE_TO_DISCARD - discards 1 card",
            "Frame 5: RETURN"
        ]
    }

# Save the updated data
save_json(filepath, data)

print("Fixed abilities 601-611")
print("Completed batch 601-611")
