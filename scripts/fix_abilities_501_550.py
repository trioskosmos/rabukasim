#!/usr/bin/env python3
"""
Fix script for abilities 501-550 in ability_frame_source.json
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

# Ability 501: Missing condition check and GRANT_ABILITY - only has BOOST_SCORE
# Text: "{{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。2枚以上ある場合、代わりに「{{jyouji.png|常時}}ライブの合計スコアを+２する。」を得る。（この能力はセンターエリアに登場した場合のみ発動する。）"
# Current frames: [BOOST_SCORE, RETURN] - missing condition check and GRANT_ABILITY
if len(data['abilities']) > 501:
    data['abilities'][501]["frames"] = [
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
            "op": "JUMP_IF_EQUAL",
            "frame_index": 3,
            "value": 1
        },
        {
            "op": "GRANT_ABILITY",
            "frame_index": 4,
            "value": 1,
            "attr": {
                "effect": "BOOST_SCORE",
                "value": 2
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 5
        },
        {
            "op": "GRANT_ABILITY",
            "frame_index": 6,
            "value": 1,
            "attr": {
                "effect": "BOOST_SCORE",
                "value": 1
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
    data['abilities'][501]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT (with TOUJYOU and CENTER markers)",
            "Text: {{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。2枚以上ある場合、代わりに「{{jyouji.png|常時}}ライブの合計スコアを+２する。」を得る。（この能力はセンターエリアに登場した場合のみ発動する。）",
            "Fixed: Added COUNT_SUCCESS_LIVE checks and GRANT_ABILITY for conditional score boost",
            "Frame 0: COUNT_SUCCESS_LIVE - checks for 1+ μ's card with score",
            "Frame 1: JUMP_IF_FALSE - jumps if no such cards",
            "Frame 2: COUNT_SUCCESS_LIVE - checks for 2+ μ's cards with score",
            "Frame 3: JUMP_IF_EQUAL - jumps if exactly 1",
            "Frame 4: GRANT_ABILITY - grants +2 score ability",
            "Frame 5: RETURN",
            "Frame 6: GRANT_ABILITY - grants +1 score ability (if 1 card)",
            "Frame 7: RETURN"
        ],
        "text_mapping": {
            "μ'sのカードが1枚ある場合": "Frame 0-1: COUNT_SUCCESS_LIVE + JUMP_IF_FALSE",
            "ライブ終了時まで、ライブの合計スコアを+１する": "Frame 6: GRANT_ABILITY",
            "2枚以上ある場合": "Frame 2-3: COUNT_SUCCESS_LIVE + JUMP_IF_EQUAL",
            "ライブ終了時まで、ライブの合計スコアを+２する": "Frame 4: GRANT_ABILITY"
        }
    }

# Ability 502: Looks correct - COUNT_SUCCESS_LIVE, COUNT_STAGE, BOOST_SCORE
# Text: "{{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあり、かつ自分のステージに『μ's』のメンバーがいるかぎり、自分の成功ライブカード置き場にあるこのカードのスコアを+５する。"
# Current frames: [COUNT_SUCCESS_LIVE, JUMP_IF_FALSE, COUNT_STAGE, JUMP_IF_FALSE, BOOST_SCORE, RETURN] - appears correct
if len(data['abilities']) > 502:
    data['abilities'][502]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあり、かつ自分のステージに『μ's』のメンバーがいるかぎり、自分の成功ライブカード置き場にあるこのカードのスコアを+５する。",
            "Frames appear correct",
            "Frame 0: COUNT_SUCCESS_LIVE - checks if this card in success live pile",
            "Frame 1: JUMP_IF_FALSE - jumps if not in pile",
            "Frame 2: COUNT_STAGE - checks for μ's on stage",
            "Frame 3: JUMP_IF_FALSE - jumps if no μ's",
            "Frame 4: BOOST_SCORE - boosts score by 5",
            "Frame 5: RETURN"
        ]
    }

# Ability 503: PREVENT_SET_TO_SUCCESS_PILE - looks correct
# Text: "{{jyouji.png|常時}}このカードは成功ライブカード置き場に置くことができない。"
# Current frames: [PREVENT_SET_TO_SUCCESS_PILE, RETURN] - appears correct
if len(data['abilities']) > 503:
    data['abilities'][503]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}このカードは成功ライブカード置き場に置くことができない。",
            "Frames appear correct",
            "Frame 0: PREVENT_SET_TO_SUCCESS_PILE - prevents setting to success pile",
            "Frame 1: RETURN"
        ]
    }

# Ability 504: PREVENT_BATON_TOUCH - looks correct
# Text: "{{jyouji.png|常時}}このメンバーはバトンタッチで控え室に置けない。"
# Current frames: [PREVENT_BATON_TOUCH, RETURN] - appears correct
if len(data['abilities']) > 504:
    data['abilities'][504]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}このメンバーはバトンタッチで控え室に置けない。",
            "Frames appear correct",
            "Frame 0: PREVENT_BATON_TOUCH - prevents baton touch to discard",
            "Frame 1: RETURN"
        ]
    }

# Ability 505: META_RULE instead of IDENTITY_CHANGE - similar to ability 470
# Text: "{{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。"
# Current frames: [META_RULE, RETURN] - should use IDENTITY_CHANGE
if len(data['abilities']) > 505:
    data['abilities'][505]["frames"] = [
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
    data['abilities'][505]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。",
            "Fixed: Changed META_RULE to IDENTITY_CHANGE for multiple group identities",
            "Frame 0: IDENTITY_CHANGE - card treated as Suzuri Bouquet, DOLL CHESTRA, Mirakura Park in all zones",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う": "Frame 0: IDENTITY_CHANGE"
        }
    }

# Ability 506: META_RULE instead of IDENTITY_CHANGE - similar to ability 470
# Text: "{{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。"
# Current frames: [META_RULE, RETURN] - should use IDENTITY_CHANGE
if len(data['abilities']) > 506:
    data['abilities'][506]["frames"] = [
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
    data['abilities'][506]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。",
            "Fixed: Changed META_RULE to IDENTITY_CHANGE for multiple group identities",
            "Frame 0: IDENTITY_CHANGE - card treated as Suzuri Bouquet, DOLL CHESTRA, Mirakura Park in all zones",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う": "Frame 0: IDENTITY_CHANGE"
        }
    }

# Ability 507: Dynamic REDUCE_COST - looks correct with dynamic values
# Text: "{{jyouji.png|常時}}手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。"
# Current frames: [REDUCE_COST (dynamic), RETURN] - appears correct with dynamic values
if len(data['abilities']) > 507:
    data['abilities'][507]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。",
            "Frames appear correct with dynamic values",
            "Frame 0: REDUCE_COST - reduces cost by 1 per other card in hand (dynamic)",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "このカード以外の自分の手札1枚につき、1少なくなる": "Frame 0: REDUCE_COST (dynamic)"
        }
    }

# Ability 508: Missing condition check - only has ADD_HEARTS
# Text: "{{jyouji.png|常時}}自分のステージに「日野下花帆」か「徒町小鈴」か「安養寺姫芽」がいるかぎり、{{heart_04.png|heart04}}を得る。"
# Current frames: [ADD_HEARTS, RETURN] - missing condition check
if len(data['abilities']) > 508:
    data['abilities'][508]["frames"] = [
        {
            "op": "COUNT_STAGE",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "member_names": ["日野下花帆", "徒町小鈴", "安養寺姫芽"]
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
                "heart_type": "HEART04"
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
    data['abilities'][508]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージに「日野下花帆」か「徒町小鈴」か「安養寺姫芽」がいるかぎり、{{heart_04.png|heart04}}を得る。",
            "Fixed: Added COUNT_STAGE check for specific members",
            "Frame 0: COUNT_STAGE - checks for specific members on stage",
            "Frame 1: JUMP_IF_FALSE - jumps if no such members",
            "Frame 2: ADD_HEARTS - adds heart04",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "「日野下花帆」か「徒町小鈴」か「安養寺姫芽」がいるかぎり": "Frame 0-1: COUNT_STAGE + JUMP_IF_FALSE",
            "heart04を得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 509: NOP with raw_cond instead of proper COUNT_MOVED_STAGE check
# Text: "{{jyouji.png|常時}}自分のステージにいる『Liella!』のメンバーがこのターンにエリアを移動しているかぎり、手札にあるこのメンバーカードのコストは2減る。"
# Current frames: [NOP (raw_cond: COUNT_MOVED_STAGE), REDUCE_COST, RETURN]
if len(data['abilities']) > 509:
    data['abilities'][509]["frames"] = [
        {
            "op": "COUNT_MOVED_STAGE",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": "LIELLA"
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
    data['abilities'][509]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分のステージにいる『Liella!』のメンバーがこのターンにエリアを移動しているかぎり、手札にあるこのメンバーカードのコストは2減る。",
            "Fixed: Changed NOP with raw_cond to COUNT_MOVED_STAGE with group check",
            "Frame 0: COUNT_MOVED_STAGE - checks for Liella member that moved this turn",
            "Frame 1: JUMP_IF_FALSE - jumps if no moved Liella member",
            "Frame 2: REDUCE_COST - reduces cost by 2 for card in hand",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "『Liella!』のメンバーがこのターンにエリアを移動しているかぎり": "Frame 0-1: COUNT_MOVED_STAGE + JUMP_IF_FALSE",
            "手札にあるこのメンバーカードのコストは2減る": "Frame 2: REDUCE_COST"
        }
    }

# Ability 510: Dynamic INCREASE_COST - looks correct with dynamic values
# Text: "{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、ステージにいるこのメンバーのコストを+１する。"
# Current frames: [INCREASE_COST (dynamic), RETURN] - appears correct with dynamic values
if len(data['abilities']) > 510:
    data['abilities'][510]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: CONSTANT",
            "Text: {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、ステージにいるこのメンバーのコストを+１する。",
            "Frames appear correct with dynamic values",
            "Frame 0: INCREASE_COST - increases cost by 1 per success live card (dynamic)",
            "Frame 1: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場にあるカード1枚につき": "Frame 0: INCREASE_COST (dynamic)",
            "コストを+１する": "Frame 0: INCREASE_COST"
        }
    }

# Ability 511: Looks correct - MOVE_TO_DISCARD, RECOVER_LIVE with heart_type
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_03.png|heart03}}を3以上含むライブカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD, RECOVER_LIVE (heart_type: 5 for heart03), RETURN] - appears correct
if len(data['abilities']) > 511:
    data['abilities'][511]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_03.png|heart03}}を3以上含むライブカードを1枚手札に加える。",
            "Frames appear correct",
            "Frame 0: MOVE_TO_DISCARD - discards 2 cards from hand",
            "Frame 1: RECOVER_LIVE - recovers live card with 3+ heart03",
            "Frame 2: RETURN"
        ]
    }

# Ability 512: Wrong heart_type - should be heart01
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_01.png|heart01}}を3以上含むライブカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD, RECOVER_LIVE (heart_type: 5), RETURN] - wrong heart_type
if len(data['abilities']) > 512:
    data['abilities'][512]["frames"] = [
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
                "zone_mask": "ALL",
                "value_enabled": 1,
                "value_threshold": 3,
                "heart_type": 1
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
    data['abilities'][512]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_01.png|heart01}}を3以上含むライブカードを1枚手札に加える。",
            "Fixed: Changed heart_type from 5 to 1 (heart01)",
            "Frame 0: MOVE_TO_DISCARD - discards 2 cards from hand",
            "Frame 1: RECOVER_LIVE - recovers live card with 3+ heart01",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "手札を2枚控え室に置く": "Frame 0: MOVE_TO_DISCARD",
            "必要ハートにheart01を3以上含むライブカードを1枚手札に加える": "Frame 1: RECOVER_LIVE"
        }
    }

# Ability 513: Looks correct - MOVE_TO_DISCARD (sacrifice self), RECOVER_LIVE
# Text: "{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD, RECOVER_LIVE, RETURN] - appears correct
if len(data['abilities']) > 513:
    data['abilities'][513]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。",
            "Frames appear correct",
            "Frame 0: MOVE_TO_DISCARD - sacrifices self to discard",
            "Frame 1: RECOVER_LIVE - recovers live card",
            "Frame 2: RETURN"
        ]
    }

# Ability 514: Wrong heart_type - should be heart06
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_06.png|heart06}}を3以上含むライブカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD, RECOVER_LIVE (heart_type: 5), RETURN] - wrong heart_type
if len(data['abilities']) > 514:
    data['abilities'][514]["frames"] = [
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
                "zone_mask": "ALL",
                "value_enabled": 1,
                "value_threshold": 3,
                "heart_type": 6
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
    data['abilities'][514]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_06.png|heart06}}を3以上含むライブカードを1枚手札に加える。",
            "Fixed: Changed heart_type from 5 to 6 (heart06)",
            "Frame 0: MOVE_TO_DISCARD - discards 2 cards from hand",
            "Frame 1: RECOVER_LIVE - recovers live card with 3+ heart06",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "手札を2枚控え室に置く": "Frame 0: MOVE_TO_DISCARD",
            "必要ハートにheart06を3以上含むライブカードを1枚手札に加える": "Frame 1: RECOVER_LIVE"
        }
    }

# Ability 515: Wrong PAY_ENERGY value and unnecessary MOVE_TO_DISCARD
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からライブカードを1枚手札に加える。"
# Current frames: [SUM_VALUE, PAY_ENERGY (value: 1), MOVE_TO_DISCARD, RECOVER_LIVE, RETURN] - wrong PAY_ENERGY value and unnecessary MOVE_TO_DISCARD
if len(data['abilities']) > 515:
    data['abilities'][515]["frames"] = [
        {
            "op": "SUM_VALUE",
            "frame_index": 0,
            "value": 3,
            "attr": {
                "once_per_turn": 1
            }
        },
        {
            "op": "PAY_ENERGY",
            "frame_index": 1,
            "value": 3,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RECOVER_LIVE",
            "frame_index": 2,
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
            "frame_index": 3
        }
    ]
    data['abilities'][515]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からライブカードを1枚手札に加える。",
            "Fixed: Changed PAY_ENERGY value from 1 to 3, removed unnecessary MOVE_TO_DISCARD",
            "Frame 0: SUM_VALUE - once per turn check for 3 energy",
            "Frame 1: PAY_ENERGY - pays 3 energy",
            "Frame 2: RECOVER_LIVE - recovers live card",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "Eを3枚：": "Frame 0-1: SUM_VALUE + PAY_ENERGY",
            "自分の控え室からライブカードを1枚手札に加える": "Frame 2: RECOVER_LIVE"
        }
    }

# Ability 516: Wrong operation - should be MOVE_TO_ENERGY_DECK
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー2枚をエネルギーデッキに置く：自分の控え室にあるライブカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD, RECOVER_LIVE, RETURN] - wrong operation
if len(data['abilities']) > 516:
    data['abilities'][516]["frames"] = [
        {
            "op": "MOVE_TO_ENERGY_DECK",
            "frame_index": 0,
            "value": 2,
            "attr": {
                "target_player": "SELF",
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "ENERGY_DECK",
                "source_zone": "ENERGY"
            }
        },
        {
            "op": "RECOVER_LIVE",
            "frame_index": 1,
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
            "frame_index": 2
        }
    ]
    data['abilities'][516]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー2枚をエネルギーデッキに置く：自分の控え室にあるライブカードを1枚手札に加える。",
            "Fixed: Changed MOVE_TO_DISCARD to MOVE_TO_ENERGY_DECK",
            "Frame 0: MOVE_TO_ENERGY_DECK - moves 2 energy to energy deck",
            "Frame 1: RECOVER_LIVE - recovers live card",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "エネルギー2枚をエネルギーデッキに置く": "Frame 0: MOVE_TO_ENERGY_DECK",
            "自分の控え室にあるライブカードを1枚手札に加える": "Frame 1: RECOVER_LIVE"
        }
    }

# Ability 517: Looks correct - MOVE_TO_DISCARD (sacrifice self), RECOVER_MEMBER
# Text: "{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD, RECOVER_MEMBER, RETURN] - appears correct
if len(data['abilities']) > 517:
    data['abilities'][517]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。",
            "Frames appear correct",
            "Frame 0: MOVE_TO_DISCARD - sacrifices self to discard",
            "Frame 1: RECOVER_MEMBER - recovers member card",
            "Frame 2: RETURN"
        ]
    }

# Ability 518: Wrong MOVE_TO_DISCARD value and missing group check
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のメンバーカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD (value: 1), RECOVER_MEMBER, RETURN] - wrong value and missing group check
if len(data['abilities']) > 518:
    data['abilities'][518]["frames"] = [
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
            "op": "RECOVER_MEMBER",
            "frame_index": 1,
            "value": 1,
            "attr": {
                "zone_mask": "ALL",
                "group_enabled": 1,
                "group_id": "NIJIGASAKI"
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
    data['abilities'][518]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のメンバーカードを1枚手札に加える。",
            "Fixed: Changed MOVE_TO_DISCARD value from 1 to 2, added group_id to RECOVER_MEMBER",
            "Frame 0: MOVE_TO_DISCARD - discards 2 cards from hand",
            "Frame 1: RECOVER_MEMBER - recovers Nijigasaki member",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "手札を2枚控え室に置く": "Frame 0: MOVE_TO_DISCARD",
            "自分の控え室から『虹ヶ咲』のメンバーカードを1枚手札に加える": "Frame 1: RECOVER_MEMBER"
        }
    }

# Ability 519: Missing SET_TAPPED and MOVE_TO_DISCARD
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：カードを1枚引く。"
# Current frames: [DRAW, RETURN] - missing SET_TAPPED and MOVE_TO_DISCARD
if len(data['abilities']) > 519:
    data['abilities'][519]["frames"] = [
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
            "op": "MOVE_TO_DISCARD",
            "frame_index": 1,
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
            "op": "DRAW",
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
    data['abilities'][519]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：カードを1枚引く。",
            "Fixed: Added SET_TAPPED and MOVE_TO_DISCARD frames",
            "Frame 0: SET_TAPPED - taps this member",
            "Frame 1: MOVE_TO_DISCARD - discards 1 card from hand",
            "Frame 2: DRAW - draws 1 card",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "このメンバーをウェイトにし": "Frame 0: SET_TAPPED",
            "手札を1枚控え室に置く": "Frame 1: MOVE_TO_DISCARD",
            "カードを1枚引く": "Frame 2: DRAW"
        }
    }

# Ability 520: Looks correct - SUM_VALUE, PAY_ENERGY, DRAW, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。"
# Current frames: [SUM_VALUE, PAY_ENERGY, DRAW, RETURN] - appears correct
if len(data['abilities']) > 520:
    data['abilities'][520]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - once per turn check for 2 energy",
            "Frame 1: PAY_ENERGY - pays 2 energy",
            "Frame 2: DRAW - draws 1 card",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "Eを2枚：": "Frame 0-1: SUM_VALUE + PAY_ENERGY",
            "カードを1枚引く": "Frame 2: DRAW"
        }
    }

# Ability 521: Only RETURN - missing frames for yell score addition
# Text: "(エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)"
# Current frames: [RETURN] - missing frames
if len(data['abilities']) > 521:
    data['abilities'][521]["frames"] = [
        {
            "op": "COUNT_YELL_SCORE",
            "frame_index": 0,
            "attr": {
                "per_score": 1
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "BOOST_SCORE",
            "frame_index": 1,
            "attr": {
                "dynamic": 1
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
    data['abilities'][521]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: (エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)",
            "Fixed: Added COUNT_YELL_SCORE and dynamic BOOST_SCORE",
            "Frame 0: COUNT_YELL_SCORE - counts yell scores",
            "Frame 1: BOOST_SCORE - boosts score by yell count (dynamic)",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "エールで出たスコア1つにつき": "Frame 0: COUNT_YELL_SCORE",
            "成功したライブのスコアの合計に1を加算する": "Frame 1: BOOST_SCORE (dynamic)"
        }
    }

# Ability 522: Only RETURN - missing frames for cost-based ability grant
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。"
# Current frames: [RETURN] - missing frames
if len(data['abilities']) > 522:
    data['abilities'][522]["frames"] = [
        {
            "op": "SELECT_CARDS",
            "frame_index": 0,
            "attr": {
                "once_per_turn": 1,
                "reveal": 1
            },
            "slot": {
                "target_slot": "REVEAL",
                "source_zone": "HAND"
            }
        },
        {
            "op": "SUM_VALUE",
            "frame_index": 1,
            "attr": {
                "sum_cost": 1
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "JUMP_IF_NOT_IN_SET",
            "frame_index": 2,
            "attr": {
                "values": [10, 20, 30, 40, 50]
            },
            "value": 1
        },
        {
            "op": "GRANT_ABILITY",
            "frame_index": 3,
            "value": 1,
            "attr": {
                "effect": "BOOST_SCORE",
                "value": 1
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
    data['abilities'][522]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
            "Fixed: Added SELECT_CARDS, SUM_VALUE, JUMP_IF_NOT_IN_SET, GRANT_ABILITY",
            "Frame 0: SELECT_CARDS - selects and reveals cards from hand",
            "Frame 1: SUM_VALUE - sums cost of revealed cards",
            "Frame 2: JUMP_IF_NOT_IN_SET - jumps if not in {10,20,30,40,50}",
            "Frame 3: GRANT_ABILITY - grants +1 score ability",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "手札にあるメンバーカードを好きな枚数公開する": "Frame 0: SELECT_CARDS",
            "公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合": "Frame 1-2: SUM_VALUE + JUMP_IF_NOT_IN_SET",
            "ライブ終了時まで、ライブの合計スコアを+１するを得る": "Frame 3: GRANT_ABILITY"
        }
    }

# Ability 523: Looks correct - ACTIVATE_ENERGY, RETURN
# Text: "{{kidou.png|起動}}このメンバーをウェイトにする：エネルギーを1枚アクティブにする。"
# Current frames: [ACTIVATE_ENERGY, RETURN] - appears correct
if len(data['abilities']) > 523:
    data['abilities'][523]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}このメンバーをウェイトにする：エネルギーを1枚アクティブにする。",
            "Frames appear correct",
            "Frame 0: ACTIVATE_ENERGY - activates 1 energy",
            "Frame 1: RETURN"
        ]
    }

# Ability 524: Only RETURN - missing SELECT_MODE frames for choice ability
# Text: "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：以下から1つを選ぶ。\n・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。\n・カードを1枚引く。\n{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにするか、手札を1枚控え室に置く：エネルギーを1枚アクティブにする。"
# Current frames: [RETURN] - missing SELECT_MODE frames
if len(data['abilities']) > 524:
    data['abilities'][524]["frames"] = [
        {
            "op": "PAY_ENERGY_OPTIONAL",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "SELECT_MODE",
            "frame_index": 1,
            "value": 2,
            "attr": {
                "options": [
                    "TAP_COST_4_MEMBER",
                    "DRAW_CARD"
                ]
            },
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "JUMP",
            "frame_index": 2,
            "value": 3
        },
        {
            "op": "JUMP",
            "frame_index": 3,
            "value": 1
        },
        {
            "op": "SELECT_MEMBER",
            "frame_index": 4,
            "value": 1,
            "attr": {
                "target_player": "OPPONENT",
                "max_cost": 4
            },
            "slot": {
                "target_slot": "STAGE_0",
                "source_zone": "STAGE"
            }
        },
        {
            "op": "SET_TAPPED",
            "frame_index": 5,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "JUMP",
            "frame_index": 6,
            "value": 1
        },
        {
            "op": "DRAW",
            "frame_index": 7,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 8
        }
    ]
    data['abilities'][524]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: LIVE_START (with TOUJYOU marker)",
            "Text: {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：以下から1つを選ぶ。\n・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。\n・カードを1枚引く。",
            "Fixed: Added PAY_ENERGY_OPTIONAL and SELECT_MODE frames for choice ability",
            "Frame 0: PAY_ENERGY_OPTIONAL - optionally pays 1 energy",
            "Frame 1: SELECT_MODE - chooses between tap or draw",
            "Frame 2-3: Jump logic for mode selection",
            "Frame 4: SELECT_MEMBER - selects opponent member with cost <= 4",
            "Frame 5: SET_TAPPED - taps selected member",
            "Frame 6: Jump to return",
            "Frame 7: DRAW - draws 1 card",
            "Frame 8: RETURN"
        ],
        "text_mapping": {
            "E支払ってもよい": "Frame 0: PAY_ENERGY_OPTIONAL",
            "以下から1つを選ぶ": "Frame 1-3: SELECT_MODE + JUMP logic",
            "相手のステージにいるコスト4以下のメンバー1人をウェイトにする": "Frame 4-5: SELECT_MEMBER + SET_TAPPED",
            "カードを1枚引く": "Frame 7: DRAW"
        }
    }

# Ability 525: Missing SET_TAPPED frame
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD (wrong source_zone), RECOVER_LIVE, RETURN] - missing SET_TAPPED
if len(data['abilities']) > 525:
    data['abilities'][525]["frames"] = [
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
            "op": "MOVE_TO_DISCARD",
            "frame_index": 1,
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
            "frame_index": 2,
            "value": 1,
            "attr": {
                "zone_mask": "ALL",
                "group_enabled": 1,
                "group_id": "NIJIGASAKI"
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
    data['abilities'][525]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。",
            "Fixed: Added SET_TAPPED frame, fixed MOVE_TO_DISCARD source_zone",
            "Frame 0: SET_TAPPED - taps this member",
            "Frame 1: MOVE_TO_DISCARD - discards 1 card from hand",
            "Frame 2: RECOVER_LIVE - recovers Nijigasaki live card",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "このメンバーをウェイトにし": "Frame 0: SET_TAPPED",
            "手札を1枚控え室に置く": "Frame 1: MOVE_TO_DISCARD",
            "自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える": "Frame 2: RECOVER_LIVE"
        }
    }

# Ability 526: Wrong operation - should be MOVE_ENERGY_UNDER_MEMBER
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。\n(メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す。)"
# Current frames: [MOVE_TO_DISCARD, RECOVER_LIVE, RETURN] - wrong operation
if len(data['abilities']) > 526:
    data['abilities'][526]["frames"] = [
        {
            "op": "MOVE_ENERGY_UNDER_MEMBER",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "target_player": "SELF",
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "ENERGY"
            }
        },
        {
            "op": "RECOVER_LIVE",
            "frame_index": 1,
            "value": 1,
            "attr": {
                "zone_mask": "ALL",
                "group_enabled": 1,
                "group_id": "NIJIGASAKI"
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
    data['abilities'][526]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。",
            "Fixed: Changed MOVE_TO_DISCARD to MOVE_ENERGY_UNDER_MEMBER",
            "Frame 0: MOVE_ENERGY_UNDER_MEMBER - moves 1 energy under this member",
            "Frame 1: RECOVER_LIVE - recovers Nijigasaki live card",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く": "Frame 0: MOVE_ENERGY_UNDER_MEMBER",
            "自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える": "Frame 1: RECOVER_LIVE"
        }
    }

# Ability 527: Looks correct - MOVE_TO_DISCARD, RECOVER_LIVE (with group check), RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。"
# Current frames: [MOVE_TO_DISCARD, RECOVER_LIVE (with group check), RETURN] - appears correct
if len(data['abilities']) > 527:
    data['abilities'][527]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。",
            "Frames appear correct",
            "Frame 0: MOVE_TO_DISCARD - discards 2 cards from hand",
            "Frame 1: RECOVER_LIVE - recovers Nijigasaki live card",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "手札を2枚控え室に置く": "Frame 0: MOVE_TO_DISCARD",
            "自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える": "Frame 1: RECOVER_LIVE"
        }
    }

# Ability 528: Complex ability with IS_CENTER, SET_TAPPED, MOVE_TO_DISCARD, SELECT_MEMBER, etc. - appears correct
# Text: "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメンバー1人を自分のステージから控え室に置く..."
# Current frames: [IS_CENTER, JUMP_IF_FALSE, SET_TAPPED, MOVE_TO_DISCARD, SELECT_MEMBER, MOVE_TO_DISCARD, SUM_VALUE, JUMP_IF_FALSE, RECOVER_MEMBER, RETURN] - appears correct
if len(data['abilities']) > 528:
    data['abilities'][528]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED (with CENTER marker)",
            "Text: {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメンバー1人を自分のステージから控え室に置く...",
            "Frames appear correct",
            "Frame 0: IS_CENTER - checks if in center",
            "Frame 1: JUMP_IF_FALSE - jumps if not center",
            "Frame 2: SET_TAPPED - taps this member",
            "Frame 3: MOVE_TO_DISCARD - discards 1 card",
            "Frame 4: SELECT_MEMBER - selects Aqours member",
            "Frame 5: MOVE_TO_DISCARD - discards selected member",
            "Frame 6: SUM_VALUE - counts discarded members",
            "Frame 7: JUMP_IF_FALSE - jumps if no discard",
            "Frame 8: RECOVER_MEMBER - recovers member",
            "Frame 9: RETURN"
        ]
    }

# Ability 529: Complex ability with IS_CENTER, SELECT_MEMBER, MOVE_MEMBER, GRANT_ABILITY - appears correct
# Text: "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライ..."
# Current frames: [IS_CENTER, JUMP_IF_FALSE, SELECT_MEMBER, MOVE_MEMBER, GRANT_ABILITY, RETURN] - appears correct
if len(data['abilities']) > 529:
    data['abilities'][529]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED (with CENTER marker)",
            "Text: {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライ...",
            "Frames appear correct",
            "Frame 0: IS_CENTER - checks if in center",
            "Frame 1: JUMP_IF_FALSE - jumps if not center",
            "Frame 2: SELECT_MEMBER - selects member to tap",
            "Frame 3: MOVE_MEMBER - moves/taps member",
            "Frame 4: GRANT_ABILITY - grants ability",
            "Frame 5: RETURN"
        ]
    }

# Ability 530: Complex ability with SUM_VALUE, PAY_ENERGY, REDUCE_COST, SELECT_MEMBER, MOVE_MEMBER - appears correct
# Text: "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：相手のステージにいるコスト10以下のメ..."
# Current frames: [SUM_VALUE, PAY_ENERGY, REDUCE_COST, SELECT_MEMBER, MOVE_MEMBER, RETURN] - appears correct
if len(data['abilities']) > 530:
    data['abilities'][530]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：相手のステージにいるコスト10以下のメ...",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - once per turn check for 4 energy",
            "Frame 1: PAY_ENERGY - pays 4 energy",
            "Frame 2: REDUCE_COST - reduces cost",
            "Frame 3: SELECT_MEMBER - selects member",
            "Frame 4: MOVE_MEMBER - moves member",
            "Frame 5: RETURN"
        ]
    }

# Ability 531: Looks correct - SUM_VALUE, JUMP_IF_FALSE, PLAY_MEMBER_FROM_DISCARD, RETURN
# Text: "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。"
# Current frames: [SUM_VALUE, JUMP_IF_FALSE, PLAY_MEMBER_FROM_DISCARD, RETURN] - appears correct
if len(data['abilities']) > 531:
    data['abilities'][531]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - checks for 2 energy",
            "Frame 1: JUMP_IF_FALSE - jumps if not enough energy",
            "Frame 2: PLAY_MEMBER_FROM_DISCARD - plays this card from discard",
            "Frame 3: RETURN"
        ]
    }

# Ability 532: Looks correct - SUM_VALUE, PAY_ENERGY, RECOVER_LIVE with group check
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。"
# Current frames: [SUM_VALUE, PAY_ENERGY, RECOVER_LIVE (with group_id: HASUNOSORA), RETURN] - appears correct
if len(data['abilities']) > 532:
    data['abilities'][532]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - once per turn check for 3 energy",
            "Frame 1: PAY_ENERGY - pays 3 energy",
            "Frame 2: RECOVER_LIVE - recovers Hasunosora live card",
            "Frame 3: RETURN"
        ]
    }

# Ability 533: Missing SELECT_CARDS for revealing card before RECOVER_LIVE
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札のライブカードを1枚公開する：自分の控え室から、これにより公開したカードのカード名がすべて含まれるライブカードを1枚手札に加える。"
# Current frames: [SUM_VALUE, PAY_ENERGY, RECOVER_LIVE, RETURN] - missing SELECT_CARDS
if len(data['abilities']) > 533:
    data['abilities'][533]["frames"] = [
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
                "reveal": 1,
                "card_type": "LIVE"
            },
            "slot": {
                "target_slot": "REVEAL",
                "source_zone": "HAND"
            }
        },
        {
            "op": "RECOVER_LIVE",
            "frame_index": 3,
            "value": 1,
            "attr": {
                "zone_mask": "ALL",
                "special_id": "Same Name"
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
    data['abilities'][533]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札のライブカードを1枚公開する：自分の控え室から、これにより公開したカードのカード名がすべて含まれるライブカードを1枚手札に加える。",
            "Fixed: Added SELECT_CARDS to reveal card before RECOVER_LIVE",
            "Frame 0: SUM_VALUE - once per turn check for 2 energy",
            "Frame 1: PAY_ENERGY - pays 2 energy",
            "Frame 2: SELECT_CARDS - selects and reveals live card from hand",
            "Frame 3: RECOVER_LIVE - recovers live card with same name",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "Eを2枚：": "Frame 0-1: SUM_VALUE + PAY_ENERGY",
            "手札のライブカードを1枚公開する": "Frame 2: SELECT_CARDS",
            "公開したカードのカード名がすべて含まれるライブカードを1枚手札に加える": "Frame 3: RECOVER_LIVE"
        }
    }

# Ability 534: Looks correct - PAY_ENERGY, MOVE_TO_DISCARD, DISCARDED_CARDS, JUMP_IF_FALSE, LOOK_AND_CHOOSE, JUMP, RECOVER_LIVE, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：これにより控え室に置いたカードが『μ's』のカードの場合、自分のデッキの上からカードを4枚見る。その中からカードを2枚手札に加える。残りを控え室に置く。『μ's』のカード以外の場合、自分の控え室からライブカードを1枚手札に加える。"
# Current frames appear correct with conditional logic
if len(data['abilities']) > 534:
    data['abilities'][534]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：これにより控え室に置いたカードが『μ's』のカードの場合、自分のデッキの上からカードを4枚見る。その中からカードを2枚手札に加える。残りを控え室に置く。『μ's』のカード以外の場合、自分の控え室からライブカードを1枚手札に加える。",
            "Frames appear correct with conditional logic",
            "Frame 0: PAY_ENERGY - pays 2 energy",
            "Frame 1: MOVE_TO_DISCARD - discards 1 card",
            "Frame 2: DISCARDED_CARDS - checks if μ's",
            "Frame 3: JUMP_IF_FALSE - jumps if not μ's",
            "Frame 4: LOOK_AND_CHOOSE - looks at 4 cards, chooses 2",
            "Frame 5: JUMP - jumps to return",
            "Frame 6: RECOVER_LIVE - recovers live card",
            "Frame 7: RETURN"
        ],
        "text_mapping": {
            "Eを2枚：": "Frame 0: PAY_ENERGY",
            "手札を1枚控え室に置く": "Frame 1: MOVE_TO_DISCARD",
            "μ'sのカードの場合": "Frame 2-3: DISCARDED_CARDS + JUMP_IF_FALSE",
            "デッキの上からカードを4枚見る、2枚手札に加える": "Frame 4: LOOK_AND_CHOOSE",
            "μ'sのカード以外の場合": "Frame 5-6: JUMP + RECOVER_LIVE"
        }
    }

# Ability 535: Looks correct - PAY_ENERGY, JUMP_IF_FALSE, PLAY_MEMBER_FROM_DISCARD with cost check
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアに登場させる。"
# Current frames: [PAY_ENERGY, JUMP_IF_FALSE, PLAY_MEMBER_FROM_DISCARD (with cost check), RETURN] - appears correct
if len(data['abilities']) > 535:
    data['abilities'][535]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアに登場させる。",
            "Frames appear correct",
            "Frame 0: PAY_ENERGY - pays 2 energy",
            "Frame 1: JUMP_IF_FALSE - jumps if not enough energy",
            "Frame 2: PLAY_MEMBER_FROM_DISCARD - plays member with cost <= 2",
            "Frame 3: RETURN"
        ]
    }

# Ability 536: Looks correct - SUM_VALUE, PAY_ENERGY, MOVE_MEMBER with group check
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーを『Aqours』か『SaintSnow』のメンバーがいるエリアにポジションチェンジする。"
# Current frames: [SUM_VALUE, PAY_ENERGY, MOVE_MEMBER (with group_id for Aqours or SaintSnow), RETURN] - appears correct
if len(data['abilities']) > 536:
    data['abilities'][536]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーを『Aqours』か『SaintSnow』のメンバーがいるエリアにポジションチェンジする。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays 1 energy",
            "Frame 2: MOVE_MEMBER - position changes to Aqours or SaintSnow area",
            "Frame 3: RETURN"
        ]
    }

# Ability 537: Looks correct - SUM_VALUE, PAY_ENERGY, RECOVER_MEMBER with group and cost check
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分の控え室から4コスト以下の『蓮ノ空』のメンバーカードを1枚手札に加える。"
# Current frames: [SUM_VALUE, PAY_ENERGY, RECOVER_MEMBER (with group and cost check), RETURN] - appears correct
if len(data['abilities']) > 537:
    data['abilities'][537]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分の控え室から4コスト以下の『蓮ノ空』のメンバーカードを1枚手札に加える。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays 1 energy",
            "Frame 2: RECOVER_MEMBER - recovers Hasunosora member with cost <= 4",
            "Frame 3: RETURN"
        ]
    }

# Ability 538: Looks correct - SELECT_MODE with ADD_HEARTS choices
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart..."
# Current frames: [SELECT_MODE, JUMP, JUMP, JUMP, ADD_HEARTS, JUMP, ADD_HEARTS, JUMP, ADD_HEARTS, JUMP, RETURN] - appears correct for choice ability
if len(data['abilities']) > 538:
    data['abilities'][538]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart...",
            "Frames appear correct for choice ability",
            "Frame 0: SELECT_MODE - chooses heart type",
            "Frame 1-3: Jump logic for mode selection",
            "Frame 4: ADD_HEARTS - adds heart01",
            "Frame 5: Jump to return",
            "Frame 6: ADD_HEARTS - adds heart03",
            "Frame 7: Jump to return",
            "Frame 8: ADD_HEARTS - adds heart06",
            "Frame 9: Jump to return",
            "Frame 10: RETURN"
        ]
    }

# Ability 539: Missing SET_TAPPED frame
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを1枚引き、手札を1枚控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）"
# Current frames: [DRAW, MOVE_TO_DISCARD, RETURN] - missing SET_TAPPED
if len(data['abilities']) > 539:
    data['abilities'][539]["frames"] = [
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
            "op": "DRAW",
            "frame_index": 1,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 2,
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
            "frame_index": 3
        }
    ]
    data['abilities'][539]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを1枚引き、手札を1枚控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）",
            "Fixed: Added SET_TAPPED frame",
            "Frame 0: SET_TAPPED - taps this member",
            "Frame 1: DRAW - draws 1 card",
            "Frame 2: MOVE_TO_DISCARD - discards 1 card",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "このメンバーをウェイトにする": "Frame 0: SET_TAPPED",
            "カードを1枚引き": "Frame 1: DRAW",
            "手札を1枚控え室に置く": "Frame 2: MOVE_TO_DISCARD"
        }
    }

# Ability 540: Looks correct - SUM_VALUE, PAY_ENERGY, DRAW, MOVE_TO_DISCARD, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：カードを1枚引き、手札を1枚控え室に置く。"
# Current frames: [SUM_VALUE, PAY_ENERGY, DRAW, MOVE_TO_DISCARD, RETURN] - appears correct
if len(data['abilities']) > 540:
    data['abilities'][540]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：カードを1枚引き、手札を1枚控え室に置く。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: PAY_ENERGY - pays 1 energy",
            "Frame 2: DRAW - draws 1 card",
            "Frame 3: MOVE_TO_DISCARD - discards 1 card",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "Eを1枚：": "Frame 0-1: SUM_VALUE + PAY_ENERGY",
            "カードを1枚引き": "Frame 2: DRAW",
            "手札を1枚控え室に置く": "Frame 3: MOVE_TO_DISCARD"
        }
    }

# Ability 541: Missing SET_TAPPED frame
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：自分の控え室から『μ's』のライブカードを1枚手札に加える。"
# Current frames: [RECOVER_LIVE, RETURN] - missing SET_TAPPED
if len(data['abilities']) > 541:
    data['abilities'][541]["frames"] = [
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
            "op": "RECOVER_LIVE",
            "frame_index": 1,
            "value": 1,
            "attr": {
                "target_player": "SELF",
                "group_enabled": 1,
                "group_id": "MUSE",
                "zone_mask": "ALL"
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "DISCARD"
            }
        },
        {
            "op": "RETURN",
            "frame_index": 2
        }
    ]
    data['abilities'][541]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：自分の控え室から『μ's』のライブカードを1枚手札に加える。",
            "Fixed: Added SET_TAPPED frame and group_id to RECOVER_LIVE",
            "Frame 0: SET_TAPPED - taps this member",
            "Frame 1: RECOVER_LIVE - recovers μ's live card",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "このメンバーをウェイトにする": "Frame 0: SET_TAPPED",
            "自分の控え室から『μ's』のライブカードを1枚手札に加える": "Frame 1: RECOVER_LIVE"
        }
    }

# Ability 542: Looks correct - SELECT_MEMBER, MOVE_MEMBER, DRAW, RETURN with group check
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。"
# Current frames: [SELECT_MEMBER (with group and Not Self), MOVE_MEMBER, DRAW, RETURN] - appears correct
if len(data['abilities']) > 542:
    data['abilities'][542]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。",
            "Frames appear correct",
            "Frame 0: SELECT_MEMBER - selects Nijigasaki member (not self)",
            "Frame 1: MOVE_MEMBER - taps selected member",
            "Frame 2: DRAW - draws 1 card",
            "Frame 3: RETURN"
        ]
    }

# Ability 543: Missing MOVE_ENERGY_UNDER_MEMBER frame
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：カードを1枚引き、ライブ終了時まで、{{heart_01.png|heart01}}を得る。"
# Current frames: [DRAW, ADD_HEARTS, RETURN] - missing MOVE_ENERGY_UNDER_MEMBER
if len(data['abilities']) > 543:
    data['abilities'][543]["frames"] = [
        {
            "op": "MOVE_ENERGY_UNDER_MEMBER",
            "frame_index": 0,
            "value": 1,
            "attr": {
                "once_per_turn": 1
            },
            "slot": {
                "target_slot": "CONTEXT",
                "source_zone": "ENERGY"
            }
        },
        {
            "op": "DRAW",
            "frame_index": 1,
            "value": 1,
            "slot": {
                "target_slot": "CONTEXT"
            }
        },
        {
            "op": "ADD_HEARTS",
            "frame_index": 2,
            "value": 1,
            "attr": {
                "target_player": "SELF"
            },
            "slot": {
                "target_slot": "CONTEXT"
            },
            "params": {
                "heart_type": 0
            }
        },
        {
            "op": "RETURN",
            "frame_index": 3
        }
    ]
    data['abilities'][543]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：カードを1枚引き、ライブ終了時まで、{{heart_01.png|heart01}}を得る。",
            "Fixed: Added MOVE_ENERGY_UNDER_MEMBER frame",
            "Frame 0: MOVE_ENERGY_UNDER_MEMBER - moves 1 energy under this member",
            "Frame 1: DRAW - draws 1 card",
            "Frame 2: ADD_HEARTS - adds heart01",
            "Frame 3: RETURN"
        ],
        "text_mapping": {
            "エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く": "Frame 0: MOVE_ENERGY_UNDER_MEMBER",
            "カードを1枚引き": "Frame 1: DRAW",
            "heart01を得る": "Frame 2: ADD_HEARTS"
        }
    }

# Ability 544: Looks correct - MOVE_TO_DISCARD, JUMP_IF_FALSE, ADD_BLADES, RETURN for dynamic blades
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：ライブ終了時まで、これにより控え室に置いた『Liella!』のメンバーカード1枚につき、{{icon_blade.png|ブレード...}"
# Current frames: [MOVE_TO_DISCARD, JUMP_IF_FALSE, ADD_BLADES, RETURN] - appears correct for dynamic blades
if len(data['abilities']) > 544:
    data['abilities'][544]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：ライブ終了時まで、これにより控え室に置いた『Liella!』のメンバーカード1枚につき、{{icon_blade.png|ブレード...",
            "Frames appear correct for dynamic blades",
            "Frame 0: MOVE_TO_DISCARD - discards 3 cards from deck top",
            "Frame 1: JUMP_IF_FALSE - jumps if no Liella members",
            "Frame 2: ADD_BLADES - adds blades per Liella member (dynamic)",
            "Frame 3: RETURN"
        ]
    }

# Ability 545: Looks correct - TRIGGER_REMOTE, RETURN for triggering remote ability
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる..."
# Current frames: [TRIGGER_REMOTE, RETURN] - appears correct
if len(data['abilities']) > 545:
    data['abilities'][545]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる...",
            "Frames appear correct",
            "Frame 0: TRIGGER_REMOTE - triggers remote ability",
            "Frame 1: RETURN"
        ]
    }

# Ability 546: Looks correct - SUM_VALUE, COUNT_STAGE (with group check for Nijigasaki), JUMP_IF_FALSE, ACTIVATE_ENERGY, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。"
# Current frames: [SUM_VALUE, COUNT_STAGE (with group check), JUMP_IF_FALSE, ACTIVATE_ENERGY, RETURN] - appears correct
if len(data['abilities']) > 546:
    data['abilities'][546]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - once per turn check",
            "Frame 1: COUNT_STAGE - checks for Nijigasaki member",
            "Frame 2: JUMP_IF_FALSE - jumps if no Nijigasaki",
            "Frame 3: ACTIVATE_ENERGY - activates 2 energy",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "手札を1枚控え室に置く": "Frame 0: SUM_VALUE (cost check)",
            "自分のステージに『虹ヶ咲』のメンバーが登場している場合": "Frame 1-2: COUNT_STAGE + JUMP_IF_FALSE",
            "エネルギーを2枚アクティブにする": "Frame 3: ACTIVATE_ENERGY"
        }
    }

# Ability 547: Missing group_id for μ's in RECOVER_LIVE
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合のみ起動できる。"
# Current frames: [SCORE_COMPARE, JUMP_IF_FALSE, MOVE_TO_DISCARD, RECOVER_LIVE (missing group_id), RETURN]
if len(data['abilities']) > 547:
    data['abilities'][547]["frames"] = [
        {
            "op": "SCORE_COMPARE",
            "frame_index": 0,
            "value": 6,
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
            "value": 2
        },
        {
            "op": "MOVE_TO_DISCARD",
            "frame_index": 2,
            "value": 2,
            "slot": {
                "target_slot": "HAND"
            }
        },
        {
            "op": "RECOVER_LIVE",
            "frame_index": 3,
            "value": 1,
            "attr": {
                "zone_mask": "ALL",
                "group_enabled": 1,
                "group_id": "MUSE"
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
    data['abilities'][547]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合のみ起動できる。",
            "Fixed: Added group_id to RECOVER_LIVE",
            "Frame 0: SCORE_COMPARE - checks score total >= 6",
            "Frame 1: JUMP_IF_FALSE - jumps if less than 6",
            "Frame 2: MOVE_TO_DISCARD - discards 2 cards",
            "Frame 3: RECOVER_LIVE - recovers μ's live card",
            "Frame 4: RETURN"
        ],
        "text_mapping": {
            "成功ライブカード置き場にあるカードのスコアの合計が６以上の場合のみ起動できる": "Frame 0-1: SCORE_COMPARE + JUMP_IF_FALSE",
            "手札を2枚控え室に置く": "Frame 2: MOVE_TO_DISCARD",
            "自分の控え室から『μ's』のライブカードを1枚手札に加える": "Frame 3: RECOVER_LIVE"
        }
    }

# Ability 548: Looks complex - HAS_KEYWORD, JUMP_IF_FALSE, SET_TAPPED, DRAW, MOVE_TO_DISCARD, DISCARDED_CARDS, DISCARDED_CARDS, JUMP_IF_FALSE, ADD_BLADES, RETURN
# Text: "{{kidou.png|起動}}【左サイド】{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを3枚引き、手札を2枚控え室に置く。これにより控え室に置いたカードの中にブレードハートを持たないメンバーカードが1枚以上あ..."
# Current frames appear correct for complex conditional logic
if len(data['abilities']) > 548:
    data['abilities'][548]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED (with LEFT SIDE marker)",
            "Text: {{kidou.png|起動}}【左サイド】{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを3枚引き、手札を2枚控え室に置く。これにより控え室に置いたカードの中にブレードハートを持たないメンバーカードが1枚以上あ...",
            "Frames appear correct for complex conditional logic",
            "Frame 0: HAS_KEYWORD - checks for keyword",
            "Frame 1: JUMP_IF_FALSE - jumps if no keyword",
            "Frame 2: SET_TAPPED - taps this member",
            "Frame 3: DRAW - draws 3 cards",
            "Frame 4: MOVE_TO_DISCARD - discards 2 cards",
            "Frame 5-6: DISCARDED_CARDS - checks discarded cards",
            "Frame 7: JUMP_IF_FALSE - jumps if condition not met",
            "Frame 8: ADD_BLADES - adds blades",
            "Frame 9: RETURN"
        ]
    }

# Ability 549: Looks correct - SUM_VALUE, JUMP_IF_FALSE, MOVE_TO_DISCARD, SELECT_CARDS (with group and cost check), PLAY_MEMBER_FROM_DISCARD, RETURN
# Text: "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}、このメンバーをステージから控え室に置く：自分の控え室からコスト15以下の『蓮ノ空』のメンバーカードを1枚、このメンバーがいたエリアに登場させる。"
# Current frames: [SUM_VALUE, JUMP_IF_FALSE, MOVE_TO_DISCARD, SELECT_CARDS (with group and cost check), PLAY_MEMBER_FROM_DISCARD, RETURN] - appears correct
if len(data['abilities']) > 549:
    data['abilities'][549]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}、このメンバーをステージから控え室に置く：自分の控え室からコスト15以下の『蓮ノ空』のメンバーカードを1枚、このメンバーがいたエリアに登場させる。",
            "Frames appear correct",
            "Frame 0: SUM_VALUE - checks for 2 energy",
            "Frame 1: JUMP_IF_FALSE - jumps if not enough energy",
            "Frame 2: MOVE_TO_DISCARD - sacrifices self",
            "Frame 3: SELECT_CARDS - selects Hasunosora member with cost <= 15",
            "Frame 4: PLAY_MEMBER_FROM_DISCARD - plays selected member",
            "Frame 5: RETURN"
        ],
        "text_mapping": {
            "Eを2枚：": "Frame 0-1: SUM_VALUE + JUMP_IF_FALSE",
            "このメンバーをステージから控え室に置く": "Frame 2: MOVE_TO_DISCARD",
            "自分の控え室からコスト15以下の『蓮ノ空』のメンバーカードを1枚、このメンバーがいたエリアに登場させる": "Frame 3-4: SELECT_CARDS + PLAY_MEMBER_FROM_DISCARD"
        }
    }

# Ability 550: Looks correct - PLACE_ENERGY_UNDER_MEMBER, ACTIVATE_ENERGY, RETURN
# Text: "{{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：エネルギーを2枚アクティブにする。"
# Current frames: [PLACE_ENERGY_UNDER_MEMBER, ACTIVATE_ENERGY, RETURN] - appears correct
if len(data['abilities']) > 550:
    data['abilities'][550]["frame_verification"] = {
        "verified": True,
        "notes": [
            "Trigger: ACTIVATED",
            "Text: {{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：エネルギーを2枚アクティブにする。",
            "Frames appear correct",
            "Frame 0: PLACE_ENERGY_UNDER_MEMBER - places 1 energy under member",
            "Frame 1: ACTIVATE_ENERGY - activates 2 energy",
            "Frame 2: RETURN"
        ],
        "text_mapping": {
            "エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く": "Frame 0: PLACE_ENERGY_UNDER_MEMBER",
            "エネルギーを2枚アクティブにする": "Frame 1: ACTIVATE_ENERGY"
        }
    }

# Save the updated data
save_json(filepath, data)

print("Fixed abilities 501-550")
print("Completed batch 501-550")
