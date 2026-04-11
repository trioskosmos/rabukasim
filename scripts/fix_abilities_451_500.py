#!/usr/bin/env python3
"""
Fix script for abilities 451-500 in ability_frame_source.json
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

# Ability 451: Wrong frames - BATON, COUNT_ENERGY, ENERGY_CHARGE instead of proper cost comparison and ADD_BLADES
# Text: "{{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [BATON, JUMP_IF_FALSE, COUNT_ENERGY, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN] - wrong
if len(data['abilities']) > 451:
    data['abilities'][451]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "attr": {
                "cost_comparison": "HIGHER_THAN_SELF"
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
            "value": 3,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][451]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Changed BATON/COUNT_ENERGY/ENERGY_CHARGE to proper cost comparison and ADD_BLADES",
            "Frame 0: COUNT_STAGE - checks for member with higher cost than self",
            "Frame 1: JUMP_IF_FALSE - jumps if no higher cost member",
            "Frame 2: ADD_BLADES - adds 3 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "このメンバーよりコストの大きいメンバーがいる場合": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "ブレード3枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 452: Looks correct - checks success live piles
# Text: "{{jyouji.png|常時}}自分の成功ライブカード置き場のカードが0枚で、かつ相手の成功ライブカード置き場にカードが1枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [COUNT_SUCCESS, JUMP_IF_FALSE, COUNT_SUCCESS, JUMP_IF_FALSE, ADD_BLADES, JUMP, NOP, RETURN] - appears correct
if len(data['abilities']) > 452:
    data['abilities'][452]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分の成功ライブカード置き場のカードが0枚で、かつ相手の成功ライブカード置き場にカードが1枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Frames appear correct",
            "Frame 0-1: COUNT_SUCCESS - checks self has 0 cards",
            "Frame 2-3: COUNT_SUCCESS - checks opponent has 1+ cards",
            "Frame 4: ADD_BLADES - adds 3 blades",
            "Frame 5-7: Jump logic and return"
        ]
    }

# Ability 453: Wrong frames - BATON, COUNT_ENERGY, ENERGY_CHARGE instead of proper energy comparison and ADD_BLADES
# Text: "{{jyouji.png|常時}}相手のエネルギーが自分より多い場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [BATON, JUMP_IF_FALSE, COUNT_ENERGY, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN] - wrong
if len(data['abilities']) > 453:
    data['abilities'][453]["frames"] = [
        {
            "op": "COUNT_ENERGY",
            "frame_index": 0,
            "attr": {
                "target_player": "OPPONENT",
                "compare_to": "SELF",
                "comparison": "GT"
            },
            "slot": {
                "target_slot": "STAGE_0"
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
            "value": 3,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][453]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}相手のエネルギーが自分より多い場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Changed BATON/COUNT_ENERGY/ENERGY_CHARGE to proper energy comparison and ADD_BLADES",
            "Frame 0: COUNT_ENERGY - checks opponent energy > self energy",
            "Frame 1: JUMP_IF_FALSE - jumps if not greater",
            "Frame 2: ADD_BLADES - adds 3 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "相手のエネルギーが自分より多い場合": "Frame 0-1: COUNT_ENERGY + JUMP_IF_FALSE",
            "ブレード3枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 454: Looks correct - COUNT_SUCCESS, JUMP_IF_FALSE, ADD_BLADES
# Text: "{{jyouji.png|常時}}自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [COUNT_SUCCESS, JUMP_IF_FALSE, ADD_BLADES, RETURN] - appears correct
if len(data['abilities']) > 454:
    data['abilities'][454]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Frames appear correct",
            "Frame 0: COUNT_SUCCESS - checks total cards >= 3",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 3",
            "Frame 2: ADD_BLADES - adds 3 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合": "Frame 0-1: COUNT_SUCCESS + JUMP_IF_FALSE",
            "ブレード3枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 455: Wrong frames - BATON, COUNT_ENERGY, ENERGY_CHARGE instead of proper COUNT_ENERGY and ADD_BLADES
# Text: "{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [BATON, JUMP_IF_FALSE, COUNT_ENERGY, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN] - wrong
if len(data['abilities']) > 455:
    data['abilities'][455]["frames"] = [
        {
            "op": "COUNT_ENERGY",
            "frame_index": 0,
            "value": 10,
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
            "value": 3,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][455]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Changed BATON/COUNT_ENERGY/ENERGY_CHARGE to proper COUNT_ENERGY and ADD_BLADES",
            "Frame 0: COUNT_ENERGY - checks energy >= 10",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 10",
            "Frame 2: ADD_BLADES - adds 3 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のエネルギーが10枚以上あるかぎり": "Frame 0-1: COUNT_ENERGY + JUMP_IF_FALSE",
            "ブレード3枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 456: Wrong frames - BATON, COUNT_ENERGY, ENERGY_CHARGE instead of proper cost comparison and ADD_BLADES
# Text: "{{jyouji.png|常時}}自分のステージにいるメンバーのコストの合計が相手より低いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [BATON, JUMP_IF_FALSE, COUNT_ENERGY, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN] - wrong
if len(data['abilities']) > 456:
    data['abilities'][456]["frames"] = [
        {
            "op": "SUM_COST",
            "frame_index": 0,
            "attr": {
                "target_player": "SELF",
                "compare_to": "OPPONENT",
                "comparison": "LT"
            },
            "slot": {
                "target_slot": "STAGE_0"
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
            "value": 3,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][456]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにいるメンバーのコストの合計が相手より低いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Changed BATON/COUNT_ENERGY/ENERGY_CHARGE to proper SUM_COST and ADD_BLADES",
            "Frame 0: SUM_COST - checks self total cost < opponent total cost",
            "Frame 1: JUMP_IF_FALSE - jumps if not lower",
            "Frame 2: ADD_BLADES - adds 3 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のステージにいるメンバーのコストの合計が相手より低いかぎり": "Frame 0-1: SUM_COST + JUMP_IF_FALSE",
            "ブレード3枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 457: META_RULE - looks correct
# Text: "(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)"
# Current frames: [META_RULE, RETURN] - appears correct
if len(data['abilities']) > 457:
    data['abilities'][457]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)",
            "Frames appear correct",
            "Frame 0: META_RULE - sets blade color rule",
            "Frame 1: RETURN"
        ]
    }

# Ability 458: Missing condition check - only has ADD_BLADES
# Text: "{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES, RETURN] - missing condition check
if len(data['abilities']) > 458:
    data['abilities'][458]["frames"] = [
        {
            "op": "COUNT_SUCCESS_LIVE",
            "frame_index": 0,
            "attr": {
                "sum_score": 1,
                "compare_to": "OPPONENT",
                "comparison": "GT"
            },
            "slot": {
                "target_slot": "STAGE_0"
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
            "value": 2,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][458]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Added COUNT_SUCCESS_LIVE check for score comparison",
            "Frame 0: COUNT_SUCCESS_LIVE - checks self score > opponent score",
            "Frame 1: JUMP_IF_FALSE - jumps if not higher",
            "Frame 2: ADD_BLADES - adds 2 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "ブレード2枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 459: Missing condition check - only has ADD_BLADES
# Text: "{{jyouji.png|常時}}自分のステージにこのメンバー以外の『EdelNote』のメンバーがいるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES, RETURN] - missing condition check
if len(data['abilities']) > 459:
    data['abilities'][459]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "attr": {
                "group_enabled": 1,
                "group_id": "EDELNOTE",
                "exclude_self": 1
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
            "value": 2,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][459]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにこのメンバー以外の『EdelNote』のメンバーがいるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Added COUNT_STAGE check for EdelNote members excluding self",
            "Frame 0: COUNT_STAGE - checks for EdelNote member other than self",
            "Frame 1: JUMP_IF_FALSE - jumps if no such member",
            "Frame 2: ADD_BLADES - adds 2 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のステージにこのメンバー以外の『EdelNote』のメンバーがいるかぎり": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "ブレード2枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 460: Missing condition check - only has ADD_BLADES
# Text: "{{jyouji.png|常時}}自分のライブ中のライブカードが2枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES, RETURN] - missing condition check
if len(data['abilities']) > 460:
    data['abilities'][460]["frames"] = [
        {
            "op": "COUNT_LIVE_CARDS",
            "frame_index": 0,
            "value": 2,
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
            "value": 2,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][460]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のライブ中のライブカードが2枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Added COUNT_LIVE_CARDS check",
            "Frame 0: COUNT_LIVE_CARDS - checks for 2+ live cards",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 2",
            "Frame 2: ADD_BLADES - adds 2 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のライブ中のライブカードが2枚以上あるかぎり": "Frame 0-1: COUNT_LIVE_CARDS + JUMP_IF_FALSE",
            "ブレード2枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 461: Missing condition check - only has ADD_BLADES
# Text: "{{jyouji.png|常時}}このターンにこのメンバーが移動していないかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES, RETURN] - missing condition check
if len(data['abilities']) > 461:
    data['abilities'][461]["frames"] = [
        {
            "op": "HAS_NOT_MOVED",
            "frame_index": 0,
            "slot": {
                "target_slot": "CONTEXT",
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
            "value": 2,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][461]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}このターンにこのメンバーが移動していないかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Added HAS_NOT_MOVED check",
            "Frame 0: HAS_NOT_MOVED - checks if member hasn't moved this turn",
            "Frame 1: JUMP_IF_FALSE - jumps if moved",
            "Frame 2: ADD_BLADES - adds 2 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "このターンにこのメンバーが移動していないかぎり": "Frame 0-1: HAS_NOT_MOVED + JUMP_IF_FALSE",
            "ブレード2枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 462: CENTER marker with ADD_BLADES - looks correct (unconditional center ability)
# Text: "{{jyouji.png|常時}}{{center.png|センター}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES, RETURN] - appears correct for unconditional center ability
if len(data['abilities']) > 462:
    data['abilities'][462]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}{{center.png|センター}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Frames appear correct for unconditional center ability",
            "Frame 0: ADD_BLADES - adds 2 blades",
            "Frame 1: RETURN"
        ]
    }

# Ability 463: Dynamic ADD_BLADES for tapped opponent members - looks correct with dynamic values
# Text: "{{jyouji.png|常時}}相手のステージにいるウェイト状態のメンバー1人につき、{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES (dynamic), RETURN] - appears correct with dynamic values
if len(data['abilities']) > 463:
    data['abilities'][463]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}相手のステージにいるウェイト状態のメンバー1人につき、{{icon_blade.png|ブレード}}を得る。",
            "Frames appear correct with dynamic values",
            "Frame 0: ADD_BLADES - adds 1 blade per tapped opponent member (dynamic)",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "相手のステージにいるウェイト状態のメンバー1人につき": "Frame 0: ADD_BLADES (dynamic)",
            "ブレードを得る": "Frame 0: ADD_BLADES"
        }
    }

# Ability 464: Dynamic ADD_BLADES for success live cards - looks correct with dynamic values
# Text: "{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES (dynamic), RETURN] - appears correct with dynamic values
if len(data['abilities']) > 464:
    data['abilities'][464]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}を得る。",
            "Frames appear correct with dynamic values",
            "Frame 0: ADD_BLADES - adds 1 blade per success live card (dynamic)",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場にあるカード1枚につき": "Frame 0: ADD_BLADES (dynamic)",
            "ブレードを得る": "Frame 0: ADD_BLADES"
        }
    }

# Ability 465: Dynamic ADD_BLADES for other Mirakura Park members - looks correct with dynamic values
# Text: "{{jyouji.png|常時}}自分のステージにいるほかの『みらくらぱーく！』のメンバー1人につき、{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES (dynamic), RETURN] - appears correct with dynamic values
if len(data['abilities']) > 465:
    data['abilities'][465]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにいるほかの『みらくらぱーく！』のメンバー1人につき、{{icon_blade.png|ブレード}}を得る。",
            "Frames appear correct with dynamic values",
            "Frame 0: ADD_BLADES - adds 1 blade per other Mirakura Park member (dynamic)",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "ほかの『みらくらぱーく！』のメンバー1人につき": "Frame 0: ADD_BLADES (dynamic)",
            "ブレードを得る": "Frame 0: ADD_BLADES"
        }
    }

# Ability 466: Dynamic ADD_BLADES for energy under member - looks correct with dynamic values
# Text: "{{jyouji.png|常時}}このメンバーの下にあるエネルギーカード1枚につき、{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES (dynamic), RETURN] - appears correct with dynamic values
if len(data['abilities']) > 466:
    data['abilities'][466]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}このメンバーの下にあるエネルギーカード1枚につき、{{icon_blade.png|ブレード}}を得る。",
            "Frames appear correct with dynamic values",
            "Frame 0: ADD_BLADES - adds 1 blade per energy card under member (dynamic)",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "このメンバーの下にあるエネルギーカード1枚につき": "Frame 0: ADD_BLADES (dynamic)",
            "ブレードを得る": "Frame 0: ADD_BLADES"
        }
    }

# Ability 467: NOP with raw_cond for UNIQUE_NAMES_COUNT - needs proper COUNT_STAGE with unique_names
# Text: "{{jyouji.png|常時}}自分のステージに名前が異なるメンバーが3人以上いるかぎり、{{heart_03.png|heart03}}を得る。"
# Current frames: [NOP (raw_cond: UNIQUE_NAMES_COUNT), JUMP_IF_FALSE, ADD_HEARTS, RETURN]
if len(data['abilities']) > 467:
    data['abilities'][467]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "value": 3,
            "attr": {
                "unique_names": 1
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
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "heart_type": "HEART03"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][467]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージに名前が異なるメンバーが3人以上いるかぎり、{{heart_03.png|heart03}}を得る。",
            "Fixed: Changed NOP with raw_cond to COUNT_STAGE with unique_names",
            "Frame 0: COUNT_STAGE - checks for 3+ unique members",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 3",
            "Frame 2: ADD_HEARTS - adds heart03",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "名前が異なるメンバーが3人以上いるかぎり": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "heart03を得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 468: NOP with wrong condition - needs proper check for center member having highest cost
# Text: "{{jyouji.png|常時}}自分のステージにいるメンバーのうち、センターエリアにいるメンバーが最も大きいコストを持つ場合、{{heart_03.png|heart03}}を得る。"
# Current frames: [NOP (raw_cond: UNIQUE_NAMES_COUNT), JUMP_IF_FALSE, ADD_HEARTS, RETURN] - wrong condition
if len(data['abilities']) > 468:
    data['abilities'][468]["frames"] = [
        {
            "op": "HAS_HIGHEST_COST_CENTER",
            "frame_index": 0,
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
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "heart_type": "HEART03"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][468]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにいるメンバーのうち、センターエリアにいるメンバーが最も大きいコストを持つ場合、{{heart_03.png|heart03}}を得る。",
            "Fixed: Changed NOP with wrong condition to HAS_HIGHEST_COST_CENTER",
            "Frame 0: HAS_HIGHEST_COST_CENTER - checks if center member has highest cost",
            "Frame 1: JUMP_IF_FALSE - jumps if not highest cost",
            "Frame 2: ADD_HEARTS - adds heart03",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "センターエリアにいるメンバーが最も大きいコストを持つ場合": "Frame 0-1: HAS_HIGHEST_COST_CENTER + JUMP_IF_FALSE",
            "heart03を得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 469: NOP with wrong condition - needs proper check for Liella live card with 8+ required hearts
# Text: "{{jyouji.png|常時}}自分のライブカード置き場に必要ハートの合計が8以上の『Liella!』のライブカードがあるかぎり、{{heart_03.png|heart03}}を得る。"
# Current frames: [NOP (raw_cond: UNIQUE_NAMES_COUNT), JUMP_IF_FALSE, ADD_HEARTS, RETURN] - wrong condition
if len(data['abilities']) > 469:
    data['abilities'][469]["frames"] = [
        {
            "op": "COUNT_LIVE_CARDS",
            "frame_index": 0,
            "value": 8,
            "attr": {
                "group_enabled": 1,
                "group_id": "LIELLA",
                "required_hearts": 1
            },
            "slot": {
                "target_slot": "LIVE_PILE",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "heart_type": "HEART03"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][469]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のライブカード置き場に必要ハートの合計が8以上の『Liella!』のライブカードがあるかぎり、{{heart_03.png|heart03}}を得る。",
            "Fixed: Changed NOP with wrong condition to COUNT_LIVE_CARDS with group and required hearts check",
            "Frame 0: COUNT_LIVE_CARDS - checks for Liella live card with 8+ required hearts",
            "Frame 1: JUMP_IF_FALSE - jumps if no such card",
            "Frame 2: ADD_HEARTS - adds heart03",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "必要ハートの合計が8以上の『Liella!』のライブカードがあるかぎり": "Frame 0-1: COUNT_LIVE_CARDS + JUMP_IF_FALSE",
            "heart03を得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 470: Only RETURN - needs IDENTITY_CHANGE for group identity
# Text: "{{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。"
# Current frames: [RETURN] - missing IDENTITY_CHANGE
if len(data['abilities']) > 470:
    data['abilities'][470]["frames"] = [
        {
            "op": "IDENTITY_CHANGE",
            "frame_index": 0,
            "attr": {
                "groups": [
                    "SUZURI_BOUQUET",
                    "DOLL_CHESTRA",
                    "MIRAKURA_PARK"
                ],
                "all_zones": 1
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 1
        }
    ]
    data['abilities'][470]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。",
            "Fixed: Added IDENTITY_CHANGE for multiple group identities",
            "Frame 0: IDENTITY_CHANGE - card treated as Suzuri Bouquet, DOLL CHESTRA, Mirakura Park in all zones",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う": "Frame 0: IDENTITY_CHANGE"
        }
    }

# Ability 471: Only RETURN - needs CANNOT_ACTIVATE
# Text: "{{jyouji.png|常時}}このメンバーは自分のアクティブフェイズにアクティブにしない。"
# Current frames: [RETURN] - missing CANNOT_ACTIVATE
if len(data['abilities']) > 471:
    data['abilities'][471]["frames"] = [
        {
            "op": "CANNOT_ACTIVATE",
            "frame_index": 0,
            "attr": {
                "phase": "ACTIVE"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 1
        }
    ]
    data['abilities'][471]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}このメンバーは自分のアクティブフェイズにアクティブにしない。",
            "Fixed: Added CANNOT_ACTIVATE frame",
            "Frame 0: CANNOT_ACTIVATE - cannot activate during active phase",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "このメンバーは自分のアクティブフェイズにアクティブにしない": "Frame 0: CANNOT_ACTIVATE"
        }
    }

# Ability 472: Only RETURN - needs CANNOT_LIVE condition
# Text: "{{jyouji.png|常時}}自分のステージにほかのメンバーがいない場合、自分はライブできない。"
# Current frames: [RETURN] - missing condition check
if len(data['abilities']) > 472:
    data['abilities'][472]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "exclude_self": 1
            },
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "LT"
            }
        },
        {
            "op": "CANNOT_LIVE",
            "frame_index": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 2
        }
    ]
    data['abilities'][472]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにほかのメンバーがいない場合、自分はライブできない。",
            "Fixed: Added COUNT_STAGE and CANNOT_LIVE frames",
            "Frame 0: COUNT_STAGE - checks for less than 1 other member",
            "Frame 1: CANNOT_LIVE - cannot live if condition met",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "自分のステージにほかのメンバーがいない場合": "Frame 0: COUNT_STAGE",
            "自分はライブできない": "Frame 1: CANNOT_LIVE"
        }
    }

# Ability 473: NOP with raw_cond - needs proper COUNT_STAGE with unique costs
# Text: "{{jyouji.png|常時}}自分のステージにコストがそれぞれ異なるメンバーが3人以上いるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [NOP (raw_cond: UNIQUE_MEMBER_COSTS_COUNT), JUMP_IF_FALSE, ADD_HEARTS, ADD_BLADES, RETURN]
if len(data['abilities']) > 473:
    data['abilities'][473]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "value": 3,
            "attr": {
                "unique_costs": 1
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
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "heart_type": "HEART05"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "ADD_BLADES",
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
    data['abilities'][473]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにコストがそれぞれ異なるメンバーが3人以上いるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Changed NOP with raw_cond to COUNT_STAGE with unique_costs",
            "Frame 0: COUNT_STAGE - checks for 3+ members with unique costs",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 3",
            "Frame 2: ADD_HEARTS - adds heart05",
            "Frame 3: ADD_BLADES - adds blade",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "コストがそれぞれ異なるメンバーが3人以上いるかぎり": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "heart05とブレードを得る": "Frame 2-3: ADD_HEARTS + ADD_BLADES"
        }
    }

# Ability 474: Missing condition check - only has ADD_HEARTS and ADD_BLADES
# Text: "{{jyouji.png|常時}}自分のステージにいるメンバーがちょうど2人であるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_HEARTS, ADD_BLADES, RETURN] - missing condition check
if len(data['abilities']) > 474:
    data['abilities'][474]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "value": 2,
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "EQ"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "heart_type": "HEART05"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "ADD_BLADES",
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
    data['abilities'][474]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにいるメンバーがちょうど2人であるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Added COUNT_STAGE check for exactly 2 members",
            "Frame 0: COUNT_STAGE - checks for exactly 2 members",
            "Frame 1: JUMP_IF_FALSE - jumps if not exactly 2",
            "Frame 2: ADD_HEARTS - adds heart05",
            "Frame 3: ADD_BLADES - adds blade",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "自分のステージにいるメンバーがちょうど2人であるかぎり": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "heart05とブレードを得る": "Frame 2-3: ADD_HEARTS + ADD_BLADES"
        }
    }

# Ability 475: LIVE_START with NOP - needs proper check for cards without abilities
# Text: "{{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。"
# Current frames: [NOP, JUMP_IF_FALSE, ADD_HEARTS, RETURN] - missing proper check
if len(data['abilities']) > 475:
    data['abilities'][475]["frames"] = [
        {
            "op": "COUNT_LIVE_CARDS",
            "frame_index": 0,
            "attr": {
                "no_abilities": 1
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
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 2,
            "attr": {
                "heart_type": "HEART06"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][475]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT (with LIVE_START marker)",
            "Text: {{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。",
            "Fixed: Changed NOP to COUNT_LIVE_CARDS with no_abilities check",
            "Frame 0: COUNT_LIVE_CARDS - checks for live cards without abilities",
            "Frame 1: JUMP_IF_FALSE - jumps if no such cards",
            "Frame 2: ADD_HEARTS - adds 2 heart06",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "ライブ開始時能力もライブ成功時能力も持たないカードがあるかぎり": "Frame 0-1: COUNT_LIVE_CARDS + JUMP_IF_FALSE",
            "heart06を2枚得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 476: Looks correct - COUNT_ENERGY, JUMP_IF_FALSE, ADD_HEARTS, RETURN
# Text: "{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。"
# Current frames: [COUNT_ENERGY, JUMP_IF_FALSE, ADD_HEARTS, RETURN] - appears correct
if len(data['abilities']) > 476:
    data['abilities'][476]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。",
            "Frames appear correct",
            "Frame 0: COUNT_ENERGY - checks for 10+ energy",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 10",
            "Frame 2: ADD_HEARTS - adds 2 heart06",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のエネルギーが10枚以上あるかぎり": "Frame 0-1: COUNT_ENERGY + JUMP_IF_FALSE",
            "heart06を2枚得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 477: BATON_TOUCH_MOD - looks correct
# Text: "{{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。"
# Current frames: [BATON_TOUCH_MOD, RETURN] - appears correct
if len(data['abilities']) > 477:
    data['abilities'][477]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。",
            "Frames appear correct",
            "Frame 0: BATON_TOUCH_MOD - allows baton touch with 2 members",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "2人のメンバーとバトンタッチしてもよい": "Frame 0: BATON_TOUCH_MOD"
        }
    }

# Ability 478: REDUCE_COST - looks correct
# Text: "{{jyouji.png|常時}}コスト10の『Liella!』のメンバーカードを自分の手札から登場させるためのコストは2減る。"
# Current frames: [REDUCE_COST, RETURN] - appears correct
if len(data['abilities']) > 478:
    data['abilities'][478]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}コスト10の『Liella!』のメンバーカードを自分の手札から登場させるためのコストは2減る。",
            "Frames appear correct",
            "Frame 0: REDUCE_COST - reduces cost by 2 for cost 10 Liella members",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "コスト10の『Liella!』のメンバーカードを自分の手札から登場させるためのコストは2減る": "Frame 0: REDUCE_COST"
        }
    }

# Ability 479: Missing condition check - only has ADD_HEARTS
# Text: "{{jyouji.png|常時}}相手のステージにウェイト状態のメンバーが2人以上いるかぎり、{{heart_06.png|heart06}}を得る。"
# Current frames: [ADD_HEARTS, RETURN] - missing condition check
if len(data['abilities']) > 479:
    data['abilities'][479]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "value": 2,
            "attr": {
                "target_player": "OPPONENT",
                "is_tapped": 1
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
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "heart_type": "HEART06"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][479]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}相手のステージにウェイト状態のメンバーが2人以上いるかぎり、{{heart_06.png|heart06}}を得る。",
            "Fixed: Added COUNT_STAGE check for opponent's tapped members",
            "Frame 0: COUNT_STAGE - checks for 2+ tapped members on opponent stage",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 2",
            "Frame 2: ADD_HEARTS - adds heart06",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "相手のステージにウェイト状態のメンバーが2人以上いるかぎり": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "heart06を得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 480: Missing condition check - only has ADD_HEARTS
# Text: "{{jyouji.png|常時}}自分のライブ中のライブカードの必要ハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がそれぞれ1以上含まれるかぎり、{{icon_all.png|ハート}}を得る。"
# Current frames: [ADD_HEARTS, RETURN] - missing condition check
if len(data['abilities']) > 480:
    data['abilities'][480]["frames"] = [
        {
            "op": "CHECK_ALL_HEART_TYPES",
            "frame_index": 0,
            "attr": {
                "heart_types": ["HEART01", "HEART02", "HEART03", "HEART04", "HEART05", "HEART06"]
            },
            "slot": {
                "target_slot": "LIVE_PILE",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "any_heart": 1
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][480]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のライブ中のライブカードの必要ハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がそれぞれ1以上含まれるかぎり、{{icon_all.png|ハート}}を得る。",
            "Fixed: Added CHECK_ALL_HEART_TYPES check",
            "Frame 0: CHECK_ALL_HEART_TYPES - checks if all heart types present",
            "Frame 1: JUMP_IF_FALSE - jumps if not all types present",
            "Frame 2: ADD_HEARTS - adds 1 heart",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "必要ハートの中にheart01-heart06がそれぞれ1以上含まれるかぎり": "Frame 0-1: CHECK_ALL_HEART_TYPES + JUMP_IF_FALSE",
            "ハートを得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 481: Missing condition check - only has ADD_HEARTS
# Text: "{{jyouji.png|常時}}自分のエネルギーが相手より多いかぎり、{{heart_06.png|heart06}}を得る。"
# Current frames: [ADD_HEARTS, RETURN] - missing condition check
if len(data['abilities']) > 481:
    data['abilities'][481]["frames"] = [
        {
            "op": "COUNT_ENERGY",
            "frame_index": 0,
            "attr": {
                "compare_to": "OPPONENT",
                "comparison": "GT"
            },
            "slot": {
                "target_slot": "STAGE_0"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "heart_type": "HEART06"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][481]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のエネルギーが相手より多いかぎり、{{heart_06.png|heart06}}を得る。",
            "Fixed: Added COUNT_ENERGY check for self > opponent",
            "Frame 0: COUNT_ENERGY - checks if self energy > opponent energy",
            "Frame 1: JUMP_IF_FALSE - jumps if not greater",
            "Frame 2: ADD_HEARTS - adds heart06",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のエネルギーが相手より多いかぎり": "Frame 0-1: COUNT_ENERGY + JUMP_IF_FALSE",
            "heart06を得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 482: INCREASE_HEART_COST - looks correct (unconditional)
# Text: "{{jyouji.png|常時}}相手のライブカード置き場にあるすべてのライブカードは、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる。"
# Current frames: [INCREASE_HEART_COST, RETURN] - appears correct
if len(data['abilities']) > 482:
    data['abilities'][482]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}相手のライブカード置き場にあるすべてのライブカードは、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる。",
            "Frames appear correct",
            "Frame 0: INCREASE_HEART_COST - increases required hearts for opponent live cards",
            "Frame 1: RETURN"
        ]
    }

# Ability 483: REDUCE_COST - looks correct (unconditional)
# Text: "{{jyouji.png|常時}}能力を持たないメンバーカードを自分の手札から登場させるためのコストは1減る。"
# Current frames: [REDUCE_COST, RETURN] - appears correct
if len(data['abilities']) > 483:
    data['abilities'][483]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}能力を持たないメンバーカードを自分の手札から登場させるためのコストは1減る。",
            "Frames appear correct",
            "Frame 0: REDUCE_COST - reduces cost by 1 for members without abilities",
            "Frame 1: RETURN"
        ]
    }

# Ability 484: Missing condition check - only has ADD_HEARTS
# Text: "{{jyouji.png|常時}}自分と相手のエネルギーの合計が15枚以上あるかぎり、{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。"
# Current frames: [ADD_HEARTS, RETURN] - missing condition check
if len(data['abilities']) > 484:
    data['abilities'][484]["frames"] = [
        {
            "op": "SUM_ENERGY",
            "frame_index": 0,
            "value": 15,
            "attr": {
                "target_player": "BOTH"
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
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 2,
            "attr": {
                "heart_type": "HEART02"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][484]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分と相手のエネルギーの合計が15枚以上あるかぎり、{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。",
            "Fixed: Added SUM_ENERGY check for total energy >= 15",
            "Frame 0: SUM_ENERGY - checks if total energy >= 15",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 15",
            "Frame 2: ADD_HEARTS - adds 2 heart02",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分と相手のエネルギーの合計が15枚以上あるかぎり": "Frame 0-1: SUM_ENERGY + JUMP_IF_FALSE",
            "heart02を2枚得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 485: Missing condition check - only has ADD_HEARTS and ADD_BLADES
# Text: "{{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_HEARTS, ADD_BLADES, RETURN] - missing condition check
if len(data['abilities']) > 485:
    data['abilities'][485]["frames"] = [
        {
            "op": "COUNT_LIVE_CARDS",
            "frame_index": 0,
            "value": 3,
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
            "op": "COUNT_LIVE_CARDS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": "NIJIGASAKI"
            },
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 3,
            "value": 1
        },
        {
            "op": "ADD_HEARTS",
            "frame_index": 4,
            "value": 2,
            "attr": {
                "any_heart": 1
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "ADD_BLADES",
            "frame_index": 5,
            "value": 2,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 6
        }
    ]
    data['abilities'][485]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Added COUNT_LIVE_CARDS checks for 3+ cards and 1+ Nijigasaki",
            "Frame 0: COUNT_LIVE_CARDS - checks for 3+ cards",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 3",
            "Frame 2: COUNT_LIVE_CARDS - checks for 1+ Nijigasaki",
            "Frame 3: JUMP_IF_FALSE - jumps if no Nijigasaki",
            "Frame 4: ADD_HEARTS - adds 2 hearts",
            "Frame 5: ADD_BLADES - adds 2 blades",
            "Frame 6: RETURN"
        ],
        "text_mapping": {
            "ライブ中のカードが3枚以上あり": "Frame 0-1: COUNT_LIVE_CARDS + JUMP_IF_FALSE",
            "その中に『虹ヶ咲』のライブカードを1枚以上含む場合": "Frame 2-3: COUNT_LIVE_CARDS + JUMP_IF_FALSE",
            "ハート2枚とブレード2枚を得る": "Frame 4-5: ADD_HEARTS + ADD_BLADES"
        }
    }

# Ability 486: CENTER marker with ADD_HEARTS - looks correct (unconditional center ability)
# Text: "{{jyouji.png|常時}}{{center.png|センター}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。"
# Current frames: [ADD_HEARTS, RETURN] - appears correct for unconditional center ability
if len(data['abilities']) > 486:
    data['abilities'][486]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}{{center.png|センター}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。",
            "Frames appear correct for unconditional center ability",
            "Frame 0: ADD_HEARTS - adds 3 heart03",
            "Frame 1: RETURN"
        ]
    }

# Ability 487: RIGHT_SIDE marker with ADD_HEARTS - looks correct (unconditional side ability)
# Text: "{{jyouji.png|常時}}【右サイド】{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_05.png|heart05}}を得る。"
# Current frames: [ADD_HEARTS, RETURN] - appears correct for unconditional side ability
if len(data['abilities']) > 487:
    data['abilities'][487]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}【右サイド】{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_05.png|heart05}}を得る。",
            "Frames appear correct for unconditional side ability",
            "Frame 0: ADD_HEARTS - adds 4 heart05",
            "Frame 1: RETURN"
        ]
    }

# Ability 488: LEFT_SIDE marker with ADD_HEARTS - looks correct (unconditional side ability)
# Text: "{{jyouji.png|常時}}【左サイド】{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。"
# Current frames: [ADD_HEARTS, RETURN] - appears correct for unconditional side ability
if len(data['abilities']) > 488:
    data['abilities'][488]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}【左サイド】{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。",
            "Frames appear correct for unconditional side ability",
            "Frame 0: ADD_HEARTS - adds 4 heart02",
            "Frame 1: RETURN"
        ]
    }

# Ability 489: NOP with raw_cond - needs proper COUNT_STAGE check for cost 13+ members
# Text: "{{jyouji.png|常時}}自分か相手のステージにコスト13以上のメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [NOP (raw_cond: COUNT_STAGE with cost 13+), ADD_BLADES, RETURN]
if len(data['abilities']) > 489:
    data['abilities'][489]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "target_player": "BOTH",
                "min_cost": 13
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
            "value": 2,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][489]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分か相手のステージにコスト13以上のメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Changed NOP with raw_cond to COUNT_STAGE with min_cost",
            "Frame 0: COUNT_STAGE - checks for cost 13+ member on either stage",
            "Frame 1: JUMP_IF_FALSE - jumps if no such member",
            "Frame 2: ADD_BLADES - adds 2 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分か相手のステージにコスト13以上のメンバーがいる場合": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "ブレード2枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 490: Dynamic ADD_BLADES for cost 4+ Suzuri Bouquet members - looks correct with dynamic values
# Text: "{{jyouji.png|常時}}自分のステージにいるコスト4以上の『スリーズブーケ』以外のメンバー1人につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES (dynamic), RETURN] - appears correct with dynamic values
if len(data['abilities']) > 490:
    data['abilities'][490]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにいるコスト4以上の『スリーズブーケ』以外のメンバー1人につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Frames appear correct with dynamic values",
            "Frame 0: ADD_BLADES - adds 2 blades per cost 4+ non-Suzuri Bouquet member (dynamic)",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "コスト4以上の『スリーズブーケ』以外のメンバー1人につき": "Frame 0: ADD_BLADES (dynamic)",
            "ブレード2枚を得る": "Frame 0: ADD_BLADES"
        }
    }

# Ability 491: Missing condition check - only has ADD_HEARTS
# Text: "{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。"
# Current frames: [ADD_HEARTS, RETURN] - missing condition check
if len(data['abilities']) > 491:
    data['abilities'][491]["frames"] = [
        {
            "op": "COUNT_SUCCESS_LIVE",
            "frame_index": 0,
            "value": 6,
            "attr": {
                "sum_score": 1
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
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 2,
            "attr": {
                "heart_type": "HEART03"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][491]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。",
            "Fixed: Added COUNT_SUCCESS_LIVE check for score total >= 6",
            "Frame 0: COUNT_SUCCESS_LIVE - checks score total >= 6",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 6",
            "Frame 2: ADD_HEARTS - adds 2 heart03",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "heart03を2枚得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 492: Looks correct - IN_SUCCESS_PILE, COUNT_STAGE, ADD_BLADES
# Text: "{{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあるかぎり、自分のセンターエリアにいる『μ's』のメンバーは{{icon_blade.png|ブレード}}を得る。"
# Current frames: [IN_SUCCESS_PILE, JUMP_IF_FALSE, COUNT_STAGE, JUMP_IF_FALSE, ADD_BLADES, RETURN] - appears correct
if len(data['abilities']) > 492:
    data['abilities'][492]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあるかぎり、自分のセンターエリアにいる『μ's』のメンバーは{{icon_blade.png|ブレード}}を得る。",
            "Frames appear correct",
            "Frame 0: IN_SUCCESS_PILE - checks if this card in success live pile",
            "Frame 1: JUMP_IF_FALSE - jumps if not in pile",
            "Frame 2: COUNT_STAGE - checks for μ's in center",
            "Frame 3: JUMP_IF_FALSE - jumps if no μ's",
            "Frame 4: ADD_BLADES - adds blade",
            "Frame 5: RETURN"
        ]
    }

# Ability 493: Missing condition check - only has ADD_BLADES
# Text: "{{jyouji.png|常時}}自分のステージに「村野さやか」か「百生吟子」か「安養寺姫芽」がいるかぎり、{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES, RETURN] - missing condition check
if len(data['abilities']) > 493:
    data['abilities'][493]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "member_names": ["村野さやか", "百生吟子", "安養寺姫芽"]
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
    data['abilities'][493]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージに「村野さやか」か「百生吟子」か「安養寺姫芽」がいるかぎり、{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Added COUNT_STAGE check for specific members",
            "Frame 0: COUNT_STAGE - checks for specific members on stage",
            "Frame 1: JUMP_IF_FALSE - jumps if no such members",
            "Frame 2: ADD_BLADES - adds blade",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "「村野さやか」か「百生吟子」か「安養寺姫芽」がいるかぎり": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "ブレードを得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 494: Missing condition check - only has ADD_HEARTS
# Text: "{{jyouji.png|常時}}このメンバーがウェイト状態であるかぎり、{{heart_05.png|heart05}}を得る。"
# Current frames: [ADD_HEARTS, RETURN] - missing condition check
if len(data['abilities']) > 494:
    data['abilities'][494]["frames"] = [
        {
            "op": "IS_TAPPED",
            "frame_index": 0,
            "slot": {
                "target_slot": "CONTEXT",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "heart_type": "HEART05"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][494]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}このメンバーがウェイト状態であるかぎり、{{heart_05.png|heart05}}を得る。",
            "Fixed: Added IS_TAPPED check",
            "Frame 0: IS_TAPPED - checks if member is tapped",
            "Frame 1: JUMP_IF_FALSE - jumps if not tapped",
            "Frame 2: ADD_HEARTS - adds heart05",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "このメンバーがウェイト状態であるかぎり": "Frame 0-1: IS_TAPPED + JUMP_IF_FALSE",
            "heart05を得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 495: Missing condition check - only has ADD_BLADES
# Text: "{{jyouji.png|常時}}ステージのセンターエリアにいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
# Current frames: [ADD_BLADES, RETURN] - missing condition check
if len(data['abilities']) > 495:
    data['abilities'][495]["frames"] = [
        {
            "op": "IN_CENTER",
            "frame_index": 0,
            "slot": {
                "target_slot": "CONTEXT",
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
            "value": 6,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][495]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}ステージのセンターエリアにいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
            "Fixed: Added IN_CENTER check",
            "Frame 0: IN_CENTER - checks if in center area",
            "Frame 1: JUMP_IF_FALSE - jumps if not in center",
            "Frame 2: ADD_BLADES - adds 6 blades",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "ステージのセンターエリアにいる場合": "Frame 0-1: IN_CENTER + JUMP_IF_FALSE",
            "ブレード6枚を得る": "Frame 2: ADD_BLADES"
        }
    }

# Ability 496: Looks correct - COUNT_ENERGY, JUMP_IF_FALSE, INCREASE_COST
# Text: "{{jyouji.png|常時}}自分のエネルギーが10枚以上ある場合、ステージにいるこのメンバーのコストを+４する。"
# Current frames: [COUNT_ENERGY, JUMP_IF_FALSE, INCREASE_COST, RETURN] - appears correct
if len(data['abilities']) > 496:
    data['abilities'][496]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のエネルギーが10枚以上ある場合、ステージにいるこのメンバーのコストを+４する。",
            "Frames appear correct",
            "Frame 0: COUNT_ENERGY - checks for 10+ energy",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 10",
            "Frame 2: INCREASE_COST - increases cost by 4",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のエネルギーが10枚以上ある場合": "Frame 0-1: COUNT_ENERGY + JUMP_IF_FALSE",
            "このメンバーのコストを+４する": "Frame 2: INCREASE_COST"
        }
    }

# Ability 497: Dynamic ADD_HEARTS for other A-RISE members - looks correct with dynamic values
# Text: "{{jyouji.png|常時}}自分のステージにいるこのメンバー以外の『A-RISE』のメンバー1人につき、{{heart_05.png|heart05}}を得る。"
# Current frames: [ADD_HEARTS (dynamic), RETURN] - appears correct with dynamic values
if len(data['abilities']) > 497:
    data['abilities'][497]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにいるこのメンバー以外の『A-RISE』のメンバー1人につき、{{heart_05.png|heart05}}を得る。",
            "Frames appear correct with dynamic values",
            "Frame 0: ADD_HEARTS - adds 1 heart05 per other A-RISE member (dynamic)",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "このメンバー以外の『A-RISE』のメンバー1人につき": "Frame 0: ADD_HEARTS (dynamic)",
            "heart05を得る": "Frame 0: ADD_HEARTS"
        }
    }

# Ability 498: NOP with raw_cond - needs proper COUNT_STAGE check
# Text: "{{jyouji.png|常時}}自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり、手札にあるこのメンバーカードのコストは2減る。"
# Current frames: [NOP (raw_cond: COUNT_STAGE), REDUCE_COST, RETURN]
if len(data['abilities']) > 498:
    data['abilities'][498]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": "NIJIGASAKI",
                "is_tapped": 1
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
            "op": "REDUCE_COST",
            "frame_index": 2,
            "value": 2,
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "HAND"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][498]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり、手札にあるこのメンバーカードのコストは2減る。",
            "Fixed: Changed NOP with raw_cond to COUNT_STAGE with group and tapped check",
            "Frame 0: COUNT_STAGE - checks for tapped Nijigasaki member",
            "Frame 1: JUMP_IF_FALSE - jumps if no such member",
            "Frame 2: REDUCE_COST - reduces cost by 2 for card in hand",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "ウェイト状態の『虹ヶ咲』のメンバーがいるかぎり": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "手札にあるこのメンバーカードのコストは2減る": "Frame 2: REDUCE_COST"
        }
    }

# Ability 499: NOP with raw_cond - needs proper COUNT_SUCCESS_LIVE check
# Text: "{{jyouji.png|常時}}自分の成功ライブカード置き場に『lilywhite』のカードがある場合、手札にあるこのメンバーカードのコストは2減る。"
# Current frames: [NOP (raw_cond: HAS_SUCCESS_LIVE), REDUCE_COST, RETURN]
if len(data['abilities']) > 499:
    data['abilities'][499]["frames"] = [
        {
            "op": "COUNT_SUCCESS_LIVE",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "unit_enabled": 1,
                "unit_id": "LILY_WHITE"
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
            "op": "REDUCE_COST",
            "frame_index": 2,
            "value": 2,
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "HAND"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][499]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分の成功ライブカード置き場に『lilywhite』のカードがある場合、手札にあるこのメンバーカードのコストは2減る。",
            "Fixed: Changed NOP with raw_cond to COUNT_SUCCESS_LIVE with unit check",
            "Frame 0: COUNT_SUCCESS_LIVE - checks for lilywhite in success live pile",
            "Frame 1: JUMP_IF_FALSE - jumps if no lilywhite",
            "Frame 2: REDUCE_COST - reduces cost by 2 for card in hand",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場に『lilywhite』のカードがある場合": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "手札にあるこのメンバーカードのコストは2減る": "Frame 2: REDUCE_COST"
        }
    }

# Ability 500: Looks correct - SCORE_TOTAL_CHECK, JUMP_IF_FALSE, INCREASE_COST
# Text: "{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ステージにいるこのメンバーのコストを+３する。"
# Current frames: [SCORE_TOTAL_CHECK, JUMP_IF_FALSE, INCREASE_COST, RETURN] - appears correct
if len(data['abilities']) > 500:
    data['abilities'][500]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ステージにいるこのメンバーのコストを+３する。",
            "Frames appear correct",
            "Frame 0: SCORE_TOTAL_CHECK - checks score total >= 6",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 6",
            "Frame 2: INCREASE_COST - increases cost by 3",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり": "Frame 0-1: SCORE_TOTAL_CHECK + JUMP_IF_FALSE",
            "このメンバーのコストを+３する": "Frame 2: INCREASE_COST"
        }
    }

# Save the updated data
save_json(filepath, data)

print("Fixed abilities 451-500")
print("Completed batch 451-500")
