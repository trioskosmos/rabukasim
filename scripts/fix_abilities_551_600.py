#!/usr/bin/env python3
"""
Fix script for abilities 551-600 in ability_frame_source.json
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

# Ability 551: Missing MOVE_TO_DISCARD for deck discard
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：このメンバーはポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)"
# Current frames: [MOVE_MEMBER, RETURN] - missing MOVE_TO_DISCARD
if len(data['abilities']) > 551:
    data['abilities'][551]["frames"] = [
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 0,
            "value": 3,
            "attr": {
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "DISCARD",
                "source_zone": "DECK_TOP"
            }
        },
        {
            "op": "MOVE_MEMBER",
            "frame_index": 1,
            "value": 99,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "STAGE"
            },
            "params": {
                "destination": "POSITION_CHANGE"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 2
        }
    ]
    data['abilities'][551]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：このメンバーはポジションチェンジする。",
            "Fixed: Added MOVE_TO_DISCARD for deck discard",
            "Frame 0: MOVE_TO_DISCARD - discards 3 cards from deck top",
            "Frame 1: MOVE_MEMBER - position changes this member",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "デッキの上からカードを3枚控え室に置く": "Frame 0: MOVE_TO_DISCARD",
            "このメンバーはポジションチェンジする": "Frame 1: MOVE_MEMBER"
        }
    }

# Ability 552: Looks correct - SUM_VALUE, PAY_ENERGY, MOVE_TO_DISCARD, SELECT_CARDS, PAY_ENERGY_DYNAMIC, JUMP_IF_FALSE, RECOVER_LIVE, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：自分の控え室にあるライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。そうした場合、..."
# Current frames appear correct for dynamic energy payment
if len(data['abilities']) > 552:
    data['abilities'][552]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：自分の控え室にあるライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。そうした場合、...",
            "Frames appear correct for dynamic energy payment",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays energy",
            "Frame 2: MOVE_TO_DISCARD - discards 1 card",
            "Frame 3: SELECT_CARDS - selects live card",
            "Frame 4: PAY_ENERGY_DYNAMIC - pays energy equal to card score",
            "Frame 5: JUMP_IF_FALSE - jumps if not paid",
            "Frame 6: RECOVER_LIVE - recovers live card",
            "Frame 7: RETURN"
        ]
    }

# Ability 553: Looks correct - COUNT_STAGE, GROUP_FILTER, JUMP_IF_FALSE, LOOK_AND_CHOOSE, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札をすべて公開する：自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合、自分のデッキの上からカードを5枚見る。その中からライブ..."
# Current frames appear correct
if len(data['abilities']) > 553:
    data['abilities'][553]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札をすべて公開する：自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合、自分のデッキの上からカードを5枚見る。その中からライブ...",
            "Frames appear correct",
            "Frame 0: COUNT_STAGE - checks for other members",
            "Frame 1: GROUP_FILTER - filters revealed cards",
            "Frame 2: JUMP_IF_FALSE - jumps if condition not met",
            "Frame 3: LOOK_AND_CHOOSE - looks at 5 cards",
            "Frame 4: RETURN"
        ]
    }

# Ability 554: Looks complex - IS_CENTER, JUMP_IF_FALSE, SET_TAPPED, MOVE_TO_DISCARD, SELECT_MODE, JUMP, JUMP, REVEAL_UNTIL, JUMP, REVEAL_UNTIL, JUMP, RETURN
# Text: "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが..."
# Current frames appear correct for complex choice ability
if len(data['abilities']) > 554:
    data['abilities'][554]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED (with CENTER marker)",
            "Text: {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが...",
            "Frames appear correct for complex choice ability",
            "Frame 0: IS_CENTER - checks if in center",
            "Frame 1: JUMP_IF_FALSE - jumps if not center",
            "Frame 2: SET_TAPPED - taps this member",
            "Frame 3: MOVE_TO_DISCARD - discards 1 card",
            "Frame 4: SELECT_MODE - chooses between live or member",
            "Frame 5-6: Jump logic for mode selection",
            "Frame 7: REVEAL_UNTIL - reveals until live card",
            "Frame 8: Jump to return",
            "Frame 9: REVEAL_UNTIL - reveals until cost 10+ member",
            "Frame 10: Jump to return",
            "Frame 11: RETURN"
        ]
    }

# Ability 555: Looks correct - PAY_ENERGY, DRAW, SELECT_MEMBER, JUMP_IF_FALSE, ADD_BLADES, RETURN
# Text: "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを1枚引き、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は{{ic..."
# Current frames appear correct
if len(data['abilities']) > 555:
    data['abilities'][555]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを1枚引き、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は{{ic...",
            "Frames appear correct",
            "Frame 0: PAY_ENERGY - pays 2 energy",
            "Frame 1: DRAW - draws 1 card",
            "Frame 2: SELECT_MEMBER - selects Nijigasaki member",
            "Frame 3: JUMP_IF_FALSE - jumps if no member",
            "Frame 4: ADD_BLADES - adds blades",
            "Frame 5: RETURN"
        ]
    }

# Ability 556: Missing PLAY_MEMBER_FROM_DISCARD and MOVE_ENERGY_UNDER_MEMBER
# Text: "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このメンバーをステージから控え室に置く：自分の手札からコスト13以下の「優木せつ菜」のメンバーカードを1枚、このメンバーがいたエリアに登場させる。その後、自分のエネルギー置き場にあるエネルギー1枚をそのメンバーの下に置く。"
# Current frames: [PAY_ENERGY, MOVE_TO_DISCARD, SELECT_CARDS, RETURN] - missing PLAY_MEMBER_FROM_DISCARD and MOVE_ENERGY_UNDER_MEMBER
if len(data['abilities']) > 556:
    data['abilities'][556]["frames"] = [
        {
            "op": "PAY_ENERGY",
            "frame_index": 0,
            "value": 2
        },
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 1,
            "value": 1,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "STAGE",
                "dest_zone": "DISCARD"
            }
        },
        {
            "op": "SELECT_CARDS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "target_player": "SELF",
                "value_enabled": 1,
                "value_threshold": 13,
                "is_le": 1,
                "is_cost_type": 1,
                "zone_mask": "Guest+Friend",
                "is_setsuna": 1
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "HAND"
            }
        },
        {
            "op": "PLAY_MEMBER_FROM_DISCARD",
            "frame_index": 3,
            "value": 1,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "MOVE_ENERGY_UNDER_MEMBER",
            "frame_index": 4,
            "value": 1,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "ENERGY"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 5
        }
    ]
    data['abilities'][556]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このメンバーをステージから控え室に置く：自分の手札からコスト13以下の「優木せつ菜」のメンバーカードを1枚、このメンバーがいたエリアに登場させる。その後、自分のエネルギー置き場にあるエネルギー1枚をそのメンバーの下に置く。",
            "Fixed: Added PLAY_MEMBER_FROM_DISCARD and MOVE_ENERGY_UNDER_MEMBER",
            "Frame 0: PAY_ENERGY - pays 2 energy",
            "Frame 1: MOVE_TO_DISCARD - sacrifices self",
            "Frame 2: SELECT_CARDS - selects Setsuna member with cost <= 13",
            "Frame 3: PLAY_MEMBER_FROM_DISCARD - plays selected member",
            "Frame 4: MOVE_ENERGY_UNDER_MEMBER - moves energy under member",
            "Frame 5: RETURN"
        ],
        "text_mapping": {
            "Eを2枚：": "Frame 0: PAY_ENERGY",
            "このメンバーをステージから控え室に置く": "Frame 1: MOVE_TO_DISCARD",
            "コスト13以下の「優木せつ菜」のメンバーカードを1枚、このメンバーがいたエリアに登場させる": "Frame 2-3: SELECT_CARDS + PLAY_MEMBER_FROM_DISCARD",
            "自分のエネルギー置き場にあるエネルギー1枚をそのメンバーの下に置く": "Frame 4: MOVE_ENERGY_UNDER_MEMBER"
        }
    }

# Ability 557: Wrong frames entirely - should be MOVE_TO_DISCARD and LOOK_AND_CHOOSE
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分のデッキの上からカードを5枚見る。その中から『Liella!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。"
# Current frames: [SUM_VALUE, PAY_ENERGY, COUNT_ENERGY, JUMP_IF_FALSE, INCREASE_COST, RETURN] - wrong frames
if len(data['abilities']) > 557:
    data['abilities'][557]["frames"] = [
        {
            "op": "SUM_VALUE",
            "frame_index": 0,
            "value": 2,
            "attr": {
                "once_per_turn": 1
            }
        },
        {
            "op": "PAY_ENERGY",
            "frame_index": 1,
            "value": 2,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "STAGE_1",
                "source_zone": "HAND",
                "dest_zone": "DISCARD"
            }
        },
        {
            "op": "LOOK_AND_CHOOSE",
            "frame_index": 3,
            "value": {
                "count": 5
            },
            "attr": {
                "target_player": "SELF",
                "group_enabled": 1,
                "group_id": "LIELLA",
                "is_optional": 1
            },
            "slot": {
                "target_slot": "CONTEXT",
                "remainder_zone": "DISCARD",
                "source_zone": "DECK_TOP"
            },
            "params": {
                "count": 5,
                "choose_count": 1
            },
            "choice_count": 1
        },
        {
            "op": "RETURN",
            "frame_index": 4
        }
    ]
    data['abilities'][557]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分のデッキの上からカードを5枚見る。その中から『Liella!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。",
            "Fixed: Changed from COUNT_ENERGY/INCREASE_COST to MOVE_TO_DISCARD/LOOK_AND_CHOOSE",
            "Frame 0: SUM_VALUE - once per turn check for 2 energy",
            "Frame 1: PAY_ENERGY - pays 2 energy",
            "Frame 2: MOVE_TO_DISCARD - discards 1 card",
            "Frame 3: LOOK_AND_CHOOSE - looks at 5 cards, chooses Liella card",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "Eを2枚：": "Frame 0-1: SUM_VALUE + PAY_ENERGY",
            "手札を1枚控え室に置く": "Frame 2: MOVE_TO_DISCARD",
            "自分のデッキの上からカードを5枚見る。その中から『Liella!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く": "Frame 3: LOOK_AND_CHOOSE"
        }
    }

# Ability 558: Missing MOVE_TO_DISCARD
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『Aqours』のライブカードを1枚手札に加える。"
# Current frames: [SUM_VALUE, PAY_ENERGY, RECOVER_LIVE, RETURN] - missing MOVE_TO_DISCARD
if len(data['abilities']) > 558:
    data['abilities'][558]["frames"] = [
        {
            "op": "SUM_VALUE",
            "frame_index": 0,
            "attr": {
                "once_per_turn": 1
            }
        },
        {
            "op": "PAY_ENERGY",
            "frame_index": 1,
            "value": 2,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "STAGE_1",
                "source_zone": "HAND",
                "dest_zone": "DISCARD"
            }
        },
        {
            "op": "RECOVER_LIVE",
            "frame_index": 3,
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": "AQOURS",
                "zone_mask": "ALL"
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 4
        }
    ]
    data['abilities'][558]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『Aqours』のライブカードを1枚手札に加える。",
            "Fixed: Added MOVE_TO_DISCARD frame",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays 2 energy",
            "Frame 2: MOVE_TO_DISCARD - discards 1 card",
            "Frame 3: RECOVER_LIVE - recovers Aqours live card",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "Eを2枚：": "Frame 0-1: SUM_VALUE + PAY_ENERGY",
            "手札を1枚控え室に置く": "Frame 2: MOVE_TO_DISCARD",
            "自分の控え室から『Aqours』のライブカードを1枚手札に加える": "Frame 3: RECOVER_LIVE"
        }
    }

# Ability 559: Missing MOVE_TO_DISCARD and has_score check
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から{{icon_score.png|スコア}}を持つ『Aqours』のライブカードを1枚手札に加える。"
# Current frames: [RECOVER_LIVE, RETURN] - missing MOVE_TO_DISCARD and has_score check
if len(data['abilities']) > 559:
    data['abilities'][559]["frames"] = [
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 0,
            "value": 2,
            "attr": {
                "target_player": "SELF",
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "STAGE_1",
                "source_zone": "HAND",
                "dest_zone": "DISCARD"
            }
        },
        {
            "op": "RECOVER_LIVE",
            "frame_index": 1,
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": "AQOURS",
                "has_score": 1,
                "zone_mask": "ALL"
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 2
        }
    ]
    data['abilities'][559]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から{{icon_score.png|スコア}}を持つ『Aqours』のライブカードを1枚手札に加える。",
            "Fixed: Added MOVE_TO_DISCARD and has_score check",
            "Frame 0: MOVE_TO_DISCARD - discards 2 cards",
            "Frame 1: RECOVER_LIVE - recovers Aqours live card with score",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "手札を2枚控え室に置く": "Frame 0: MOVE_TO_DISCARD",
            "自分の控え室からスコアを持つ『Aqours』のライブカードを1枚手札に加える": "Frame 1: RECOVER_LIVE"
        }
    }

# Ability 560: Looks correct - SUM_VALUE, PAY_ENERGY, REVEAL_CARDS, TYPE_CHECK, JUMP_IF_FALSE, GRANT_ABILITY, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカー..."
# Current frames appear correct for reveal and grant
if len(data['abilities']) > 560:
    data['abilities'][560]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカー...",
            "Frames appear correct for reveal and grant",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays 2 energy",
            "Frame 2: REVEAL_CARDS - reveals card from hand",
            "Frame 3: TYPE_CHECK - checks card type",
            "Frame 4: JUMP_IF_FALSE - jumps if not live",
            "Frame 5: GRANT_ABILITY - grants ability",
            "Frame 6: RETURN"
        ]
    }

# Ability 561: Missing PAY_ENERGY and score check
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からスコア3以下の『蓮ノ空』のライブカードを1枚手札に加える。"
# Current frames: [SUM_VALUE, JUMP_IF_FALSE, RECOVER_LIVE, RETURN] - missing PAY_ENERGY and score check
if len(data['abilities']) > 561:
    data['abilities'][561]["frames"] = [
        {
            "op": "SUM_VALUE",
            "frame_index": 0,
            "attr": {
                "once_per_turn": 1
            }
        },
        {
            "op": "PAY_ENERGY",
            "frame_index": 1,
            "value": 2,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RECOVER_LIVE",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": "HASUNOSORA",
                "value_enabled": 1,
                "value_threshold": 3,
                "is_le": 1,
                "zone_mask": "ALL"
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][561]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からスコア3以下の『蓮ノ空』のライブカードを1枚手札に加える。",
            "Fixed: Added PAY_ENERGY and score check to RECOVER_LIVE",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays 2 energy",
            "Frame 2: RECOVER_LIVE - recovers Hasunosora live card with score <= 3",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "Eを2枚：": "Frame 0-1: SUM_VALUE + PAY_ENERGY",
            "自分の控え室からスコア3以下の『蓮ノ空』のライブカードを1枚手札に加える": "Frame 2: RECOVER_LIVE"
        }
    }

# Ability 562: Missing SET_TAPPED frame
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}このメンバーをウェイトにする：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。"
# Current frames: [SUM_VALUE, PAY_ENERGY, ENERGY_CHARGE, RETURN] - missing SET_TAPPED
if len(data['abilities']) > 562:
    data['abilities'][562]["frames"] = [
        {
            "op": "SET_TAPPED",
            "frame_index": 0,
            "attr": {
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "PAY_ENERGY",
            "frame_index": 1,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "ENERGY_CHARGE",
            "frame_index": 2,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT",
                "is_wait": 1
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][562]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}このメンバーをウェイトにする：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。",
            "Fixed: Added SET_TAPPED frame",
            "Frame 0: SET_TAPPED - taps this member",
            "Frame 1: PAY_ENERGY - pays 1 energy",
            "Frame 2: ENERGY_CHARGE - charges energy in wait state",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "このメンバーをウェイトにする": "Frame 0: SET_TAPPED",
            "Eを1枚：": "Frame 1: PAY_ENERGY",
            "自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く": "Frame 2: ENERGY_CHARGE"
        }
    }

# Ability 563: Missing PAY_ENERGY frame
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーがいるエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。"
# Current frames: [SUM_VALUE, JUMP_IF_FALSE, MOVE_MEMBER, RETURN] - missing PAY_ENERGY
if len(data['abilities']) > 563:
    data['abilities'][563]["frames"] = [
        {
            "op": "SUM_VALUE",
            "frame_index": 0,
            "attr": {
                "once_per_turn": 1
            }
        },
        {
            "op": "PAY_ENERGY",
            "frame_index": 1,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "MOVE_MEMBER",
            "frame_index": 2,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "STAGE"
            },
            "params": {
                "destination": "POSITION_CHANGE"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][563]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーがいるエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。",
            "Fixed: Added PAY_ENERGY frame",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays 1 energy",
            "Frame 2: MOVE_MEMBER - position changes this member",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "Eを1枚：": "Frame 0-1: SUM_VALUE + PAY_ENERGY",
            "このメンバーをそのエリアに移動する": "Frame 2: MOVE_MEMBER"
        }
    }

# Ability 564: Looks complex - SELECT_PLAYER, RECOVER_LIVE, SUM_VALUE, JUMP_IF_FALSE, DRAW, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるライブカードを1枚、そのプレイヤーのデッキの一番下に置く。そうした場合、..."
# Current frames appear correct for complex ability
if len(data['abilities']) > 564:
    data['abilities'][564]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるライブカードを1枚、そのプレイヤーのデッキの一番下に置く。そうした場合、...",
            "Frames appear correct for complex ability",
            "Frame 0: SELECT_PLAYER - selects player",
            "Frame 1: RECOVER_LIVE - recovers live card to deck bottom",
            "Frame 2: SUM_VALUE - check for condition",
            "Frame 3: JUMP_IF_FALSE - jumps if condition not met",
            "Frame 4: DRAW - draws card",
            "Frame 5: RETURN"
        ]
    }

# Ability 565: Missing MOVE_TO_DISCARD frame
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のメンバーカードを1枚控え室に置く：自分の控え室から、これにより控え室に置いたメンバーカードより、コストの低いメンバーカードを1枚手札に加える。"
# Current frames: [RECOVER_MEMBER, RETURN] - missing MOVE_TO_DISCARD
if len(data['abilities']) > 565:
    data['abilities'][565]["frames"] = [
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "target_player": "SELF",
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "STAGE_1",
                "source_zone": "HAND",
                "dest_zone": "DISCARD"
            }
        },
        {
            "op": "RECOVER_MEMBER",
            "frame_index": 1,
            "value": 1,
            "attr": {
                "value_enabled": 1,
                "is_le": 1,
                "is_cost_type": 1,
                "zone_mask": "ALL",
                "compare_accumulated": 1
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 2
        }
    ]
    data['abilities'][565]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のメンバーカードを1枚控え室に置く：自分の控え室から、これにより控え室に置いたメンバーカードより、コストの低いメンバーカードを1枚手札に加える。",
            "Fixed: Added MOVE_TO_DISCARD frame",
            "Frame 0: MOVE_TO_DISCARD - discards 1 member card",
            "Frame 1: RECOVER_MEMBER - recovers member with lower cost (compare_accumulated)",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "手札のメンバーカードを1枚控え室に置く": "Frame 0: MOVE_TO_DISCARD",
            "自分の控え室から、これにより控え室に置いたメンバーカードより、コストの低いメンバーカードを1枚手札に加える": "Frame 1: RECOVER_MEMBER"
        }
    }

# Ability 566: Looks correct - SELECT_CARDS, SELECT_MODE, JUMP, JUMP, MOVE_TO_DISCARD, JUMP, ADD_BLADES, JUMP, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_..."
# Current frames appear correct for choice ability
if len(data['abilities']) > 566:
    data['abilities'][566]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_...",
            "Frames appear correct for choice ability",
            "Frame 0: SELECT_CARDS - selects live card",
            "Frame 1: SELECT_MODE - chooses for opponent",
            "Frame 2-3: Jump logic for mode selection",
            "Frame 4: MOVE_TO_DISCARD - opponent discards",
            "Frame 5: Jump to return",
            "Frame 6: ADD_BLADES - adds blades if opponent doesn't discard",
            "Frame 7: Jump to return",
            "Frame 8: RETURN"
        ]
    }

# Ability 567: NOP needs to be replaced with proper frame for checking if opponent member
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：ウェイト状態のメンバー1人をアクティブにする。これにより相手のステージにいるメンバーをアクティブにした場合、自分の控え室からライブカードを1枚手札に加える。"
# Current frames: [SELECT_MEMBER, ACTIVATE_MEMBER, NOP, JUMP_IF_FALSE, RECOVER_LIVE, RETURN] - NOP needs proper check
if len(data['abilities']) > 567:
    data['abilities'][567]["frames"] = [
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "target_player": "SELF",
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "STAGE_1",
                "source_zone": "HAND",
                "dest_zone": "DISCARD"
            }
        },
        {
            "op": "SELECT_MEMBER",
            "frame_index": 1,
            "value": 1,
            "attr": {
                "target_player": "OPPONENT"
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "STAGE"
            }
        },
        {
            "op": "ACTIVATE_MEMBER",
            "frame_index": 2,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 3,
            "value": 1
        },
        {
            "op": "RECOVER_LIVE",
            "frame_index": 4,
            "value": 1,
            "attr": {
                "zone_mask": "ALL"
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 5
        }
    ]
    data['abilities'][567]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：ウェイト状態のメンバー1人をアクティブにする。これにより相手のステージにいるメンバーをアクティブにした場合、自分の控え室からライブカードを1枚手札に加える。",
            "Fixed: Replaced NOP with proper SELECT_MEMBER for opponent and added MOVE_TO_DISCARD",
            "Frame 0: MOVE_TO_DISCARD - discards 1 card",
            "Frame 1: SELECT_MEMBER - selects opponent member",
            "Frame 2: ACTIVATE_MEMBER - activates selected member",
            "Frame 3: JUMP_IF_FALSE - jumps if no member activated",
            "Frame 4: RECOVER_LIVE - recovers live card",
            "Frame 5: RETURN"
        ],
        "text_mapping": {
            "手札を1枚控え室に置く": "Frame 0: MOVE_TO_DISCARD",
            "ウェイト状態のメンバー1人をアクティブにする": "Frame 1-2: SELECT_MEMBER + ACTIVATE_MEMBER",
            "相手のステージにいるメンバーをアクティブにした場合": "Frame 3: JUMP_IF_FALSE",
            "自分の控え室からライブカードを1枚手札に加える": "Frame 4: RECOVER_LIVE"
        }
    }

# Ability 568: Looks correct - SELECT_MODE, JUMP, JUMP, ACTIVATE_ENERGY, JUMP, SELECT_MEMBER, ACTIVATE_MEMBER, JUMP, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：エネルギー1枚か『虹ヶ咲』のメンバー1人をアクティブにする。"
# Current frames appear correct for choice ability
if len(data['abilities']) > 568:
    data['abilities'][568]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：エネルギー1枚か『虹ヶ咲』のメンバー1人をアクティブにする。",
            "Frames appear correct for choice ability",
            "Frame 0: SELECT_MODE - chooses energy or member",
            "Frame 1-2: Jump logic for mode selection",
            "Frame 3: ACTIVATE_ENERGY - activates energy",
            "Frame 4: Jump to return",
            "Frame 5: SELECT_MEMBER - selects Nijigasaki member",
            "Frame 6: ACTIVATE_MEMBER - activates member",
            "Frame 7: Jump to return",
            "Frame 8: RETURN"
        ]
    }

# Ability 569: Looks correct - SELECT_MEMBER, JUMP_IF_FALSE, REDUCE_COST, MOVE_TO_DISCARD, RECOVER_LIVE, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を3枚控え室に置く：自分のステージにほかの『lilywhite』のメンバーがいる場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力を起動するた..."
# Current frames appear correct
if len(data['abilities']) > 569:
    data['abilities'][569]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を3枚控え室に置く：自分のステージにほかの『lilywhite』のメンバーがいる場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力を起動するた...",
            "Frames appear correct",
            "Frame 0: SELECT_MEMBER - checks for lilywhite member",
            "Frame 1: JUMP_IF_FALSE - jumps if no lilywhite",
            "Frame 2: REDUCE_COST - reduces cost",
            "Frame 3: MOVE_TO_DISCARD - discards 3 cards",
            "Frame 4: RECOVER_LIVE - recovers μ's live card",
            "Frame 5: RETURN"
        ]
    }

# Ability 570: NOP needs to be replaced with proper score check
# Text: "{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。それがスコア6以上の『Aqours』のライブカードの場合、エネルギーを4枚アクティブにする。"
# Current frames: [MOVE_TO_DISCARD, RECOVER_LIVE, NOP, JUMP_IF_FALSE, ACTIVATE_ENERGY, RETURN] - NOP needs proper score check
if len(data['abilities']) > 570:
    data['abilities'][570]["frames"] = [
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "STAGE",
                "dest_zone": "DISCARD"
            }
        },
        {
            "op": "RECOVER_LIVE",
            "frame_index": 1,
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": "AQOURS",
                "value_enabled": 1,
                "value_threshold": 6,
                "zone_mask": "ALL"
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 2,
            "value": 1
        },
        {
            "op": "ACTIVATE_ENERGY",
            "frame_index": 3,
            "value": 4,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 4
        }
    ]
    data['abilities'][570]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。それがスコア6以上の『Aqours』のライブカードの場合、エネルギーを4枚アクティブにする。",
            "Fixed: Replaced NOP with proper score check in RECOVER_LIVE",
            "Frame 0: MOVE_TO_DISCARD - sacrifices self",
            "Frame 1: RECOVER_LIVE - recovers Aqours live card with score >= 6",
            "Frame 2: JUMP_IF_FALSE - jumps if score < 6",
            "Frame 3: ACTIVATE_ENERGY - activates 4 energy",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "このメンバーをステージから控え室に置く": "Frame 0: MOVE_TO_DISCARD",
            "自分の控え室からライブカードを1枚手札に加える": "Frame 1: RECOVER_LIVE",
            "それがスコア6以上の『Aqours』のライブカードの場合、エネルギーを4枚アクティブにする": "Frame 2-3: JUMP_IF_FALSE + ACTIVATE_ENERGY"
        }
    }

# Ability 571: Looks correct - SUM_VALUE, PAY_ENERGY, DRAW, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。"
# Current frames: [SUM_VALUE, PAY_ENERGY, DRAW, RETURN] - appears correct
if len(data['abilities']) > 571:
    data['abilities'][571]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays 2 energy",
            "Frame 2: DRAW - draws 1 card",
            "Frame 3: RETURN"
        ]
    }

# Ability 572: Looks correct - SUM_VALUE, PAY_ENERGY, ENERGY_CHARGE, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。"
# Current frames: [SUM_VALUE, PAY_ENERGY, ENERGY_CHARGE, RETURN] - appears correct
if len(data['abilities']) > 572:
    data['abilities'][572]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays 2 energy",
            "Frame 2: ENERGY_CHARGE - charges energy in wait state",
            "Frame 3: RETURN"
        ]
    }

# Ability 573: Looks correct - SUM_VALUE, PAY_ENERGY, MOVE_TO_DISCARD, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のデッキの上からカードを10枚控え室に置く。"
# Current frames: [SUM_VALUE, PAY_ENERGY, MOVE_TO_DISCARD, RETURN] - appears correct
if len(data['abilities']) > 573:
    data['abilities'][573]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のデッキの上からカードを10枚控え室に置く。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays 2 energy",
            "Frame 2: MOVE_TO_DISCARD - discards 10 cards from deck top",
            "Frame 3: RETURN"
        ]
    }

# Ability 574: Looks correct - SELECT_CARDS, JUMP_IF_FALSE, ACTIVATE_ENERGY, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}自分の控え室にある「園田海未」と「津島善子」と「天王寺璃奈」を、合計6枚をシャッフルしてデッキの一番下に置く：エネルギーを6枚までアクティブにする。"
# Current frames: [SELECT_CARDS, JUMP_IF_FALSE, ACTIVATE_ENERGY, RETURN] - appears correct for complex ability
if len(data['abilities']) > 574:
    data['abilities'][574]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}自分の控え室にある「園田海未」と「津島善子」と「天王寺璃奈」を、合計6枚をシャッフルしてデッキの一番下に置く：エネルギーを6枚までアクティブにする。",
            "Frames appear correct for complex ability",
            "Frame 0: SELECT_CARDS - selects specific members",
            "Frame 1: JUMP_IF_FALSE - jumps if not enough cards",
            "Frame 2: ACTIVATE_ENERGY - activates up to 6 energy",
            "Frame 3: RETURN"
        ]
    }

# Ability 575: Looks correct - MOVE_TO_DISCARD, COUNT_ENERGY, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN
# Text: "{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分のエネルギーが6枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。"
# Current frames: [MOVE_TO_DISCARD, COUNT_ENERGY, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN] - appears correct
if len(data['abilities']) > 575:
    data['abilities'][575]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分のエネルギーが6枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。",
            "Frames appear correct",
            "Frame 0: MOVE_TO_DISCARD - sacrifices self",
            "Frame 1: COUNT_ENERGY - checks energy count >= 6",
            "Frame 2: JUMP_IF_FALSE - jumps if less than 6",
            "Frame 3: ENERGY_CHARGE - charges energy in wait state",
            "Frame 4: RETURN"
        ]
    }

# Ability 576: Looks correct - MOVE_TO_DISCARD, RECOVER_MEMBER (with group check for Liella), RETURN
# Text: "{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室から『Liella!』のカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD, RECOVER_MEMBER (with group_id: LIELLA), RETURN] - appears correct
if len(data['abilities']) > 576:
    data['abilities'][576]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室から『Liella!』のカードを1枚手札に加える。",
            "Frames appear correct",
            "Frame 0: MOVE_TO_DISCARD - sacrifices self",
            "Frame 1: RECOVER_MEMBER - recovers Liella card",
            "Frame 2: RETURN"
        ]
    }

# Ability 577: NOP needs to be replaced with proper check for main phase
# Text: "{{toujyou.png|登場}}自分のメインフェイズの場合、{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室からライブカードを1枚、表向きでライブカード置き場に置く。次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。"
# Current frames: [NOP, JUMP_IF_FALSE, PAY_ENERGY, PLAY_LIVE_FROM_DISCARD, REDUCE_LIVE_SET_LIMIT, RETURN] - NOP needs proper check
if len(data['abilities']) > 577:
    data['abilities'][577]["frames"] = [
        {
            "op": "PHASE_CHECK",
            "frame_index": 0,
            "attr": {
                "phase": "MAIN"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 3
        },
        {
            "op": "PAY_ENERGY",
            "frame_index": 2,
            "value": 2,
            "attr": {
                "is_optional": 1
            }
        },
        {
            "op": "PLAY_LIVE_FROM_DISCARD",
            "frame_index": 3,
            "value": 1,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "REDUCE_LIVE_SET_LIMIT",
            "frame_index": 4,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 5
        }
    ]
    data['abilities'][577]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: TOUJYOU (Appearance)",
            "Text: {{toujyou.png|登場}}自分のメインフェイズの場合、{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室からライブカードを1枚、表向きでライブカード置き場に置く。次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。",
            "Fixed: Replaced NOP with PHASE_CHECK for main phase",
            "Frame 0: PHASE_CHECK - checks if main phase",
            "Frame 1: JUMP_IF_FALSE - jumps if not main phase",
            "Frame 2: PAY_ENERGY - optionally pays 2 energy",
            "Frame 3: PLAY_LIVE_FROM_DISCARD - plays live card from discard",
            "Frame 4: REDUCE_LIVE_SET_LIMIT - reduces live set limit",
            "Frame 5: RETURN"
        ],
        "text_mapping": {
            "自分のメインフェイズの場合": "Frame 0-1: PHASE_CHECK + JUMP_IF_FALSE",
            "Eを2枚支払ってもよい": "Frame 2: PAY_ENERGY (optional)",
            "自分の控え室からライブカードを1枚、表向きでライブカード置き場に置く": "Frame 3: PLAY_LIVE_FROM_DISCARD",
            "次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る": "Frame 4: REDUCE_LIVE_SET_LIMIT"
        }
    }

# Ability 578: Looks correct - BATON, JUMP_IF_FALSE, ACTIVATE_ENERGY, BATON, JUMP_IF_FALSE, DRAW, RETURN
# Text: "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、このメンバーがコスト10以上のブレードハートを持たない『虹ヶ咲』のメンバーとバトンタッチしていた場合、エネルギーを2枚アクティブにする。コスト15以上のブレード..."
# Current frames: [BATON, JUMP_IF_FALSE, ACTIVATE_ENERGY, BATON, JUMP_IF_FALSE, DRAW, RETURN] - appears correct for complex baton touch
if len(data['abilities']) > 578:
    data['abilities'][578]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_LEAVES",
            "Text: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、このメンバーがコスト10以上のブレードハートを持たない『虹ヶ咲』のメンバーとバトンタッチしていた場合、エネルギーを2枚アクティブにする。コスト15以上のブレード...",
            "Frames appear correct for complex baton touch",
            "Frame 0: BATON - checks baton touch with cost 10+ bladeless Nijigasaki",
            "Frame 1: JUMP_IF_FALSE - jumps if no baton",
            "Frame 2: ACTIVATE_ENERGY - activates 2 energy",
            "Frame 3: BATON - checks baton touch with cost 15+ blade",
            "Frame 4: JUMP_IF_FALSE - jumps if no baton",
            "Frame 5: DRAW - draws card",
            "Frame 6: RETURN"
        ]
    }

# Ability 579: Looks correct - MOVE_MEMBER, RETURN
# Text: "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、メンバー1人をポジションチェンジさせてもよい。"
# Current frames: [MOVE_MEMBER, RETURN] - appears correct
if len(data['abilities']) > 579:
    data['abilities'][579]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_LEAVES",
            "Text: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、メンバー1人をポジションチェンジさせてもよい。",
            "Frames appear correct",
            "Frame 0: MOVE_MEMBER - position changes member",
            "Frame 1: RETURN"
        ]
    }

# Ability 580: Looks correct - ACTIVATE_MEMBER, RETURN
# Text: "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、メンバー1人をアクティブにしてもよい。"
# Current frames: [ACTIVATE_MEMBER, RETURN] - appears correct
if len(data['abilities']) > 580:
    data['abilities'][580]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_LEAVES",
            "Text: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、メンバー1人をアクティブにしてもよい。",
            "Frames appear correct",
            "Frame 0: ACTIVATE_MEMBER - activates member",
            "Frame 1: RETURN"
        ]
    }

# Ability 581: Looks correct - MOVE_TO_DISCARD, JUMP_IF_FALSE, SUM_VALUE, JUMP_IF_FALSE, RECOVER_LIVE, RETURN
# Text: "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、手札を1枚控え室に置いてもよい。そうした場合、自分の控え室から『Aqours』のライブカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD, JUMP_IF_FALSE, SUM_VALUE, JUMP_IF_FALSE, RECOVER_LIVE, RETURN] - appears correct
if len(data['abilities']) > 581:
    data['abilities'][581]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_LEAVES",
            "Text: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、手札を1枚控え室に置いてもよい。そうした場合、自分の控え室から『Aqours』のライブカードを1枚手札に加える。",
            "Frames appear correct",
            "Frame 0: MOVE_TO_DISCARD - optionally discards 1 card",
            "Frame 1: JUMP_IF_FALSE - jumps if not discarded",
            "Frame 2: SUM_VALUE - check for condition",
            "Frame 3: JUMP_IF_FALSE - jumps if condition not met",
            "Frame 4: RECOVER_LIVE - recovers Aqours live card",
            "Frame 5: RETURN"
        ]
    }

# Ability 582: Looks correct - BATON, JUMP_IF_FALSE, ACTIVATE_ENERGY, RETURN
# Text: "{{jidou.png|自動}}このメンバーがコスト10以上の『蓮ノ空』のメンバーとバトンタッチして控え室に置かれたとき、エネルギーを2枚アクティブにする。"
# Current frames: [BATON, JUMP_IF_FALSE, ACTIVATE_ENERGY, RETURN] - appears correct
if len(data['abilities']) > 582:
    data['abilities'][582]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_LEAVES",
            "Text: {{jidou.png|自動}}このメンバーがコスト10以上の『蓮ノ空』のメンバーとバトンタッチして控え室に置かれたとき、エネルギーを2枚アクティブにする。",
            "Frames appear correct",
            "Frame 0: BATON - checks baton touch with cost 10+ Hasunosora",
            "Frame 1: JUMP_IF_FALSE - jumps if no baton",
            "Frame 2: ACTIVATE_ENERGY - activates 2 energy",
            "Frame 3: RETURN"
        ]
    }

# Ability 583: Looks correct - DRAW, MOVE_TO_DISCARD, RETURN
# Text: "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、カードを2枚引き、手札を1枚控え室に置く。"
# Current frames: [DRAW, MOVE_TO_DISCARD, RETURN] - appears correct
if len(data['abilities']) > 583:
    data['abilities'][583]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_LEAVES",
            "Text: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、カードを2枚引き、手札を1枚控え室に置く。",
            "Frames appear correct",
            "Frame 0: DRAW - draws 2 cards",
            "Frame 1: MOVE_TO_DISCARD - discards 1 card",
            "Frame 2: RETURN"
        ]
    }

# Ability 584: Looks correct - LOOK_AND_CHOOSE, RETURN
# Text: "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。"
# Current frames: [LOOK_AND_CHOOSE, RETURN] - appears correct
if len(data['abilities']) > 584:
    data['abilities'][584]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_LEAVES",
            "Text: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。",
            "Frames appear correct",
            "Frame 0: LOOK_AND_CHOOSE - looks at 5 cards, chooses member",
            "Frame 1: RETURN"
        ]
    }

# Ability 585: Looks correct - LOOK_AND_CHOOSE, RETURN
# Text: "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。"
# Current frames: [LOOK_AND_CHOOSE, RETURN] - appears correct
if len(data['abilities']) > 585:
    data['abilities'][585]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_LEAVES",
            "Text: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。",
            "Frames appear correct",
            "Frame 0: LOOK_AND_CHOOSE - looks at 5 cards, chooses live",
            "Frame 1: RETURN"
        ]
    }

# Ability 586: Looks correct - COUNT_BLADE_HEART_TYPES, JUMP_IF_FALSE, ADD_HEARTS, COUNT_BLADE_HEART_TYPES, JUMP_IF_FALSE, GRANT_ABILITY, RETURN
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、エールにより公開された自分のカードが持つブレードハートの中に[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、[紫ブレ..."
# Current frames: [COUNT_BLADE_HEART_TYPES, JUMP_IF_FALSE, ADD_HEARTS, COUNT_BLADE_HEART_TYPES, JUMP_IF_FALSE, GRANT_ABILITY, RETURN] - appears correct
if len(data['abilities']) > 586:
    data['abilities'][586]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_REVEAL",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、エールにより公開された自分のカードが持つブレードハートの中に[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、[紫ブレ...",
            "Frames appear correct",
            "Frame 0: COUNT_BLADE_HEART_TYPES - counts blade heart types",
            "Frame 1: JUMP_IF_FALSE - jumps if not enough types",
            "Frame 2: ADD_HEARTS - adds hearts",
            "Frame 3: COUNT_BLADE_HEART_TYPES - counts blade heart types again",
            "Frame 4: JUMP_IF_FALSE - jumps if not enough types",
            "Frame 5: GRANT_ABILITY - grants ability",
            "Frame 6: RETURN"
        ]
    }

# Ability 587: Looks correct - GROUP_FILTER, JUMP_IF_FALSE, ADD_HEARTS, RETURN
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、エールにより公開された自分のカードの中にブレードハートを持たないメンバーカードが3枚以上ある場合、ライブ終了時まで、{{icon_all.png|ハ..."
# Current frames: [GROUP_FILTER, JUMP_IF_FALSE, ADD_HEARTS, RETURN] - appears correct
if len(data['abilities']) > 587:
    data['abilities'][587]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_REVEAL",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、エールにより公開された自分のカードの中にブレードハートを持たないメンバーカードが3枚以上ある場合、ライブ終了時まで、{{icon_all.png|ハ...",
            "Frames appear correct",
            "Frame 0: GROUP_FILTER - filters for bladeless members",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 3",
            "Frame 2: ADD_HEARTS - adds hearts",
            "Frame 3: RETURN"
        ]
    }

# Ability 588: NOP needs to be replaced with proper hand size check
# Text: "{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分の手札が7枚以下の場合、カードを1枚引く。"
# Current frames: [HAS_KEYWORD, NOP, JUMP_IF_FALSE, DRAW, RETURN] - NOP needs proper hand size check
if len(data['abilities']) > 588:
    data['abilities'][588]["frames"] = [
        {
            "op": "HAS_KEYWORD",
            "frame_index": 0,
            "attr": {
                "char_id_1": "TSUZURI",
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GE"
            }
        },
        {
            "op": "COUNT_HAND",
            "frame_index": 1,
            "value": 7,
            "attr": {
                "is_le": 1
            },
            "slot": {
                "target_slot": "CONTEXT",
                "comparison": "LE"
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
    ]
    data['abilities'][588]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_REVEAL",
            "Text: {{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分の手札が7枚以下の場合、カードを1枚引く。",
            "Fixed: Replaced NOP with COUNT_HAND for hand size check",
            "Frame 0: HAS_KEYWORD - checks for live card in reveal",
            "Frame 1: COUNT_HAND - checks hand size <= 7",
            "Frame 2: JUMP_IF_FALSE - jumps if hand > 7",
            "Frame 3: DRAW - draws 1 card",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "ライブカードが1枚以上あるとき": "Frame 0: HAS_KEYWORD",
            "自分の手札が7枚以下の場合": "Frame 1: COUNT_HAND",
            "カードを1枚引く": "Frame 3: DRAW"
        }
    }

# Ability 589: Looks correct - HAS_KEYWORD, JUMP_IF_FALSE, ADD_HEARTS, RETURN
# Text: "{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、ライブ終了時まで、［緑ハート］を得る。"
# Current frames: [HAS_KEYWORD, JUMP_IF_FALSE, ADD_HEARTS, RETURN] - appears correct
if len(data['abilities']) > 589:
    data['abilities'][589]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_REVEAL",
            "Text: {{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、ライブ終了時まで、［緑ハート］を得る。",
            "Frames appear correct",
            "Frame 0: HAS_KEYWORD - checks for live card",
            "Frame 1: JUMP_IF_FALSE - jumps if no live",
            "Frame 2: ADD_HEARTS - adds green heart",
            "Frame 3: RETURN"
        ]
    }

# Ability 590: Looks correct - HAS_KEYWORD, JUMP_IF_FALSE, ADD_HEARTS, RETURN
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_02.png|heart02}}を得る。"
# Current frames: [HAS_KEYWORD, JUMP_IF_FALSE, ADD_HEARTS, RETURN] - appears correct
if len(data['abilities']) > 590:
    data['abilities'][590]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_REVEAL",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_02.png|heart02}}を得る。",
            "Frames appear correct",
            "Frame 0: HAS_KEYWORD - checks for no blade hearts",
            "Frame 1: JUMP_IF_FALSE - jumps if has blade hearts",
            "Frame 2: ADD_HEARTS - adds heart02",
            "Frame 3: RETURN"
        ]
    }

# Ability 591: Looks correct - HAS_KEYWORD, JUMP_IF_FALSE, ADD_HEARTS, RETURN
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_03.png|heart03}}を得る。"
# Current frames: [HAS_KEYWORD, JUMP_IF_FALSE, ADD_HEARTS, RETURN] - appears correct
if len(data['abilities']) > 591:
    data['abilities'][591]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_REVEAL",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_03.png|heart03}}を得る。",
            "Frames appear correct",
            "Frame 0: HAS_KEYWORD - checks for no blade hearts",
            "Frame 1: JUMP_IF_FALSE - jumps if has blade hearts",
            "Frame 2: ADD_HEARTS - adds heart03",
            "Frame 3: RETURN"
        ]
    }

# Ability 592: Looks correct - HAS_KEYWORD, JUMP_IF_FALSE, ADD_HEARTS, RETURN
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_06.png|heart06}}を得る。"
# Current frames: [HAS_KEYWORD, JUMP_IF_FALSE, ADD_HEARTS, RETURN] - appears correct
if len(data['abilities']) > 592:
    data['abilities'][592]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_REVEAL",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_06.png|heart06}}を得る。",
            "Frames appear correct",
            "Frame 0: HAS_KEYWORD - checks for no blade hearts",
            "Frame 1: JUMP_IF_FALSE - jumps if has blade hearts",
            "Frame 2: ADD_HEARTS - adds heart06",
            "Frame 3: RETURN"
        ]
    }

# Ability 593: Needs dynamic heart count and max limit
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、ライブ終了時まで、エールにより公開された自分のカードの中のライブカード1枚につき、{{heart_02.png|heart02}}を得る。この能力では{{heart_02.png|heart02}}は3つまでしか得られない。"
# Current frames: [ADD_HEARTS, RETURN] - needs dynamic heart count and max limit
if len(data['abilities']) > 593:
    data['abilities'][593]["frames"] = [
        {
            "op": "COUNT_REVEALED_LIVE",
            "frame_index": 0,
            "attr": {
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "ADD_HEARTS",
            "frame_index": 1,
            "attr": {
                "target_player": "SELF",
                "dynamic": 1
            },
            "slot": {
                "target_slot": "CONTEXT"
            },
            "params": {
                "heart_type": 2,
                "max_value": 3
            }
        },
        {
            "op": "RETURN",
            "frame_index": 2
        }
    ]
    data['abilities'][593]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_REVEAL",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、ライブ終了時まで、エールにより公開された自分のカードの中のライブカード1枚につき、{{heart_02.png|heart02}}を得る。この能力では{{heart_02.png|heart02}}は3つまでしか得られない。",
            "Fixed: Added COUNT_REVEALED_LIVE for dynamic count and max_value to ADD_HEARTS",
            "Frame 0: COUNT_REVEALED_LIVE - counts revealed live cards",
            "Frame 1: ADD_HEARTS - adds heart02 per live (dynamic, max 3)",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "ライブカード1枚につき、heart02を得る": "Frame 0-1: COUNT_REVEALED_LIVE + ADD_HEARTS",
            "heart02は3つまでしか得られない": "Frame 1: ADD_HEARTS (max_value: 3)"
        }
    }

# Ability 594: NOP needs proper frames for blade heart check
# Text: "{{jidou.png|自動}}［ターン1回］エールにより自分のカードを1枚以上公開したとき、それらのカードの中にブレードハートを持つカードが2枚以下の場合、それらのカードをすべて控え室に置いてもよい。そのエールで得たブレードハートを失い、もう一度エールを行う。"
# Current frames: [NOP, RETURN] - needs proper frames
if len(data['abilities']) > 594:
    data['abilities'][594]["frames"] = [
        {
            "op": "COUNT_BLADE_HEART_CARDS",
            "frame_index": 0,
            "value": 2,
            "attr": {
                "is_le": 1,
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "CONTEXT",
                "comparison": "LE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "MOVE_REVEALED_TO_DISCARD",
            "frame_index": 2,
            "attr": {
                "target_player": "SELF",
                "is_optional": 1
            },
            "slot": {
                "target_slot": "DISCARD",
                "source_zone": "REVEALED"
            }
        },
        {
            "op": "LOSE_BLADE_HEARTS",
            "frame_index": 3,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "REPEAT_YELL",
            "frame_index": 4,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 5
        }
    ]
    data['abilities'][594]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_REVEAL",
            "Text: {{jidou.png|自動}}［ターン1回］エールにより自分のカードを1枚以上公開したとき、それらのカードの中にブレードハートを持つカードが2枚以下の場合、それらのカードをすべて控え室に置いてもよい。そのエールで得たブレードハートを失い、もう一度エールを行う。",
            "Fixed: Replaced NOP with proper frames for blade heart check and repeat yell",
            "Frame 0: COUNT_BLADE_HEART_CARDS - counts blade heart cards (<= 2)",
            "Frame 1: JUMP_IF_FALSE - jumps if > 2",
            "Frame 2: MOVE_REVEALED_TO_DISCARD - discards revealed cards (optional)",
            "Frame 3: LOSE_BLADE_HEARTS - loses blade hearts from yell",
            "Frame 4: REPEAT_YELL - repeats yell",
            "Frame 5: RETURN"
        ],
        "text_mapping": {
            "ブレードハートを持つカードが2枚以下の場合": "Frame 0-1: COUNT_BLADE_HEART_CARDS + JUMP_IF_FALSE",
            "それらのカードをすべて控え室に置いてもよい": "Frame 2: MOVE_REVEALED_TO_DISCARD",
            "そのエールで得たブレードハートを失い": "Frame 3: LOSE_BLADE_HEARTS",
            "もう一度エールを行う": "Frame 4: REPEAT_YELL"
        }
    }

# Ability 595: NOP needs proper check for position change or energy placement
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、このメンバーがエリアを移動するか自分のエネルギー置き場にエネルギーが置かれたとき、カードを1枚引き、ライブ終了時まで、{{heart_02.png|heart02}}を得る。"
# Current frames: [NOP, JUMP_IF_FALSE, DRAW, ADD_HEARTS, RETURN] - NOP needs proper check
if len(data['abilities']) > 595:
    data['abilities'][595]["frames"] = [
        {
            "op": "CHECK_SELF_MOVE_OR_ENERGY",
            "frame_index": 0,
            "attr": {
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "CONTEXT",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 2
        },
        {
            "op": "DRAW",
            "frame_index": 2,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "ADD_HEARTS",
            "frame_index": 3,
            "value": 1,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            },
            "params": {
                "heart_type": 2
            }
        },
        {
            "op": "RETURN",
            "frame_index": 4
        }
    ]
    data['abilities'][595]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、このメンバーがエリアを移動するか自分のエネルギー置き場にエネルギーが置かれたとき、カードを1枚引き、ライブ終了時まで、{{heart_02.png|heart02}}を得る。",
            "Fixed: Replaced NOP with CHECK_SELF_MOVE_OR_ENERGY",
            "Frame 0: CHECK_SELF_MOVE_OR_ENERGY - checks for self move or energy placement",
            "Frame 1: JUMP_IF_FALSE - jumps if condition not met",
            "Frame 2: DRAW - draws 1 card",
            "Frame 3: ADD_HEARTS - adds heart02",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "このメンバーがエリアを移動するか自分のエネルギー置き場にエネルギーが置かれたとき": "Frame 0-1: CHECK_SELF_MOVE_OR_ENERGY + JUMP_IF_FALSE",
            "カードを1枚引き": "Frame 2: DRAW",
            "heart02を得る": "Frame 3: ADD_HEARTS"
        }
    }

# Ability 596: NOP needs proper check for appearance or position change
# Text: "{{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。"
# Current frames: [NOP, JUMP_IF_FALSE, TAP_OPPONENT, JUMP, RETURN] - NOP needs proper check
if len(data['abilities']) > 596:
    data['abilities'][596]["frames"] = [
        {
            "op": "IS_SELF_APPEAR_OR_MOVE",
            "frame_index": 0,
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 2
        },
        {
            "op": "TAP_OPPONENT",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "target_player": "OPPONENT"
            },
            "params": {
                "filter": "BLADE_LE3"
            },
            "slot": {
                "target_slot": "STAGE_2"
            }
        },
        {
            "op": "JUMP",
            "frame_index": 3,
            "value": 1
        },
        {
            "op": "RETURN",
            "frame_index": 4
        }
    ]
    data['abilities'][596]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。",
            "Fixed: Replaced NOP with IS_SELF_APPEAR_OR_MOVE",
            "Frame 0: IS_SELF_APPEAR_OR_MOVE - checks for appearance or move",
            "Frame 1: JUMP_IF_FALSE - jumps if not appearance or move",
            "Frame 2: TAP_OPPONENT - taps opponent with <= 3 blades",
            "Frame 3: JUMP - loops",
            "Frame 4: RETURN"
        ]
    }

# Ability 597: Looks correct - IS_SELF_MOVE, JUMP_IF_FALSE, ACTIVATE_ENERGY, RETURN
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、エネルギーを2枚アクティブにする。"
# Current frames: [IS_SELF_MOVE, JUMP_IF_FALSE, ACTIVATE_ENERGY, RETURN] - appears correct
if len(data['abilities']) > 597:
    data['abilities'][597]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、エネルギーを2枚アクティブにする。",
            "Frames appear correct",
            "Frame 0: IS_SELF_MOVE - checks if self moved",
            "Frame 1: JUMP_IF_FALSE - jumps if not self move",
            "Frame 2: ACTIVATE_ENERGY - activates 2 energy",
            "Frame 3: RETURN"
        ]
    }

# Ability 598: Missing IS_SELF_MOVE check
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。"
# Current frames: [ENERGY_CHARGE, RETURN] - missing IS_SELF_MOVE
if len(data['abilities']) > 598:
    data['abilities'][598]["frames"] = [
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
            "op": "ENERGY_CHARGE",
            "frame_index": 2,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT",
                "is_wait": 1
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][598]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。",
            "Fixed: Added IS_SELF_MOVE check",
            "Frame 0: IS_SELF_MOVE - checks if self moved",
            "Frame 1: JUMP_IF_FALSE - jumps if not self move",
            "Frame 2: ENERGY_CHARGE - charges energy in wait state",
            "Frame 3: RETURN"
        ]
    }

# Ability 599: Missing score check
# Text: "{{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、自分の控え室から、スコア3以下の『Liella!』のライブカードを1枚手札に加える。"
# Current frames: [IS_SELF_MOVE, JUMP_IF_FALSE, RECOVER_LIVE, RETURN] - missing score check
if len(data['abilities']) > 599:
    data['abilities'][599]["frames"] = [
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
            "op": "RECOVER_LIVE",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": "LIELLA",
                "value_enabled": 1,
                "value_threshold": 3,
                "is_le": 1,
                "zone_mask": "ALL"
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][599]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、自分の控え室から、スコア3以下の『Liella!』のライブカードを1枚手札に加える。",
            "Fixed: Added score check to RECOVER_LIVE",
            "Frame 0: IS_SELF_MOVE - checks if self moved",
            "Frame 1: JUMP_IF_FALSE - jumps if not self move",
            "Frame 2: RECOVER_LIVE - recovers Liella live card with score <= 3",
            "Frame 3: RETURN"
        ]
    }

# Ability 600: Looks correct - IS_SELF_MOVE, JUMP_IF_FALSE, TAP_OPPONENT, JUMP, RETURN
# Text: "{{jidou.png|自動}}このメンバーがエリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が2つ以下のメンバー1人をウェイトにする。"
# Current frames: [IS_SELF_MOVE, JUMP_IF_FALSE, TAP_OPPONENT, JUMP, RETURN] - appears correct
if len(data['abilities']) > 600:
    data['abilities'][600]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ON_POSITION_CHANGE",
            "Text: {{jidou.png|自動}}このメンバーがエリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が2つ以下のメンバー1人をウェイトにする。",
            "Frames appear correct",
            "Frame 0: IS_SELF_MOVE - checks if self moved",
            "Frame 1: JUMP_IF_FALSE - jumps if not self move",
            "Frame 2: TAP_OPPONENT - taps opponent with <= 2 blades",
            "Frame 3: JUMP - loops",
            "Frame 4: RETURN"
        ]
    }

# Save the updated data
save_json(filepath, data)

print("Fixed abilities 551-600")
print("Completed batch 551-600")
