"""
Simple Semantic Extractor

Extracts simple semantic structure from Japanese ability text:
- when (trigger)
- if (condition)
- then (effect)
- with (parameters)

Simple structure like: "when [trigger], if [condition], then [effect] with [params]"

Groups similar phrasings and makes game terms switchable.
"""

import re
from typing import Any, Dict, List, Optional, Union


# ============================================================================
# NORMALIZATION - Group similar phrasings
# ============================================================================

def normalize_text(text: str) -> str:
    """Normalize text to group similar phrasings"""
    # Remove template markers ({{icon.png|label}} → label)
    text = re.sub(r'\{\{[^|]+\|([^}]+)\}\}', r'\1', text)
    
    # Normalize verb forms (be precise to avoid breaking compound words)
    # Only normalize when followed by typical verb endings
    text = re.sub(r'引き([、。])', r'引く\1', text)
    text = re.sub(r'置き([、。])', r'置く\1', text)
    text = re.sub(r'見([、。])', r'見る\1', text)
    text = re.sub(r'加え([、。])', r'加える\1', text)
    text = re.sub(r'得([、。])', r'得る\1', text)
    
    # Normalize zone variations
    text = text.replace("デッキの一番上", "デッキの上")
    text = text.replace("デッキトップ", "デッキの上")
    text = text.replace("一番上のカード", "デッキの上のカード")
    
    return text


# ============================================================================
# OPCODE MAPPING - Map semantic patterns to game opcodes
# ============================================================================

_SEMANTIC_TO_OPCODE = {
    # Card movement
    "draw": "DRAW",
    "draw_until": "DRAW_UNTIL",
    "discard": "MOVE_TO_DISCARD",
    "discard_hand_until": "DISCARD_HAND",
    "add_to_hand": "ADD_TO_HAND",
    "look_deck": "LOOK_DECK",
    "reveal_deck": "REVEAL_CARDS",
    "search_deck": "SEARCH_DECK",
    "place": "MOVE_TO_DECK",
    "place_energy": "ENERGY_CHARGE",
    "place_energy_under_member": "PLACE_ENERGY_UNDER_MEMBER",
    
    # Member actions
    "tap": "TAP_MEMBER",
    "activate": "ACTIVATE_MEMBER",
    "activate_all": "ACTIVATE_MEMBER",
    "play_card": "PLAY_MEMBER_FROM_HAND",
    "discard_member": "MOVE_TO_DISCARD",
    "move_member": "MOVE_MEMBER",
    
    # Gains
    "gain_blade": "ADD_BLADES",
    "gain_heart": "ADD_HEARTS",
    "gain_energy": "ENERGY_CHARGE",
    
    # Score
    "score_up": "BOOST_SCORE",
    "score_down": "REDUCE_SCORE",
    
    # Other
    "negate": "NEGATE_EFFECT",
    "cost_reduction": "REDUCE_COST",
    "power_up": "BUFF_POWER",
    "ability_gain": "GRANT_ABILITY",
    "shuffle_deck": "ORDER_DECK",
    "return_to_hand": "RETURN_MEMBER_TO_HAND",
    "return_to_deck": "RETURN_MEMBER_TO_DECK",
    "retire_member": "MOVE_TO_DISCARD",
    "heal": "RECOVER_MEMBER",
    "damage": "TAP_MEMBER",
}


# ============================================================================
# GAME TERMS - Switchable parameters (words stay as words)
# ============================================================================

# Zones - where cards can be
_ZONE_PATTERNS = {
    "手札": "HAND",
    "デッキ": "DECK",
    "デッキの上": "DECK_TOP",
    "デッキの一番上": "DECK_TOP",
    "デッキトップ": "DECK_TOP",
    "一番上": "DECK_TOP",
    "デッキの下": "DECK_BOTTOM",
    "控え室": "DISCARD",
    "ステージ": "STAGE",
    "ステージの左サイドエリア": "STAGE_LEFT",
    "ステージの右サイドエリア": "STAGE_RIGHT",
    "ステージのセンター": "STAGE_CENTER",
    "エリア": "AREA",
    "ライブカード置き場": "LIVE_PLACE",
    "成功ライブカード置き場": "SUCCESS_LIVE_PLACE",
    "エネルギー置き場": "ENERGY_ZONE",
    "エネルギーデッキ": "ENERGY_DECK",
    "エール": "APPEAL",
    "エネルギー": "ENERGY",
    "すべての領域": "ALL_ZONES",
}

# Card types
_CARD_TYPES = {
    "メンバーカード": "MEMBER",
    "ライブカード": "LIVE",
    "エネルギーカード": "ENERGY",
    "カード": "CARD",
}

# Group names (common idol groups)
_GROUP_NAMES = {
    "μ's": "MUSE",
    "Aqours": "AQOURS",
    "虹ヶ咲学園スクールアイドル同好会": "NIJIGASAKI",
    "虹ヶ咲": "NIJIGASAKI",
    "Liella!": "LIELLA",
    "Hasunosora": "HASUNOSORA",
    "蓮ノ空": "HASUNOSORA",
    "BiBi": "BIBI",
    "Printemps": "PRINTEMPS",
    "lily white": "LILY_WHITE",
    "CYaRon!": "CYARON",
    "Guilty Kiss": "GUILTY_KISS",
    "A-RISE": "ARISE",
    "Saint Snow": "SAINT_SNOW",
    "Sunny Passion": "SUNNY_PASSION",
    "スクールアイドルミュージカル": "MUSICAL",
    "スリーズブーケ": "CERISE_BOUQUET",
    "DOLLCHESTRA": "DOLLCHESTRA",
    "みらくらぱーく!": "MIRAKURAPARK",
    "EdelNote": "EDELNOTE",
}

# Unit names
_UNIT_NAMES = {
    "Printemps": "PRINTEMPS",
    "lily white": "LILY_WHITE",
    "BiBi": "BIBI",
    "CYaRon!": "CYARON",
    "AZALEA": "AZALEA",
    "Guilty Kiss": "GUILTY_KISS",
    "DiverDiva": "DIVER_DIVA",
    "A・ZU・NA": "A_ZU_NA",
    "QU4RTZ": "QU4RTZ",
    "R3BIRTH": "R3BIRTH",
    "CatChu!": "CATCHU",
    "KALEIDOSCORE": "KALEIDOSCORE",
    "5yncri5e!": "SYNCRISE",
    "スリーズブーケ": "CERISE_BOUQUET",
    "DOLLCHESTRA": "DOLLCHESTRA",
    "みらくらぱーく!": "MIRA_CRA_PARK",
    "エデルノート": "EDEL_NOTE",
    "アアイスクリーム": "AISCREAM",
}

# Heart colors (these stay as numbers since they're numeric values)
_HEART_COLORS = {
    "桃ハート": 0,
    "ピンクハート": 0,
    "赤ハート": 1,
    "黄ハート": 2,
    "緑ハート": 3,
    "青ハート": 4,
    "紫ハート": 5,
}

# Triggers (these stay as strings since they're words)
_TRIGGER_NAMES = {
    "登場": "ON_PLAY",
    "ライブ成功時": "ON_LIVE_SUCCESS",
    "ライブ開始時": "ON_LIVE_START",
    "ライブ終了時": "ON_LIVE_END",
    "ターン開始": "TURN_START",
    "ターン終了": "TURN_END",
    "常時": "CONSTANT",
    "起動": "ACTIVATED",
    "アピール": "ON_REVEAL",
    "自動": "CONSTANT",
    "メイン": "MAIN",
    "エールで出": "ON_APPEAL",
    "エール": "ON_APPEAL",
    "ステージから離れた": "ON_LEAVE_STAGE",
    "ステージから控え室に置かれた": "ON_LEAVE_STAGE",
}


# ============================================================================
# TRIGGER PATTERNS - When does this happen? (numeric IDs)
# ============================================================================

_WHEN_PATTERNS = [
    "登場",
    "ライブ成功時",
    "ライブ開始時",
    "ライブ終了時",
    "ターン開始",
    "ターン終了",
    "常時",
    "起動",
    "アピール",
    "自動",
    "メイン",
    "エールで出",
    "エール",
    "ステージから離れた",
    "ステージから控え室に置かれた",
]


# ============================================================================
# CONDITION PATTERNS - If X
# ============================================================================

_IF_KEYWORDS = ["とき", "なら", "場合", "かぎり", "ないかぎり"]

# Condition types
_CONDITION_TYPES = {
    "count": r"(\d+)枚(?:以上|以下|)",
    "cost": r"コスト(\d+)(?:以上|以下|)",
    "sum_cost": r"コストの合計(?:が|)",
    "heart_sum": r"heart\d+の合計(?:が)?(\d+)(?:以上|以下|)",
    "energy_count": r"エネルギー(?:が)?(\d+)枚(?:以上|以下|)",
    "has_card": r"(.+)(?:の)?カード(?:が|)",
    "has_member": r"(.+)(?:の)?メンバー(?:が|)",
    "zone_check": r"(手札|デッキ|控え室|ステージ)(?:に|)",
    "blade_count": r"元々持つブレード(?:の数)?(?:が)?(\d+)(?:以上|以下|)",
    "blade_count_exact": r"元々持つブレード(?:の数)?(?:が)?ちょうど(\d+)",
    "energy_above": r"エネルギー(?:が)?(\d+)枚以上(?:ある|)",
    "cost_sum_below": r"コストの合計(?:が)?(\d+)以下",
}


# ============================================================================
# ACTION PATTERNS - Then do Y
# ============================================================================

_ACTION_PATTERNS = {
    # Card movement
    "draw": r"カードを(\d+)枚引(?:く|き)(?:てもよい)?",
    "draw_until": r"手札が(\d+)枚になるまでカードを引(?:く|き)",
    "discard_hand_until": r"手札(\d+)枚まで",
    "discard_hand_until_trigger": r"登場時手札(\d+)枚まで控え室に置く",
    "discard_hand_until_trigger_with_particle": r"登場手札を(\d+)枚まで控え室に置いてもよい",
    "discard_hand_optional": r"(?:.+)?手札(\d+)枚控え室に置いてもよい",
    "discard": r"(?:登場時)?(?:手札|デッキ|デッキの上)?(\d+)枚(?:まで|までまで)?(?:の)?(?:カード)?(?:を)?(?:控え室に置|捨て)(?:く|て(?:もよい)?)",
    "discard_simple": r"(\d+)枚(?:まで)?(?:控え室に置|捨て)(?:く|て(?:もよい)?)",
    "discard_group": r"(?:登場時)?「(.+)」以外の(?:.+)?(\d+)枚(?:まで)?(?:控え室に置|捨て)(?:く|て(?:もよい)?)",
    "discard_all": r"すべて(?:の)?(?:カード)?(?:を)?(?:控え室に置|捨て)(?:く|て(?:もよい)?)",
    "add_to_hand": r"(?:登場時)?(\d+)枚(?:その中から|自分の控え室から)?(?:.+)?(?:カード)?を手札に加(?:え|えてもよい)",
    "add_to_hand_discard": r"(?:.+)?(\d+)枚(?:カード)?を手札に加(?:え|えてもよい)",
    "add_to_hand_discard_full": r"(?:自分の)?(?:その)?控え室(?:から)?(?:「.+」の)?(?:.+)?(\d+)枚(?:カード)?(?:を)?手札に加(?:え|える)",
    "add_to_hand_group": r"(?:登場時)?(?:.+)?「(.+)」(?:の)?(?:.+)?(\d+)枚(?:カード)?を手札に加(?:え|えてもよい)",
    "add_to_hand_simple": r"(\d+)枚(?:.+)?(?:カード)?を手札に加(?:え|える|てもよい)",
    "add_to_hand_member": r"(?:自分の)?(?:その)?控え室(?:から)?メンバーカード(\d+)枚(?:を)?(?:カード)?手札に加(?:え|える)",
    "add_to_hand_ultra_simple": r"(\d+)枚手札に加(?:え|える)",
    "reveal_add_to_hand": r"公開して手札に加(?:え|えてもよい)",
    "discard_rest": r"残りを控え室に置(?:く|く)",
    "tap_all_condition": r"すべて.*ウェイトに(?:する|してもよい)",
    "look_deck": r"デッキ(?:の上)?(?:から)?(?:カード)?を(\d+)枚見(?:る|てもよい)",
    "reveal_deck": r"デッキ(?:の上)?(?:から)?(?:カード)?を(\d+)枚公開(?:する|してもよい)",
    "search_deck": r"デッキ(?:から)?(?:.+)?(?:カード)?を(\d+)枚選(?:ぶ|んでもよい)",
    "place": r"(\d+)枚(?:.+)?(?:デッキの上|デッキの下|ウェイト|アクティブ)?(?:に|で)?置(?:く|て(?:もよい)?)",
    "place_general": r"(?:登場時)?(\d+)枚(?:デッキ(?:の上|の下)?|エネルギーデッキ)?(?:から)?(?:カード)?(?:を)?(?:デッキの上|デッキの下|ウェイト|アクティブ)?(?:に|で)?置(?:く|て(?:もよい)?)",
    "place_energy": r"(?:登場時)?(?:エネルギーデッキ)?(?:、)?エネルギーカード(\d+)枚(?:ウェイト|アクティブ)?(?:で)?置(?:く|て(?:もよい)?)",
    "place_energy_under_member": r"エネルギー置き場.*エネルギー(\d+)枚.*このメンバーの下に置",
    "place_discard_to_deck_top": r"控え室.*カード(\d+)枚.*デッキ.*一番上に置",
    "place_discard_to_deck_top_simple": r"控え室.*カード(\d+)枚.*デッキの上に置",
    
    # Member actions
    "tap": r"メンバー(\d+)人をウェイトに(?:する|してもよい)",
    "activate": r"メンバー(\d+)人をアクティブに(?:する|してもよい)",
    "activate_all": r"すべて(?:の)?メンバーをアクティブに(?:する|してもよい)",
    "activate_with_group": r"(?:自分のステージにいる)?(?:「.+」の)?メンバー(?:を)?(\d+)人(?:まで)?アクティブに(?:する|してもよい)",
    "play_card": r"(\d+)枚(?:手札|控え室)?(?:から)?(?:コスト\d+以下の)?(?:.+)?(?:カード)?をステージに登場(?:させる|してもよい)",
    "play_card_cost_after": r"手札(?:から)?コスト\d+以下の(?:「.+」の)?(?:.+)?(?:カード)?(\d+)枚をステージに登場(?:させる|してもよい)",
    "play_card_cost_general": r"手札(?:から)?コスト\d+以下の.*(\d+)枚.*ステージに登場",
    "discard_member": r"メンバー(\d+)人(?:を)?(?:控え室に置|捨て)(?:く|て(?:もよい)?)",
    "move_member": r"メンバーを(.+)に移動(?:する|させてもよい)",
    "position_change": r"ポジションチェンジ(?:させる|してもよい)",
    "move_to_area": r"エリアに移動(?:する|させる)",
    
    # Gains
    "gain_blade": r"ブレード(?:ブレード(?:ブレード)?)?を得る",
    "gain_heart": r"heart\d+を得る",
    "gain_energy": r"エネルギーを(\d+)枚(?:アクティブに|得る)",
    
    # Score
    "score_up": r"スコアを\+\d+する",
    "score_down": r"スコアを-\d+する",
    "score_set": r"スコアを\d+にする",
    "score_plus_per": r"スコアの合計\+\d+",
    
    # Special
    "negate": r"能力を無効に(?:する|してもよい)",
    "repeat": r"この手順を(\d+)回(?:まで)?繰り返(?:す|してもよい)",
    "blade_as_heart": r"ブレードは任意の色のハートとして扱う",
    "heart_cost_check": r"必要ハート確認時",
    
    # Turn limits
    "turn_limit": r"ターン(\d+)回(?:E+|)",
    "unless_pay": r"E+支払わないかぎり",
    
    # Position change
    "position_change": r"ポジションチェンジ(?:する|してもよい)",
    
    # Conditional blade gains
    "gain_blade_conditional_energy": r"エネルギー(?:が)?(\d+)枚以上(?:ある|かぎり)、ブレード(?:ブレード(?:ブレード)?)?を得る",
    "gain_blade_conditional_cost": r"コストの合計(?:が)?(?:相手より)?低いかぎり、ブレード(?:ブレード(?:ブレード)?)?を得る",
    "gain_blade_conditional_score": r"スコア(?:の合計)?(?:が)?(?:相手より)?高いかぎり、ブレード(?:ブレード(?:ブレード)?)?を得る",
    "gain_blade_conditional_count": r"(\d+)人(?:につき|以上|かぎり)、ブレード(?:を)?(?:得る|)",
    "gain_blade_conditional_has_member": r"(?:.+)(?:の)?メンバー(?:が)?(?:いる|かぎり)、ブレード(?:ブレード(?:ブレード)?)?を得る",
    "gain_blade_conditional_live_cards": r"ライブ(?:中)?のライブカード(?:が)?(\d+)枚以上(?:ある|かぎり)、ブレード(?:ブレード(?:ブレード)?)?を得る",
    "gain_blade_conditional_moved": r"このターン(?:に)?(?:このメンバーが)?移動(?:して)?(?:いない|かぎり)、ブレード(?:ブレード(?:ブレード)?)?を得る",
    
    # Cost-based add to hand
    "add_to_hand_cost": r"(?:自分の)?(?:その)?控え室(?:から)?コスト(\d+)以下のメンバーカード(\d+)枚(?:まで)?(?:カード)?を手札に加(?:え|える)",
    
    # Zone-based conditions
    "zone_left_side": r"ステージ(?:の)?左サイドエリア(?:に登場)?(?:している|なら)",
    "zone_center": r"ステージ(?:の)?センター(?:に登場)?(?:している|なら)",
    
    # Card identity modification
    "card_identity": r"すべて.*領域.*このカード.*として扱う",
    
    # Specific card discard (by name)
    "discard_specific_cards": r"手札(?:の)?「(.+)」(?:と|、)?「(.+)」(?:と|、)?「(.+)」(?:を|、)?(?:好きな(?:枚数|組み合わせ)で合計)?(\d+)枚、(?:控え室に置|捨て)(?:く|て(?:もよい)?)",
    "discard_specific_cards_simple": r"手札(?:の)?「(.+)」(?:と|、)?「(.+)」(?:を|、)?(?:好きな枚数)?(?:控え室に置|捨て)(?:く|て(?:もよい)?)",
    
    # Center-specific tap
    "tap_center": r"センター「(.+)」(?:の)?メンバー(\d+)人をウェイトに(?:する|してもよい)",
    
    # Count-based triggers
    "trigger_member_appear_count": r"このターン、(?:自分の)?ステージ(?:に)?メンバー(?:が)?(\d+)回(?:登場した|登場したとき)",
    
    # Duration conditions
    "duration_until_reveal": r"(.+)(?:が)?(?:公開|登場)されるまで",
    "duration_until_live_end": r"ライブ終了時まで",
    
    # Restriction conditions
    "restriction_area_play": r"このターン(?:に)?ステージ(?:に)?登場したメンバー(?:が)?(?:いる)?(?:エリア|場所)(?:には)?(?:登場|プレイ)(?:できない)",
    
    # Discard by unit/group name
    "discard_by_unit": r"手札(?:の)?(?:同じ)?(?:ユニット名|グループ名)?(?:を持つ)?カード(\d+)枚(?:を)?(?:控え室に置|捨て)(?:く|て(?:もよい)?)",
    
    # Ask opponent
    "ask_opponent": r"相手に(.+)(?:と)?(?:聞く|尋ねる)",
    
    # Place member to empty area
    "place_member_empty_area": r"メンバー(?:の)?(?:いない)?エリア(?:に)?ウェイト状態で登場(?:させる|してもよい)",
    
    # Heart reduction
    "heart_cost_reduction": r"このカードを成功させるための必要ハート(?:は|を)(.+)(?:少なくなる|減る)",
    
    # Score conditions
    "score_not_below_zero": r"ライブ(?:の)?合計スコア(?:は)?0未満(?:に)?(?:なれない|ならない)",
    
    # Live success conditions
    "live_success_condition": r"ライブ成功時(.+)",
    
    # Appeal-only activation
    "appeal_only": r"この能力(?:は)?、このカード(?:が)?自分のエール(?:によって)?(?:公開)?(?:されている)?(?:場合)?(?:のみ)?発動(?:する|する)",
    
    # Movement restriction
    "movement_restriction": r"この効果(?:で)?(\d+)つのエリア(?:に)?(\d+)人以上のメンバー(?:を)?移動(?:させる)?(?:こと)?(?:は)?(?:できない)",
    
    # Heart cost reduction
    "heart_cost_reduction_per": r"(.+)(?:\d+)人(?:につき|ごとに)、このカード(?:を)?(?:成功させるための)?必要ハート(?:を)?(.+)(?:減らす|少なくなる)",
    "heart_cost_reduction_simple": r"このカード(?:を)?(?:成功させるための)?必要ハート(?:を|は)(.+)(?:減らす|少なくなる)",
    "heart_cost_reduction_per_simple": r".*(\d+)人.*必要ハート.*減らす",
    "heart_cost_reduction_card_simple": r".*カード.*枚.*必要ハート.*減らす",
    
    # Center-prefix actions
    "activate_all_center_prefix": r"センター.*すべて.*メンバー.*エネルギー.*アクティブにする",
    
    # Baton touch
    "baton_touch": r"バトンタッチしてもよい",
    
    # Negative actions
    "dont_activate": r"アクティブにしない",
    "cannot_play": r"登場できない",
    "cannot_place": r"プレイできない",
    "cannot_place_zone": r"置くことができない",
    "cannot_discard_baton": r"バトンタッチで控え室に置けない",
    
    # Heart cost changes
    "heart_cost_increase": r"必要ハート.*多くなる",
    "heart_cost_decrease": r"必要ハート.*減らす",
    "heart_cost_increase_simple": r"必要ハート.*増やす",
    
    # Cost reduction
    "cost_reduction": r"コスト.*減る",
    "cost_reduction_specific": r"能力を持たないメンバーカード.*コスト.*減る",
    "cost_reduction_per_card": r"手札.*枚につき.*コスト.*少なくなる",
    "cost_reduction_per_card_simple": r"手札.*枚につき.*少なくなる",
    "cost_increase_per_card": r"カード.*枚につき.*コスト.*する",
    
    # Score calculation
    "score_per_appeal": r"エールで出たスコア.*つき.*スコア.*合計.*加算",
    
    # Complex conditional play with cost sum
    "play_cost_sum_condition": r"コストの合計.*以下になるように.*ステージに登場",
    
    # Complex discard and place to area
    "discard_and_place_area": r"これにより控え室に置いた.*そのメンバーがいたエリアに登場",
    
    # Selection actions
    "select_player": r"自分か相手(?:を)?選(?:ぶ|んでもよい)",
    "select_card": r"カード(?:を)?(\d+)枚(?:まで)?(?:選(?:ぶ|んでもよい)|公開(?:する|してもよい))",
}


# ============================================================================
# PARAMETER EXTRACTION PATTERNS
# ============================================================================

_PARAM_PATTERNS = {
    "count": r"(\d+)枚",
    "count_people": r"(\d+)人",
    "cost": r"コスト(\d+)",
    "energy": r"E+",
    "heart": r"heart(\d+)",
    "group": r"「(.+)」",
}


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

def extract_when(text: str) -> Optional[str]:
    """Extract when/trigger from text (returns string name)"""
    for pattern in _WHEN_PATTERNS:
        if pattern in text:
            return _TRIGGER_NAMES.get(pattern)
    return None


def extract_if(text: str) -> Optional[Dict[str, Any]]:
    """Extract if/condition from text"""
    for keyword in _IF_KEYWORDS:
        if keyword in text:
            # Try to extract condition type from full text first
            for cond_type, pattern in _CONDITION_TYPES.items():
                match = re.search(pattern, text)
                if match:
                    # Extract the condition part before the keyword
                    parts = text.split(keyword)
                    if len(parts) > 0:
                        condition = parts[0].strip()
                    else:
                        condition = match.group(0)
                    return {
                        "keyword": keyword,
                        "condition": condition,
                        "type": cond_type,
                        "value": match.group(1) if match.groups() else None,
                    }
            # If no pattern matched, return the condition before the keyword
            parts = text.split(keyword)
            if len(parts) > 0:
                condition = parts[0].strip()
                return {"keyword": keyword, "condition": condition}
    return None


def extract_then(text: str) -> List[Dict[str, Any]]:
    """Extract then/actions from text"""
    actions = []
    for action_type, pattern in _ACTION_PATTERNS.items():
        match = re.search(pattern, text)
        if match:
            action = {
                "type": action_type,
                "matched": match.group(0),
            }
            # Extract count if present
            if match.groups():
                action["count"] = match.group(1)
            actions.append(action)
    return actions


def extract_all_actions(text: str) -> List[Dict[str, Any]]:
    """Extract all actions from text using pattern matching"""
    actions = []
    seen_positions = set()  # Track match positions to avoid duplicates
    
    for action_type, pattern in _ACTION_PATTERNS.items():
        for match in re.finditer(pattern, text):
            # Check if this position overlaps with already seen positions
            match_start = match.start()
            match_end = match.end()
            overlaps = any(start <= match_start < end or start < match_end <= end 
                          for start, end in seen_positions)
            
            if not overlaps:
                seen_positions.add((match_start, match_end))
                action = {
                    "type": action_type,
                    "matched": match.group(0),
                }
                # Extract count if present
                if match.groups():
                    for group in match.groups():
                        if group and group.isdigit():
                            action["count"] = group
                actions.append(action)
    
    return actions


def extract_zones(text: str) -> List[str]:
    """Extract all zones from text (normalized to game terms, returns strings)"""
    zones = []
    for zone_text, zone_code in _ZONE_PATTERNS.items():
        if zone_text in text:
            zones.append(zone_code)
    return zones


def extract_card_types(text: str) -> List[str]:
    """Extract card types from text (returns strings)"""
    card_types = []
    for card_text, card_code in _CARD_TYPES.items():
        if card_text in text:
            card_types.append(card_code)
    return card_types


def extract_groups(text: str) -> List[str]:
    """Extract group names from text (normalized, returns strings)"""
    groups = []
    for group_text, group_code in _GROUP_NAMES.items():
        if group_text in text:
            groups.append(group_code)
    # Also extract from brackets
    bracket_matches = re.findall(r"「(.+)」", text)
    for match in bracket_matches:
        if match not in groups:
            groups.append(match)
    return groups


def extract_with(text: str) -> Dict[str, Any]:
    """Extract with/parameters from text (numeric values as int, words as strings)"""
    params = {}
    
    # Count (cards) - numeric
    count_match = re.search(r"(\d+)枚", text)
    if count_match:
        params["count"] = int(count_match.group(1))
    
    # Count (people) - numeric
    people_match = re.search(r"(\d+)人", text)
    if people_match:
        params["people"] = int(people_match.group(1))
    
    # Zones - strings
    params["zones"] = extract_zones(text)
    
    # Card types - strings
    params["card_types"] = extract_card_types(text)
    
    # Cost - numeric
    cost_match = re.search(r"コスト(\d+)", text)
    if cost_match:
        params["cost"] = int(cost_match.group(1))
    
    # Energy - boolean
    if "E" in text or "エネルギー" in text:
        params["energy"] = True
    
    # Heart - numeric
    heart_match = re.search(r"heart(\d+)", text, re.IGNORECASE)
    if heart_match:
        params["heart"] = int(heart_match.group(1))
    
    # Groups - strings
    params["groups"] = extract_groups(text)
    
    # Optional - boolean
    if "てもよい" in text:
        params["optional"] = True
    
    return params


# ============================================================================
# MAIN EXTRACTION
# ============================================================================

def split_multi_trigger_abilities(normalized: str) -> List[str]:
    """Split normalized text by trigger markers"""
    # Find all trigger positions
    trigger_positions = []
    for trigger_pattern in _WHEN_PATTERNS:
        if trigger_pattern in normalized:
            start = 0
            while True:
                pos = normalized.find(trigger_pattern, start)
                if pos == -1:
                    break
                trigger_positions.append((pos, trigger_pattern))
                start = pos + 1
    
    # Sort by position
    trigger_positions.sort()
    
    # If only one trigger or none, return as single ability
    if len(trigger_positions) <= 1:
        return [normalized]
    
    # Group triggers that are close together (separated by "/")
    trigger_groups = []
    current_group = [trigger_positions[0]]
    
    for i in range(1, len(trigger_positions)):
        prev_pos, prev_trigger = trigger_positions[i-1]
        curr_pos, curr_trigger = trigger_positions[i]
        
        # Check if triggers are separated by "/" (within 5 chars)
        if curr_pos - prev_pos < 5 and "/" in normalized[prev_pos:curr_pos]:
            current_group.append((curr_pos, curr_trigger))
        else:
            trigger_groups.append(current_group)
            current_group = [(curr_pos, curr_trigger)]
    
    trigger_groups.append(current_group)
    
    # If only one group, return as single ability
    if len(trigger_groups) == 1:
        return [normalized]
    
    # Split by trigger groups
    abilities = []
    for i, group in enumerate(trigger_groups):
        group_start = group[0][0]
        if i < len(trigger_groups) - 1:
            next_group_start = trigger_groups[i + 1][0][0]
            ability_text = normalized[group_start:next_group_start]
        else:
            ability_text = normalized[group_start:]
        
        if ability_text.strip():
            abilities.append(ability_text.strip())
    
    return abilities


def extract_semantic_simple(text: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Extract simple semantic structure.
    
    Returns:
    {
        "when": "trigger",
        "if": "condition",
        "then": [{"type": "action", "count": N}],
        "with": {"count": N, "zone": "..."},
        "choices": [...],
        "sequences": [...],
        "costs": [...],
        "or_actions": [...]
    }
    """
    normalized = normalize_text(text)
    
    # For now, disable multi-trigger splitting to avoid text truncation
    # Multi-trigger abilities will be treated as single abilities with multiple triggers
    return extract_single_ability(normalized, text)


def extract_single_ability(normalized: str, original: str) -> Dict[str, Any]:
    """Extract semantic structure for a single ability"""
    clauses = re.split(r'[。:；：]', normalized)
    clauses = [c.strip() for c in clauses if c.strip()]

    result = {
        "when": None,
        "if": None,
        "then": [],
        "with": {},
        "choices": [],  # Choice structures
        "sequences": [],  # Sequential relationships
        "costs": [],  # Cost conditions
        "or_actions": [],  # "or" relationships
        "raw": original,
        "normalized": normalized,
        "clauses": clauses,
    }

    # Extract from entire text first
    result["then"] = extract_all_actions(normalized)
    result["with"] = extract_with(normalized)
    
    # Extract choice structures (以下から1つを選ぶ, etc.)
    if "以下から1つを選ぶ" in normalized or "以下から選ぶ" in normalized:
        result["choices"] = extract_choices(normalized)
    
    # Extract "or" relationships (〜か、〜)
    or_patterns = re.findall(r'([^。]+)か、([^。]+)', normalized)
    for pattern in or_patterns:
        result["or_actions"].append({
            "option1": pattern[0].strip(),
            "option2": pattern[1].strip()
        })
    
    # Extract sequential relationships (その後、, その後)
    if "その後" in normalized:
        seq_parts = normalized.split("その後")
        if len(seq_parts) > 1:
            result["sequences"] = [
                extract_all_actions(seq_parts[0]),
                extract_all_actions(seq_parts[1])
            ]
    
    # Extract cost conditions (E支払ってもよい, etc.)
    cost_match = re.search(r'(E+|エネルギー\d+枚)(支払ってもよい|支払う)', normalized)
    if cost_match:
        result["costs"].append({
            "cost": cost_match.group(1),
            "optional": "てもよい" in cost_match.group(2)
        })
    
    # Extract trigger(s) - handle "/" separated triggers
    # Exclude duration modifiers (e.g., "ライブ終了時まで" is not a trigger)
    # Only detect triggers at the start of text or after colons, not in parenthetical notes
    triggers = []
    for trigger_pattern in _WHEN_PATTERNS:
        # Check if this trigger appears as a standalone trigger
        if trigger_pattern in normalized:
            trigger_pos = normalized.find(trigger_pattern)
            
            # Check if it's at the start or after a colon or "/" (for multi-trigger)
            before_trigger = normalized[:trigger_pos]
            is_at_start = trigger_pos == 0 or before_trigger.strip() == "" or before_trigger.strip().endswith("：") or before_trigger.strip().endswith("/")
            
            # Check if it's in parenthetical note
            in_parens = False
            open_parens = normalized[:trigger_pos].count("（")
            close_parens = normalized[:trigger_pos].count("）")
            if open_parens > close_parens:
                in_parens = True
            
            # Check if it's followed by "まで" (duration modifier)
            after_trigger = normalized[trigger_pos + len(trigger_pattern):trigger_pos + len(trigger_pattern) + 10]
            is_duration = "まで" in after_trigger[:5]
            
            if is_at_start and not in_parens and not is_duration:
                triggers.append(_TRIGGER_NAMES.get(trigger_pattern))
    
    if len(triggers) == 1:
        result["when"] = triggers[0]
    elif len(triggers) > 1:
        result["when"] = triggers
    
    # Then extract per-clause for triggers, conditions, and actions
    for clause in clauses:
        # Check for if
        if_clause = extract_if(clause)
        if if_clause and not result["if"]:
            result["if"] = if_clause
    
    return result


def extract_choices(text: str) -> List[Dict[str, Any]]:
    """Extract choice structures from text"""
    choices = []
    # Split by bullet points
    parts = re.split(r'[・]', text)
    for part in parts:
        part = part.strip()
        # Filter out the "以下から1つを選ぶ" prefix and empty parts
        if part and len(part) > 2 and "以下から" not in part and "選ぶ" not in part:
            actions = extract_all_actions(part)
            choices.append({
                "text": part,
                "actions": actions
            })
    return choices
