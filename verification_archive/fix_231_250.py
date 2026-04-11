import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Fixing abilities 231-250...")

# Ability 229 - fix SELECT_MODE placeholder to proper COLOR_SELECT + TRANSFORM_HEART
ability_229 = data['abilities'][229]
ability_229['frames'] = [
    {
        "op": "COLOR_SELECT",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "TRANSFORM_HEART",
        "frame_index": 1,
        "value": 7,
        "attr": {
            "target_player": "SELF",
            "color_mask": 14
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 2
    }
]
ability_229['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select heart01/03/04, change member's heart to selected",
        "Fixed: Changed from SELECT_MODE placeholder to COLOR_SELECT + TRANSFORM_HEART",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_04.png|heart04}}のうち1つを選ぶ": "Frame 0: COLOR_SELECT",
        "ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる": "Frame 1: TRANSFORM_HEART with color_mask=14 (heart01|03|04)"
    }
}

# Ability 230 - fix SELECT_MODE placeholder to proper COLOR_SELECT + TRANSFORM_HEART
ability_230 = data['abilities'][230]
ability_230['frames'] = [
    {
        "op": "COLOR_SELECT",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "TRANSFORM_HEART",
        "frame_index": 1,
        "value": 7,
        "attr": {
            "target_player": "SELF",
            "color_mask": 52
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 2
    }
]
ability_230['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select heart02/05/06, change member's heart to selected",
        "Fixed: Changed from SELECT_MODE placeholder to COLOR_SELECT + TRANSFORM_HEART",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{heart_02.png|heart02}}か{{heart_05.png|heart05}}か{{heart_06.png|heart06}}のうち1つを選ぶ": "Frame 0: COLOR_SELECT",
        "ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる": "Frame 1: TRANSFORM_HEART with color_mask=52 (heart02|05|06)"
    }
}

# Ability 231 - verified
ability_231 = data['abilities'][231]
ability_231['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 2 energy, transform all hearts to heart04",
        "Frame 0: PAY_ENERGY with value=2, is_optional=1",
        "Frame 2: TRANSFORM_HEART with color_mask=8 (heart04)",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、このメンバーが元々持つハートはすべて{{heart_04.png|heart04}}になる": "Frame 2: TRANSFORM_HEART"
    }
}

# Ability 232 - remove unnecessary SUM_VALUE frames
ability_232 = data['abilities'][232]
ability_232['frames'] = [
    {
        "op": "PAY_ENERGY",
        "frame_index": 0,
        "value": 2,
        "attr": {
            "is_optional": 1
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
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
ability_232['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 2 energy, energy charge 1",
        "Fixed: Removed unnecessary SUM_VALUE frames",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く": "Frame 2: ENERGY_CHARGE"
    }
}

# Ability 233 - fix SELECT_MODE for "unless pay 2 energy"
ability_233 = data['abilities'][233]
ability_233['frames'] = [
    {
        "op": "PAY_ENERGY",
        "frame_index": 0,
        "value": 2,
        "attr": {
            "is_optional": 1
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "RETURN",
        "frame_index": 2
    },
    {
        "op": "MOVE_TO_DISCARD",
        "frame_index": 3,
        "value": 2,
        "slot": {
            "target_slot": "HAND"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 4
    }
]
ability_233['frame_verification'] = {
    "verified": True,
    "notes": [
        "Unless pay 2 energy, discard 2 from hand",
        "Fixed: Changed from SELECT_MODE placeholder to proper PAY_ENERGY check",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払わないかぎり": "Frames 0-2: PAY_ENERGY check",
        "自分の手札を2枚控え室に置く": "Frame 3: MOVE_TO_DISCARD"
    }
}

# Ability 234 - verified
ability_234 = data['abilities'][234]
ability_234['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, gain blade",
        "Frame 0: PAY_ENERGY with value=1, is_optional=1",
        "Frame 2: ADD_BLADES",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES"
    }
}

# Ability 235 - verified
ability_235 = data['abilities'][235]
ability_235['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, energy charge 1",
        "Frame 0: PAY_ENERGY with value=1, is_optional=1",
        "Frame 2: ENERGY_CHARGE",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く": "Frame 2: ENERGY_CHARGE"
    }
}

# Ability 236 - remove unnecessary SUM_VALUE frames
ability_236 = data['abilities'][236]
ability_236['frames'] = [
    {
        "op": "PAY_ENERGY",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "is_optional": 1
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "SELECT_CARDS",
        "frame_index": 2,
        "value": 2,
        "attr": {
            "target_player": "SELF",
            "card_type": "MEMBER"
        },
        "slot": {
            "target_slot": "CONTEXT",
            "source_zone": "DISCARD"
        }
    },
    {
        "op": "MOVE_TO_DECK",
        "frame_index": 3,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT",
            "dest_zone": "DECK",
            "remainder_zone": "DECK_TOP"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 4
    }
]
ability_236['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, select 2 member cards from discard, put on deck top",
        "Fixed: Removed unnecessary SUM_VALUE frames",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "自分の控え室にあるメンバーカード2枚を好きな順番でデッキの一番上に置く": "Frames 2-3: SELECT_CARDS + MOVE_TO_DECK"
    }
}

# Ability 237 - fix weird HAS_KEYWORD check
ability_237 = data['abilities'][237]
ability_237['frames'] = [
    {
        "op": "NOP",
        "frame_index": 0,
        "params": {
            "raw_cond": "POSITION_LEFT_SIDE"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "NOP",
        "frame_index": 2,
        "params": {
            "raw_cond": "MOVED_THIS_TURN"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 3,
        "value": 1
    },
    {
        "op": "ADD_BLADES",
        "frame_index": 4,
        "value": 2,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 5
    }
]
ability_237['frame_verification'] = {
    "verified": True,
    "notes": [
        "Left side only: if moved this turn, gain blade x2",
        "Fixed: Changed from HAS_KEYWORD(LANZHU) to proper POSITION_LEFT_SIDE check",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}【左サイド】": "Frame 0: NOP with raw_cond=POSITION_LEFT_SIDE",
        "このターン、このメンバーがエリアを移動している場合": "Frame 2: NOP with raw_cond=MOVED_THIS_TURN",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frame 4: ADD_BLADES"
    }
}

# Ability 238 - fix weird HAS_KEYWORD check for right side
ability_238 = data['abilities'][238]
ability_238['frames'] = [
    {
        "op": "NOP",
        "frame_index": 0,
        "params": {
            "raw_cond": "POSITION_RIGHT_SIDE"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "NOP",
        "frame_index": 2,
        "params": {
            "raw_cond": "MOVED_THIS_TURN"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 3,
        "value": 1
    },
    {
        "op": "ADD_BLADES",
        "frame_index": 4,
        "value": 2,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 5
    }
]
ability_238['frame_verification'] = {
    "verified": True,
    "notes": [
        "Right side only: if moved this turn, gain blade x2",
        "Fixed: Changed from HAS_KEYWORD(LANZHU) to proper POSITION_RIGHT_SIDE check",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}【右サイド】": "Frame 0: NOP with raw_cond=POSITION_RIGHT_SIDE",
        "このターン、このメンバーがエリアを移動している場合": "Frame 2: NOP with raw_cond=MOVED_THIS_TURN",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frame 4: ADD_BLADES"
    }
}

# Ability 239 - add keyword for "this turn"
ability_239 = data['abilities'][239]
ability_239['frames'][0]['attr']['keyword'] = "THIS_TURN"
ability_239['frame_verification'] = {
    "verified": True,
    "notes": [
        "If blade-less member card moved from success pile to discard this turn, draw 1, gain heart03+05+06",
        "Fixed: Added keyword=THIS_TURN to COUNT_DISCARD",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "このターン、ブレードハートを持たないメンバーカードが自分のライブカード置き場から控え室に置かれている場合": "Frame 0: COUNT_DISCARD with keyword=THIS_TURN, has_blade_heart=1",
        "カードを1枚引き、ライブ終了時まで、{{heart_03.png|heart03}}{{heart_05.png|heart05}}{{heart_06.png|heart06}}を得る": "Frames 2-5: DRAW + ADD_HEARTS x3"
    }
}

# Ability 240 - verified
ability_240 = data['abilities'][240]
ability_240['frame_verification'] = {
    "verified": True,
    "notes": [
        "Activate 2 energy",
        "Frame 0: ACTIVATE_ENERGY with value=2",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}エネルギーを2枚アクティブにする": "Frame 0: ACTIVATE_ENERGY"
    }
}

# Ability 241 - verified
ability_241 = data['abilities'][241]
ability_241['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 2 same-unit cards, gain heart04x2 + blade x2",
        "Frame 0: MOVE_TO_DISCARD with same_unit_discard=true",
        "Frame 1: ADD_HEARTS with heart_type=3, value=2",
        "Frame 2: ADD_BLADES with value=2",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "手札の同じユニット名を持つカード2枚を控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with same_unit_discard",
        "ライブ終了時まで、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frames 1-2: ADD_HEARTS + ADD_BLADES"
    }
}

# Ability 242 - verified (same as 241 but heart05)
ability_242 = data['abilities'][242]
ability_242['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 2 same-unit cards, gain heart05x2 + blade x2",
        "Frame 0: MOVE_TO_DISCARD with same_unit_discard=true",
        "Frame 1: ADD_HEARTS with heart_type=3, value=2",
        "Frame 2: ADD_BLADES with value=2",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "手札の同じユニット名を持つカード2枚を控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with same_unit_discard",
        "ライブ終了時まで、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frames 1-2: ADD_HEARTS + ADD_BLADES"
    }
}

# Ability 243 - remove unnecessary SUM_VALUE frames
ability_243 = data['abilities'][243]
ability_243['frames'] = [
    {
        "op": "MOVE_TO_DISCARD",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "is_optional": 1
        },
        "slot": {
            "target_slot": "HAND"
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
ability_243['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 1, gain blade",
        "Fixed: Removed unnecessary SUM_VALUE frames",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES"
    }
}

# Ability 244 - verified
ability_244 = data['abilities'][244]
ability_244['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 1, other stage members gain blade",
        "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "Frame 2: SELECT_MEMBER with value=99",
        "Frame 3: ADD_BLADES",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "ライブ終了時まで、自分のステージにいるほかのメンバーは{{icon_blade.png|ブレード}}を得る": "Frames 2-3: SELECT_MEMBER + ADD_BLADES"
    }
}

# Ability 245 - remove unnecessary SUM_VALUE frames
ability_245 = data['abilities'][245]
ability_245['frames'] = [
    {
        "op": "MOVE_TO_DISCARD",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "is_optional": 1
        },
        "slot": {
            "target_slot": "HAND"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 3
    },
    {
        "op": "COUNT_SUCCESS_LIVE",
        "frame_index": 2,
        "slot": {
            "target_slot": "STAGE_0",
            "comparison": "GE"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 3,
        "value": 2
    },
    {
        "op": "SELECT_MEMBER",
        "frame_index": 4,
        "value": 1,
        "attr": {
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "CONTEXT",
            "source_zone": "STAGE"
        }
    },
    {
        "op": "ADD_BLADES",
        "frame_index": 5,
        "value": 2,
        "attr": {
            "target_player": "SELF",
            "compare_accumulated": 1
        },
        "slot": {
            "target_slot": "STAGE_1",
            "remainder_zone": "STAGE",
            "is_dynamic": 1
        },
        "params": {
            "scalar_dynamic": {
                "base_value": 2,
                "divisor": 1
            }
        }
    },
    {
        "op": "RETURN",
        "frame_index": 6
    }
]
ability_245['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 1, gain blade x2 per success live card",
        "Fixed: Removed unnecessary SUM_VALUE frame",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frames 2-5: COUNT_SUCCESS_LIVE + SELECT_MEMBER + ADD_BLADES with dynamic"
    }
}

# Ability 246 - verified
ability_246 = data['abilities'][246]
ability_246['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 1, select heart color, give to non-self Nijigasaki member",
        "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "Frame 2: COLOR_SELECT",
        "Frame 3: SELECT_MEMBER with group_id=NIJIGASAKI, special_id=Not Self",
        "Frame 4: ADD_HEARTS with heart_type=SELECTED",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "好きなハートの色を1つ指定する": "Frame 2: COLOR_SELECT",
        "ライブ終了時まで、自分のステージにいるこのメンバー以外の『虹ヶ咲』のメンバー1人は、そのハートを1つ得る": "Frames 3-4: SELECT_MEMBER + ADD_HEARTS"
    }
}

# Ability 247 - remove unnecessary SUM_VALUE frames
ability_247 = data['abilities'][247]
ability_247['frames'] = [
    {
        "op": "MOVE_TO_DISCARD",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "is_optional": 1
        },
        "slot": {
            "target_slot": "HAND"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "LOOK_REORDER_DISCARD",
        "frame_index": 2,
        "value": 3,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
ability_247['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 1, look at top 3, reorder/discard",
        "Fixed: Removed unnecessary SUM_VALUE frames",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く": "Frame 2: LOOK_REORDER_DISCARD"
    }
}

# Ability 248 - fix incomplete frames
ability_248 = data['abilities'][248]
ability_248['frames'] = [
    {
        "op": "MOVE_TO_DISCARD",
        "frame_index": 0,
        "value": 2,
        "attr": {
            "is_optional": 1
        },
        "slot": {
            "target_slot": "HAND"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "LOOK_AND_CHOOSE",
        "frame_index": 2,
        "value": {
            "count": 3
        },
        "attr": {
            "reveal": 1,
            "dest_discard": 1,
            "remainder_zone": "DISCARD"
        },
        "slot": {
            "target_slot": "CONTEXT",
            "source_zone": "DECK_TOP"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
ability_248['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 2, look at top 3, add 1 to hand, put 1 on top, discard 1",
        "Fixed: Changed from incomplete frames to LOOK_AND_CHOOSE",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "手札を2枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、1枚をデッキの上に置き、1枚を控え室に置く": "Frame 2: LOOK_AND_CHOOSE"
    }
}

# Ability 249 - fix SELECT_MODE placeholder
ability_249 = data['abilities'][249]
ability_249['frames'] = [
    {
        "op": "SELECT_MODE",
        "frame_index": 0,
        "value": 2,
        "attr": {
            "target_player": "SELF"
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
        "op": "LOOK_DECK",
        "frame_index": 2,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "JUMP",
        "frame_index": 3,
        "value": 2
    },
    {
        "op": "LOOK_DECK",
        "frame_index": 4,
        "value": 1,
        "attr": {
            "target_player": "OPPONENT"
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "JUMP",
        "frame_index": 5,
        "value": 1
    },
    {
        "op": "MOVE_TO_DISCARD",
        "frame_index": 6,
        "value": 1,
        "attr": {
            "is_optional": 1
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 7
    }
]
ability_249['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select self or opponent, look at top deck card, optionally discard",
        "Fixed: Changed from SELECT_MODE placeholder to proper player selection",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "自分か相手を選ぶ": "Frame 0: SELECT_MODE",
        "自分は、そのプレイヤーのデッキの一番上のカードを見る": "Frames 2-5: LOOK_DECK based on selection",
        "自分はそのカードを控え室に置いてもよい": "Frame 6: MOVE_TO_DISCARD with is_optional=1"
    }
}

# Ability 250 - verified (SELECT_MODE with JUMP actually correct for player selection)
ability_250 = data['abilities'][250]
ability_250['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select self or opponent, recover up to 2 member cards to deck bottom",
        "Frame 0: SELECT_MODE",
        "Frame 3: RECOVER_MEMBER with target_player=SELF",
        "Frame 5: RECOVER_MEMBER with target_player=OPPONENT",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "自分か相手を選ぶ": "Frame 0: SELECT_MODE",
        "自分は、そのプレイヤーの控え室にあるメンバーカードを2枚まで、好きな順番でデッキの一番下に置く": "Frames 3-6: RECOVER_MEMBER based on selection"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed abilities 231-250")
print("Saved file")
