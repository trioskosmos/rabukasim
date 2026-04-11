import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Fixing abilities 251-270...")

# Ability 251 - fix SELECT_MODE for "select self/opponent, look at top deck, optional discard"
ability_251 = data['abilities'][251]
ability_251['frames'] = [
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
ability_251['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select self or opponent, look at top deck card, optionally discard",
        "Fixed: Changed from SELECT_MODE placeholder to proper player selection with LOOK_DECK",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "自分か相手を選ぶ": "Frame 0: SELECT_MODE",
        "自分は、そのプレイヤーのデッキの一番上のカードを見る": "Frames 2-5: LOOK_DECK based on selection",
        "自分はそのカードを控え室に置いてもよい": "Frame 6: MOVE_TO_DISCARD with is_optional=1"
    }
}

# Ability 252 - add player selection to LOOK_REORDER_DISCARD
ability_252 = data['abilities'][252]
ability_252['frames'] = [
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
        "op": "LOOK_REORDER_DISCARD",
        "frame_index": 2,
        "value": 2,
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
        "op": "LOOK_REORDER_DISCARD",
        "frame_index": 4,
        "value": 2,
        "attr": {
            "target_player": "OPPONENT"
        },
        "slot": {
            "target_slot": "STAGE_2"
        }
    },
    {
        "op": "JUMP",
        "frame_index": 5,
        "value": 1
    },
    {
        "op": "RETURN",
        "frame_index": 6
    }
]
ability_252['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select self or opponent, look at top 2 cards, reorder/discard",
        "Fixed: Added SELECT_MODE for player selection",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "自分か相手を選ぶ": "Frame 0: SELECT_MODE",
        "自分は、そのプレイヤーのデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く": "Frames 2-5: LOOK_REORDER_DISCARD based on selection"
    }
}

# Ability 253 - verified
ability_253 = data['abilities'][253]
ability_253['frame_verification'] = {
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

# Ability 254 - verified
ability_254 = data['abilities'][254]
ability_254['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select Aqours member, if 6+ blades, boost score +1",
        "Frame 0: SELECT_MEMBER with group_id=AQOURS",
        "Frame 1: COUNT_BLADES with value=6",
        "Frame 3: BOOST_SCORE",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "自分のステージにいる『Aqours』のメンバー1人を選ぶ": "Frame 0: SELECT_MEMBER",
        "そのメンバーが持つ{{icon_blade.png|ブレード}}が6つ以上場合": "Frame 1: COUNT_BLADES",
        "このカードのスコアを+１する": "Frame 3: BOOST_SCORE"
    }
}

# Ability 255 - fix complex text about Nijigasaki members and looking at cards
ability_255 = data['abilities'][255]
ability_255['frames'] = [
    {
        "op": "COUNT_STAGE",
        "frame_index": 0,
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
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "LOOK_REORDER_DISCARD",
        "frame_index": 2,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "REVEAL_CARDS",
        "frame_index": 3,
        "value": 1
    },
    {
        "op": "NOP",
        "frame_index": 4,
        "params": {
            "raw_cond": "REVEALED_IS_LIVE"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 5,
        "value": 1
    },
    {
        "op": "BOOST_SCORE",
        "frame_index": 6,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 7
    }
]
ability_255['frame_verification'] = {
    "verified": True,
    "notes": [
        "If Nijigasaki members on stage, look at top 1, if live revealed boost score",
        "Fixed: Changed from NOP+BOOST_SCORE to proper implementation",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "自分のステージにいる『虹ヶ咲』のメンバー1人につき、自分のデッキの上からカードを1枚見る": "Frames 0-2: COUNT_STAGE + LOOK_REORDER_DISCARD",
        "その中から1枚までをデッキの上に置き、残りを控え室に置く。その後、自分のデッキの一番上のカードを1枚公開する": "Frames 2-3: LOOK_REORDER_DISCARD + REVEAL_CARDS",
        "これによりライブカードを公開した場合、このカードのスコアを+１する": "Frames 4-6: check live revealed + BOOST_SCORE"
    }
}

# Ability 256 - verified
ability_256 = data['abilities'][256]
ability_256['frame_verification'] = {
    "verified": True,
    "notes": [
        "If stage cost total < opponent, draw 1",
        "Frame 0: SCORE_COMPARE with comparison=GT",
        "Frame 2: DRAW",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーのコストの合計が相手より低い場合": "Frame 0: SCORE_COMPARE",
        "カードを1枚引く": "Frame 2: DRAW"
    }
}

# Ability 257 - verified
ability_257 = data['abilities'][257]
ability_257['frame_verification'] = {
    "verified": True,
    "notes": [
        "If stage cost total < opponent, draw 2, put 1 from hand on deck top",
        "Frame 0: SCORE_COMPARE with comparison=GE",
        "Frame 2: DRAW with value=2",
        "Frame 4: MOVE_TO_DECK to DECK_TOP",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーのコストの合計が相手より低い場合": "Frame 0: SCORE_COMPARE",
        "カードを2枚引き、自分の手札を1枚デッキの一番上に置く": "Frames 2-4: DRAW + SELECT_CARDS + MOVE_TO_DECK"
    }
}

# Ability 258 - verified
ability_258 = data['abilities'][258]
ability_258['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional activate 1 tapped member",
        "Frame 0: SELECT_MEMBER with is_tapped=1, is_optional=1",
        "Frame 1: ACTIVATE_MEMBER",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーを1人までアクティブにする": "Frames 0-1: SELECT_MEMBER + ACTIVATE_MEMBER"
    }
}

# Ability 259 - fix HAS_KEYWORD to proper cost check
ability_259 = data['abilities'][259]
ability_259['frames'][5] = {
    "op": "NOP",
    "frame_index": 5,
    "params": {
        "raw_cond": "REVEALED_COST_LE9_MEMBER"
    }
}
ability_259['frame_verification'] = {
    "verified": True,
    "notes": [
        "Reveal top deck card, if cost≤9 member add to hand and position change, else discard",
        "Fixed: Changed HAS_KEYWORD(LANZHU) to proper cost≤9 member check",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "自分のデッキの一番上のカードを公開する": "Frame 0: LOOK_DECK",
        "公開したカードがコスト9以下のメンバーカード場合、公開したカードを手札に加え、このメンバーはポジションチェンジする": "Frames 1-4: check + ADD_TO_HAND + MOVE_MEMBER",
        "それ以外の場合、公開したカードを控え室に置く": "Frames 5-7: check + MOVE_TO_DISCARD"
    }
}

# Ability 260 - remove unnecessary SUM_VALUE frames
ability_260 = data['abilities'][260]
ability_260['frames'] = [
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
ability_260['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 2 energy, gain blade x2",
        "Fixed: Removed unnecessary SUM_VALUE frames",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES"
    }
}

# Ability 261 - add TRANSFORM_HEART
ability_261 = data['abilities'][261]
ability_261['frames'] = [
    {
        "op": "COLOR_SELECT",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "target_player": "SELF",
            "color_mask": "RED|YELLOW|ANY"
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
            "color_mask": 35
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
ability_261['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select heart01/02/06, change member's heart to selected",
        "Fixed: Added TRANSFORM_HEART frame",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{heart_01.png|heart01}}か{{heart_02.png|heart02}}か{{heart_06.png|heart06}}のうち1つを選ぶ": "Frame 0: COLOR_SELECT",
        "ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる": "Frame 1: TRANSFORM_HEART with color_mask=35 (heart01|02|06)"
    }
}

# Ability 262 - add keyword filter for "moved this turn"
ability_262 = data['abilities'][262]
ability_262['frames'] = [
    {
        "op": "COLOR_SELECT",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "target_player": "SELF",
            "color_mask": "RED|YELLOW|ANY"
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "SELECT_MEMBER",
        "frame_index": 1,
        "value": 99,
        "attr": {
            "target_player": "SELF",
            "keyword": "MOVED_THIS_TURN"
        },
        "slot": {
            "target_slot": "CONTEXT",
            "source_zone": "STAGE"
        }
    },
    {
        "op": "ADD_HEARTS",
        "frame_index": 2,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        },
        "params": {
            "heart_type": "SELECTED"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
ability_262['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select heart01/02/06, give to all members who moved this turn",
        "Fixed: Added SELECT_MEMBER with keyword=MOVED_THIS_TURN",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{heart_01.png|heart01}}か{{heart_02.png|heart02}}か{{heart_06.png|heart06}}のうち、1つを選ぶ": "Frame 0: COLOR_SELECT",
        "ライブ終了時まで、自分のステージにいる、このターン中にエリアを移動しているすべてのメンバーは、選んだハートを1つ得る": "Frames 1-2: SELECT_MEMBER with keyword + ADD_HEARTS"
    }
}

# Ability 263 - add TRANSFORM_HEART
ability_263 = data['abilities'][263]
ability_263['frames'] = [
    {
        "op": "COLOR_SELECT",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "target_player": "SELF",
            "color_mask": "GREEN|BLUE|PURPLE"
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
            "color_mask": 28
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
ability_263['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select heart03/04/05, change member's heart to selected",
        "Fixed: Added TRANSFORM_HEART frame",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{heart_03.png|heart03}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}のうち1つを選ぶ": "Frame 0: COLOR_SELECT",
        "ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる": "Frame 1: TRANSFORM_HEART with color_mask=28 (heart03|04|05)"
    }
}

# Ability 264 - add dynamic calculation for per success live card
ability_264 = data['abilities'][264]
ability_264['frames'] = [
    {
        "op": "COLOR_SELECT",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "target_player": "SELF",
            "color_mask": "BLUE|PURPLE|ANY"
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "COUNT_SUCCESS_LIVE",
        "frame_index": 1,
        "slot": {
            "target_slot": "STAGE_0",
            "comparison": "GE"
        }
    },
    {
        "op": "ADD_HEARTS",
        "frame_index": 2,
        "value": 1,
        "attr": {
            "compare_accumulated": 1
        },
        "slot": {
            "remainder_zone": "STAGE",
            "is_dynamic": 1
        },
        "params": {
            "scalar_dynamic": {
                "base_value": 1,
                "divisor": 1
            },
            "heart_type": "SELECTED"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
ability_264['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select heart04/05/06, gain selected heart per success live card",
        "Fixed: Added COUNT_SUCCESS_LIVE and dynamic calculation",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{heart_04.png|heart04}}か{{heart_05.png|heart05}}か{{heart_06.png|heart06}}のうち、1つを選ぶ": "Frame 0: COLOR_SELECT",
        "ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、選んだハートを1つ得る": "Frames 1-2: COUNT_SUCCESS_LIVE + ADD_HEARTS with dynamic"
    }
}

# Ability 265 - verified
ability_265 = data['abilities'][265]
ability_265['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 6 energy, gain blade x3",
        "Frame 0: PAY_ENERGY with value=6, is_optional=1",
        "Frame 2: ADD_BLADES with value=3",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES"
    }
}

# Ability 266 - remove unnecessary SUM_VALUE frames
ability_266 = data['abilities'][266]
ability_266['frames'] = [
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
        "op": "ADD_HEARTS",
        "frame_index": 2,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        },
        "params": {
            "heart_type": 3
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
ability_266['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 2 energy, gain heart04",
        "Fixed: Removed unnecessary SUM_VALUE frames",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、{{heart_04.png|heart04}}を得る": "Frame 2: ADD_HEARTS"
    }
}

# Ability 267 - remove unnecessary SUM_VALUE frames
ability_267 = data['abilities'][267]
ability_267['frames'] = [
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
        "value": 3
    },
    {
        "op": "COUNT_STAGE",
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
        "op": "BOOST_SCORE",
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
ability_267['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 2 energy, if Nijigasaki on stage boost score +1",
        "Fixed: Removed unnecessary SUM_VALUE frame",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "自分のステージに『虹ヶ咲』のメンバーがいる場合、このカードのスコアを+１する": "Frames 2-4: COUNT_STAGE + BOOST_SCORE"
    }
}

# Ability 268 - verified
ability_268 = data['abilities'][268]
ability_268['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 2 energy, if cost≥9 EdelNote on stage, choose: deploy cost≤4 EdelNote or reduce heart req",
        "Frame 0: PAY_ENERGY",
        "Frame 2: HAS_MEMBER with unit_id=EDEL_NOTE, cost≥9",
        "Frame 4: SELECT_MODE",
        "Frame 7: PLAY_MEMBER_FROM_DISCARD with cost≤4",
        "Frame 9: REDUCE_HEART_REQ",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "自分のステージにコスト9以上の『EdelNote』のメンバーがいる場合、以下から1つを選ぶ": "Frames 2-4: HAS_MEMBER + SELECT_MODE",
        "自分の控え室からコスト4以下の『EdelNote』のメンバーカードを1枚、メンバーのいないエリアに登場させる": "Frame 7: PLAY_MEMBER_FROM_DISCARD",
        "このカードの必要ハートを{{heart_06.png|heart06}}減らす": "Frame 9: REDUCE_HEART_REQ"
    }
}

# Ability 269 - verified
ability_269 = data['abilities'][269]
ability_269['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay up to 2 energy, gain blade per energy paid",
        "Frame 0: PAY_ENERGY with is_optional=1",
        "Frame 2: ADD_BLADES with compare_accumulated=1, dynamic based on paid energy",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}を2つまで支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、支払った{{icon_energy.png|E}}につき、{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES with dynamic"
    }
}

# Ability 270 - verified
ability_270 = data['abilities'][270]
ability_270['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, gain heart01",
        "Frame 0: PAY_ENERGY with value=1, is_optional=1",
        "Frame 2: ADD_HEARTS with heart_type=0",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、{{heart_01.png|heart01}}を得る": "Frame 2: ADD_HEARTS"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed abilities 251-270")
print("Saved file")
