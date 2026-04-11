import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Fixing abilities 271-300...")

# First, fix the mismatched frame_verification entries from abilities 267-270
# Ability 267 - correct frame_verification
ability_267 = data['abilities'][267]
ability_267['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 2 energy, if Nijigasaki on stage boost score +1",
        "Fixed: Corrected mismatched frame_verification",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "自分のステージに『虹ヶ咲』のメンバーがいる場合、このカードのスコアを+１する": "Frames 2-4: COUNT_STAGE + BOOST_SCORE"
    }
}

# Ability 268 - correct frame_verification
ability_268 = data['abilities'][268]
ability_268['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay up to 2 energy, gain blade per energy paid",
        "Fixed: Corrected mismatched frame_verification",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}を2つまで支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、支払った{{icon_energy.png|E}}につき、{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES with dynamic"
    }
}

# Ability 269 - correct frame_verification
ability_269 = data['abilities'][269]
ability_269['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, gain heart01",
        "Fixed: Corrected mismatched frame_verification",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、{{heart_01.png|heart01}}を得る": "Frame 2: ADD_HEARTS"
    }
}

# Ability 270 - correct frame_verification
ability_270 = data['abilities'][270]
ability_270['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, gain heart02",
        "Fixed: Corrected mismatched frame_verification",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、{{heart_02.png|heart02}}を得る": "Frame 2: ADD_HEARTS"
    }
}

# Ability 271 - verified
ability_271 = data['abilities'][271]
ability_271['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, non-self Hasunosora member gains heart01 + blade",
        "Frame 0: PAY_ENERGY",
        "Frame 2: SELECT_MEMBER with group_id=HASUNOSORA, special_id=Not Self",
        "Frames 3-4: ADD_HEARTS + ADD_BLADES",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、自分のステージにいるこのメンバー以外の『蓮ノ空』のメンバー1人は、{{heart_01.png|heart01}}{{icon_blade.png|ブレード}}を得る": "Frames 2-4: SELECT_MEMBER + ADD_HEARTS + ADD_BLADES"
    }
}

# Ability 272 - remove unnecessary SUM_VALUE frames
ability_272 = data['abilities'][272]
ability_272['frames'] = [
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
        "value": 2
    },
    {
        "op": "SELECT_MEMBER",
        "frame_index": 2,
        "value": 99,
        "attr": {
            "target_player": "SELF",
            "group_enabled": 1,
            "group_id": "NIJIGASAKI",
            "special_id": "Not Self"
        },
        "slot": {
            "target_slot": "CONTEXT",
            "source_zone": "STAGE"
        }
    },
    {
        "op": "ADD_BLADES",
        "frame_index": 3,
        "value": 1,
        "slot": {
            "target_slot": "STAGE_1"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 4
    }
]
ability_272['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, other Nijigasaki members gain blade",
        "Fixed: Removed unnecessary SUM_VALUE frames",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "ライブ終了時まで、自分のステージにいるほかの『虹ヶ咲』のメンバーは{{icon_blade.png|ブレード}}を得る": "Frames 2-3: SELECT_MEMBER + ADD_BLADES"
    }
}

# Ability 273 - verified
ability_273 = data['abilities'][273]
ability_273['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, if Hasunosora member + 2+ members with unique unit names, boost score",
        "Frame 0: PAY_ENERGY",
        "Frame 2: HAS_MEMBER with group_id=HASUNOSORA",
        "Frame 3: COUNT_STAGE with value=2",
        "Frame 4: NOP with raw_cond=UNIQUE_UNIT_NAMES_COUNT, MIN=2",
        "Frame 6: BOOST_SCORE",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY",
        "自分のステージに『蓮ノ空』のメンバー1人を含むメンバーが2人以上おり、かつそれらのメンバーのユニット名がそれぞれ異なる場合": "Frames 2-4: HAS_MEMBER + COUNT_STAGE + NOP check",
        "このカードのスコアを+１する": "Frame 6: BOOST_SCORE"
    }
}

# Ability 274 - fix NOP frame for "1st turn live phase"
ability_274 = data['abilities'][274]
ability_274['frames'][0] = {
    "op": "NOP",
    "frame_index": 0,
    "params": {
        "raw_cond": "FIRST_TURN_LIVE_PHASE"
    }
}
ability_274['frame_verification'] = {
    "verified": True,
    "notes": [
        "If 1st turn live phase, boost score +1, Nijigasaki member gains blade",
        "Fixed: Added raw_cond=FIRST_TURN_LIVE_PHASE to NOP",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "このゲームの1ターン目のライブフェイズの場合": "Frame 0: NOP with raw_cond=FIRST_TURN_LIVE_PHASE",
        "このカードのスコアを+１し": "Frame 2: BOOST_SCORE",
        "ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}を得る": "Frame 3: ADD_BLADES with group_id=NIJIGASAKI"
    }
}

# Ability 275 - verified
ability_275 = data['abilities'][275]
ability_275['frame_verification'] = {
    "verified": True,
    "notes": [
        "If Nijigasaki effect activated energy this turn, boost +1. If also activated member, boost +2 instead",
        "Frame 0: HAS_KEYWORD with group_id=NIJIGASAKI, keyword_energy=1",
        "Frame 3: HAS_KEYWORD with group_id=NIJIGASAKI, keyword_member=1",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "このターン、自分の『虹ヶ咲』のカードの効果によってウェイト状態の自分のエネルギーをアクティブにしていた場合": "Frame 0: HAS_KEYWORD with keyword_energy",
        "このカードのスコアを+１する": "Frame 2: BOOST_SCORE",
        "さらに、自分の『虹ヶ咲』のカードの効果によって自分のステージにいるウェイト状態のメンバーもアクティブにしていた場合、代わりにスコアを+２する": "Frames 3-5: HAS_KEYWORD + BOOST_SCORE with value=2"
    }
}

# Ability 276 - verified
ability_276 = data['abilities'][276]
ability_276['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional tap self, center area μ's members gain blade x2",
        "Frame 0: SET_TAPPED with is_optional=1",
        "Frame 2: SELECT_MEMBER with area_idx=2 (center)",
        "Frame 3: ADD_BLADES with value=2",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "このメンバーをウェイトにしてもよい": "Frame 0: SET_TAPPED",
        "ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frames 2-3: SELECT_MEMBER with area_idx=2 + ADD_BLADES"
    }
}

# Ability 277 - fix MOVE_MEMBER to SET_TAPPED and add center area filter
ability_277 = data['abilities'][277]
ability_277['frames'] = [
    {
        "op": "SET_TAPPED",
        "frame_index": 0,
        "value": 1,
        "attr": {
            "is_optional": 1
        },
        "slot": {
            "target_slot": "CONTEXT"
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
        "attr": {
            "target_player": "SELF",
            "group_enabled": 1
        },
        "slot": {
            "target_slot": "CONTEXT",
            "area_idx": 2
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
ability_277['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional tap self, center area μ's members gain blade",
        "Fixed: Changed MOVE_MEMBER to SET_TAPPED, added area_idx=2 to ADD_BLADES",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "このメンバーをウェイトにしてもよい": "Frame 0: SET_TAPPED",
        "ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES with area_idx=2"
    }
}

# Ability 278 - verified
ability_278 = data['abilities'][278]
ability_278['frame_verification'] = {
    "verified": True,
    "notes": [
        "If active energy exists, boost score +1",
        "Frame 0: COUNT_ENERGY",
        "Frame 2: BOOST_SCORE",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "アクティブ状態の自分のエネルギーがある場合、このカードのスコアを+１する": "Frames 0-2: COUNT_ENERGY + BOOST_SCORE"
    }
}

# Ability 279 - verified
ability_279 = data['abilities'][279]
ability_279['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional draw 1, then put 2 from hand on deck top",
        "Frame 0: DRAW with is_optional=1",
        "Frames 1-2: SELECT_CARDS + MOVE_TO_DECK to DECK_TOP",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "カードを1枚引いてもよい": "Frame 0: DRAW",
        "そうした場合、手札2枚を好きな順番でデッキの上に置く": "Frames 1-2: SELECT_CARDS + MOVE_TO_DECK"
    }
}

# Ability 280 - verified
ability_280 = data['abilities'][280]
ability_280['frame_verification'] = {
    "verified": True,
    "notes": [
        "Transform pink/red/yellow/green/purple/ALL blades to blue",
        "Frame 0: TRANSFORM_COLOR with value=4 (blue)",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "ライブ終了時まで、エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[紫ブレード]、{{icon_b_all.png|ALLブレード}}は、すべて[青ブレード]になる": "Frame 0: TRANSFORM_COLOR"
    }
}

# Ability 281 - verified
ability_281 = data['abilities'][281]
ability_281['frame_verification'] = {
    "verified": True,
    "notes": [
        "Transform pink/red/yellow/green/blue/ALL blades to purple",
        "Frame 0: TRANSFORM_COLOR with value=5 (purple)",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "ライブ終了時まで、エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、{{icon_b_all.png|ALLブレード}}は、すべて[紫ブレード]になる": "Frame 0: TRANSFORM_COLOR"
    }
}

# Ability 282 - verified
ability_282 = data['abilities'][282]
ability_282['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select Kanon/Margarete/Tomari, and other Liella member, both gain blade",
        "Frame 0: SELECT_MEMBER with char_ids",
        "Frame 1: SELECT_MEMBER with group_id=LIELLA, special_id=Not Selected",
        "Frames 2-3: ADD_BLADES x2",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "自分のステージにいる、「澁谷かのん」「ウィーン・マルガレーテ」「鬼塚冬毬」のうちのメンバー1人と": "Frame 0: SELECT_MEMBER",
        "これにより選んだメンバー以外の『Liella!』のメンバー1人は、{{icon_blade.png|ブレード}}を得る": "Frames 1-3: SELECT_MEMBER + ADD_BLADES x2"
    }
}

# Ability 283 - add keyword filter for "moved this turn"
ability_283 = data['abilities'][283]
ability_283['frames'] = [
    {
        "op": "SELECT_MEMBER",
        "frame_index": 0,
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
        "op": "ADD_BLADES",
        "frame_index": 1,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 2
    }
]
ability_283['frame_verification'] = {
    "verified": True,
    "notes": [
        "Members who moved this turn gain blade",
        "Fixed: Added keyword=MOVED_THIS_TURN to SELECT_MEMBER",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "ライブ終了時まで、自分のステージにいる、このターン中にエリアを移動したメンバーは{{icon_blade.png|ブレード}}を得る": "Frames 0-1: SELECT_MEMBER with keyword + ADD_BLADES"
    }
}

# Ability 284 - verified
ability_284 = data['abilities'][284]
ability_284['frame_verification'] = {
    "verified": True,
    "notes": [
        "Kanon gains heart05+blade, Keke gains heart01+blade",
        "Frame 0: SELECT_MEMBER with char_id=KANON",
        "Frames 1-2: ADD_HEARTS(heart05) + ADD_BLADES",
        "Frame 3: SELECT_MEMBER with char_id=KEKE",
        "Frames 4-5: ADD_HEARTS(heart01) + ADD_BLADES",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "自分のステージにいる「澁谷かのん」1人は{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を": "Frames 0-2: SELECT_MEMBER(KANON) + ADD_HEARTS + ADD_BLADES",
        "「唐可可」1人は{{heart_01.png|heart01}}{{icon_blade.png|ブレード}}を得る": "Frames 3-5: SELECT_MEMBER(KEKE) + ADD_HEARTS + ADD_BLADES"
    }
}

# Ability 285 - verified
ability_285 = data['abilities'][285]
ability_285['frame_verification'] = {
    "verified": True,
    "notes": [
        "Aqours members gain blade",
        "Frame 0: ADD_BLADES with group_id=AQOURS",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "ライブ終了時まで、自分のステージにいる『Aqours』のメンバーは{{icon_blade.png|ブレード}}を得る": "Frame 0: ADD_BLADES"
    }
}

# Ability 286 - verified
ability_286 = data['abilities'][286]
ability_286['frame_verification'] = {
    "verified": True,
    "notes": [
        "μ's member gains blade",
        "Frame 0: ADD_BLADES with group_id=MUSE",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、{{icon_blade.png|ブレード}}を得る": "Frame 0: ADD_BLADES"
    }
}

# Ability 287 - verified
ability_287 = data['abilities'][287]
ability_287['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select Hasunosora member, transform all hearts to heart01",
        "Frame 0: SELECT_MEMBER with group_id=HASUNOSORA",
        "Frame 1: TRANSFORM_HEART with color_mask=1 (heart01)",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "ライブ終了時まで、自分のステージにいる『蓮ノ空』のメンバー1人が元々持つハートをすべて{{heart_01.png|heart01}}にする": "Frames 0-1: SELECT_MEMBER + TRANSFORM_HEART"
    }
}

# Ability 288 - verified
ability_288 = data['abilities'][288]
ability_288['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select center area Liella member, blades become 3",
        "Frame 0: SELECT_MEMBER with group_id=LIELLA, area_idx=2",
        "Frame 1: TRANSFORM_BLADES with value=3",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つ{{icon_blade.png|ブレード}}の数は3つになる": "Frames 0-1: SELECT_MEMBER + TRANSFORM_BLADES"
    }
}

# Ability 289 - verified
ability_289 = data['abilities'][289]
ability_289['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard Ayumu/Kanon/Kaho (any 3), gain constant boost score +3",
        "Frame 0: MOVE_TO_DISCARD with char_ids, value=3, is_optional=1",
        "Frame 2: BOOST_SCORE with value=3",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "手札の「上原歩夢」と「澁谷かのん」と「日野下花帆」を、好きな組み合わせで合計3枚、控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+３する。」を得る": "Frame 2: BOOST_SCORE"
    }
}

# Ability 290 - fix source_zone from DISCARD to HAND
ability_290 = data['abilities'][290]
ability_290['frames'][0]['slot']['source_zone'] = 'HAND'
ability_290['frames'][0]['slot']['target_slot'] = 'CONTEXT'
ability_290['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard You/Natsumi/Rurino (any), gain blade per discarded",
        "Fixed: Changed source_zone from DISCARD to HAND",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "手札の「渡辺曜」と「鬼塚夏美」と「大沢瑠璃乃」を、好きな枚数控え室に置いてもよい": "Frame 0: SELECT_CARDS from HAND",
        "ライブ終了時まで、これによって控え室に置いた枚数1枚につき、{{icon_blade.png|ブレード}}を得る": "Frames 2-4: SUM_VALUE + ADD_BLADES with dynamic"
    }
}

# Ability 291 - remove unnecessary SUM_VALUE frames
ability_291 = data['abilities'][291]
ability_291['frames'] = [
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
        "op": "COLOR_SELECT",
        "frame_index": 2,
        "value": 1,
        "attr": {
            "target_player": "SELF",
            "color_mask": "RED|GREEN|ANY"
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "ADD_HEARTS",
        "frame_index": 3,
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
        "frame_index": 4
    }
]
ability_291['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 1, select heart01/03/06, gain selected",
        "Fixed: Removed unnecessary SUM_VALUE frames",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、選んだハートを1つ得る": "Frames 2-3: COLOR_SELECT + ADD_HEARTS"
    }
}

# Ability 292 - remove unnecessary SUM_VALUE frames
ability_292 = data['abilities'][292]
ability_292['frames'] = [
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
ability_292['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 1, gain blade x2",
        "Fixed: Removed unnecessary SUM_VALUE frames",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES"
    }
}

# Ability 293 - verified
ability_293 = data['abilities'][293]
ability_293['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 1, discard top 3, recover A-RISE member to hand",
        "Frame 0: MOVE_TO_DISCARD from HAND",
        "Frame 2: MOVE_TO_DISCARD from DECK_TOP",
        "Frame 3: RECOVER_MEMBER with group_id=ARISE",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "自分のデッキの上からカードを3枚控え室に置く。その後、自分の控え室から『A-RISE』のメンバーカードを1枚手札に加える": "Frames 2-3: MOVE_TO_DISCARD + RECOVER_MEMBER"
    }
}

# Ability 294 - remove unnecessary SUM_VALUE frames
ability_294 = data['abilities'][294]
ability_294['frames'] = [
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
        "op": "ADD_BLADES",
        "frame_index": 2,
        "value": 5,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
ability_294['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 2, gain blade x5",
        "Fixed: Removed unnecessary SUM_VALUE frames",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "手札を2枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES"
    }
}

# Ability 295 - verified
ability_295 = data['abilities'][295]
ability_295['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 2, select member, gain blade x3",
        "Frame 0: MOVE_TO_DISCARD",
        "Frame 2: SELECT_MEMBER",
        "Frame 3: ADD_BLADES with value=3",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "手札を2枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frames 2-3: SELECT_MEMBER + ADD_BLADES"
    }
}

# Ability 296 - fix NOP check to properly check if added card was Hasunosora
ability_296 = data['abilities'][296]
ability_296['frames'][4] = {
    "op": "NOP",
    "frame_index": 4,
    "params": {
        "raw_cond": "ADDED_CARD_GROUP_HASUNOSORA"
    }
}
ability_296['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 2, look at top 5, optionally add member to hand. If Hasunosora added, gain heart05+blade",
        "Fixed: Changed NOP check to verify added card was Hasunosora",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "手札を2枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD",
        "自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい": "Frames 2-3: LOOK_DECK + ADD_TO_HAND",
        "これにより『蓮ノ空』のカードを手札に加えた場合、ライブ終了時まで、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る": "Frames 4-7: NOP check + ADD_HEARTS + ADD_BLADES"
    }
}

# Ability 297 - verified
ability_297 = data['abilities'][297]
ability_297['frame_verification'] = {
    "verified": True,
    "notes": [
        "Ask opponent to choose, effects based on choice",
        "Frame 0: SELECT_MODE with is_opponent=1",
        "Frames 3-4: DRAW x2",
        "Frames 6-7: ADD_BLADES x2 (self + opponent)",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "相手に何が好き？と聞く": "Frame 0: SELECT_MODE with is_opponent=1",
        "回答があなたの場合、自分と相手はカードを1枚引く": "Frames 3-4: DRAW x2",
        "回答がそれ以外の場合、ライブ終了時まで、自分と相手のステージにいるメンバーは{{icon_blade.png|ブレード}}を得る": "Frames 6-7: ADD_BLADES x2"
    }
}

# Ability 298 - verified
ability_298 = data['abilities'][298]
ability_298['frame_verification'] = {
    "verified": True,
    "notes": [
        "If self has member with higher cost than all opponent members, gain blade x2",
        "Frame 0: HAS_MEMBER with target_player=OPPONENT",
        "Frame 2: ADD_BLADES with value=2",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "相手のステージにいるすべてのメンバーのそれぞれのコストよりコストが高いメンバーが自分のステージにいる場合": "Frame 0: HAS_MEMBER",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES"
    }
}

# Ability 299 - verified
ability_299 = data['abilities'][299]
ability_299['frame_verification'] = {
    "verified": True,
    "notes": [
        "If opponent has tapped member, reduce heart req by 2",
        "Frame 0: SELECT_MEMBER with target_player=OPPONENT, is_tapped=1",
        "Frame 2: REDUCE_HEART_REQ with value=2",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "相手のステージにウェイト状態のメンバーがいる場合": "Frame 0: SELECT_MEMBER with is_tapped=1",
        "このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}減らす": "Frame 2: REDUCE_HEART_REQ"
    }
}

# Ability 300 - verified
ability_300 = data['abilities'][300]
ability_300['frame_verification'] = {
    "verified": True,
    "notes": [
        "If 2+ success live cards AND 3+ unique name members, boost score +1",
        "Frame 0: COUNT_SUCCESS_LIVE with value=2",
        "Frame 1: NOP with value=3 (unique name check)",
        "Frame 3: BOOST_SCORE",
        "1 card shares this pattern"
    ],
    "text_mapping": {
        "自分か相手の成功ライブカード置き場にカードが2枚以上あり": "Frame 0: COUNT_SUCCESS_LIVE",
        "かつ自分のステージに名前の異なるメンバーが3人以上いる場合": "Frame 1: NOP with unique name check",
        "このカードのスコアを+１する": "Frame 3: BOOST_SCORE"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed abilities 271-300")
print("Saved file")
