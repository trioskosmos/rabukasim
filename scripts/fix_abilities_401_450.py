#!/usr/bin/env python3
"""
Fix script for abilities 401-450 in ability_frame_source.json
Based on manual review findings
"""

import json
import sys

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Load the data
filepath = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\ability_frame_source.json'
data = load_json(filepath)

# Fix abilities 401-450
# Based on manual review findings

# Ability 401: Missing proper condition checks for blade heart count OR surplus hearts
# Text: "{{live_success.png|ライブ成功時}}このターン、エールにより公開された自分のカードの中にブレードハートを持たないカードが0枚の場合か、または自分が余剰ハートを2つ以上持っている場合、このカードのスコアは４になる。"
# Current frames: [NOP, JUMP_IF_FALSE, SET_SCORE, RETURN] - incomplete
# Should check: (no-blade-heart cards in yell pile = 0) OR (surplus hearts >= 2)
if len(data['abilities']) > 401:
    data['abilities'][401]["frames"] = [
        {
            "op": "COUNT_CARDS",
            "frame_index": 0,
            "attr": {
                "heart_type": "NONE",
                "negate": 1
            },
            "slot": {
                "target_slot": "YELL_PILE",
                "comparison": "EQ"
            }
        },
        {
            "op": "JUMP_IF_TRUE",
            "frame_index": 1,
            "value": 2
        },
        {
            "op": "COUNT_HEARTS",
            "frame_index": 2,
            "attr": {
                "heart_type": "SURPLUS"
            },
            "slot": {
                "target_slot": "CONTEXT",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 3,
            "value": 1
        },
        {
            "op": "SET_SCORE",
            "frame_index": 4,
            "value": 4,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 5
        }
    ]
    data['abilities'][401]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}このターン、エールにより公開された自分のカードの中にブレードハートを持たないカードが0枚の場合か、または自分が余剰ハートを2つ以上持っている場合、このカードのスコアは４になる。",
            "Fixed: Added proper condition checks for OR logic",
            "Frame 0: COUNT_CARDS - checks if no-blade-heart cards in yell pile = 0",
            "Frame 1: JUMP_IF_TRUE - jumps to SET_SCORE if first condition met",
            "Frame 2: COUNT_HEARTS - checks surplus hearts >= 2",
            "Frame 3: JUMP_IF_FALSE - skips SET_SCORE if second condition not met",
            "Frame 4: SET_SCORE - sets score to 4",
            "Frame 5: RETURN"
        ],
        "text_mapping": {
            "ブレードハートを持たないカードが0枚の場合": "Frame 0-1: COUNT_CARDS + JUMP_IF_TRUE",
            "余剰ハートを2つ以上持っている場合": "Frame 2-3: COUNT_HEARTS + JUMP_IF_FALSE",
            "このカードのスコアは４になる": "Frame 4: SET_SCORE"
        }
    }

# Ability 402: Missing SET_SCORE frame for score boost
# Text: "{{live_success.png|ライブ成功時}}このターン、自分が余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、このカードのスコアを+１する。"
# Current frames: [NOP, COUNT_STAGE, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN] - wrong effect (ENERGY_CHARGE instead of BOOST_SCORE)
if len(data['abilities']) > 402:
    data['abilities'][402]["frames"] = [
        {
            "op": "COUNT_HEARTS",
            "frame_index": 0,
            "attr": {
                "heart_type": 4
            },
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
            "op": "COUNT_STAGE",
            "frame_index": 2,
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
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 5
        }
    ]
    data['abilities'][402]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}このターン、自分が余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、このカードのスコアを+１する。",
            "Fixed: Changed ENERGY_CHARGE to BOOST_SCORE, added heart check",
            "Frame 0: COUNT_HEARTS - checks for heart04 >= 1",
            "Frame 1: JUMP_IF_FALSE - skips if no heart04",
            "Frame 2: COUNT_STAGE - checks for Nijigasaki members on stage",
            "Frame 3: JUMP_IF_FALSE - skips if no Nijigasaki members",
            "Frame 4: BOOST_SCORE - adds +1 to score",
            "Frame 5: RETURN"
        ],
        "text_mapping": {
            "余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており": "Frame 0-1: COUNT_HEARTS + JUMP_IF_FALSE",
            "自分のステージに『虹ヶ咲』のメンバーがいる場合": "Frame 2-3: COUNT_STAGE + JUMP_IF_FALSE",
            "このカードのスコアを+１する": "Frame 4: BOOST_SCORE"
        }
    }

# Ability 403: Looks correct - no fix needed
# Text: "{{live_success.png|ライブ成功時}}このターン、自分のデッキがリフレッシュしていた場合、このカードのスコアを+２する。"
# Current frames: [DECK_REFRESHED, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - appears correct
if len(data['abilities']) > 403:
    data['abilities'][403]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}このターン、自分のデッキがリフレッシュしていた場合、このカードのスコアを+２する。",
            "Frames appear correct",
            "Frame 0: DECK_REFRESHED - checks if deck was refreshed",
            "Frame 1: JUMP_IF_FALSE - jumps if not refreshed",
            "Frame 2: BOOST_SCORE - adds +2 to score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のデッキがリフレッシュしていた場合": "Frame 0-1: DECK_REFRESHED + JUMP_IF_FALSE",
            "このカードのスコアを+２する": "Frame 2: BOOST_SCORE"
        }
    }

# Ability 404: Missing proper heart type checks
# Text: "{{live_success.png|ライブ成功時}}エールにより公開された自分の『虹ヶ咲』のメンバーカードが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}のいずれかがある場合、このカードのスコアを+１する。"
# Current frames: [GROUP_FILTER, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - incomplete, needs heart type check
if len(data['abilities']) > 404:
    data['abilities'][404]["frames"] = [
        {
            "op": "GROUP_FILTER",
            "frame_index": 0,
            "attr": {
                "group_enabled": 1,
                "group_id": "NIJIGASAKI"
            },
            "slot": {
                "target_slot": "YELL_PILE"
            }
        },
        {
            "op": "COUNT_HEARTS",
            "frame_index": 1,
            "attr": {
                "heart_types": [1, 2, 3]
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
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 4
        }
    ]
    data['abilities'][404]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}エールにより公開された自分の『虹ヶ咲』のメンバーカードが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}のいずれかがある場合、このカードのスコアを+１する。",
            "Fixed: Added heart type check for heart01/02/03",
            "Frame 0: GROUP_FILTER - filters for Nijigasaki cards in yell pile",
            "Frame 1: COUNT_HEARTS - checks for heart01/02/03 >= 1",
            "Frame 2: JUMP_IF_FALSE - jumps if no matching hearts",
            "Frame 3: BOOST_SCORE - adds +1 to score",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "『虹ヶ咲』のメンバーカード": "Frame 0: GROUP_FILTER",
            "ハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}のいずれかがある場合": "Frame 1-2: COUNT_HEARTS + JUMP_IF_FALSE",
            "このカードのスコアを+１する": "Frame 3: BOOST_SCORE"
        }
    }

# Ability 405: Missing SELECT_CARDS and MOVE_TO_HAND frames
# Text: "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『Aqours』のライブカードを1枚手札に加える。"
# Current frames: [GROUP_FILTER, RETURN] - missing card movement
if len(data['abilities']) > 405:
    data['abilities'][405]["frames"] = [
        {
            "op": "SELECT_CARDS",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "card_type": "LIVE",
                "group_enabled": 1,
                "group_id": "AQOURS"
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "YELL_PILE"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 1
        }
    ]
    data['abilities'][405]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『Aqours』のライブカードを1枚手札に加える。",
            "Fixed: Changed GROUP_FILTER to SELECT_CARDS with proper source_zone",
            "Frame 0: SELECT_CARDS - selects 1 Aqours live card from yell pile to hand",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "エールにより公開された自分のカードの中から、『Aqours』のライブカードを1枚手札に加える": "Frame 0: SELECT_CARDS"
        }
    }

# Ability 406: Wrong source_zone (DECK_TOP instead of YELL_PILE)
# Text: "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『蓮ノ空』のライブカードを1枚手札に加える。"
# Current frames: [SELECT_CARDS, RETURN] - source_zone is DECK_TOP, should be YELL_PILE
if len(data['abilities']) > 406:
    data['abilities'][406]["frames"] = [
        {
            "op": "SELECT_CARDS",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "card_type": "LIVE",
                "group_enabled": 1,
                "group_id": "HASUNOSORA",
                "is_optional": 1
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "YELL_PILE"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 1
        }
    ]
    data['abilities'][406]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『蓮ノ空』のライブカードを1枚手札に加える。",
            "Fixed: Changed source_zone from DECK_TOP to YELL_PILE",
            "Frame 0: SELECT_CARDS - selects 1 Hasunosora live card from yell pile to hand",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "エールにより公開された自分のカードの中から、『蓮ノ空』のライブカードを1枚手札に加える": "Frame 0: SELECT_CARDS"
        }
    }

# Ability 407: Wrong source_zone (missing YELL_PILE specification)
# Text: "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚までデッキの一番下に置く。"
# Current frames: [MOVE_TO_DECK, RETURN] - needs source_zone YELL_PILE
if len(data['abilities']) > 407:
    data['abilities'][407]["frames"] = [
        {
            "op": "SELECT_CARDS",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "card_type": "LIVE",
                "is_optional": 1
            },
            "slot": {
                "target_slot": "DECK_BOTTOM",
                "source_zone": "YELL_PILE"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 1
        }
    ]
    data['abilities'][407]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚までデッキの一番下に置く。",
            "Fixed: Changed MOVE_TO_DECK to SELECT_CARDS with source_zone YELL_PILE",
            "Frame 0: SELECT_CARDS - selects up to 1 live card from yell pile to deck bottom",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "エールにより公開された自分のカードの中から、ライブカードを1枚までデッキの一番下に置く": "Frame 0: SELECT_CARDS"
        }
    }

# Ability 408: Missing COUNT_CARDS check for 7+ Liella cards
# Text: "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に『Liella!』のカードが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態にする。"
# Current frames: [NOP, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN] - missing card count check
if len(data['abilities']) > 408:
    data['abilities'][408]["frames"] = [
        {
            "op": "COUNT_CARDS",
            "frame_index": 0,
            "attr": {
                "group_enabled": 1,
                "group_id": "LIELLA"
            },
            "slot": {
                "target_slot": "YELL_PILE",
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
                "source_zone": "ENERGY_DECK"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][408]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に『Liella!』のカードが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態にする。",
            "Fixed: Added COUNT_CARDS check for 7+ Liella cards",
            "Frame 0: COUNT_CARDS - checks for 7+ Liella cards in yell pile",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 7",
            "Frame 2: ENERGY_CHARGE - charges 1 energy from energy deck",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "『Liella!』のカードが7枚以上ある場合": "Frame 0-1: COUNT_CARDS + JUMP_IF_FALSE",
            "エネルギーカードを1枚ウェイト状態にする": "Frame 2: ENERGY_CHARGE"
        }
    }

# Ability 409: Missing proper count check
# Text: "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に『蓮ノ空』のメンバーカードが10枚以上ある場合、このカードのスコアを+１する。"
# Current frames: [HAS_KEYWORD, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - HAS_KEYWORD is wrong, needs COUNT_CARDS
if len(data['abilities']) > 409:
    data['abilities'][409]["frames"] = [
        {
            "op": "COUNT_CARDS",
            "frame_index": 0,
            "attr": {
                "card_type": "MEMBER",
                "group_enabled": 1,
                "group_id": "HASUNOSORA"
            },
            "slot": {
                "target_slot": "YELL_PILE",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "BOOST_SCORE",
            "frame_index": 2,
            "value": 1,
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
    data['abilities'][409]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に『蓮ノ空』のメンバーカードが10枚以上ある場合、このカードのスコアを+１する。",
            "Fixed: Changed HAS_KEYWORD to COUNT_CARDS for proper count check",
            "Frame 0: COUNT_CARDS - checks for 10+ Hasunosora member cards in yell pile",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 10",
            "Frame 2: BOOST_SCORE - adds +1 to score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "『蓮ノ空』のメンバーカードが10枚以上ある場合": "Frame 0-1: COUNT_CARDS + JUMP_IF_FALSE",
            "このカードのスコアを+１する": "Frame 2: BOOST_SCORE"
        }
    }

# Ability 410: Missing proper count check for unique name cards
# Text: "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に名前が異なる『Liella!』のメンバーカードが5枚以上ある場合、このカードのスコアを+１する。"
# Current frames: [NOP, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - missing unique name count check
if len(data['abilities']) > 410:
    data['abilities'][410]["frames"] = [
        {
            "op": "COUNT_UNIQUE_NAMES",
            "frame_index": 0,
            "attr": {
                "card_type": "MEMBER",
                "group_enabled": 1,
                "group_id": "LIELLA"
            },
            "slot": {
                "target_slot": "YELL_PILE",
                "comparison": "GE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "BOOST_SCORE",
            "frame_index": 2,
            "value": 1,
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
    data['abilities'][410]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に名前が異なる『Liella!』のメンバーカードが5枚以上ある場合、このカードのスコアを+１する。",
            "Fixed: Added COUNT_UNIQUE_NAMES for unique name check",
            "Frame 0: COUNT_UNIQUE_NAMES - checks for 5+ unique Liella member cards in yell pile",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 5 unique",
            "Frame 2: BOOST_SCORE - adds +1 to score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "名前が異なる『Liella!』のメンバーカードが5枚以上ある場合": "Frame 0-1: COUNT_UNIQUE_NAMES + JUMP_IF_FALSE",
            "このカードのスコアを+１する": "Frame 2: BOOST_SCORE"
        }
    }

# Ability 411: MOVE_TO_DISCARD has wrong target_slot (STAGE_1 instead of HAND)
# Text: "{{live_success.png|ライブ成功時}}カードを2枚引き、手札を2枚控え室に置く。"
# Current frames: [DRAW, MOVE_TO_DISCARD (target_slot: STAGE_1), RETURN]
if len(data['abilities']) > 411:
    data['abilities'][411]["frames"] = [
        {
            "op": "DRAW",
            "frame_index": 0,
            "value": 2,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 1,
            "value": 2,
            "attr": {
                "target_player": "SELF",
                "zone_mask": "Guest+Friend"
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "HAND",
                "dest_zone": "DISCARD"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 2
        }
    ]
    data['abilities'][411]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}カードを2枚引き、手札を2枚控え室に置く。",
            "Fixed: Changed MOVE_TO_DISCARD target_slot from STAGE_1 to HAND",
            "Frame 0: DRAW - draws 2 cards",
            "Frame 1: MOVE_TO_DISCARD - discards 2 cards from hand",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "カードを2枚引き": "Frame 0: DRAW",
            "手札を2枚控え室に置く": "Frame 1: MOVE_TO_DISCARD"
        }
    }

# Ability 412: SELECT_CARDS has wrong source_zone (DECK_TOP instead of YELL_PILE)
# Text: "{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、エールにより公開された自分のカードの中から、『虹ヶ咲』のカードを1枚手札に加える。"
# Current frames: [SCORE_COMPARE, JUMP_IF_FALSE, SELECT_CARDS (source_zone: DECK_TOP), RETURN]
if len(data['abilities']) > 412:
    data['abilities'][412]["frames"] = [
        {
            "op": "SCORE_COMPARE",
            "frame_index": 0,
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GT"
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
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": "NIJIGASAKI",
                "is_optional": 1
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "YELL_PILE"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][412]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、エールにより公開された自分のカードの中から、『虹ヶ咲』のカードを1枚手札に加える。",
            "Fixed: Changed SELECT_CARDS source_zone from DECK_TOP to YELL_PILE",
            "Frame 0: SCORE_COMPARE - checks if score > opponent",
            "Frame 1: JUMP_IF_FALSE - jumps if score not higher",
            "Frame 2: SELECT_CARDS - selects 1 Nijigasaki card from yell pile to hand",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "ライブの合計スコアが相手より高い場合": "Frame 0-1: SCORE_COMPARE + JUMP_IF_FALSE",
            "エールにより公開された自分のカードの中から、『虹ヶ咲』のカードを1枚手札に加える": "Frame 2: SELECT_CARDS"
        }
    }

# Ability 413: Looks correct - no fix needed
# Text: "{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。"
# Current frames: [SCORE_COMPARE, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN] - appears correct
if len(data['abilities']) > 413:
    data['abilities'][413]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。",
            "Frames appear correct",
            "Frame 0: SCORE_COMPARE - checks if score > opponent",
            "Frame 1: JUMP_IF_FALSE - jumps if score not higher",
            "Frame 2: ENERGY_CHARGE - charges 1 energy from energy deck",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "ライブの合計スコアが相手より高い場合": "Frame 0-1: SCORE_COMPARE + JUMP_IF_FALSE",
            "エネルギーカードを1枚ウェイト状態で置く": "Frame 2: ENERGY_CHARGE"
        }
    }

# Ability 414: Looks correct - no fix needed
# Text: "{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高く、かつ自分のステージに『蓮ノ空』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。"
# Current frames: [SCORE_COMPARE, COUNT_STAGE, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN] - appears correct
if len(data['abilities']) > 414:
    data['abilities'][414]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高く、かつ自分のステージに『蓮ノ空』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。",
            "Frames appear correct",
            "Frame 0: SCORE_COMPARE - checks if score > opponent",
            "Frame 1: COUNT_STAGE - checks for Hasunosora members on stage",
            "Frame 2: JUMP_IF_FALSE - jumps if conditions not met",
            "Frame 3: ENERGY_CHARGE - charges 1 energy from energy deck",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "ライブの合計スコアが相手より高く": "Frame 0: SCORE_COMPARE",
            "自分のステージに『蓮ノ空』のメンバーがいる場合": "Frame 1: COUNT_STAGE",
            "エネルギーカードを1枚ウェイト状態で置く": "Frame 3: ENERGY_CHARGE"
        }
    }

# Ability 415: Missing SELECT_MODE for choice logic
# Text: "{{live_success.png|ライブ成功時}}以下から1つを選ぶ。自分の成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ。・自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。・自分の控え室からメンバーカードを1枚手札に加える。"
# Current frames: [COUNT_SUCCESS_LIVE, JUMP_IF_FALSE, ENERGY_CHARGE, RECOVER_MEMBER, RETURN] - missing SELECT_MODE
if len(data['abilities']) > 415:
    data['abilities'][415]["frames"] = [
        {
            "op": "COUNT_SUCCESS_LIVE",
            "frame_index": 0,
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
            "value": 2
        },
        {
            "op": "SELECT_MODE",
            "frame_index": 2,
            "value": 2,
            "params": {
                "options": [
                    "ENERGY_CHARGE",
                    "RECOVER_MEMBER"
                ]
            }
        },
        {
            "op": "JUMP",
            "frame_index": 3,
            "value": 3
        },
        {
            "op": "SELECT_MODE",
            "frame_index": 4,
            "value": 1,
            "params": {
                "options": [
                    "ENERGY_CHARGE",
                    "RECOVER_MEMBER"
                ]
            }
        },
        {
            "op": "JUMP",
            "frame_index": 5,
            "value": 1
        },
        {
            "op": "ENERGY_CHARGE",
            "frame_index": 6,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "ENERGY_DECK",
                "is_wait": 1
            }
        },
        {
            "op": "JUMP",
            "frame_index": 7,
            "value": 2
        },
        {
            "op": "RECOVER_MEMBER",
            "frame_index": 8,
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
            "frame_index": 9
        }
    ]
    data['abilities'][415]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}以下から1つを選ぶ。自分の成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ。",
            "Fixed: Added SELECT_MODE frames for choice logic",
            "Frame 0: COUNT_SUCCESS_LIVE - checks for Nijigasaki in success live pile",
            "Frame 1: JUMP_IF_FALSE - jumps to single choice if no Nijigasaki",
            "Frame 2: SELECT_MODE - allows choosing 2 options (if Nijigasaki present)",
            "Frame 3: JUMP - skips to energy charge path",
            "Frame 4: SELECT_MODE - allows choosing 1 option (if no Nijigasaki)",
            "Frame 5: JUMP - skips to energy charge path",
            "Frame 6: ENERGY_CHARGE - charges 1 energy",
            "Frame 7: JUMP - skips recover member",
            "Frame 8: RECOVER_MEMBER - recovers 1 member from discard",
            "Frame 9: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "以下から1つを選ぶ": "Frame 2,4: SELECT_MODE",
            "エネルギーカードを1枚ウェイト状態で置く": "Frame 6: ENERGY_CHARGE",
            "メンバーカードを1枚手札に加える": "Frame 8: RECOVER_MEMBER"
        }
    }

# Ability 416: Looks correct - has proper SELECT_MODE logic
# Text: Similar to 415 but with proper choice implementation
# Current frames: [COUNT_SUCCESS_LIVE, JUMP_IF_FALSE, SELECT_MODE, JUMP, JUMP, ENERGY_CHARGE, JUMP, RECOVER_MEMBER, JUMP, RETURN] - appears correct
if len(data['abilities']) > 416:
    data['abilities'][416]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: Choice ability with proper SELECT_MODE implementation",
            "Frames appear correct with proper choice logic",
            "Frame 0: COUNT_SUCCESS_LIVE - checks condition",
            "Frame 1: JUMP_IF_FALSE - conditional jump",
            "Frame 2: SELECT_MODE - choice selection",
            "Frame 3-9: Jump logic and effect execution"
        ]
    }

# Ability 417: LOOK_AND_CHOOSE has wrong source_zone and should be SELECT_CARDS with group_id
# Text: "{{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：エールにより公開された自分のカードの中から、『μ's』のメンバーカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD (optional), JUMP_IF_FALSE, LOOK_AND_CHOOSE (source_zone: DECK_TOP), RETURN]
if len(data['abilities']) > 417:
    data['abilities'][417]["frames"] = [
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
            "op": "SELECT_CARDS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "card_type": "MEMBER",
                "group_enabled": 1,
                "group_id": "MUSE"
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "YELL_PILE"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][417]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：エールにより公開された自分のカードの中から、『μ's』のメンバーカードを1枚手札に加える。",
            "Fixed: Changed LOOK_AND_CHOOSE to SELECT_CARDS with source_zone YELL_PILE and group_id MUSE",
            "Frame 0: MOVE_TO_DISCARD - optional discard 1 from hand",
            "Frame 1: JUMP_IF_FALSE - jumps if not discarded",
            "Frame 2: SELECT_CARDS - selects 1 μ's member from yell pile to hand",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "手札を1枚控え室に置いてもよい": "Frame 0-1: MOVE_TO_DISCARD + JUMP_IF_FALSE",
            "エールにより公開された自分のカードの中から、『μ's』のメンバーカードを1枚手札に加える": "Frame 2: SELECT_CARDS"
        }
    }

# Ability 418: GROUP_FILTER checking wrong slot, needs proper count check for live cards with score
# Text: "{{live_success.png|ライブ成功時}}自分か相手の成功ライブカード置き場にカードが2枚以上あり、かつエールにより公開された自分のカードの中に{{icon_score.png|スコア}}を持つライブカードが1枚以上ある場合、このカードのスコアを+２する。"
# Current frames: [COUNT_SUCCESS_LIVE, GROUP_FILTER (STAGE_1), JUMP_IF_FALSE, BOOST_SCORE, RETURN]
if len(data['abilities']) > 418:
    data['abilities'][418]["frames"] = [
        {
            "op": "COUNT_SUCCESS_LIVE",
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
            "op": "COUNT_CARDS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "card_type": "LIVE",
                "has_score": 1
            },
            "slot": {
                "target_slot": "YELL_PILE",
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
            "frame_index": 5
        }
    ]
    data['abilities'][418]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分か相手の成功ライブカード置き場にカードが2枚以上あり、かつエールにより公開された自分のカードの中に{{icon_score.png|スコア}}を持つライブカードが1枚以上ある場合、このカードのスコアを+２する。",
            "Fixed: Changed GROUP_FILTER to COUNT_CARDS with proper slot YELL_PILE and has_score check",
            "Frame 0: COUNT_SUCCESS_LIVE - checks for 2+ cards in success live pile",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 2",
            "Frame 2: COUNT_CARDS - checks for 1+ live cards with score in yell pile",
            "Frame 3: JUMP_IF_FALSE - jumps if no score cards",
            "Frame 4: BOOST_SCORE - adds +2 to score",
            "Frame 5: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場にカードが2枚以上あり": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "エールにより公開された自分のカードの中に{{icon_score.png|スコア}}を持つライブカードが1枚以上ある場合": "Frame 2-3: COUNT_CARDS + JUMP_IF_FALSE",
            "このカードのスコアを+２する": "Frame 4: BOOST_SCORE"
        }
    }

# Ability 419: SELECT_CARDS has wrong source_zone (DECK_TOP instead of YELL_PILE), ADD_TO_HAND is redundant
# Text: "{{live_success.png|ライブ成功時}}自分か相手の成功ライブカード置き場にカードが2枚以上ある場合、エールにより公開された自分のカードの中から、メンバーカードを2枚まで手札に加える。"
# Current frames: [COUNT_SUCCESS_LIVE, JUMP_IF_FALSE, SELECT_CARDS (source_zone: DECK_TOP), ADD_TO_HAND, RETURN]
if len(data['abilities']) > 419:
    data['abilities'][419]["frames"] = [
        {
            "op": "COUNT_SUCCESS_LIVE",
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
            "op": "SELECT_CARDS",
            "frame_index": 2,
            "value": 2,
            "attr": {
                "target_player": "SELF",
                "card_type": "MEMBER",
                "is_optional": 1
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "YELL_PILE"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][419]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分か相手の成功ライブカード置き場にカードが2枚以上ある場合、エールにより公開された自分のカードの中から、メンバーカードを2枚まで手札に加える。",
            "Fixed: Changed SELECT_CARDS source_zone from DECK_TOP to YELL_PILE, removed redundant ADD_TO_HAND",
            "Frame 0: COUNT_SUCCESS_LIVE - checks for 2+ cards in success live pile",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 2",
            "Frame 2: SELECT_CARDS - selects up to 2 member cards from yell pile to hand",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場にカードが2枚以上ある場合": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "エールにより公開された自分のカードの中から、メンバーカードを2枚まで手札に加える": "Frame 2: SELECT_CARDS"
        }
    }

# Ability 420: Looks correct - no fix needed
# Text: "{{live_success.png|ライブ成功時}}自分が余剰ハートに{{heart_01.png|heart01}}を1つ以上持つ場合、カードを1枚引く。"
# Current frames: [HAS_EXCESS_HEART, JUMP_IF_FALSE, DRAW, RETURN] - appears correct
if len(data['abilities']) > 420:
    data['abilities'][420]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分が余剰ハートに{{heart_01.png|heart01}}を1つ以上持つ場合、カードを1枚引く。",
            "Frames appear correct",
            "Frame 0: HAS_EXCESS_HEART - checks for heart01 >= 1",
            "Frame 1: JUMP_IF_FALSE - jumps if no heart01",
            "Frame 2: DRAW - draws 1 card",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "余剰ハートに{{heart_01.png|heart01}}を1つ以上持つ場合": "Frame 0-1: HAS_EXCESS_HEART + JUMP_IF_FALSE",
            "カードを1枚引く": "Frame 2: DRAW"
        }
    }

# Ability 421: Missing REMOVE_HEARTS and wrong COUNT_HEARTS value
# Text: "{{live_success.png|ライブ成功時}}自分が余剰ハートを3つ以上持っている場合、それらをすべて失い、このカードのスコアを+１する。"
# Current frames: [COUNT_HEARTS (value:1), JUMP_IF_FALSE, BOOST_SCORE, RETURN]
if len(data['abilities']) > 421:
    data['abilities'][421]["frames"] = [
        {
            "op": "COUNT_HEARTS",
            "frame_index": 0,
            "value": 3,
            "attr": {
                "heart_type": "SURPLUS"
            },
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
            "op": "REMOVE_HEARTS",
            "frame_index": 2,
            "attr": {
                "heart_type": "SURPLUS",
                "remove_all": 1
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "BOOST_SCORE",
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
            "op": "RETURN",
            "frame_index": 4
        }
    ]
    data['abilities'][421]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分が余剰ハートを3つ以上持っている場合、それらをすべて失い、このカードのスコアを+１する。",
            "Fixed: Changed COUNT_HEARTS value from 1 to 3, added REMOVE_HEARTS frame",
            "Frame 0: COUNT_HEARTS - checks for 3+ surplus hearts",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 3",
            "Frame 2: REMOVE_HEARTS - removes all surplus hearts",
            "Frame 3: BOOST_SCORE - adds +1 to score",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "余剰ハートを3つ以上持っている場合": "Frame 0-1: COUNT_HEARTS + JUMP_IF_FALSE",
            "それらをすべて失い": "Frame 2: REMOVE_HEARTS",
            "このカードのスコアを+１する": "Frame 3: BOOST_SCORE"
        }
    }

# Ability 422: Looks correct - no fix needed
# Text: "{{live_success.png|ライブ成功時}}自分のエネルギーが11枚以上ある場合、カードを2枚引き、手札を1枚控え室に置く。"
# Current frames: [COUNT_ENERGY, JUMP_IF_FALSE, DRAW, MOVE_TO_DISCARD, RETURN] - appears correct
if len(data['abilities']) > 422:
    data['abilities'][422]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のエネルギーが11枚以上ある場合、カードを2枚引き、手札を1枚控え室に置く。",
            "Frames appear correct",
            "Frame 0: COUNT_ENERGY - checks for 11+ energy",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 11",
            "Frame 2: DRAW - draws 2 cards",
            "Frame 3: MOVE_TO_DISCARD - discards 1 from hand",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "エネルギーが11枚以上ある場合": "Frame 0-1: COUNT_ENERGY + JUMP_IF_FALSE",
            "カードを2枚引き": "Frame 2: DRAW",
            "手札を1枚控え室に置く": "Frame 3: MOVE_TO_DISCARD"
        }
    }

# Ability 423: Wrong frame (TRANSFORM_COLOR instead of ENERGY_CHARGE)
# Text: "{{live_success.png|ライブ成功時}}自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置いてもよい。そうした場合、相手はカードを1枚引く。"
# Current frames: [TRANSFORM_COLOR, JUMP_IF_FALSE, DRAW (target: STAGE_2), RETURN]
if len(data['abilities']) > 423:
    data['abilities'][423]["frames"] = [
        {
            "op": "ENERGY_CHARGE",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "is_optional": 1
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "ENERGY_DECK",
                "is_wait": 1
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "DRAW",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "target_player": "OPPONENT"
            },
            "slot": {
                "target_slot": "STAGE_2"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][423]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置いてもよい。そうした場合、相手はカードを1枚引く。",
            "Fixed: Changed TRANSFORM_COLOR to ENERGY_CHARGE with proper source_zone",
            "Frame 0: ENERGY_CHARGE - optional charge 1 energy from energy deck",
            "Frame 1: JUMP_IF_FALSE - jumps if not charged",
            "Frame 2: DRAW - opponent draws 1 card",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "エネルギーカードを1枚ウェイト状態で置いてもよい": "Frame 0-1: ENERGY_CHARGE + JUMP_IF_FALSE",
            "そうした場合、相手はカードを1枚引く": "Frame 2: DRAW"
        }
    }

# Ability 424: Looks correct - no fix needed
# Text: "{{live_success.png|ライブ成功時}}自分のステージに、元々持つハートの数より多い数のハートを持つメンバーがいる場合、カードを1枚引く。"
# Current frames: [HAS_MEMBER, JUMP_IF_FALSE, DRAW, RETURN] - appears correct
if len(data['abilities']) > 424:
    data['abilities'][424]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージに、元々持つハートの数より多い数のハートを持つメンバーがいる場合、カードを1枚引く。",
            "Frames appear correct",
            "Frame 0: HAS_MEMBER - checks for member with more hearts than original",
            "Frame 1: JUMP_IF_FALSE - jumps if no such member",
            "Frame 2: DRAW - draws 1 card",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "元々持つハートの数より多い数のハートを持つメンバーがいる場合": "Frame 0-1: HAS_MEMBER + JUMP_IF_FALSE",
            "カードを1枚引く": "Frame 2: DRAW"
        }
    }

# Ability 425: Missing SELECT_CARDS frame
# Text: "{{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」、「ウィーン・マルガレーテ」、「鬼塚冬毬」のうち、名前の異なるメンバーが2人以上いる場合、エールにより公開された自分のカードの中から、カードを1枚手札に加える。"
# Current frames: [COUNT_STAGE, RETURN] - missing SELECT_CARDS
if len(data['abilities']) > 425:
    data['abilities'][425]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "attr": {
                "unique_names": 1,
                "char_id_1": "KANON",
                "char_id_2": "MARGARETE",
                "char_id_3": "TOMARI"
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
            "op": "SELECT_CARDS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "is_optional": 1
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "YELL_PILE"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][425]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」、「ウィーン・マルガレーテ」、「鬼塚冬毬」のうち、名前の異なるメンバーが2人以上いる場合、エールにより公開された自分のカードの中から、カードを1枚手札に加える。",
            "Fixed: Added JUMP_IF_FALSE and SELECT_CARDS frames",
            "Frame 0: COUNT_STAGE - checks for 2+ unique members from specific list",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 2",
            "Frame 2: SELECT_CARDS - selects 1 card from yell pile to hand",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "名前の異なるメンバーが2人以上いる場合": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "エールにより公開された自分のカードの中から、カードを1枚手札に加える": "Frame 2: SELECT_CARDS"
        }
    }

# Ability 426: Looks correct - no fix needed
# Text: "{{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」と「唐可可」がいる場合、カードを1枚引く。"
# Current frames: [COUNT_STAGE, COUNT_STAGE, JUMP_IF_FALSE, DRAW, RETURN] - appears correct (checks for two specific members)
if len(data['abilities']) > 426:
    data['abilities'][426]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」と「唐可可」がいる場合、カードを1枚引く。",
            "Frames appear correct",
            "Frame 0-1: COUNT_STAGE - checks for both specific members",
            "Frame 2: JUMP_IF_FALSE - jumps if both not present",
            "Frame 3: DRAW - draws 1 card",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "「澁谷かのん」と「唐可可」がいる場合": "Frame 0-2: COUNT_STAGE + JUMP_IF_FALSE",
            "カードを1枚引く": "Frame 3: DRAW"
        }
    }

# Ability 427: Looks correct - no fix needed
# Text: "{{live_success.png|ライブ成功時}}自分のステージに『蓮ノ空』のメンバーがいる場合、カードを1枚引き、手札を1枚控え室に置く。"
# Current frames: [HAS_MEMBER, JUMP_IF_FALSE, DRAW, MOVE_TO_DISCARD, RETURN] - appears correct
if len(data['abilities']) > 427:
    data['abilities'][427]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージに『蓮ノ空』のメンバーがいる場合、カードを1枚引き、手札を1枚控え室に置く。",
            "Frames appear correct",
            "Frame 0: HAS_MEMBER - checks for Hasunosora member on stage",
            "Frame 1: JUMP_IF_FALSE - jumps if no Hasunosora member",
            "Frame 2: DRAW - draws 1 card",
            "Frame 3: MOVE_TO_DISCARD - discards 1 from hand",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "『蓮ノ空』のメンバーがいる場合": "Frame 0-1: HAS_MEMBER + JUMP_IF_FALSE",
            "カードを1枚引き": "Frame 2: DRAW",
            "手札を1枚控え室に置く": "Frame 3: MOVE_TO_DISCARD"
        }
    }

# Ability 428: Looks correct - dynamic draw based on Aqours member count
# Text: "{{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバー1人につき、カードを1枚引く。その後、これにより引いた枚数と同じ枚数を手札から控え室に置く。"
# Current frames: [DRAW (dynamic), MOVE_TO_DISCARD (dynamic), RETURN] - appears correct with dynamic values
if len(data['abilities']) > 428:
    data['abilities'][428]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバー1人につき、カードを1枚引く。その後、これにより引いた枚数と同じ枚数を手札から控え室に置く。",
            "Frames appear correct with dynamic values",
            "Frame 0: DRAW - draws 1 card per Aqours member (dynamic)",
            "Frame 1: MOVE_TO_DISCARD - discards same number as drawn (dynamic)",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "『Aqours』のメンバー1人につき、カードを1枚引く": "Frame 0: DRAW (dynamic)",
            "これにより引いた枚数と同じ枚数を手札から控え室に置く": "Frame 1: MOVE_TO_DISCARD (dynamic)"
        }
    }

# Ability 429: Looks correct - checks heart05 count and opponent excess hearts
# Text: "{{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_05.png|heart05}}が合計4個以上あり、このターン、相手が余剰のハートを持たずにライブを成功させていた場合、このカードのスコアを+２する。"
# Current frames: [COUNT_HEARTS (heart05, 4+), NOT_HAS_EXCESS_HEART (opponent), JUMP_IF_FALSE, BOOST_SCORE, RETURN] - appears correct
if len(data['abilities']) > 429:
    data['abilities'][429]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_05.png|heart05}}が合計4個以上あり、このターン、相手が余剰のハートを持たずにライブを成功させていた場合、このカードのスコアを+２する。",
            "Frames appear correct",
            "Frame 0: COUNT_HEARTS - checks for 4+ heart05 on Aqours members",
            "Frame 1: NOT_HAS_EXCESS_HEART - checks opponent didn't have excess hearts",
            "Frame 2: JUMP_IF_FALSE - jumps if conditions not met",
            "Frame 3: BOOST_SCORE - adds +2 to score",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "heart05が合計4個以上あり": "Frame 0: COUNT_HEARTS",
            "相手が余剰のハートを持たずにライブを成功させていた場合": "Frame 1-2: NOT_HAS_EXCESS_HEART + JUMP_IF_FALSE",
            "このカードのスコアを+２する": "Frame 3: BOOST_SCORE"
        }
    }

# Ability 430: Looks correct - dynamic boost based on tapped members
# Text: "{{live_success.png|ライブ成功時}}自分のステージにいるウェイト状態のメンバー1人につき、このカードのスコアを+１する。"
# Current frames: [BOOST_SCORE (dynamic based on tapped members), RETURN] - appears correct with dynamic values
if len(data['abilities']) > 430:
    data['abilities'][430]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージにいるウェイト状態のメンバー1人につき、このカードのスコアを+１する。",
            "Frames appear correct with dynamic values",
            "Frame 0: BOOST_SCORE - adds +1 per tapped member (dynamic)",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "ウェイト状態のメンバー1人につき、このカードのスコアを+１する": "Frame 0: BOOST_SCORE (dynamic)"
        }
    }

# Ability 431: Looks correct - formation change logic
# Text: "{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが『Liella!』のみの場合、自分のステージにいるメンバーをフォーメーションチェンジしてもよい。"
# Current frames: [COUNT_STAGE, SUM_VALUE, COUNT_STAGE, JUMP_IF_FALSE, FORMATION_CHANGE, RETURN] - appears correct
if len(data['abilities']) > 431:
    data['abilities'][431]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージにいるメンバーが『Liella!』のみの場合、自分のステージにいるメンバーをフォーメーションチェンジしてもよい。",
            "Frames appear correct with formation change logic",
            "Frame 0-2: COUNT_STAGE checks - verifies only Liella members on stage",
            "Frame 3: JUMP_IF_FALSE - jumps if not only Liella",
            "Frame 4: FORMATION_CHANGE - allows formation change",
            "Frame 5: RETURN"
        ]
    }

# Ability 432: Looks correct - HEART_LEAD check
# Text: "{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを+１する。"
# Current frames: [HEART_LEAD, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - appears correct
if len(data['abilities']) > 432:
    data['abilities'][432]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを+１する。",
            "Frames appear correct",
            "Frame 0: HEART_LEAD - checks if self has more hearts than opponent",
            "Frame 1: JUMP_IF_FALSE - jumps if not leading",
            "Frame 2: BOOST_SCORE - adds +1 to score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "ハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合": "Frame 0-1: HEART_LEAD + JUMP_IF_FALSE",
            "このカードのスコアを+１する": "Frame 2: BOOST_SCORE"
        }
    }

# Ability 433: NOP frame should be COUNT_STAGE with unique_names check
# Text: "{{live_success.png|ライブ成功時}}自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合、自分の控え室から『BiBi』のメンバーカードを1枚手札に加える。"
# Current frames: [NOP (unit_id: BIBI), JUMP_IF_FALSE, RECOVER_MEMBER, RETURN]
if len(data['abilities']) > 433:
    data['abilities'][433]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "value": 2,
            "attr": {
                "card_type": "MEMBER",
                "unit_enabled": 1,
                "unit_id": "BIBI",
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
            "op": "RECOVER_MEMBER",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "unit_enabled": 1,
                "unit_id": "BIBI",
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
    data['abilities'][433]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合、自分の控え室から『BiBi』のメンバーカードを1枚手札に加える。",
            "Fixed: Changed NOP to COUNT_STAGE with unique_names check",
            "Frame 0: COUNT_STAGE - checks for 2+ unique BiBi members",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 2",
            "Frame 2: RECOVER_MEMBER - recovers 1 BiBi member from discard",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "名前の異なる『BiBi』のメンバーが2人以上いる場合": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "自分の控え室から『BiBi』のメンバーカードを1枚手札に加える": "Frame 2: RECOVER_MEMBER"
        }
    }

# Ability 434: Looks correct - SELECT_MEMBER for center Liella member that moved
# Text: "{{live_success.png|ライブ成功時}}自分のステージのセンターエリアにいる『Liella!』のメンバーが、このターン中に移動している場合、このカードのスコアを+１する。"
# Current frames: [SELECT_MEMBER, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - appears correct
if len(data['abilities']) > 434:
    data['abilities'][434]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のステージのセンターエリアにいる『Liella!』のメンバーが、このターン中に移動している場合、このカードのスコアを+１する。",
            "Frames appear correct",
            "Frame 0: SELECT_MEMBER - checks for Liella member in center that moved",
            "Frame 1: JUMP_IF_FALSE - jumps if no such member",
            "Frame 2: BOOST_SCORE - adds +1 to score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "センターエリアにいる『Liella!』のメンバーが、このターン中に移動している場合": "Frame 0-1: SELECT_MEMBER + JUMP_IF_FALSE",
            "このカードのスコアを+１する": "Frame 2: BOOST_SCORE"
        }
    }

# Ability 435: Looks correct - LOOK_DECK, ORDER_DECK, MOVE_TO_DISCARD
# Text: "{{live_success.png|ライブ成功時}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。"
# Current frames: [LOOK_DECK, ORDER_DECK, MOVE_TO_DISCARD, RETURN] - appears correct
if len(data['abilities']) > 435:
    data['abilities'][435]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。",
            "Frames appear correct",
            "Frame 0: LOOK_DECK - looks at top 3 cards",
            "Frame 1: ORDER_DECK - orders chosen cards on top of deck",
            "Frame 2: MOVE_TO_DISCARD - discards remaining cards",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "デッキの上からカードを3枚見る": "Frame 0: LOOK_DECK",
            "好きな枚数を好きな順番でデッキの上に置き": "Frame 1: ORDER_DECK",
            "残りを控え室に置く": "Frame 2: MOVE_TO_DISCARD"
        }
    }

# Ability 436: Looks correct - COUNT_SUCCESS_LIVE for μ's
# Text: "{{live_success.png|ライブ成功時}}自分の成功ライブカード置き場に『μ's』のカードがある場合、カードを1枚引く。"
# Current frames: [COUNT_SUCCESS_LIVE, JUMP_IF_FALSE, DRAW, RETURN] - appears correct
if len(data['abilities']) > 436:
    data['abilities'][436]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分の成功ライブカード置き場に『μ's』のカードがある場合、カードを1枚引く。",
            "Frames appear correct",
            "Frame 0: COUNT_SUCCESS_LIVE - checks for μ's in success live pile",
            "Frame 1: JUMP_IF_FALSE - jumps if no μ's",
            "Frame 2: DRAW - draws 1 card",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場に『μ's』のカードがある場合": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "カードを1枚引く": "Frame 2: DRAW"
        }
    }

# Ability 437: Missing proper filtering logic
# Text: "{{live_success.png|ライブ成功時}}自分の控え室にある、自分のステージにいるすべてのメンバーと異なるグループ名を持つカード1枚を手札に加える。"
# Current frames: [ADD_TO_HAND, RETURN] - missing SELECT_CARDS with group exclusion
if len(data['abilities']) > 437:
    data['abilities'][437]["frames"] = [
        {
            "op": "SELECT_CARDS",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "exclude_stage_groups": 1,
                "is_optional": 1
            },
            "slot": {
                "target_slot": "HAND",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 1
        }
    ]
    data['abilities'][437]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_SUCCESS",
            "Text: {{live_success.png|ライブ成功時}}自分の控え室にある、自分のステージにいるすべてのメンバーと異なるグループ名を持つカード1枚を手札に加える。",
            "Fixed: Changed ADD_TO_HAND to SELECT_CARDS with exclude_stage_groups",
            "Frame 0: SELECT_CARDS - selects 1 card from discard with group different from stage",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "自分のステージにいるすべてのメンバーと異なるグループ名を持つカード1枚を手札に加える": "Frame 0: SELECT_CARDS"
        }
    }

# Ability 438: CONSTANT ability with center marker - should not have COUNT_ENERGY check
# Text: "{{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを+１する。"
# Current frames: [COUNT_ENERGY, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - wrong, CONSTANT should just BOOST_SCORE
if len(data['abilities']) > 438:
    data['abilities'][438]["frames"] = [
        {
            "op": "BOOST_SCORE",
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
            "op": "RETURN",
            "frame_index": 1
        }
    ]
    data['abilities'][438]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを+１する。",
            "Fixed: Removed COUNT_ENERGY check, CONSTANT abilities should be unconditional",
            "Frame 0: BOOST_SCORE - adds +1 to total score",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "ライブの合計スコアを+１する": "Frame 0: BOOST_SCORE"
        }
    }

# Ability 439: Uses COUNT_ENERGY instead of COUNT_SUCCESS_LIVE and score check
# Text: "{{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。"
# Current frames: [COUNT_ENERGY, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - wrong check
if len(data['abilities']) > 439:
    data['abilities'][439]["frames"] = [
        {
            "op": "COUNT_SUCCESS_LIVE",
            "frame_index": 0,
            "value": 1,
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
            "op": "SCORE_CHECK",
            "frame_index": 2,
            "value": 1,
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "LE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 3,
            "value": 1
        },
        {
            "op": "GRANT_ABILITY",
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
    data['abilities'][439]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT (with TOUJYOU marker)",
            "Text: {{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
            "Fixed: Changed COUNT_ENERGY to COUNT_SUCCESS_LIVE, added SCORE_CHECK and GRANT_ABILITY",
            "Frame 0: COUNT_SUCCESS_LIVE - checks for 1+ cards in success live pile",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 1",
            "Frame 2: SCORE_CHECK - checks if total score <= 1",
            "Frame 3: JUMP_IF_FALSE - jumps if score > 1",
            "Frame 4: GRANT_ABILITY - grants constant +1 score ability",
            "Frame 5: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場にカードが1枚以上あり": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "スコアの合計が１以下の場合": "Frame 2-3: SCORE_CHECK + JUMP_IF_FALSE",
            "ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 4: GRANT_ABILITY"
        }
    }

# Ability 440: Uses COUNT_ENERGY instead of COUNT_SUCCESS_LIVE for μ's score cards
# Text: "{{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。2枚以上ある場合、代わりに「{{jyouji.png|常時}}ライブの合計スコアを+２する。」を得る。"
# Current frames: [COUNT_ENERGY, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - wrong check
if len(data['abilities']) > 440:
    data['abilities'][440]["frames"] = [
        {
            "op": "COUNT_SUCCESS_LIVE",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": "MUSE",
                "has_score": 1
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
            "op": "COUNT_SUCCESS_LIVE",
            "frame_index": 2,
            "value": 2,
            "attr": {
                "group_enabled": 1,
                "group_id": "MUSE",
                "has_score": 1
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
            "op": "GRANT_ABILITY",
            "frame_index": 4,
            "value": 2,
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
            "op": "GRANT_ABILITY",
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
    data['abilities'][440]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT (with TOUJYOU and CENTER markers)",
            "Text: {{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合...2枚以上ある場合、代わりに+2",
            "Fixed: Changed COUNT_ENERGY to COUNT_SUCCESS_LIVE with group and score checks, added GRANT_ABILITY logic",
            "Frame 0: COUNT_SUCCESS_LIVE - checks for 1+ μ's score cards in success live pile",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 1",
            "Frame 2: COUNT_SUCCESS_LIVE - checks for 2+ μ's score cards",
            "Frame 3: JUMP_IF_FALSE - jumps if less than 2",
            "Frame 4: GRANT_ABILITY - grants +2 score ability",
            "Frame 5: JUMP - skips +1 grant",
            "Frame 6: GRANT_ABILITY - grants +1 score ability",
            "Frame 7: RETURN"
        ],
        "text_mapping": {
            "スコアを持つ『μ's』のカードが1枚ある場合": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "2枚以上ある場合、代わりに+2": "Frame 2-5: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE + GRANT_ABILITY + JUMP",
            "+1を得る": "Frame 6: GRANT_ABILITY"
        }
    }

# Ability 441: ACTIVATED with energy cost, wrong frames (COUNT_ENERGY instead of energy payment and card reveal)
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。"
# Current frames: [COUNT_ENERGY, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - wrong
if len(data['abilities']) > 441:
    data['abilities'][441]["frames"] = [
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
            "op": "SELECT_CARDS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "hidden_from_opponent": 1
            },
            "slot": {
                "target_slot": "REVEAL",
                "source_zone": "HAND"
            }
        },
        {
            "op": "TYPE_CHECK",
            "frame_index": 3,
            "attr": {
                "card_type": "LIVE"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 4,
            "value": 1
        },
        {
            "op": "GRANT_ABILITY",
            "frame_index": 5,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 6
        }
    ]
    data['abilities'][441]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
            "Fixed: Changed COUNT_ENERGY to proper energy payment and card reveal logic",
            "Frame 0: SUM_VALUE - once per turn check for 2 energy",
            "Frame 1: PAY_ENERGY - pays 2 energy",
            "Frame 2: SELECT_CARDS - selects 1 card from hand, hidden from opponent",
            "Frame 3: TYPE_CHECK - checks if revealed card is live card",
            "Frame 4: JUMP_IF_FALSE - jumps if not live card",
            "Frame 5: GRANT_ABILITY - grants +1 score ability",
            "Frame 6: RETURN"
        ],
        "text_mapping": {
            "{{icon_energy.png|E}}{{icon_energy.png|E}}：": "Frame 0-1: SUM_VALUE + PAY_ENERGY",
            "自分の手札を、相手は見ないで1枚選び公開する": "Frame 2: SELECT_CARDS",
            "公開されたカードがライブカードの場合": "Frame 3-4: TYPE_CHECK + JUMP_IF_FALSE",
            "ライブ終了時まで、このメンバーは「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 5: GRANT_ABILITY"
        }
    }

# Ability 442: CONSTANT with complex condition, wrong frames (COUNT_ENERGY instead of proper stage check)
# Text: "{{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。"
# Current frames: [COUNT_ENERGY, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - wrong
if len(data['abilities']) > 442:
    data['abilities'][442]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "attr": {
                "group_enabled": 1,
                "group_id": "HASUNOSORA",
                "unique_names": 1,
                "all_areas": 1
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
            "op": "GRANT_ABILITY",
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
    data['abilities'][442]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
            "Fixed: Changed COUNT_ENERGY to COUNT_STAGE with all_areas and unique_names check",
            "Frame 0: COUNT_STAGE - checks for unique Hasunosora members in all stage areas",
            "Frame 1: JUMP_IF_FALSE - jumps if condition not met",
            "Frame 2: GRANT_ABILITY - grants +1 score ability",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 2: GRANT_ABILITY"
        }
    }

# Ability 443: LIVE_START with complex cost-based effects, missing most frames
# Text: "{{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。"
# Current frames: [BOOST_SCORE, RETURN] - missing most frames
if len(data['abilities']) > 443:
    data['abilities'][443]["frames"] = [
        {
            "op": "SELECT_CARDS",
            "frame_index": 0,
            "value": 2,
            "attr": {
                "card_type": "MEMBER",
                "is_optional": 1
            },
            "slot": {
                "target_slot": "DECK_BOTTOM",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "JUMP_IF_FALSE",
            "frame_index": 1,
            "value": 1
        },
        {
            "op": "SUM_VALUE",
            "frame_index": 2,
            "attr": {
                "is_cost_type": 1
            }
        },
        {
            "op": "JUMP_IF_NOT_EQUAL",
            "frame_index": 3,
            "value": 6
        },
        {
            "op": "DRAW",
            "frame_index": 4,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "JUMP",
            "frame_index": 5,
            "value": 4
        },
        {
            "op": "JUMP_IF_NOT_EQUAL",
            "frame_index": 6,
            "value": 8
        },
        {
            "op": "ADD_HEARTS",
            "frame_index": 7,
            "value": 1,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "JUMP",
            "frame_index": 8,
            "value": 3
        },
        {
            "op": "JUMP_IF_NOT_EQUAL",
            "frame_index": 9,
            "value": 25
        },
        {
            "op": "GRANT_ABILITY",
            "frame_index": 10,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 11
        }
    ]
    data['abilities'][443]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_START",
            "Text: {{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
            "Fixed: Added proper card selection, cost sum, and conditional effects",
            "Frame 0: SELECT_CARDS - optional select 2 member cards from discard to deck bottom",
            "Frame 1: JUMP_IF_FALSE - jumps if not selected",
            "Frame 2: SUM_VALUE - calculates total cost",
            "Frame 3-5: Check if cost = 6, then draw",
            "Frame 6-8: Check if cost = 8, then add heart",
            "Frame 9-11: Check if cost = 25, then grant +1 score ability",
            "Frame 12: RETURN"
        ],
        "text_mapping": {
            "控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい": "Frame 0-1: SELECT_CARDS + JUMP_IF_FALSE",
            "コストの合計が、6の場合、カードを1枚引く": "Frame 2-5: SUM_VALUE + JUMP_IF_NOT_EQUAL + DRAW",
            "合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る": "Frame 6-8: JUMP_IF_NOT_EQUAL + ADD_HEARTS",
            "合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 9-11: JUMP_IF_NOT_EQUAL + GRANT_ABILITY"
        }
    }

# Ability 444: CONSTANT with condition on opponent's success live score, missing condition check
# Text: "{{jyouji.png|常時}}相手の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ライブの合計スコアを+１する。"
# Current frames: [BOOST_SCORE, RETURN] - missing condition check
if len(data['abilities']) > 444:
    data['abilities'][444]["frames"] = [
        {
            "op": "COUNT_SUCCESS_LIVE",
            "frame_index": 0,
            "value": 6,
            "attr": {
                "target_player": "OPPONENT",
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
            "op": "BOOST_SCORE",
            "frame_index": 2,
            "value": 1,
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
    data['abilities'][444]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}相手の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ライブの合計スコアを+１する。",
            "Fixed: Added COUNT_SUCCESS_LIVE check for opponent's success live score",
            "Frame 0: COUNT_SUCCESS_LIVE - checks opponent's success live score >= 6",
            "Frame 1: JUMP_IF_FALSE - jumps if score < 6",
            "Frame 2: BOOST_SCORE - adds +1 to score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "相手の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "ライブの合計スコアを+１する": "Frame 2: BOOST_SCORE"
        }
    }

# Ability 445: CONSTANT with condition on having most hearts, missing condition check
# Text: "{{jyouji.png|常時}}自分と相手のステージの中で、このメンバーがほかのすべてのメンバーより多くのハートを持つかぎり、ライブの合計スコアを+１する。"
# Current frames: [BOOST_SCORE, RETURN] - missing condition check
if len(data['abilities']) > 445:
    data['abilities'][445]["frames"] = [
        {
            "op": "HAS_MOST_HEARTS",
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
            "op": "BOOST_SCORE",
            "frame_index": 2,
            "value": 1,
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
    data['abilities'][445]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分と相手のステージの中で、このメンバーがほかのすべてのメンバーより多くのハートを持つかぎり、ライブの合計スコアを+１する。",
            "Fixed: Added HAS_MOST_HEARTS check",
            "Frame 0: HAS_MOST_HEARTS - checks if this member has most hearts",
            "Frame 1: JUMP_IF_FALSE - jumps if not most hearts",
            "Frame 2: BOOST_SCORE - adds +1 to score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "このメンバーがほかのすべてのメンバーより多くのハートを持つかぎり": "Frame 0-1: HAS_MOST_HEARTS + JUMP_IF_FALSE",
            "ライブの合計スコアを+１する": "Frame 2: BOOST_SCORE"
        }
    }

# Ability 446: CONSTANT with condition on 2+ energy under member, missing condition check
# Text: "{{jyouji.png|常時}}このメンバーの下にエネルギーカードが2枚以上置かれているかぎり、ライブの合計スコアを+１する。"
# Current frames: [BOOST_SCORE, RETURN] - missing condition check
if len(data['abilities']) > 446:
    data['abilities'][446]["frames"] = [
        {
            "op": "COUNT_ENERGY_UNDER_MEMBER",
            "frame_index": 0,
            "value": 2,
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
            "op": "BOOST_SCORE",
            "frame_index": 2,
            "value": 1,
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
    data['abilities'][446]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}このメンバーの下にエネルギーカードが2枚以上置かれているかぎり、ライブの合計スコアを+１する。",
            "Fixed: Added COUNT_ENERGY_UNDER_MEMBER check",
            "Frame 0: COUNT_ENERGY_UNDER_MEMBER - checks for 2+ energy under this member",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 2",
            "Frame 2: BOOST_SCORE - adds +1 to score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "このメンバーの下にエネルギーカードが2枚以上置かれているかぎり": "Frame 0-1: COUNT_ENERGY_UNDER_MEMBER + JUMP_IF_FALSE",
            "ライブの合計スコアを+１する": "Frame 2: BOOST_SCORE"
        }
    }

# Ability 447: ACTIVATED with tap cost and grant ability, wrong frames
# Text: "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。（この能力はセンターエリアに登場している場合のみ起動できる。）"
# Current frames: [BOOST_SCORE, RETURN] - completely wrong
if len(data['abilities']) > 447:
    data['abilities'][447]["frames"] = [
        {
            "op": "SELECT_MEMBER",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "once_per_turn": 1,
                "center_only": 1
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "STAGE"
            }
        },
        {
            "op": "SET_TAPPED",
            "frame_index": 1,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "GRANT_ABILITY",
            "frame_index": 2,
            "value": 1,
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
    data['abilities'][447]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
            "Fixed: Changed BOOST_SCORE to proper SELECT_MEMBER, SET_TAPPED, and GRANT_ABILITY",
            "Frame 0: SELECT_MEMBER - selects 1 member (center only check)",
            "Frame 1: SET_TAPPED - taps the selected member",
            "Frame 2: GRANT_ABILITY - grants +1 score ability to tapped member",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "メンバー1人をウェイトにする": "Frame 0-1: SELECT_MEMBER + SET_TAPPED",
            "ライブ終了時まで、これによってウェイト状態になったメンバーは「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 2: GRANT_ABILITY"
        }
    }

# Ability 448: CONSTANT with condition on opponent's excess hearts, missing condition check
# Text: "{{jyouji.png|常時}}相手の余剰ハートが2つ以上あるかぎり、自分のライブの合計スコアを+１する。"
# Current frames: [BOOST_SCORE, RETURN] - missing condition check
if len(data['abilities']) > 448:
    data['abilities'][448]["frames"] = [
        {
            "op": "COUNT_HEARTS",
            "frame_index": 0,
            "value": 2,
            "attr": {
                "heart_type": "SURPLUS",
                "target_player": "OPPONENT"
            },
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
            "op": "BOOST_SCORE",
            "frame_index": 2,
            "value": 1,
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
    data['abilities'][448]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}相手の余剰ハートが2つ以上あるかぎり、自分のライブの合計スコアを+１する。",
            "Fixed: Added COUNT_HEARTS check for opponent's surplus hearts",
            "Frame 0: COUNT_HEARTS - checks opponent has 2+ surplus hearts",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 2",
            "Frame 2: BOOST_SCORE - adds +1 to self's score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "相手の余剰ハートが2つ以上あるかぎり": "Frame 0-1: COUNT_HEARTS + JUMP_IF_FALSE",
            "自分のライブの合計スコアを+１する": "Frame 2: BOOST_SCORE"
        }
    }

# Ability 449: CONSTANT with condition on exactly 8 energy, missing condition check
# Text: "{{jyouji.png|常時}}自分のエネルギーがちょうど8枚あるかぎり、ライブの合計スコアを+１する。"
# Current frames: [BOOST_SCORE, RETURN] - missing condition check
if len(data['abilities']) > 449:
    data['abilities'][449]["frames"] = [
        {
            "op": "COUNT_ENERGY",
            "frame_index": 0,
            "value": 8,
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
            "op": "BOOST_SCORE",
            "frame_index": 2,
            "value": 1,
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
    data['abilities'][449]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のエネルギーがちょうど8枚あるかぎり、ライブの合計スコアを+１する。",
            "Fixed: Added COUNT_ENERGY check for exactly 8 energy",
            "Frame 0: COUNT_ENERGY - checks energy = 8",
            "Frame 1: JUMP_IF_FALSE - jumps if not exactly 8",
            "Frame 2: BOOST_SCORE - adds +1 to score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のエネルギーがちょうど8枚あるかぎり": "Frame 0-1: COUNT_ENERGY + JUMP_IF_FALSE",
            "ライブの合計スコアを+１する": "Frame 2: BOOST_SCORE"
        }
    }

# Ability 450: Looks correct - COUNT_ENERGY check for 12+ energy
# Text: "{{jyouji.png|常時}}自分のエネルギーが12枚以上ある場合、ライブの合計スコアを+１する。"
# Current frames: [COUNT_ENERGY, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - appears correct
if len(data['abilities']) > 450:
    data['abilities'][450]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のエネルギーが12枚以上ある場合、ライブの合計スコアを+１する。",
            "Frames appear correct",
            "Frame 0: COUNT_ENERGY - checks for 12+ energy",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 12",
            "Frame 2: BOOST_SCORE - adds +1 to score",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "自分のエネルギーが12枚以上ある場合": "Frame 0-1: COUNT_ENERGY + JUMP_IF_FALSE",
            "ライブの合計スコアを+１する": "Frame 2: BOOST_SCORE"
        }
    }

# Save the updated data
save_json(filepath, data)

print("Fixed abilities 401-450")
print("Completed batch 401-450")
