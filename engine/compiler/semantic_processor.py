"""
Simple Semantic Extractor

Extracts simple semantic structure from Japanese ability text:
- when (trigger)
- if (condition)
- then (effect)
- with (parameters)

Simple structure like: "when [trigger], if [condition], then [effect] with [params]"
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional

from ..models.ability import Ability
from ..models.generated_enums import AbilityCostType, ConditionType, EffectType, TargetType, TriggerType


# ============================================================================
# SIMPLE PATTERNS
# ============================================================================

# When - trigger
_WHEN_PATTERNS = [
    "登場",
    "ライブ成功時",
    "ライブ開始時",
    "ターン開始",
    "ターン終了",
    "常時",
    "起動",
    "自動",
]

# If - condition
_IF_KEYWORDS = ["とき", "なら", "場合", "かぎり"]

# Then - actions
_ACTION_PATTERNS = {
    "draw": r"カードを(\d+)枚引",
    "discard": r"(\d+)枚控え室に置",
    "add_to_hand": r"(\d+)枚手札に加",
    "look": r"(\d+)枚見",
    "gain_blade": r"ブレードを得",
    "gain_heart": r"heart(\d+)を得",
    "score_up": r"スコアを\+(\d+)し",
    "tap": r"ウェイトに",
    "activate": r"アクティブに",
    "play": r"ステージに登場",
}

# With - parameters
_PARAM_PATTERNS = {
    "count": r"(\d+)枚",
    "zone": r"(手札|デッキ|控え室|ステージ)",
    "cost": r"コスト(\d+)",
    "energy": r"E+",
}


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

def extract_when(text: str) -> Optional[str]:
    """Extract when/trigger from text"""
    for pattern in _WHEN_PATTERNS:
        if pattern in text:
            return pattern
    return None


def extract_if(text: str) -> Optional[str]:
    """Extract if/condition from text"""
    for keyword in _IF_KEYWORDS:
        if keyword in text:
            # Extract the condition part before the keyword
            parts = text.split(keyword)
            if len(parts) > 0:
                return parts[0].strip()
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


def extract_with(text: str) -> Dict[str, Any]:
    """Extract with/parameters from text"""
    params = {}
    
    # Count
    count_match = re.search(r"(\d+)枚", text)
    if count_match:
        params["count"] = int(count_match.group(1))
    
    # Zone
    for zone_name in ["手札", "デッキ", "控え室", "ステージ"]:
        if zone_name in text:
            params["zone"] = zone_name
    
    # Cost
    cost_match = re.search(r"コスト(\d+)", text)
    if cost_match:
        params["cost"] = int(cost_match.group(1))
    
    # Energy
    if "E" in text or "エネルギー" in text:
        params["energy"] = True
    
    return params


# ============================================================================
# MAIN EXTRACTION
# ============================================================================

def extract_semantic_simple(text: str) -> Dict[str, Any]:
    """
    Extract simple semantic structure.
    
    Returns:
    {
        "when": "trigger",
        "if": "condition",
        "then": [{"type": "action", "count": N}],
        "with": {"count": N, "zone": "..."}
    }
    """
    # Split clauses
    clauses = [c.strip() for c in re.split(r"[。:；：]", text) if c.strip()]
    
    result = {
        "when": None,
        "if": None,
        "then": [],
        "with": {},
        "raw": text,
        "clauses": clauses,
    }
    
    for clause in clauses:
        # Check for when
        when = extract_when(clause)
        if when and not result["when"]:
            result["when"] = when
            continue
        
        # Check for if
        if_clause = extract_if(clause)
        if if_clause and not result["if"]:
            result["if"] = if_clause
            continue
        
        # Check for then actions
        actions = extract_then(clause)
        if actions:
            result["then"].extend(actions)
        
        # Extract parameters
        params = extract_with(clause)
        if params:
            result["with"].update(params)
    
    return result


def split_raw_text_into_ability_sections(raw_text: str) -> list[str]:
    """Split authored ability text into trigger-sized sections when multiple abilities share a card."""
    if not raw_text:
        return []

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return []

    trigger_line = re.compile(r"^\{\{[^}]+\}\}")
    sections: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if trigger_line.match(line) and current:
            sections.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append(current)

    return ["\n".join(section).strip() for section in sections if section]


def select_ability_raw_text(raw_text: str, ability_index: int, entry: dict[str, Any]) -> str:
    """Select the most specific authored text for an ability before cost inference."""
    entry_text = str(
        entry.get("raw_text", "")
        or entry.get("primary_text_jp", "")
        or entry.get("primary_text_en", "")
        or ""
    ).strip()
    if entry_text:
        return entry_text

    sections = split_raw_text_into_ability_sections(raw_text)
    if sections:
        if 0 <= ability_index < len(sections):
            return sections[ability_index]
        if len(sections) == 1:
            return sections[0]

    return raw_text


def infer_trigger_id_from_text(text: str) -> int:
    """Infer a trigger enum value from the authored text markers."""
    semantic_form = extract_semantic_form_from_text(text)
    markers = semantic_form.get("trigger_markers", [])
    if not isinstance(markers, list):
        markers = []
    marker = str(markers[0]) if markers else ""
    trigger_map = {
        "登場": TriggerType.ON_PLAY,
        "起動": TriggerType.ACTIVATED,
        "常時": TriggerType.CONSTANT,
        "アピール": TriggerType.ON_PLAY,
        "メイン": TriggerType.ACTIVATED,
        "ターン開始": TriggerType.TURN_START,
        "ターン終了": TriggerType.TURN_END,
        "ライブ開始時": TriggerType.ON_LIVE_START,
        "自動": TriggerType.ON_PLAY,
        "ライブ成功時": TriggerType.ON_LIVE_SUCCESS,
    }
    trigger = trigger_map.get(marker, TriggerType.ON_PLAY)
    return int(trigger)


def build_ability_from_text(card_no: str, raw_text: str, ability_index: int) -> Ability:
    """Build a runtime Ability object directly from authored text."""
    ability_text = select_ability_raw_text(raw_text, ability_index, {})
    semantic_form = extract_semantic_form_from_text(ability_text)
    trigger_id = infer_trigger_id_from_text(ability_text)
    frames = semantic_form_to_frame_program(semantic_form).get("frames", [])
    if not isinstance(frames, list):
        frames = []
    return Ability(
        raw_text=ability_text,
        trigger=TriggerType(trigger_id),
        effects=[],
        frame_program={"frames": frames},
        semantic_form=semantic_form,
        costs=[],
        conditions=[],
        is_once_per_turn=False,
        requires_selection=False,
        card_no=card_no,
    )

_OPTIONAL_DISCARD_RE = re.compile(r"^手札を(?P<count>\d+)枚控え室に置いてもよい$")
_OPTIONAL_DISCARD_LIMIT_RE = _OPTIONAL_DISCARD_RE
_DISCARD_HAND_RE = re.compile(r"^手札を(?P<count>\d+)枚控え室に置く$")
_PLAY_MEMBER_FROM_HAND_RE = re.compile(r"^手札から(?P<count>\d+)枚?の?メンバーカードをライブに出す$")
_DRAW_AND_MOVE_BOTTOM_RE = re.compile(r"^デッキの上からカードを(?P<draw_count>\d+)枚見て、その中から(?P<move_count>\d+)枚をデッキの下に置く$")
_ADD_TO_HAND_FROM_DISCARD_RE = re.compile(r"^控え室から(?P<count>\d+)枚手札に加える$")
_ACTIVATE_ENERGY_RE = re.compile(r"^(?:E|エネルギー)(?:(?P<count>\d+)枚?)?(?:を)?アクティブに(?:する|してもよい)$")
_DISCARD_TO_BOTTOM_RE = re.compile(r"^(?:残りを)?控え室に置く$")
_PER_MEMBER_DRAW_RE = re.compile(r"^.+メンバー(?P<count>\d+)人につき、カードを(?P<draw_count>\d+)枚引く$")
_PER_MEMBER_DRAW_RE2 = _PER_MEMBER_DRAW_RE
_DISCARD_SPECIFIC_CARD_RE = _DISCARD_HAND_RE
_BOTH_PLAYERS_RE = re.compile(r"^(?:\u81ea\u5206\u3068\u76f8\u624b\u306f(?:\u305d\u308c\u305e\u308c)?|\u53cc\u65b9|\u4e21\u8005\u306f)")
_LOOK_AND_REVEAL_RE = re.compile(r"^\u81ea\u5206\u306e\u30c7\u30c3\u30ad\u306e\u4e0a\u304b\u3089\u30ab\u30fc\u30c9\u3092(?P<count>\d+)\u679a\u898b\u308b$")
_COMPOUND_COST_RE = re.compile(r"^(?:(?P<count>\d+)\u679a)?(?:\u3053\u306e\u30e1\u30f3\u30d0\u30fc\u3092)?\u30a6\u30a7\u30a4\u30c8\u306b\u3057\u3066\u3082\u3088\u3044$")
_MOVE_MEMBER_TO_DISCARD_RE = re.compile(r"^(?:.*(?:\u30a6\u30a7\u30a4\u30c8\u306b\u3059\u308b|\u63a7\u3048\u5ba4\u306b\u7f6e\u304f).*)$")
_CHOOSE_PLAYER_RE = re.compile(r"^(?:\u76f8\u624b|\u81ea\u5206|\u81ea\u5206\u3068\u76f8\u624b)$")
_COMPLEX_REORDER_RE = re.compile(r"^(?:\u597d\u304d\u306a\u9806\u756a\u3067\u30c7\u30c3\u30ad\u306e\u4e0a\u306b\u7f6e\u304d|\u30c7\u30c3\u30ad\u306e\u4e0a\u304b\u3089\u30ab\u30fc\u30c9\u3092\u4e26\u3079\u66ff\u3048\u308b)$")
_TURN_LIMIT_ENERGY_RE = re.compile(r"^(?:\u30bf\u30fc\u30f31\u56de.*)$")
_TURN_LIMIT_DISCARD_RE = re.compile(r"^(?:\u30bf\u30fc\u30f31\u56de.*\u624b\u672d\u3092(?P<count>\d+)\u679a\u63a7\u3048\u5ba4\u306b\u7f6e\u304f.*)$")
_TURN_LIMIT_TAP_RE = re.compile(r"^(?:\u30bf\u30fc\u30f31\u56de.*\u30a6\u30a7\u30a4\u30c8\u306b\u3059\u308b.*)$")
_TURN_LIMIT_MEMBER_LEAVE_STAGE_RE = re.compile(r"^(?:.*\u30b9\u30c6\u30fc\u30b8\u3092\u96e2\u308c\u305f\u3068\u304d.*)$")
_TURN_LIMIT_ENERGY_DISCARD_RE = re.compile(r"^(?:\u30bf\u30fc\u30f31\u56de.*\u624b\u672d\u3092(?P<count>\d+)\u679a\u63a7\u3048\u5ba4\u306b\u7f6e\u304f.*)$")
_POSITION_CHANGE_RE = re.compile(r"^(?:\u30dd\u30b8\u30b7\u30e7\u30f3\u30c1\u30a7\u30f3\u30b8(?:.*)?|\u4f4d\u7f6e\u3092\u5909\u3048\u308b(?:.*)?)$")
_LIVE_SUCCESS_TRIGGER_RE = re.compile(r"^\u30e9\u30a4\u30d6\u6210\u529f\u6642$")
_CENTER_PREFIX_RE = re.compile(r"^(?:\u30bb\u30f3\u30bf\u30fc|\u81ea\u5206\u306e\u30b9\u30c6\u30fc\u30b8\u306e\u30bb\u30f3\u30bf\u30fc)$")
_LIVE_SUCCESS_DRAW_RE = re.compile(r"^(?:.*\u30e9\u30a4\u30d6\u6210\u529f\u6642.*\u30ab\u30fc\u30c9\u3092(?P<count>\d+)\u679a\u5f15\u304f.*)$")
_LIVE_SUCCESS_CHOOSE_RE = re.compile(r"^(?:.*\u30e9\u30a4\u30d6\u6210\u529f\u6642.*)$")
_LIVE_SUCCESS_DISCARD_RE = re.compile(r"^(?:.*\u30e9\u30a4\u30d6\u6210\u529f\u6642.*\u63a7\u3048\u5ba4\u306b\u7f6e\u304f.*)$")
_LIVE_SUCCESS_ADD_TO_HAND_RE = re.compile(r"^(?:.*\u30e9\u30a4\u30d6\u6210\u529f\u6642.*\u624b\u672d\u306b\u52a0\u3048\u308b.*)$")
_LIVE_SUCCESS_ENERGY_TO_STAGE_RE = re.compile(r"^(?:.*\u30e9\u30a4\u30d6\u6210\u529f\u6642.*\u30a6\u30a7\u30a4\u30c8\u72b6\u614b\u3067\u7f6e\u304f.*)$")
_OPPONENT_TAP_ACTIVE_RE = re.compile(r"^(?:.*\u76f8\u624b\u306e\u30b9\u30c6\u30fc\u30b8.*\u30e1\u30f3\u30d0\u30fc(?P<count>\d+)?\u4eba.*\u30a6\u30a7\u30a4\u30c8\u306b\u3059\u308b.*|.*\u76f8\u624b.*\u30a6\u30a7\u30a4\u30c8\u306b\u3059\u308b.*)$")
_ENERGY_TO_MEMBER_RE = re.compile(r"^(?:.*\u30a8\u30cd\u30eb\u30ae\u30fc\u30ab\u30fc\u30c9\u3092(?P<count>\d+)\u679a\u30a6\u30a7\u30a4\u30c8\u72b6\u614b\u3067\u7f6e\u304f.*)$")
_GAIN_BLADE_DURATION_RE2 = re.compile(r"^(?!)")
_ACTIVATE_ABILITY_RE = re.compile(r"^(?!)")
_ACTIVATE_ALL_MEMBERS_AND_ENERGY_RE = re.compile(r"^(?!)")
_ACTIVATE_ALL_MEMBERS_RE = re.compile(r"^(?!)")
_ACTIVATE_GAIN_BLADE_RE = re.compile(r"^(?!)")
_ACTIVATE_MEMBER_GROUP_RE = re.compile(r"^(?!)")
_ADD_CHOSEN_CARD_TO_HAND_RE = re.compile(r"^(?!)")
_ADD_TO_HAND_AND_DISCARD_REMAINDER_RE = re.compile(r"^(?!)")
_ADD_TO_HAND_EQUAL_COUNT_RE = re.compile(r"^(?!)")
_ADD_TO_HAND_LIVE_PLACE_RE = re.compile(r"^(?!)")
_AREA_ACTIVATE_ENERGY_RE = re.compile(r"^(?!)")
_AREA_CONDITIONAL_DRAW_RE = re.compile(r"^(?!)")
_AREA_CONDITIONAL_RE = re.compile(r"^(?!)")
_AREA_DRAW_DISCARD_RE = re.compile(r"^(?!)")
_BOTH_PLAYERS_PLAY_MEMBER_COST_RE = re.compile(r"^(?!)")
_BOTH_PLAYERS_PLAY_MEMBER_RE = re.compile(r"^(?!)")
_CARD_IDENTITY_RULE_RE = re.compile(r"^(?!)")
_CENTER_ACTIVATE_ALL_RE = re.compile(r"^(?!)")
_CENTER_TURN_LIMIT_COMPOUND_RE = re.compile(r"^(?!)")
_CENTER_TURN_LIMIT_TAP_RE = re.compile(r"^(?!)")
_CHOICE_ACTIVATE_ENERGY_RE = re.compile(r"^(?!)")
_CHOOSE_CARDS_DIFFERENT_NAMES_RE = re.compile(r"^(?!)")
_CHOOSE_CARD_COST_LIMIT_RE = re.compile(r"^(?!)")
_CHOOSE_CARD_GROUP_RE = re.compile(r"^(?!)")
_CHOOSE_LIVE_CARD_RE = re.compile(r"^(?!)")
_CHOOSE_MEMBER_COST_GROUP_RE = re.compile(r"^(?!)")
_CHOOSE_MEMBER_COST_RE = re.compile(r"^(?!)")
_CHOOSE_MEMBER_FROM_STAGE_RE = re.compile(r"^(?!)")
_CHOOSE_MEMBER_GROUP_RE = re.compile(r"^(?!)")
_CHOOSE_QUESTION_RE = re.compile(r"^(?!)")
_CHOOSE_SPECIFIC_CARD_RE = re.compile(r"^(?!)")
_COMPLEX_CONDITIONAL_WHEN_RE = re.compile(r"^(?!)")
_CONDITIONAL_AREA_RESTRICTION_RE = re.compile(r"^(?!)")
_CONDITIONAL_ENERGY_PAYMENT_RE = re.compile(r"^(?!)")
_CONDITIONAL_NOT_BATON_TOUCH_RE = re.compile(r"^(?!)")
_DISCARD_EXCEPT_RE = re.compile(r"^(?!)")
_DISCARD_OPPONENT_TOP_RE = re.compile(r"^(?!)")
_DISCARD_TO_TOP_OPTIONAL_RE = re.compile(r"^(?!)")
_DISCARD_TO_TOP_OPTIONAL_SIMPLE_RE = re.compile(r"^(?!)")
_DISCARD_TO_TOP_ORDER_RE = re.compile(r"^(?!)")
_DISCARD_TO_TOP_RE = re.compile(r"^(?!)")
_DISCARD_WITHOUT_BLADE_HEART_RE = re.compile(r"^(?!)")
_DISTRIBUTE_CARDS_RE = re.compile(r"^(?!)")
_DISTRIBUTE_TWO_RE = re.compile(r"^(?!)")
_DRAW_OPTIONAL_RE = re.compile(r"^(?!)")
_ENERGY_PAY_LIMIT_RE = re.compile(r"^(?!)")
_GAIN_BLADE_DURATION_RE = re.compile(r"^(?!)")
_HEART_COST_REDUCTION_PER_MEMBER_RE = re.compile(r"^(?!)")
_HEART_SELECTION_OR_RE = re.compile(r"^(?!)")
_LOOK_AND_CHOOSE_GROUP_RE = re.compile(r"^(?!)")
_LOOK_OPPONENT_DECK_MULTI_RE = re.compile(r"^(?!)")
_LOOK_OPPONENT_DECK_RE = re.compile(r"^(?!)")
_MOVE_MEMBERS_ANY_AREA_RE = re.compile(r"^(?!)")
_MOVE_TO_AREA_RE = re.compile(r"^(?!)")
_MULTI_AREA_MARKER_RE = re.compile(r"^(?!)")
_NEGATE_ABILITY_RE = re.compile(r"^(?!)")
_NO_LIVE_CARD_DISCARD_RE = re.compile(r"^(?!)")
_OPPONENT_CHOOSE_MEMBER_EXCEPT_RE = re.compile(r"^(?!)")
_OPPONENT_DISCARD_LIVE_RE = re.compile(r"^(?!)")
_OPPONENT_DISCARD_TO_BOTTOM_RE = re.compile(r"^(?!)")
_OPPONENT_GAIN_BLADE_RE = re.compile(r"^(?!)")
_OPPONENT_TAP_ALL_COST_LIMIT_RE = re.compile(r"^(?!)")
_OPPONENT_TAP_BLADE_COUNT_RE = re.compile(r"^(?!)")
_OPPONENT_TAP_COST_EXACT_RE = re.compile(r"^(?!)")
_OR_CONDITIONAL_RE = re.compile(r"^(?!)")
_PER_ENERGY_DRAW_RE = re.compile(r"^(?!)")
_PER_MEMBER_ENERGY_RE = re.compile(r"^(?!)")
_PER_MEMBER_HEART_GAIN_RE = re.compile(r"^(?!)")
_PER_MEMBER_LOOK_RE = re.compile(r"^(?!)")
_PLACE_CARD_AT_POSITION_RE = re.compile(r"^(?!)")
_PLAY_MEMBER_CONDITIONAL_RE = re.compile(r"^(?!)")
_PLAY_MEMBER_COST_LIMIT_AREA_RE = re.compile(r"^(?!)")
_PLAY_MEMBER_COST_LIMIT_RE = re.compile(r"^(?!)")
_PLAY_MEMBER_FROM_HAND_COST_RE = re.compile(r"^(?!)")
_PLAY_MEMBER_OPTIONAL_RE = re.compile(r"^(?!)")
_POSITION_CHANGE_OPPONENT_RE = re.compile(r"^(?!)")
_REDUCE_HEART_COST_RE = re.compile(r"^(?!)")
_REPEAT_PROCEDURE_RE = re.compile(r"^(?!)")
_RESPAWN_MEMBER_RE = re.compile(r"^(?!)")
_REVEAL_ALL_DISCARD_RE = re.compile(r"^(?!)")
_REVEAL_AND_PLACE_GAIN_BLADE_RE = re.compile(r"^(?!)")
_REVEAL_GROUP_OPTIONAL_RE = re.compile(r"^(?!)")
_REVEAL_HAND_TO_OPPONENT_RE = re.compile(r"^(?!)")
_REVEAL_LIVE_OPTIONAL_RE = re.compile(r"^(?!)")
_REVEAL_LIVE_TO_BOTTOM_RE = re.compile(r"^(?!)")
_REVEAL_TOP_RE = re.compile(r"^(?!)")
_REVEAL_UNTIL_LIVE_RE = re.compile(r"^(?!)")
_SCORE_CONDITIONAL_RE = re.compile(r"^(?!)")
_SCORE_MODIFICATION_RE = re.compile(r"^(?!)")
_SCORE_PER_HEART_RE = re.compile(r"^(?!)")
_SCORE_PER_LIVE_CARD_RE = re.compile(r"^(?!)")
_SCORE_PER_MEMBER_NAME_RE = re.compile(r"^(?!)")
_SCORE_PER_MEMBER_RE = re.compile(r"^(?!)")
_SEQUENTIAL_ADD_TO_HAND_GROUP_RE = re.compile(r"^(?!)")
_SEQUENTIAL_ADD_TO_HAND_RE = re.compile(r"^(?!)")
_SEQUENTIAL_CHOOSE_AREA_RE = re.compile(r"^(?!)")
_SEQUENTIAL_PLACE_CARD_RE = re.compile(r"^(?!)")
_SEQUENTIAL_REVEAL_TOP_RE = re.compile(r"^(?!)")
_SUCCESS_LIVE_PLACE_DISCARD_RE = re.compile(r"^(?!)")
_TAP_GROUP_NAME_RE = re.compile(r"^(?!)")
_TAP_GROUP_NAME_SIMPLE_RE = re.compile(r"^(?!)")
_TAP_GROUP_OPTIONAL_RE = re.compile(r"^(?!)")
_TAP_GROUP_SIMPLE_RE = re.compile(r"^(?!)")
_TAP_OPPONENT_COST_LIMIT_RE = re.compile(r"^(?!)")
_TAP_OPTIONAL_RE = re.compile(r"^(?!)")
_TURN_COUNT_CONDITIONAL_RE = re.compile(r"^(?!)")
_TURN_LIMIT_COMPLEX_CONDITIONAL_RE = re.compile(r"^(?!)")
_TURN_LIMIT_COMPOUND_CHOICE_RE = re.compile(r"^(?!)")
_TURN_LIMIT_DECK_TO_DISCARD_RE = re.compile(r"^(?!)")
_TURN_LIMIT_EEE_RE = re.compile(r"^(?!)")
_TURN_LIMIT_ENERGY_TO_MEMBER_RE = re.compile(r"^(?!)")
_DISCARD_SAME_UNIT_RE = re.compile(r"^(?!)")
_DISCARD_SAME_GROUP_RE = re.compile(r"^(?!)")
_DISCARD_SPECIFIC_CARDS_RE = re.compile(r"^(?!)")
_DISCARD_SPECIFIC_CARDS_SIMPLE_RE = re.compile(r"^(?!)")
_DISCARD_SPECIFIC_MEMBER_RE = re.compile(r"^(?!)")
_DISCARD_TOP_OPTIONAL_RE = re.compile(r"^(?!)")
_DISCARD_TO_BOTTOM_OPTIONAL_RE = re.compile(r"^(?!)")
_HEART_SELECTION_RE = re.compile(r"^heart(?P<count>\d+)(?:\s*heart(?P=count))*.*$")
_COLOR_SELECTION_RE = re.compile(r"^heart(?P<count>\d+)(?:.*)$")

_CONDITION_OPCODE_MAP = {
    "HAS_MEMBER": ConditionType.HAS_MEMBER,
    "COUNT_STAGE": ConditionType.COUNT_STAGE,
    "COUNT_HAND": ConditionType.COUNT_HAND,
    "COUNT_DISCARD": ConditionType.COUNT_DISCARD,
    "COUNT_ENERGY": ConditionType.COUNT_ENERGY,
    "COUNT_HEARTS": ConditionType.COUNT_HEARTS,
    "COUNT_BLADES": ConditionType.COUNT_BLADES,
    "COUNT_LIVE_ZONE": ConditionType.COUNT_LIVE_ZONE,
    "COUNT_LIVE_HEARTS": ConditionType.COUNT_LIVE_HEARTS,
    "COUNT_SUCCESS_LIVE": ConditionType.COUNT_SUCCESS_LIVE,
    "COUNT_SUCCESS_LIVE_SCORE": ConditionType.COUNT_SUCCESS_LIVE_SCORE,
    "COUNT_GROUP": ConditionType.COUNT_GROUP,
    "GROUP_FILTER": ConditionType.GROUP_FILTER,
    "IS_CENTER": ConditionType.IS_CENTER,
    "BATON": ConditionType.BATON,
    "SCORE_COMPARE": ConditionType.SCORE_COMPARE,
    "OPPONENT_ENERGY_DIFF": ConditionType.OPPONENT_ENERGY_DIFF,
    "SUCCESS_PILE_COUNT": ConditionType.SUCCESS_PILE_COUNT,
    "DISCARDED_CARDS": ConditionType.DISCARDED_CARDS,
    "AREA_CHECK": ConditionType.AREA_CHECK,
    "TARGET_MEMBER_HAS_NO_HEARTS": ConditionType.TARGET_MEMBER_HAS_NO_HEARTS,
    "HAS_LIVE_CARD": ConditionType.HAS_LIVE_CARD,
    "HAS_EXCESS_HEART": ConditionType.HAS_EXCESS_HEART,
    "HAS_KEYWORD": ConditionType.HAS_KEYWORD,
    "MAIN_PHASE": ConditionType.MAIN_PHASE,
    "SYNC_COST": ConditionType.SYNC_COST,
    "TOTAL_BLADES": ConditionType.TOTAL_BLADES,
    "SCORE_TOTAL_CHECK": ConditionType.SCORE_TOTAL_CHECK,
    "COUNT_BLADE_HEART_TYPES": ConditionType.COUNT_BLADE_HEART_TYPES,
    "IS_SELF_MOVE": ConditionType.IS_SELF_MOVE,
    "DECK_REFRESHED": ConditionType.DECK_REFRESHED,
    "HEART_LEAD": ConditionType.HEART_LEAD,
    "TYPE_CHECK": ConditionType.TYPE_CHECK,
    "SUM_VALUE": ConditionType.SUM_VALUE,
    "CHECK_GROUP": ConditionType.COUNT_GROUP,
    "CHECK_HAS_COLOR": ConditionType.HAS_COLOR,
    "CHECK_BATON": ConditionType.BATON,
    "CHECK_LIFE_LEAD": ConditionType.LIFE_LEAD,
    "CHECK_IS_CENTER": ConditionType.IS_CENTER,
    "CHECK_HAS_KEYWORD": ConditionType.HAS_KEYWORD,
    "CHECK_SELF_IS_GROUP": ConditionType.SELF_IS_GROUP,
    "CHECK_HEART_COMPARE": ConditionType.HEART_COMPARE,
    "CHECK_TYPE_CHECK": ConditionType.TYPE_CHECK,
    "CHECK_SCORE_COMPARE": ConditionType.SCORE_COMPARE,
}

_COST_OPCODE_MAP = {
    "PAY_ENERGY": AbilityCostType.ENERGY,
    "SET_TAPPED": AbilityCostType.TAP_SELF,
    "TAP_MEMBER": AbilityCostType.TAP_MEMBER,
    "MOVE_TO_DISCARD": AbilityCostType.DISCARD_HAND,
    "SELECT_CARDS": AbilityCostType.SELECT_CARDS,
    "SELECT_MEMBER": AbilityCostType.SELECT_MEMBER,
}

_TARGET_SLOT_MAP = {
    4: TargetType.MEMBER_SELF,
    6: TargetType.CARD_HAND,
    7: TargetType.CARD_DISCARD,
}

_ENERGY_KEYWORDS = {"activated_energy", "DID_ACTIVATE_ENERGY", "DID_ACTIVATE_ENERGY_BY_GROUP"}
_MEMBER_KEYWORDS = {"activated_member", "DID_ACTIVATE_MEMBER", "DID_ACTIVATE_MEMBER_BY_GROUP"}
_RAW_UNIQUE_NAMES_OPCODE = "CHECK_UNIQUE_NAMES"

_TEMPLATE_TAG_RE = re.compile(r"\{\{([^}|]+)(?:\|([^}]+))?\}\}")
_NUMERIC_RUN_RE = re.compile(r"\d+")
_CLAUSE_SPLIT_RE = re.compile(r"[。:\n;；：]+")
_TRIGGER_MARKERS = ("登場", "起動", "常時", "アピール", "メイン", "ターン開始", "ターン終了", "ライブ開始時", "自動")
_AREA_MARKERS = ("【左サイド】", "【センター】", "【右サイド】", "LEFT SIDE", "CENTER", "RIGHT SIDE")

# General patterns for core game mechanics
_DRAW_CARDS_RE = re.compile(r"^カードを(?P<count>\d+)枚引(?:く|き)(?:てもよい)?$")
_DRAW_UNTIL_RE = re.compile(r"^手札が(?P<count>\d+)枚になるまでカードを引く$")
_DISCARD_CARDS_RE = re.compile(r"^(?:自分の)?手札を(?P<count>\d+)枚(?:まで)?控え室に置(?:いてもよい|く)$")
_DISCARD_FROM_DECK_RE = re.compile(r"^(?:自分の)?デッキの(?:一番上の)?カードを(?P<count>\d+)枚控え室に置(?:いてもよい|く)$")
_ADD_TO_HAND_RE = re.compile(r"^(?:その中から)?(?:自分の控え室から)?(?:.+)?カードを(?P<count>\d+)枚(?:まで)?手札に加(?:えてもよい|え)$")
_TAP_MEMBER_RE = re.compile(r"^(?:「.+」の)?メンバー(?P<count>\d+)人をウェイトに(?:してもよい|する)$")
_ACTIVATE_MEMBER_RE = re.compile(r"^(?:「.+」の)?メンバー(?P<count>\d+)人をアクティブに(?:してもよい|する)$")
_GAIN_BLADE_RE = re.compile(r"^ブレード(?:ブレード(?:ブレード)?)?を得る$")
_SCORE_MOD_RE = re.compile(r"^(?:このカードの|ライブの)?スコアを\+\d+する$")
_PAY_ENERGY_RE = re.compile(r"^E+(?:(?P<count>\d+)つ)?支払(?:ってもよい|わないかぎり)$")
_PLAY_MEMBER_RE = re.compile(r"^(?:手札から|自分の控え室から)(?:コスト\d+以下の)?(?:.+の)?メンバーカードを(?P<count>\d+)枚ステージに登場させる$")
_LOOK_CARDS_RE = re.compile(r"^(?:自分の)?デッキの(?:一番上|上から)からカードを(?P<count>\d+)枚見る$")
_REVEAL_CARDS_RE = re.compile(r"^(?:自分の)?デッキの(?:一番上の)?カードを(?P<count>\d+)枚公開(?:してもよい|する)$")

# Turn limit patterns - fix to actually filter
_TURN_LIMIT_PREFIX_RE = re.compile(r"^(?:(?:センター)?ターン\d+回)(?P<rest>.+)$")

# Trigger patterns
_TRIGGER_RE = re.compile(r"^(?P<trigger>登場|起動|常時|アピール|メイン|ターン開始|ターン終了|ライブ開始時|自動|ライブ成功時)(?P<rest>.*)$")

# Conditional patterns
_CONDITIONAL_WHEN_RE = re.compile(r"^(?P<condition>.+)とき、(?P<effect>.+)$")
_CONDITIONAL_IF_RE = re.compile(r"^(?P<condition>.+)なら、(?P<effect>.+)$")
_CONDITIONAL_UNLESS_RE = re.compile(r"^(?P<condition>.+)かぎり、(?P<effect>.+)$")

# Sequential marker
_SEQUENTIAL_MARKER_RE = re.compile(r"^その後、")

# Per-member patterns
_PER_MEMBER_RE = re.compile(r"^(?P<target>.+)メンバー(?P<count>\d+)人につき、(?P<effect>.+)$")

# Card identity/modifier rules (skip for now)
_CARD_IDENTITY_RE = re.compile(r"^すべての領域にあるこのカードは.+$")
_MODIFIER_RULE_RE = re.compile(r"^この能力では.+$")
_EFFECT_FLOOR_RE = re.compile(r"^この効果では.+$")
_HEART_COST_REDUCTION_CONDITIONAL_RE = re.compile(r"^自分のステージにいる、.+(?:の)?メンバー(?P<count>\d+)人につき、このカードを成功させるための必要ハートをheart\d+減らす$")
_HEART_COST_LIMIT_RE = re.compile(r"^この能力ではheart\d+は\d+つまでしか減らない$")
_ENERGY_MEMBER_TO_DECK_RE = re.compile(r"^自分のステージにいるメンバー(?P<count>\d+)人の下にあるエネルギーカードを、好きな枚数エネルギーデッキに置いてもよい$")
_REVEAL_PER_MEMBER_RE = re.compile(r"^自分のデッキの上から、自分と相手のステージにいるメンバー(?P<count>\d+)人につき、\d+枚公開する$")
_OPPONENT_TAP_BLADE_CONDITIONAL_RE = re.compile(r"^相手のステージにいる元々持つブレードが\d+以下のメンバー(?P<count>\d+)人をウェイトにする$")
_ACTIVATE_GROUP_SIMPLE_RE = re.compile(r"^自分のステージにいる.+(?:の)?メンバーをアクティブにする$")
_SEQUENTIAL_DISCARD_RE = re.compile(r"^その後、これにより公開したカードを控え室に置く$")
_LIVE_PLACE_SCORE_MOD_RE = re.compile(r"^自分の成功ライブカード置き場にあるカード(?P<count>\d+)枚につき、このカードのスコアを\+\d+し、.+$")
_LIVE_PLACE_HEART_REDUCTION_RE = re.compile(r"^自分のライブカード置き場にある.+(?:の)?カード(?P<count>\d+)枚につき、このカードの必要ハートをheart\d+減らす$")
_LIVE_PLACE_HEART_INCREASE_RE = re.compile(r"^自分の成功ライブカード置き場にあるカード(?P<count>\d+)枚につき、このカードを成功させるための必要ハートはheart\d+少なくなる$")
_LOOK_BASED_LIVE_SCORE_RE = re.compile(r"^自分のデッキの上から、自分のライブの合計スコアに\d+を足した数に等しい枚数見る$")
_CHOOSE_FROM_REVEALED_FILTER_RE = re.compile(r"^エールにより公開された自分のカードの中から、.+(?:の)?メンバーカードか、.+(?:の)?ライブカードを(?P<count>\d+)枚手札に加える$")
_LIVE_SUCCESS_DRAW_DISCARD_RE = re.compile(r"^ライブ成功時カードを(?P<draw_count>\d+)枚引き、手札を(?P<discard_count>\d+)枚控え室に置く$")
_DISCARD_TO_TOP_OPTIONAL_MEMBER_RE = re.compile(r"^自分の控え室にあるメンバーカード(?P<count>\d+)枚をデッキの一番上に置いてもよい$")
_LIVE_PLACE_SCORE_HEART_MOD_RE = re.compile(r"^自分の成功ライブカード置き場にあるカード名が「.+」のカード(?P<count>\d+)枚につき、.+$")
_HEART_COST_REDUCTION_LIVE_PLACE_RE = re.compile(r"^自分のライブカード置き場にあるこのカード以外の.+(?:の)?カード(?P<count>\d+)枚につき、このカードの必要ハートをheart\d+heart\d+減らす$")
_LIVE_SUCCESS_BOTH_ENERGY_RE = re.compile(r"^ライブ成功時自分と相手はそれぞれ、自身のエネルギーデッキから、エネルギーカードを(?P<count>\d+)枚ウェイト状態で置く$")
_LIVE_SUCCESS_DECK_TO_DISCARD_RE = re.compile(r"^ライブ成功時自分のデッキの上からカードを(?P<count>\d+)枚控え室に置く$")
_LIVE_SUCCESS_ENERGY_PAY_RE = re.compile(r"^ライブ成功時E+支払ってもよい$")
_LIVE_SCORE_MODIFICATION_RE = re.compile(r"^ライブの合計スコアを\+\d+する$")
_LIVE_SUCCESS_LOOK_RE = re.compile(r"^ライブ成功時自分のデッキの上からカードを(?P<count>\d+)枚見る$")
_LIVE_SCORE_FLOOR_RE = re.compile(r"^この効果ではライブの合計スコアは\d+未満にはならない$")
_SIMPLE_ADD_TO_HAND_RE = re.compile(r"^その中からカードを(?P<count>\d+)枚手札に加える$")
_LIVE_SUCCESS_ENERGY_PAY_COUNT_RE = re.compile(r"^ライブ成功時E+(?P<count>\d+)支払ってもよい$")
_LIVE_SUCCESS_CONDITIONAL_RESTRICTION_RE = re.compile(r"^ライブ成功時このターン、ライブに勝利するプレイヤーを決定するとき、.+$")
_LIVE_SUCCESS_CHOOSE_REVEALED_GROUP_RE = re.compile(r"^ライブ成功時エールにより公開された自分のカードの中から、.+(?:の)?メンバーカードを(?P<count>\d+)枚手札に加える$")
_LIVE_SUCCESS_CHOOSE_REVEALED_LIVE_RE = re.compile(r"^ライブ成功時エールにより公開された自分のカードの中から、.+(?:の)?ライブカードを(?P<count>\d+)枚手札に加える$")
_LIVE_SUCCESS_CONDITIONAL_ENERGY_RE = re.compile(r"^ライブ成功時エールにより公開された自分のカードの中にライブカードが\d+枚以上あるとき、.+$")
_ABILITY_ACTIVATION_CONDITION_RE = re.compile(r"^この能力は、このカードが自分のエールによって公開されている場合のみ発動する$")
_LIVE_SUCCESS_ENERGY_PAY_ANY_RE = re.compile(r"^ライブ成功時Eを好きな数支払ってもよい$")
_SCORE_PER_ENERGY_PAID_RE = re.compile(r"^これにより支払ったE\d+つにつき、このカードのスコアを\+\d+する$")
_LIVE_SUCCESS_REVEALED_TO_BOTTOM_RE = re.compile(r"^ライブ成功時エールにより公開された自分のカードの中から、ライブカードを(?P<count>\d+)枚までデッキの一番下に置く$")
_CHOOSE_REVEALED_GROUP_RE = re.compile(r"^エールにより公開された自分のカードの中から、.+(?:の)?メンバーカードを(?P<count>\d+)枚手札に加える$")
_LIVE_SUCCESS_OPTIONAL_ENERGY_RE = re.compile(r"^ライブ成功時自分のエネルギーデッキから、エネルギーカードを(?P<count>\d+)枚ウェイト状態で置いてもよい$")
_LIVE_SUCCESS_PER_MEMBER_DRAW_RE = re.compile(r"^ライブ成功時自分のステージにいる.+(?:の)?メンバー(?P<count>\d+)人につき、カードを(?P<draw_count>\d+)枚引く$")
_LIVE_SUCCESS_MEMBER_DRAW_RE = re.compile(r"^ライブ成功時自分のステージにいる.+(?:の)?メンバー(?P<count>\d+)人につき、カードを(?P<draw_count>\d+)枚引く$")
_SEQUENTIAL_DRAW_DISCARD_EQUAL_RE = re.compile(r"^その後、これにより引いた枚数と同じ枚数を手札から控え室に置く$")
_LIVE_SUCCESS_PER_MEMBER_SCORE_RE = re.compile(r"^ライブ成功時自分のステージにいるウェイト状態のメンバー(?P<count>\d+)人につき、このカードのスコアを\+\d+する$")
_MOVE_RESTRICTION_RE = re.compile(r"^この効果で\d+つのエリアに\d+人以上のメンバーを移動させることはできない$")
_LIVE_SUCCESS_CHOOSE_DIFFERENT_GROUP_RE = re.compile(r"^ライブ成功時自分の控え室にある、自分のステージにいるすべてのメンバーと異なるグループ名を持つカード(?P<count>\d+)枚を手札に加える$")
_CENTER_LIVE_SCORE_MOD_RE = re.compile(r"^センターライブの合計スコアを\+\d+する$")
_LIVE_SCORE_CONDITIONAL_OPPONENT_SUCCESS_RE = re.compile(r"^相手の成功ライブカード置き場にあるカードのスコアの合計が\d+以上であるかぎり、ライブの合計スコアを\+\d+する$")
_LIVE_SCORE_CONDITIONAL_HEART_COUNT_RE = re.compile(r"^自分と相手のステージの中で、このメンバーがほかのすべてのメンバーより多くのハートを持つかぎり、ライブの合計スコアを\+\d+する$")
_LIVE_SCORE_CONDITIONAL_ENERGY_CARD_COUNT_RE = re.compile(r"^このメンバーの下にエネルギーカードが\d+枚以上置かれているかぎり、ライブの合計スコアを\+\d+する$")
_LIVE_SCORE_CONDITIONAL_OPPONENT_SURPLUS_HEART_RE = re.compile(r"^相手の余剰ハートが\d+つ以上あるかぎり、自分のライブの合計スコアを\+\d+する$")
_LIVE_SCORE_CONDITIONAL_EXACT_ENERGY_COUNT_RE = re.compile(r"^自分のエネルギーがちょうど\d+枚あるかぎり、ライブの合計スコアを\+\d+する$")
_CONDITIONAL_BLADE_GAIN_ENERGY_COUNT_RE = re.compile(r"^自分のエネルギーが\d+枚以上あるかぎり、.+$")
_CONDITIONAL_BLADE_GAIN_COST_COMPARISON_RE = re.compile(r"^自分のステージにいるメンバーのコストの合計が相手より低いかぎり、.+$")
_CONDITIONAL_BLADE_GAIN_SUCCESS_LIVE_COMPARISON_RE = re.compile(r"^自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり、.+$")
_BOTH_PLAYERS_ADD_LIVE_CARD_RE = re.compile(r"^自分と相手はそれぞれ、自身の控え室からライブカードを(?P<count>\d+)枚手札に加える$")
_BOTH_PLAYERS_POSITION_CHANGE_RE = re.compile(r"^自分と相手は、自身のステージのセンターにいるメンバーをポジションチェンジする$")
_BOTH_PLAYERS_MEMBER_ENTRY_RE = re.compile(r"^自分と相手はそれぞれ、自身の控え室からコスト\d+以下のメンバーカードを(?P<count>\d+)枚、メンバーのいないエリアにウェイト状態で登場させる$")
_SEQUENTIAL_DISCARD_SIMPLE_RE = re.compile(r"^その後、手札を(?P<count>\d+)枚控え室に置く$")
_SEQUENTIAL_ADD_TO_HAND_SIMPLE_RE = re.compile(r"^その中から(?P<count>\d+)枚を手札に加える$")
_DECK_TO_DISCARD_SIMPLE_RE = re.compile(r"^デッキの上からカードを(?P<count>\d+)枚控え室に置く$")
_TURN_LIMITED_COMPOUND_COST_RE = re.compile(r"^ターン1回このメンバーをウェイトにし、手札を(?P<count>\d+)枚控え室に置く$")
_CONDITIONAL_BLADE_GAIN_GROUP_PRESENCE_RE = re.compile(r"^自分のステージにこのメンバー以外の.+(?:の)?メンバーがいるかぎり、.+$")
_CONDITIONAL_BLADE_GAIN_LIVE_CARD_COUNT_RE = re.compile(r"^自分のライブ中のライブカードが\d+枚以上あるかぎり、.+$")
_CONDITIONAL_BLADE_GAIN_MOVEMENT_RE = re.compile(r"^このターンにこのメンバーが移動していないかぎり、.+$")
_CENTER_BLADE_GAIN_RE = re.compile(r"^センターブレードブレードを得る$")
_PER_SUCCESS_LIVE_PLACE_BLADE_GAIN_RE = re.compile(r"^自分の成功ライブカード置き場にあるカード(?P<count>\d+)枚につき、ブレードを得る$")
_LOOK_TOP_RE = re.compile(r"^(?:自分の)?デッキの上からカードを(?P<count>\d+)枚見る$")
_ENERGY_PAY_RE = re.compile(r"^E+支払ってもよい$")
_DECK_TO_DISCARD_RE = re.compile(r"^自分のデッキの上からカードを(?P<count>\d+)枚控え室に置く$")
_DISCARD_TO_DECK_TOP_RE = re.compile(r"^自分の控え室からカードを(?P<count>\d+)枚までデッキの一番上に置く$")
_LOOK_AND_CHOOSE_RE = re.compile(
    r"^(?:その中から)?(?P<filter>.+?)を持つ(?P<card_kind>メンバーカード|ライブカード|カード)を(?P<count>\d+)枚まで公開して手札に加えてもよい$"
)
_DISCARD_REMAINDER_RE = re.compile(r"^(?:残りを)?控え室に置く$")
_DRAW_CARDS_RE = re.compile(r"^カードを(?P<count>\d+)枚引く$")
_ADD_TO_HAND_RE = re.compile(r"^(?:その中から)?(?P<count>\d+)枚を手札に加え$")
_DRAW_AND_DISCARD_RE = re.compile(r"^カードを(?P<draw_count>\d+)枚引き、手札を(?P<discard_count>\d+)枚控え室に置く$")
_DYNAMIC_DRAW_RE = re.compile(r"^これにより置いた枚数分カードを引く$")
_GAIN_HEARTS_RE = re.compile(r"^ブレードを得る$")
_GAIN_HEARTS_DURATION_RE = re.compile(r"^ライブ終了時まで、ブレードを得る$")
_STAGE_MEMBER_RE = re.compile(r"^ステージに登場させる$")
_WAIT_MEMBER_RE = re.compile(r"^ウェイトにする$")
_WAIT_SELF_RE = re.compile(r"^このメンバーをウェイトにしてもよい$")
_PLACE_ENERGY_RE = re.compile(r"^自分のエネルギーデッキから、エネルギーカードを(?P<count>\d+)枚ウェイト状態で置く$")
_CHOICE_PATTERN_RE = re.compile(r"^以下から(?P<count>\d+)つを選ぶ$")
_ADD_TO_HAND_REMAINDER_RE = re.compile(r"^その中から(?P<count>\d+)枚を手札に加え、残りを控え室に置く$")
_TARGET_OPPONENT_WAIT_RE = re.compile(r"^相手のステージにいるコスト(?P<cost>\d+)以下のメンバー(?P<count>\d+)人をウェイトにする$")
_CONDITIONAL_EFFECT_RE = re.compile(r"^(.+?)(?:の)?場合、(.+)$")
_DURATION_UNTIL_LIVE_END_RE = re.compile(r"^ライブ終了時まで、(.+)$")
_SEARCH_DECK_RE = re.compile(r"^デッキを(?:検索|探)して(.+)を(?P<count>\d+)枚(手札に加える|見つける)$")
_BOOST_SCORE_RE = re.compile(r"^(?:この|その)ライブのスコアを(?P<value>\d+)上げる$")


def _coerce_group_id(group_id: object) -> int:
    if isinstance(group_id, bool):
        return int(group_id)
    if isinstance(group_id, int):
        return group_id
    if isinstance(group_id, float):
        return int(group_id)
    if isinstance(group_id, str):
        normalized = unicodedata.normalize("NFKC", group_id).strip().upper()
        if not normalized:
            return 0
        if normalized.isdigit():
            return int(normalized)
        return _GROUP_ID_MAP.get(normalized, 0)
    return 0


def extract_heart_color_sequence(text: str) -> list[int]:
    """Extract heart color sequence from text (e.g., heart1 heart2 -> [1, 2])."""
    if not text:
        return []
    
    colors = []
    # Match patterns like heart1, heart2, etc.
    matches = re.findall(r"heart(\d+)", text)
    for match in matches:
        try:
            colors.append(int(match))
        except (ValueError, TypeError):
            pass
    return colors


def _normalize_authored_text(text: str) -> str:
    """Render authored text into plain text while preserving the visible labels."""
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKC", text)

    def _replace_template(match: re.Match[str]) -> str:
        label = match.group(2) or match.group(1) or ""
        return label

    normalized = _TEMPLATE_TAG_RE.sub(_replace_template, normalized)
    return normalized


def tokenize_authored_text(text: str) -> list[dict[str, Any]]:
    """Split authored text into text and template tokens without dropping markup."""
    if not text:
        return []

    tokens: list[dict[str, Any]] = []
    cursor = 0
    for match in _TEMPLATE_TAG_RE.finditer(text):
        if match.start() > cursor:
            tokens.append(
                {
                    "kind": "text",
                    "text": text[cursor:match.start()],
                }
            )
        source = match.group(1) or ""
        label = match.group(2) or source
        tokens.append(
            {
                "kind": "template",
                "raw": match.group(0),
                "source": source,
                "label": label,
            }
        )
        cursor = match.end()
    if cursor < len(text):
        tokens.append({"kind": "text", "text": text[cursor:]})
    return tokens


def abstract_authored_text(text: str) -> str:
    """Create a looser pattern view that normalizes digits but keeps labels visible."""
    rendered = _normalize_authored_text(text)
    return _NUMERIC_RUN_RE.sub("<NUM>", rendered)


def _split_authored_clauses(text: str) -> list[str]:
    if not text:
        return []

    rendered = _normalize_authored_text(text)
    return [clause.strip() for clause in _CLAUSE_SPLIT_RE.split(rendered) if clause.strip()]


def _extract_trigger_and_clauses(text: str) -> tuple[list[str], list[str]]:
    """Extract trigger markers separately from effect clauses."""
    if not text:
        return [], []

    rendered = _normalize_authored_text(text)
    clauses = [clause.strip() for clause in _CLAUSE_SPLIT_RE.split(rendered) if clause.strip()]

    trigger_markers: list[str] = []
    effect_clauses: list[str] = []

    for clause in clauses:
        # Filter out garbage: lone punctuation, empty parentheses, bullet points
        if clause in ("(", ")", "）", "（", "・", "・", "・"):
            continue
        if clause.startswith("(") and clause.endswith(")"):
            # Parenthetical note - skip
            continue
        if clause.startswith("（") and clause.endswith("）"):
            # Parenthetical note - skip
            continue
        # Filter parenthetical notes that start with ( but don't end with ) on same line
        if clause.startswith("(") or clause.startswith("（"):
            continue
        # Filter fragments that are artifacts of splitting (e.g., "」を得る")
        if len(clause) < 5:
            continue

        # Strip bullet points
        clause = clause.lstrip("・・")

        # Strip bracket turn limits like [ターン1回]
        clause = re.sub(r"\[.+?\]", "", clause).strip()

        # Strip turn limit prefixes like ターン1回 (BEFORE energy prefixes)
        clause = re.sub(r"^ターン\d+回", "", clause).strip()

        # Skip turn-limited energy-only clauses (they're just cost modifiers)
        if re.match(r"^E+$", clause):
            continue

        # Strip energy prefixes like EE (only if there's other content)
        if re.match(r"^E+", clause) and len(clause) > 1:
            clause = re.sub(r"^E+", "", clause).strip()

        # Handle slash-separated triggers like /ライブ開始時
        if "/" in clause:
            parts = clause.split("/")
            for part in parts:
                marker, remainder = _strip_leading_trigger_marker(part.strip())
                if marker:
                    trigger_markers.append(marker)
                    if remainder:
                        effect_clauses.append(remainder)
                elif remainder:
                    effect_clauses.append(remainder)
            continue

        marker, remainder = _strip_leading_trigger_marker(clause)
        if marker:
            trigger_markers.append(marker)
            if remainder:
                effect_clauses.append(remainder)
        else:
            # Check for area markers
            area_marker, remainder = _strip_leading_area_marker(clause)
            if area_marker:
                trigger_markers.append(area_marker)
                if remainder:
                    effect_clauses.append(remainder)
            else:
                effect_clauses.append(clause)

    return trigger_markers, effect_clauses


def _strip_leading_trigger_marker(clause: str) -> tuple[str | None, str]:
    """Remove a leading label like 登場 so the rest of the clause can be matched."""
    stripped = clause.strip()
    for marker in _TRIGGER_MARKERS:
        if stripped.startswith(marker):
            remainder = stripped[len(marker) :].lstrip()
            return marker, remainder
    return None, stripped


def _strip_leading_area_marker(clause: str) -> tuple[str | None, str]:
    """Remove a leading area marker like 【左サイド】 so the rest of the clause can be matched."""
    stripped = clause.strip()
    for marker in _AREA_MARKERS:
        if stripped.startswith(marker):
            remainder = stripped[len(marker) :].lstrip()
            return marker, remainder
    return None, stripped


def _semantic_runtime_frame(opcode: str, **fields: Any) -> dict[str, Any]:
    frame: dict[str, Any] = {"op": opcode}
    frame.update(fields)
    return frame


def _semantic_operation(
    *,
    kind: str,
    code: str,
    matched_text: str,
    runtime: dict[str, Any] | None = None,
    notes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    operation: dict[str, Any] = {
        "kind": kind,
        "code": code,
        "matched_text": matched_text,
    }
    if runtime is not None:
        operation["runtime"] = runtime
    if notes:
        operation["notes"] = notes
    return operation


def _strip_trailing_return(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if frames and str(frames[-1].get("op", frames[-1].get("opcode", ""))).upper() == "RETURN":
        return frames[:-1]
    return frames


def _frames_for_text(text: str) -> list[dict[str, Any]]:
    semantic_form = extract_semantic_form_from_text(text)
    frame_program = semantic_form_to_frame_program(semantic_form)
    frames = frame_program.get("frames", [])
    if not isinstance(frames, list):
        return []
    return [dict(frame) for frame in frames if isinstance(frame, dict)]


def _extract_semantic_operation(clause: str) -> tuple[dict[str, Any] | None, str | None]:
    """Extract a semantic operation from a single authored clause."""
    marker, body = _strip_leading_trigger_marker(clause)
    compact = re.sub(r"[\s\u3000]+", "", body)

    if match := _OPTIONAL_DISCARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"discard_hand_optional(limit={count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True, "limit": count},
        )
        return operation, marker

    if match := _DISCARD_HAND_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"discard_hand({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": False},
        )
        return operation, marker

    if match := _PLAY_MEMBER_FROM_HAND_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "PLAY_MEMBER_FROM_HAND",
            value=count,
            slot={"source_zone": "HAND", "dest_zone": "STAGE"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"play_member_from_hand({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "source_zone": "HAND", "dest_zone": "STAGE"},
        )
        return operation, marker

    if match := _DRAW_AND_MOVE_BOTTOM_RE.fullmatch(compact):
        draw_count = int(match.group("draw_count"))
        move_count = int(match.group("move_count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=draw_count,
            slot={"target_slot": 6},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"draw({draw_count})",
            matched_text=body,
            runtime=runtime,
            notes={"draw_count": draw_count, "move_to_bottom": move_count},
        )
        return operation, marker

    if match := _ADD_TO_HAND_FROM_DISCARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"add_to_hand_from_discard({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "source_zone": "DISCARD"},
        )
        return operation, marker

    if match := _ACTIVATE_ENERGY_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ACTIVATE_ENERGY",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"activate_energy({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _DISCARD_TO_BOTTOM_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 0)
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "CONTEXT", "dest_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"discard_remainder({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "source_zone": "CONTEXT", "dest_zone": "DISCARD"},
        )
        return operation, marker

    if match := _SEQUENTIAL_MARKER_RE.fullmatch(compact):
        # Skip sequential markers - they're just ordering hints
        return None, marker

    if match := _PER_MEMBER_DRAW_RE.fullmatch(compact):
        count = int(match.group("count"))
        draw_count = int(match.group("draw_count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=draw_count,
            slot={"target_slot": 6},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"draw_per_member({draw_count}, per={count})",
            matched_text=body,
            runtime=runtime,
            notes={"draw_count": draw_count, "per_member": count},
        )
        return operation, marker

    if match := _DISCARD_SPECIFIC_CARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"discard_specific_card({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True, "source_zone": "HAND"},
        )
        return operation, marker

    if match := _BOTH_PLAYERS_RE.fullmatch(compact):
        # Skip both players prefix - it's a scope modifier
        return None, marker

    if match := _LOOK_AND_REVEAL_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "LOOK_DECK",
            value=count,
            slot={"source_zone": "DECK_TOP"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"look_and_reveal({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _COMPOUND_COST_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=1,
            slot={"target_slot": 4},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"compound_cost(tap_self, discard={count})",
            matched_text=body,
            runtime=runtime,
            notes={"tap_self": True, "discard_count": count, "optional": True},
        )
        return operation, marker

    if match := _MOVE_MEMBER_TO_DISCARD_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=1,
            slot={"source_zone": "STAGE"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="move_member_to_discard(1)",
            matched_text=body,
            runtime=runtime,
            notes={"count": 1, "source_zone": "STAGE"},
        )
        return operation, marker

    if match := _CHOOSE_PLAYER_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "SELECT_PLAYER",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="select_player()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _COMPLEX_REORDER_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ORDER_DECK",
            value=0,
            slot={"source_zone": "DECK"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="order_deck(custom)",
            matched_text=body,
            runtime=runtime,
            notes={"reorder": "custom"},
        )
        return operation, marker

    if match := _TURN_LIMIT_ENERGY_RE.fullmatch(compact):
        # Skip turn-limited energy clauses - they're just cost modifiers
        return None, marker

    if match := _TURN_LIMIT_DISCARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"discard_hand({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": False, "turn_limited": True},
        )
        return operation, marker

    if match := _TURN_LIMIT_ENERGY_DISCARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"discard_hand_optional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True, "turn_limited": True},
        )
        return operation, marker

    if match := _TURN_LIMIT_TAP_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=1,
            slot={"target_slot": 4},
        )
        operation = _semantic_operation(
            kind="cost",
            code="tap_self()",
            matched_text=body,
            runtime=runtime,
            notes={"tap_self": True, "turn_limited": True},
        )
        return operation, marker

    if match := _ACTIVATE_MEMBER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ACTIVATE_MEMBER",
            value=count,
            slot={"target_slot": 4},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"activate_member({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _POSITION_CHANGE_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "FORMATION_CHANGE",
            value=0,
            slot={},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code="position_change()",
            matched_text=body,
            runtime=runtime,
            notes={"optional": True},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_TRIGGER_RE.fullmatch(compact):
        # Skip live success trigger - it's a trigger marker
        return None, marker

    if match := _HEART_SELECTION_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "COLOR_SELECT",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"select_heart({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _COLOR_SELECTION_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "COLOR_SELECT",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"select_color({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _CENTER_PREFIX_RE.fullmatch(compact):
        # Skip center prefix - it's a position modifier
        return None, marker

    if match := _ENERGY_TO_MEMBER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ENERGY_TO_MEMBER",
            value=count,
            slot={"source_zone": "ENERGY"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"energy_to_member({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _DISCARD_SAME_UNIT_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"discard_same_unit({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_DRAW_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=count,
            slot={"target_slot": 6},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"draw({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "trigger": "LIVE_SUCCESS"},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_DISCARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"discard_hand_optional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True, "trigger": "LIVE_SUCCESS"},
        )
        return operation, marker

    if match := _OPPONENT_TAP_ACTIVE_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4, "player": "opponent"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"tap_opponent_active({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "player": "opponent", "state": "active"},
        )
        return operation, marker

    if match := _COMPLEX_CONDITIONAL_WHEN_RE.fullmatch(compact):
        # Skip complex conditionals for now - they need more sophisticated parsing
        return None, marker

    if match := _AREA_CONDITIONAL_RE.fullmatch(compact):
        # Skip area conditionals for now - they need more sophisticated parsing
        return None, marker

    if match := _OR_CONDITIONAL_RE.fullmatch(compact):
        # Skip or conditionals for now - they need more sophisticated parsing
        return None, marker

    if match := _DISCARD_TO_BOTTOM_OPTIONAL_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK",
            value=count,
            slot={"source_zone": "DISCARD", "dest_zone": "DECK_BOTTOM"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"move_to_deck_bottom_optional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _DISCARD_WITHOUT_BLADE_HEART_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"discard_without_blade_heart({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _REVEAL_HAND_TO_OPPONENT_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REVEAL_HAND",
            value=count,
            slot={"source_zone": "HAND"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"reveal_hand_to_opponent({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_ENERGY_TO_STAGE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ENERGY_TO_STAGE",
            value=count,
            slot={"source_zone": "ENERGY", "dest_zone": "STAGE"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"energy_to_stage({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "trigger": "LIVE_SUCCESS"},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_ADD_TO_HAND_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "REVEAL"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"add_to_hand_from_reveal({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "trigger": "LIVE_SUCCESS"},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_CHOOSE_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "CHOOSE_OPTION",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_option({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "trigger": "LIVE_SUCCESS"},
        )
        return operation, marker

    if match := _MOVE_TO_AREA_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "MOVE_TO_AREA",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="move_to_area()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _CENTER_TURN_LIMIT_TAP_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"tap_member({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "turn_limited": True, "center": True},
        )
        return operation, marker

    if match := _CENTER_TURN_LIMIT_COMPOUND_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=1,
            slot={"target_slot": 4},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"compound_cost_center(tap_self, discard={count})",
            matched_text=body,
            runtime=runtime,
            notes={"tap_self": True, "discard_count": count, "optional": True, "turn_limited": True, "center": True},
        )
        return operation, marker

    if match := _TURN_LIMIT_EEE_RE.fullmatch(compact):
        # Skip turn-limited EEE clauses - they're just cost modifiers
        return None, marker

    if match := _TURN_LIMIT_COMPOUND_CHOICE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOICE_COST",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"choice_cost(tap_or_discard_{count})",
            matched_text=body,
            runtime=runtime,
            notes={"turn_limited": True},
        )
        return operation, marker

    if match := _TURN_LIMIT_ENERGY_TO_MEMBER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ENERGY_TO_MEMBER",
            value=count,
            slot={"source_zone": "ENERGY"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"energy_to_member({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True, "turn_limited": True},
        )
        return operation, marker

    if match := _TURN_LIMIT_DECK_TO_DISCARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "DECK_TO_DISCARD",
            value=count,
            slot={"source_zone": "DECK"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"deck_to_discard({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "turn_limited": True},
        )
        return operation, marker

    if match := _TURN_LIMIT_COMPLEX_CONDITIONAL_RE.fullmatch(compact):
        # Skip complex turn-limited conditionals for now
        return None, marker

    if match := _TURN_LIMIT_MEMBER_LEAVE_STAGE_RE.fullmatch(compact):
        # Skip member leave stage conditionals for now
        return None, marker

    if match := _CARD_IDENTITY_RULE_RE.fullmatch(compact):
        # Skip card identity rules - they're static rules, not effects
        return None, marker

    if match := _PER_MEMBER_ENERGY_RE.fullmatch(compact):
        count = int(match.group("count"))
        energy_count = int(match.group("energy_count"))
        runtime = _semantic_runtime_frame(
            "ACTIVATE_ENERGY",
            value=energy_count,
            slot={},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"activate_energy_per_member({energy_count}, per={count})",
            matched_text=body,
            runtime=runtime,
            notes={"energy_count": energy_count, "per_member": count},
        )
        return operation, marker

    if match := _PER_MEMBER_DRAW_RE2.fullmatch(compact):
        count = int(match.group("count"))
        draw_count = int(match.group("draw_count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=draw_count,
            slot={"target_slot": 6},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"draw_per_member({draw_count}, per={count})",
            matched_text=body,
            runtime=runtime,
            notes={"draw_count": draw_count, "per_member": count},
        )
        return operation, marker

    if match := _DISCARD_TO_TOP_OPTIONAL_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK",
            value=count,
            slot={"source_zone": "DISCARD", "dest_zone": "DECK_TOP"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"move_to_deck_top_optional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _MULTI_AREA_MARKER_RE.fullmatch(compact):
        # Skip multi-area markers - they're position modifiers
        return None, marker

    if match := _PLAY_MEMBER_FROM_HAND_COST_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "PLAY_MEMBER",
            value=count,
            slot={"source_zone": "HAND"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"play_member_from_hand({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _PLAY_MEMBER_COST_LIMIT_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "PLAY_MEMBER",
            value=count,
            slot={"source_zone": "DISCARD"},
            attr={"is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"play_member_cost_limit({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "limit": True},
        )
        return operation, marker

    if match := _DISCARD_EXCEPT_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "STAGE"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"discard_except({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _REVEAL_UNTIL_LIVE_RE.fullmatch(compact):
        # Skip reveal until live for now - complex pattern
        return None, marker

    if match := _ADD_TO_HAND_AND_DISCARD_REMAINDER_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND_AND_DISCARD",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="add_to_hand_and_discard_remainder()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _OPPONENT_DISCARD_LIVE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND", "player": "opponent"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"opponent_discard_live({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "player": "opponent", "optional": True},
        )
        return operation, marker

    if match := _DRAW_UNTIL_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=count,
            slot={"target_slot": 6},
            attr={"draw_until": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"draw_until({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "draw_until": True},
        )
        return operation, marker

    if match := _NEGATE_ABILITY_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "NEGATE_ABILITY",
            value=0,
            slot={},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code="negate_ability()",
            matched_text=body,
            runtime=runtime,
            notes={"optional": True},
        )
        return operation, marker

    if match := _BOTH_PLAYERS_PLAY_MEMBER_RE.fullmatch(compact):
        # Skip both players patterns for now - complex
        return None, marker

    if match := _OPPONENT_CHOOSE_MEMBER_EXCEPT_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOOSE_MEMBER",
            value=count,
            slot={"player": "opponent"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"opponent_choose_member_except({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "player": "opponent"},
        )
        return operation, marker

    if match := _OPPONENT_TAP_BLADE_COUNT_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4, "player": "opponent"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"opponent_tap_blade_count({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "player": "opponent"},
        )
        return operation, marker

    if match := _OPPONENT_TAP_ALL_COST_LIMIT_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=0,
            slot={"target_slot": 4, "player": "opponent"},
            attr={"all": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code="opponent_tap_all_cost_limit()",
            matched_text=body,
            runtime=runtime,
            notes={"player": "opponent", "all": True},
        )
        return operation, marker

    if match := _ACTIVATE_ALL_MEMBERS_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ACTIVATE_MEMBER",
            value=0,
            slot={"target_slot": 4},
            attr={"all": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code="activate_all_members()",
            matched_text=body,
            runtime=runtime,
            notes={"all": True},
        )
        return operation, marker

    if match := _ACTIVATE_MEMBER_GROUP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ACTIVATE_MEMBER",
            value=count,
            slot={"target_slot": 4},
            attr={"is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"activate_member_group({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "limit": True},
        )
        return operation, marker

    if match := _CHOICE_ACTIVATE_ENERGY_RE.fullmatch(compact):
        count = int(match.group("count"))
        energy_count = int(match.group("energy_count"))
        runtime = _semantic_runtime_frame(
            "CHOICE_EFFECT",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choice_activate_member_or_energy({count}, {energy_count})",
            matched_text=body,
            runtime=runtime,
            notes={"member_count": count, "energy_count": energy_count},
        )
        return operation, marker

    if match := _RESPAWN_MEMBER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "RESPAWN_MEMBER",
            value=count,
            slot={"source_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"respawn_member({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _BOTH_PLAYERS_PLAY_MEMBER_COST_RE.fullmatch(compact):
        # Skip both players patterns for now - complex
        return None, marker

    if match := _OPPONENT_GAIN_BLADE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "GAIN_BLADE",
            value=count,
            slot={},
            attr={"duration": "until_live_end"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"opponent_gain_blade({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "duration": "until_live_end"},
        )
        return operation, marker

    if match := _POSITION_CHANGE_OPPONENT_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "FORMATION_CHANGE",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"position_change_opponent({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _TAP_OPTIONAL_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4},
            attr={"is_optional": 1, "is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"tap_optional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True, "limit": True},
        )
        return operation, marker

    if match := _MOVE_MEMBERS_ANY_AREA_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "MOVE_MEMBER",
            value=0,
            slot={},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code="move_members_any_area()",
            matched_text=body,
            runtime=runtime,
            notes={"optional": True},
        )
        return operation, marker

    if match := _DISCARD_TO_TOP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK",
            value=count,
            slot={"source_zone": "DISCARD", "dest_zone": "DECK_TOP"},
            attr={"is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"discard_to_top({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "limit": True},
        )
        return operation, marker

    if match := _CHOOSE_CARDS_DIFFERENT_NAMES_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOOSE_CARD",
            value=count,
            slot={"source_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_cards_different_names({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _CHOOSE_CARD_COST_LIMIT_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOOSE_CARD",
            value=count,
            slot={"source_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_card_cost_limit({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _ACTIVATE_ABILITY_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ACTIVATE_ABILITY",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"activate_ability({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _TAP_GROUP_OPTIONAL_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"tap_group_optional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _PLAY_MEMBER_OPTIONAL_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "PLAY_MEMBER",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"play_member_optional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _PLAY_MEMBER_CONDITIONAL_RE.fullmatch(compact):
        # Skip conditional restrictions for now
        return None, marker

    if match := _REVEAL_LIVE_OPTIONAL_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REVEAL_HAND",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"reveal_live_optional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _BOTH_PLAYERS_POSITION_CHANGE_RE.fullmatch(compact):
        # Skip both players position change for now
        return None, marker

    if match := _ADD_TO_HAND_EQUAL_COUNT_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=0,
            slot={"source_zone": "DISCARD"},
            attr={"equal_count": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code="add_to_hand_equal_count()",
            matched_text=body,
            runtime=runtime,
            notes={"equal_count": True},
        )
        return operation, marker

    if match := _AREA_CONDITIONAL_DRAW_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=count,
            slot={"target_slot": 6},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"area_conditional_draw({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "area_conditional": True},
        )
        return operation, marker

    if match := _AREA_DRAW_DISCARD_RE.fullmatch(compact):
        draw_count = int(match.group("draw_count"))
        discard_count = int(match.group("discard_count"))
        runtime = _semantic_runtime_frame(
            "DRAW_AND_DISCARD",
            value=draw_count,
            slot={"target_slot": 6},
            params={"discard_count": discard_count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"area_draw_discard({draw_count}, {discard_count})",
            matched_text=body,
            runtime=runtime,
            notes={"draw_count": draw_count, "discard_count": discard_count},
        )
        return operation, marker

    if match := _AREA_ACTIVATE_ENERGY_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ACTIVATE_ENERGY",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"area_activate_energy({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _SEQUENTIAL_ADD_TO_HAND_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"sequential_add_to_hand({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "sequential": True},
        )
        return operation, marker

    if match := _LOOK_AND_CHOOSE_GROUP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "LOOK_AND_CHOOSE",
            value=count,
            slot={},
            attr={"is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"look_and_choose_group({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "limit": True},
        )
        return operation, marker

    if match := _CHOOSE_MEMBER_COST_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOOSE_MEMBER",
            value=count,
            slot={},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_member_cost({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _OPPONENT_TAP_COST_EXACT_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4, "player": "opponent"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"opponent_tap_cost_exact({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "player": "opponent"},
        )
        return operation, marker

    if match := _GAIN_BLADE_DURATION_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "GAIN_BLADE",
            value=1,
            slot={},
            attr={"duration": "until_live_end"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="gain_blade_duration()",
            matched_text=body,
            runtime=runtime,
            notes={"duration": "until_live_end"},
        )
        return operation, marker

    if match := _GAIN_BLADE_DURATION_RE2.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "GAIN_BLADE",
            value=2,
            slot={},
            attr={"duration": "until_live_end"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="gain_blade_duration_2()",
            matched_text=body,
            runtime=runtime,
            notes={"duration": "until_live_end", "value": 2},
        )
        return operation, marker

    if match := _TAP_OPPONENT_COST_LIMIT_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4, "player": "opponent"},
            attr={"is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"opponent_tap_cost_limit({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "player": "opponent", "limit": True},
        )
        return operation, marker

    if match := _PER_ENERGY_DRAW_RE.fullmatch(compact):
        energy_count = int(match.group("energy_count"))
        draw_count = int(match.group("draw_count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=draw_count,
            slot={"target_slot": 6},
            params={"per_energy": energy_count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"per_energy_draw({energy_count}, {draw_count})",
            matched_text=body,
            runtime=runtime,
            notes={"energy_count": energy_count, "draw_count": draw_count},
        )
        return operation, marker

    if match := _REPEAT_PROCEDURE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REPEAT_PROCEDURE",
            value=count,
            slot={},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"repeat_procedure({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _CHOOSE_LIVE_CARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOOSE_CARD",
            value=count,
            slot={"source_zone": "LIVE"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_live_card({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _CHOOSE_MEMBER_GROUP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOOSE_MEMBER",
            value=count,
            slot={"target_slot": 4},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_member_group({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _DISCARD_TOP_OPTIONAL_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "DECK_TO_DISCARD",
            value=1,
            slot={"source_zone": "DECK"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code="discard_top_optional()",
            matched_text=body,
            runtime=runtime,
            notes={"optional": True},
        )
        return operation, marker

    if match := _REVEAL_LIVE_TO_BOTTOM_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REVEAL_AND_BOTTOM",
            value=count,
            slot={"source_zone": "HAND", "dest_zone": "DECK_BOTTOM"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"reveal_live_to_bottom({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _TAP_GROUP_SIMPLE_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"tap_group_simple({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _CHOOSE_MEMBER_FROM_STAGE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ACTIVATE_MEMBER",
            value=count,
            slot={"target_slot": 4, "state": "wait"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_member_from_stage({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "from_state": "wait"},
        )
        return operation, marker

    if match := _ACTIVATE_ALL_MEMBERS_AND_ENERGY_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ACTIVATE_ALL",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="activate_all_members_and_energy()",
            matched_text=body,
            runtime=runtime,
            notes={"all": True},
        )
        return operation, marker

    if match := _DISCARD_TO_TOP_OPTIONAL_SIMPLE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK",
            value=count,
            slot={"source_zone": "DISCARD", "dest_zone": "DECK_TOP"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"discard_to_top_optional_simple({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _PLACE_CARD_AT_POSITION_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK_POSITION",
            value=count,
            slot={"source_zone": "DISCARD"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"place_card_at_position({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _ADD_TO_HAND_LIVE_PLACE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "LIVE_PLACE"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"add_to_hand_live_place({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _PLAY_MEMBER_COST_LIMIT_AREA_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "PLAY_MEMBER",
            value=count,
            slot={"source_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"play_member_cost_limit_area({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _CHOOSE_CARD_GROUP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOOSE_CARD",
            value=count,
            slot={},
            attr={"is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_card_group({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "limit": True},
        )
        return operation, marker

    if match := _DISCARD_SAME_GROUP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"discard_same_group({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _TAP_GROUP_NAME_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"tap_group_name({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _ADD_CHOSEN_CARD_TO_HAND_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=1,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="add_chosen_card_to_hand()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _CONDITIONAL_AREA_RESTRICTION_RE.fullmatch(compact):
        # Skip conditional area restrictions for now
        return None, marker

    if match := _CHOOSE_MEMBER_COST_GROUP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOOSE_MEMBER",
            value=count,
            slot={},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_member_cost_group({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _HEART_SELECTION_OR_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "COLOR_SELECT",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"select_heart_or({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _CONDITIONAL_ENERGY_PAYMENT_RE.fullmatch(compact):
        # Skip conditional energy payment for now - complex pattern
        return None, marker

    if match := _PER_MEMBER_HEART_GAIN_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "GAIN_HEART",
            value=0,
            slot={},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"per_member_heart_gain({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_member": count},
        )
        return operation, marker

    if match := _DISTRIBUTE_CARDS_RE.fullmatch(compact):
        count1 = int(match.group("count1"))
        count2 = int(match.group("count2"))
        count3 = int(match.group("count3"))
        runtime = _semantic_runtime_frame(
            "DISTRIBUTE_CARDS",
            value=0,
            slot={},
            params={"to_hand": count1, "to_deck": count2, "to_discard": count3},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"distribute_cards({count1}, {count2}, {count3})",
            matched_text=body,
            runtime=runtime,
            notes={"to_hand": count1, "to_deck": count2, "to_discard": count3},
        )
        return operation, marker

    if match := _LOOK_OPPONENT_DECK_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "LOOK_TOP",
            value=1,
            slot={"source_zone": "DECK", "player": "opponent"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="look_opponent_deck()",
            matched_text=body,
            runtime=runtime,
            notes={"player": "opponent"},
        )
        return operation, marker

    if match := _DISCARD_OPPONENT_TOP_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=1,
            slot={"source_zone": "DECK", "player": "opponent"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code="discard_opponent_top()",
            matched_text=body,
            runtime=runtime,
            notes={"player": "opponent", "optional": True},
        )
        return operation, marker

    if match := _LOOK_OPPONENT_DECK_MULTI_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "LOOK_TOP",
            value=count,
            slot={"source_zone": "DECK", "player": "opponent"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"look_opponent_deck_multi({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "player": "opponent"},
        )
        return operation, marker

    if match := _OPPONENT_DISCARD_TO_BOTTOM_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK",
            value=count,
            slot={"source_zone": "DISCARD", "dest_zone": "DECK_BOTTOM", "player": "opponent"},
            attr={"is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"opponent_discard_to_bottom({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "player": "opponent", "limit": True},
        )
        return operation, marker

    if match := _PER_MEMBER_LOOK_RE.fullmatch(compact):
        count = int(match.group("count"))
        look_count = int(match.group("look_count"))
        runtime = _semantic_runtime_frame(
            "LOOK_TOP",
            value=look_count,
            slot={"source_zone": "DECK"},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"per_member_look({count}, {look_count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_member": count, "look_count": look_count},
        )
        return operation, marker

    if match := _DISTRIBUTE_TWO_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "DISTRIBUTE_TWO",
            value=count,
            slot={},
            attr={"is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"distribute_two({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "limit": True},
        )
        return operation, marker

    if match := _DISCARD_TO_TOP_ORDER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK",
            value=count,
            slot={"source_zone": "DISCARD", "dest_zone": "DECK_TOP"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"discard_to_top_order({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _TAP_GROUP_NAME_SIMPLE_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"tap_group_name_simple({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _CENTER_ACTIVATE_ALL_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ACTIVATE_ALL",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="center_activate_all()",
            matched_text=body,
            runtime=runtime,
            notes={"center": True, "all": True},
        )
        return operation, marker

    if match := _SEQUENTIAL_PLACE_CARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK_POSITION",
            value=count,
            slot={"source_zone": "DISCARD"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"sequential_place_card({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True, "sequential": True},
        )
        return operation, marker

    if match := _CONDITIONAL_NOT_BATON_TOUCH_RE.fullmatch(compact):
        # Skip conditional baton touch restrictions for now
        return None, marker

    if match := _SEQUENTIAL_CHOOSE_AREA_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOOSE_AREA",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"sequential_choose_area({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "sequential": True},
        )
        return operation, marker

    if match := _TURN_COUNT_CONDITIONAL_RE.fullmatch(compact):
        # Skip turn count conditionals for now - complex pattern
        return None, marker

    if match := _NO_LIVE_CARD_DISCARD_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=0,
            slot={"source_zone": "REVEAL"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code="no_live_card_discard()",
            matched_text=body,
            runtime=runtime,
            notes={"optional": True, "conditional": "no_live_card"},
        )
        return operation, marker

    if match := _SUCCESS_LIVE_PLACE_DISCARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "LIVE_PLACE"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"success_live_place_discard({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _DRAW_OPTIONAL_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=count,
            slot={"target_slot": 6},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"draw_optional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _ENERGY_PAY_LIMIT_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ENERGY_PAY",
            value=count,
            slot={},
            attr={"is_limit": 1, "is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"energy_pay_limit({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "limit": True, "optional": True},
        )
        return operation, marker

    if match := _REDUCE_HEART_COST_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "REDUCE_HEART_COST",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="reduce_heart_cost()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _REVEAL_TOP_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "REVEAL_TOP",
            value=1,
            slot={"source_zone": "DECK"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="reveal_top()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _SEQUENTIAL_REVEAL_TOP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REVEAL_TOP",
            value=count,
            slot={"source_zone": "DECK"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"sequential_reveal_top({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "sequential": True},
        )
        return operation, marker

    if match := _DISCARD_SPECIFIC_CARDS_RE.fullmatch(compact):
        # Skip specific card discard patterns for now - too specific
        return None, marker

    if match := _DISCARD_SPECIFIC_CARDS_SIMPLE_RE.fullmatch(compact):
        # Skip specific card discard patterns for now - too specific
        return None, marker

    if match := _REVEAL_GROUP_OPTIONAL_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REVEAL_HAND",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"reveal_group_optional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _REVEAL_AND_PLACE_GAIN_BLADE_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "REVEAL_PLACE_GAIN_BLADE",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="reveal_and_place_gain_blade()",
            matched_text=body,
            runtime=runtime,
            notes={"gain_blade": True},
        )
        return operation, marker

    if match := _DISCARD_SPECIFIC_MEMBER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1, "is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"discard_specific_member({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True, "limit": True},
        )
        return operation, marker

    if match := _SEQUENTIAL_ADD_TO_HAND_GROUP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"sequential_add_to_hand_group({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "sequential": True},
        )
        return operation, marker

    if match := _CHOOSE_QUESTION_RE.fullmatch(compact):
        # Skip question patterns for now - too specific
        return None, marker

    if match := _CHOOSE_SPECIFIC_CARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "CHOOSE_CARD",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_specific_card({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _REVEAL_ALL_DISCARD_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=0,
            slot={"source_zone": "REVEAL"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="reveal_all_discard()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _ACTIVATE_GAIN_BLADE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ACTIVATE_MEMBER",
            value=count,
            slot={"target_slot": 4, "state": "wait"},
            attr={"gain_blade": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"activate_gain_blade({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "gain_blade": True},
        )
        return operation, marker

    if match := _SCORE_MODIFICATION_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="score_modification()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _SCORE_PER_MEMBER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "SCORE_MODIFICATION",
            value=0,
            slot={},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"score_per_member({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_member": count},
        )
        return operation, marker

    if match := _SCORE_PER_HEART_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="score_per_heart()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _SCORE_PER_MEMBER_NAME_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "SCORE_MODIFICATION",
            value=0,
            slot={},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"score_per_member_name({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_member": count},
        )
        return operation, marker

    if match := _SCORE_PER_LIVE_CARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "SCORE_MODIFICATION",
            value=0,
            slot={},
            params={"per_live_card": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"score_per_live_card({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_live_card": count},
        )
        return operation, marker

    if match := _SCORE_CONDITIONAL_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="score_conditional()",
            matched_text=body,
            runtime=runtime,
            notes={"conditional": True},
        )
        return operation, marker

    if match := _HEART_COST_REDUCTION_PER_MEMBER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REDUCE_HEART_COST",
            value=0,
            slot={},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"heart_cost_reduction_per_member({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_member": count},
        )
        return operation, marker

    if match := _HEART_COST_REDUCTION_CONDITIONAL_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REDUCE_HEART_COST",
            value=0,
            slot={},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"heart_cost_reduction_conditional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_member": count, "conditional": True},
        )
        return operation, marker

    if match := _HEART_COST_LIMIT_RE.fullmatch(compact):
        # Skip heart cost limit patterns for now - they're modifiers
        return None, marker

    if match := _ENERGY_MEMBER_TO_DECK_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ENERGY_TO_DECK",
            value=count,
            slot={"source_zone": "MEMBER", "dest_zone": "ENERGY_DECK"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"energy_member_to_deck({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _REVEAL_PER_MEMBER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REVEAL_TOP",
            value=0,
            slot={"source_zone": "DECK"},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"reveal_per_member({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_member": count},
        )
        return operation, marker

    if match := _OPPONENT_TAP_BLADE_CONDITIONAL_RE.fullmatch(compact):
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target_slot": 4, "player": "opponent"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"opponent_tap_blade_conditional({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "player": "opponent"},
        )
        return operation, marker

    if match := _ACTIVATE_GROUP_SIMPLE_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ACTIVATE_MEMBER",
            value=0,
            slot={"target_slot": 4},
        )
        operation = _semantic_operation(
            kind="effect",
            code="activate_group_simple()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _SEQUENTIAL_DISCARD_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=0,
            slot={"source_zone": "REVEAL"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="sequential_discard()",
            matched_text=body,
            runtime=runtime,
            notes={"sequential": True},
        )
        return operation, marker

    if match := _LIVE_PLACE_SCORE_MOD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "SCORE_MODIFICATION",
            value=0,
            slot={"source_zone": "LIVE_PLACE"},
            params={"per_card": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_place_score_mod({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_card": count},
        )
        return operation, marker

    if match := _LIVE_PLACE_HEART_REDUCTION_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REDUCE_HEART_COST",
            value=0,
            slot={"source_zone": "LIVE_PLACE"},
            params={"per_card": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_place_heart_reduction({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_card": count},
        )
        return operation, marker

    if match := _LIVE_PLACE_HEART_INCREASE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REDUCE_HEART_COST",
            value=0,
            slot={"source_zone": "LIVE_PLACE"},
            params={"per_card": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_place_heart_increase({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_card": count},
        )
        return operation, marker

    if match := _LOOK_BASED_LIVE_SCORE_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "LOOK_TOP",
            value=0,
            slot={"source_zone": "DECK"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="look_based_live_score()",
            matched_text=body,
            runtime=runtime,
            notes={"based_on": "live_score"},
        )
        return operation, marker

    if match := _CHOOSE_FROM_REVEALED_FILTER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "REVEAL"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_from_revealed_filter({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_DRAW_DISCARD_RE.fullmatch(compact):
        draw_count = int(match.group("draw_count"))
        discard_count = int(match.group("discard_count"))
        runtime = _semantic_runtime_frame(
            "DRAW_AND_DISCARD",
            value=draw_count,
            slot={"target_slot": 6},
            params={"discard_count": discard_count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_draw_discard({draw_count}, {discard_count})",
            matched_text=body,
            runtime=runtime,
            notes={"draw_count": draw_count, "discard_count": discard_count},
        )
        return operation, marker

    if match := _DISCARD_TO_TOP_OPTIONAL_MEMBER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK",
            value=count,
            slot={"source_zone": "DISCARD", "dest_zone": "DECK_TOP"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"discard_to_top_optional_member({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _LIVE_PLACE_SCORE_HEART_MOD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "SCORE_MODIFICATION",
            value=0,
            slot={"source_zone": "LIVE_PLACE"},
            params={"per_card": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_place_score_heart_mod({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_card": count},
        )
        return operation, marker

    if match := _HEART_COST_REDUCTION_LIVE_PLACE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "REDUCE_HEART_COST",
            value=0,
            slot={"source_zone": "LIVE_PLACE"},
            params={"per_card": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"heart_cost_reduction_live_place({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_card": count},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_BOTH_ENERGY_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ENERGY_TO_STAGE",
            value=count,
            slot={"source_zone": "ENERGY_DECK"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_both_energy({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "both_players": True},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_DECK_TO_DISCARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "DECK_TO_DISCARD",
            value=count,
            slot={"source_zone": "DECK"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_deck_to_discard({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_ENERGY_PAY_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ENERGY_PAY",
            value=0,
            slot={},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code="live_success_energy_pay()",
            matched_text=body,
            runtime=runtime,
            notes={"optional": True},
        )
        return operation, marker

    if match := _LIVE_SCORE_MODIFICATION_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "LIVE_SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="live_score_modification()",
            matched_text=body,
            runtime=runtime,
            notes={},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_LOOK_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "LOOK_TOP",
            value=count,
            slot={"source_zone": "DECK"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_look({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _LIVE_SCORE_FLOOR_RE.fullmatch(compact):
        # Skip live score floor patterns for now - they're modifiers
        return None, marker

    if match := _SIMPLE_ADD_TO_HAND_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"simple_add_to_hand({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_ENERGY_PAY_COUNT_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ENERGY_PAY",
            value=count,
            slot={},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"live_success_energy_pay_count({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_CONDITIONAL_RESTRICTION_RE.fullmatch(compact):
        # Skip live success conditional restrictions for now - complex pattern
        return None, marker

    if match := _LIVE_SUCCESS_CHOOSE_REVEALED_GROUP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "REVEAL"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_choose_revealed_group({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_CHOOSE_REVEALED_LIVE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "REVEAL"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_choose_revealed_live({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_CONDITIONAL_ENERGY_RE.fullmatch(compact):
        # Skip live success conditional energy for now - complex pattern
        return None, marker

    if match := _ABILITY_ACTIVATION_CONDITION_RE.fullmatch(compact):
        # Skip ability activation conditions for now - they're modifiers
        return None, marker

    if match := _LIVE_SUCCESS_ENERGY_PAY_ANY_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ENERGY_PAY",
            value=0,
            slot={},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code="live_success_energy_pay_any()",
            matched_text=body,
            runtime=runtime,
            notes={"optional": True, "any_amount": True},
        )
        return operation, marker

    if match := _SCORE_PER_ENERGY_PAID_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="score_per_energy_paid()",
            matched_text=body,
            runtime=runtime,
            notes={"per_energy": True},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_REVEALED_TO_BOTTOM_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK",
            value=count,
            slot={"source_zone": "REVEAL", "dest_zone": "DECK_BOTTOM"},
            attr={"is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_revealed_to_bottom({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "limit": True},
        )
        return operation, marker

    if match := _CHOOSE_REVEALED_GROUP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "REVEAL"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"choose_revealed_group({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_OPTIONAL_ENERGY_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ENERGY_TO_STAGE",
            value=count,
            slot={"source_zone": "ENERGY_DECK"},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_optional_energy({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "optional": True},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_PER_MEMBER_DRAW_RE.fullmatch(compact):
        count = int(match.group("count"))
        draw_count = int(match.group("draw_count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=draw_count,
            slot={"target_slot": 6},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_per_member_draw({count}, {draw_count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_member": count, "draw_count": draw_count},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_MEMBER_DRAW_RE.fullmatch(compact):
        count = int(match.group("count"))
        draw_count = int(match.group("draw_count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=draw_count,
            slot={"target_slot": 6},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_member_draw({count}, {draw_count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_member": count, "draw_count": draw_count},
        )
        return operation, marker

    if match := _SEQUENTIAL_DRAW_DISCARD_EQUAL_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=0,
            slot={"source_zone": "HAND"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="sequential_draw_discard_equal()",
            matched_text=body,
            runtime=runtime,
            notes={"equal_count": True, "sequential": True},
        )
        return operation, marker

    if match := _LIVE_SUCCESS_PER_MEMBER_SCORE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "SCORE_MODIFICATION",
            value=0,
            slot={},
            params={"per_member": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_per_member_score({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_member": count},
        )
        return operation, marker

    if match := _MOVE_RESTRICTION_RE.fullmatch(compact):
        # Skip move restriction patterns for now - they're modifiers
        return None, marker

    if match := _LIVE_SUCCESS_CHOOSE_DIFFERENT_GROUP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"live_success_choose_different_group({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _CENTER_LIVE_SCORE_MOD_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "LIVE_SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="center_live_score_mod()",
            matched_text=body,
            runtime=runtime,
            notes={"center": True},
        )
        return operation, marker

    if match := _LIVE_SCORE_CONDITIONAL_OPPONENT_SUCCESS_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "LIVE_SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="live_score_conditional_opponent_success()",
            matched_text=body,
            runtime=runtime,
            notes={"conditional": True},
        )
        return operation, marker

    if match := _LIVE_SCORE_CONDITIONAL_HEART_COUNT_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "LIVE_SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="live_score_conditional_heart_count()",
            matched_text=body,
            runtime=runtime,
            notes={"conditional": True},
        )
        return operation, marker

    if match := _LIVE_SCORE_CONDITIONAL_ENERGY_CARD_COUNT_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "LIVE_SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="live_score_conditional_energy_card_count()",
            matched_text=body,
            runtime=runtime,
            notes={"conditional": True},
        )
        return operation, marker

    if match := _LIVE_SCORE_CONDITIONAL_OPPONENT_SURPLUS_HEART_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "LIVE_SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="live_score_conditional_opponent_surplus_heart()",
            matched_text=body,
            runtime=runtime,
            notes={"conditional": True},
        )
        return operation, marker

    if match := _LIVE_SCORE_CONDITIONAL_EXACT_ENERGY_COUNT_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "LIVE_SCORE_MODIFICATION",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="live_score_conditional_exact_energy_count()",
            matched_text=body,
            runtime=runtime,
            notes={"conditional": True},
        )
        return operation, marker

    if match := _CONDITIONAL_BLADE_GAIN_ENERGY_COUNT_RE.fullmatch(compact):
        # Skip conditional blade gain patterns for now - complex pattern
        return None, marker

    if match := _CONDITIONAL_BLADE_GAIN_COST_COMPARISON_RE.fullmatch(compact):
        # Skip conditional blade gain patterns for now - complex pattern
        return None, marker

    if match := _CONDITIONAL_BLADE_GAIN_SUCCESS_LIVE_COMPARISON_RE.fullmatch(compact):
        # Skip conditional blade gain patterns for now - complex pattern
        return None, marker

    if match := _BOTH_PLAYERS_ADD_LIVE_CARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"source_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"both_players_add_live_card({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "both_players": True},
        )
        return operation, marker

    if match := _BOTH_PLAYERS_POSITION_CHANGE_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "POSITION_CHANGE",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="both_players_position_change()",
            matched_text=body,
            runtime=runtime,
            notes={"both_players": True},
        )
        return operation, marker

    if match := _BOTH_PLAYERS_MEMBER_ENTRY_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MEMBER_ENTRY",
            value=count,
            slot={"source_zone": "DISCARD"},
            attr={"is_wait": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"both_players_member_entry({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "both_players": True},
        )
        return operation, marker

    if match := _SEQUENTIAL_DISCARD_SIMPLE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"sequential_discard_simple({count})",
            matched_text=body,
            runtime=runtime,
            notes={"sequential": True},
        )
        return operation, marker

    if match := _SEQUENTIAL_ADD_TO_HAND_SIMPLE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"sequential_add_to_hand_simple({count})",
            matched_text=body,
            runtime=runtime,
            notes={"sequential": True},
        )
        return operation, marker

    if match := _DECK_TO_DISCARD_SIMPLE_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "DECK_TO_DISCARD",
            value=count,
            slot={"source_zone": "DECK"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"deck_to_discard_simple({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _TURN_LIMITED_COMPOUND_COST_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "COMPOUND_COST",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"turn_limited_compound_cost({count})",
            matched_text=body,
            runtime=runtime,
            notes={"turn_limited": True, "compound": True},
        )
        return operation, marker

    if match := _CONDITIONAL_BLADE_GAIN_GROUP_PRESENCE_RE.fullmatch(compact):
        # Skip conditional blade gain patterns for now - complex pattern
        return None, marker

    if match := _CONDITIONAL_BLADE_GAIN_LIVE_CARD_COUNT_RE.fullmatch(compact):
        # Skip conditional blade gain patterns for now - complex pattern
        return None, marker

    if match := _CONDITIONAL_BLADE_GAIN_MOVEMENT_RE.fullmatch(compact):
        # Skip conditional blade gain patterns for now - complex pattern
        return None, marker

    if match := _CENTER_BLADE_GAIN_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "BLADE_GAIN",
            value=0,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="center_blade_gain()",
            matched_text=body,
            runtime=runtime,
            notes={"center": True},
        )
        return operation, marker

    if match := _PER_SUCCESS_LIVE_PLACE_BLADE_GAIN_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "BLADE_GAIN",
            value=0,
            slot={"source_zone": "SUCCESS_LIVE_PLACE"},
            params={"per_card": count},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"per_success_live_place_blade_gain({count})",
            matched_text=body,
            runtime=runtime,
            notes={"per_card": count},
        )
        return operation, marker

    if match := _OPTIONAL_DISCARD_LIMIT_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "HAND"},
            attr={"is_optional": 1, "is_limit": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"optional_discard_limit(hand, up_to={count})",
            matched_text=body,
            runtime=runtime,
            notes={"optional": True, "is_limit": True, "source_zone": "HAND", "dest_zone": "DISCARD", "limit": count},
        )
        return operation, marker

    if match := _ENERGY_PAY_RE.fullmatch(compact):
        energy_count = len(match.group(0).replace("支払ってもよい", ""))
        runtime = _semantic_runtime_frame(
            "PAY_ENERGY",
            value=energy_count,
            slot={},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code=f"pay_energy({energy_count})",
            matched_text=body,
            runtime=runtime,
            notes={"optional": True, "energy_count": energy_count},
        )
        return operation, marker

    if match := _DECK_TO_DISCARD_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=count,
            slot={"source_zone": "DECK_TOP", "dest_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"deck_top_to_discard({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "source_zone": "DECK_TOP", "dest_zone": "DISCARD"},
        )
        return operation, marker

    if match := _DISCARD_TO_DECK_TOP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DECK",
            value=count,
            slot={"source_zone": "DISCARD", "dest_zone": "DECK_TOP"},
            attr={"is_limit": 1},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"discard_to_deck_top(up_to={count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "source_zone": "DISCARD", "dest_zone": "DECK_TOP", "is_limit": True},
        )
        return operation, marker

    if match := _LOOK_TOP_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "LOOK_DECK",
            value=count,
            slot={"source_zone": "DECK_TOP"},
        )
        operation = _semantic_operation(
            kind="look",
            code=f"look_deck(top={count})",
            matched_text=body,
            runtime=runtime,
            notes={"source_zone": "DECK_TOP"},
        )
        return operation, marker

    if match := _LOOK_AND_CHOOSE_RE.fullmatch(compact):
        choose_count = int(match.group("count"))
        heart_colors = extract_heart_color_sequence(body)
        runtime = _semantic_runtime_frame(
            "LOOK_AND_CHOOSE",
            value={"count": 0, "reveal": 1},
            params={
                "choose_count": choose_count,
                "heart_colors": heart_colors,
                "card_kind": match.group("card_kind"),
                "reveal": True,
                "add_to_hand": True,
                "remainder_to_discard": True,
            },
            slot={"target_slot": 6},
        )
        operation = _semantic_operation(
            kind="selection",
            code=(
                "look_and_choose("
                f"choose_up_to={choose_count}, "
                f"filter=heart_any{heart_colors or '[]'}, "
                f"card_kind={match.group('card_kind')}, "
                "reveal=true, add_to_hand=true, discard_remainder=true)"
            ),
            matched_text=body,
            runtime=runtime,
            notes={"heart_colors": heart_colors, "optional": True},
        )
        return operation, marker

    if match := _DISCARD_REMAINDER_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=1,
            slot={"source_zone": "REMAINDER", "dest_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="cleanup",
            code="discard_remainder(discard)",
            matched_text=body,
            runtime=runtime,
            notes={"source_zone": "REMAINDER", "dest_zone": "DISCARD"},
        )
        return operation, marker

    if match := _DRAW_CARDS_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=count,
            slot={"target_slot": 6},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"draw({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _ADD_TO_HAND_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"target_slot": 6},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"add_to_hand({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count},
        )
        return operation, marker

    if match := _DRAW_AND_DISCARD_RE.fullmatch(compact):
        draw_count = int(match.group("draw_count"))
        discard_count = int(match.group("discard_count"))
        draw_runtime = _semantic_runtime_frame(
            "DRAW",
            value=draw_count,
            slot={"target_slot": 6},
        )
        discard_runtime = _semantic_runtime_frame(
            "MOVE_TO_DISCARD",
            value=discard_count,
            slot={"source_zone": "HAND", "dest_zone": "DISCARD"},
        )
        operation = _semantic_operation(
            kind="compound",
            code=f"draw_and_discard(draw={draw_count}, discard={discard_count})",
            matched_text=body,
            runtime={
                "operations": [
                    {"op": "DRAW", "value": draw_count, "slot": {"target_slot": 6}},
                    {"op": "MOVE_TO_DISCARD", "value": discard_count, "slot": {"source_zone": "HAND", "dest_zone": "DISCARD"}},
                ]
            },
            notes={"draw_count": draw_count, "discard_count": discard_count},
        )
        return operation, marker

    if match := _DYNAMIC_DRAW_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "DRAW",
            value=0,
            slot={"target_slot": 6},
            params={"dynamic": "discard_count"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="draw_dynamic(discard_count)",
            matched_text=body,
            runtime=runtime,
            notes={"dynamic": True, "source": "discard_count"},
        )
        return operation, marker

    if match := _GAIN_HEARTS_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ADD_HEARTS",
            value=1,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="add_hearts(1)",
            matched_text=body,
            runtime=runtime,
            notes={"value": 1},
        )
        return operation, marker

    if match := _GAIN_HEARTS_DURATION_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "ADD_HEARTS",
            value=1,
            slot={},
            params={"duration": "LIVE_END"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="add_hearts(1, duration=LIVE_END)",
            matched_text=body,
            runtime=runtime,
            notes={"value": 1, "duration": "LIVE_END"},
        )
        return operation, marker

    if match := _STAGE_MEMBER_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "PLAY_MEMBER_FROM_HAND",
            value=1,
            slot={"source_zone": "HAND", "dest_zone": "STAGE"},
        )
        operation = _semantic_operation(
            kind="effect",
            code="play_member_from_hand(1)",
            matched_text=body,
            runtime=runtime,
            notes={"source_zone": "HAND", "dest_zone": "STAGE"},
        )
        return operation, marker

    if match := _WAIT_MEMBER_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=1,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code="tap_member(1)",
            matched_text=body,
            runtime=runtime,
            notes={"effect": "WAIT"},
        )
        return operation, marker

    if match := _WAIT_SELF_RE.fullmatch(compact):
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=1,
            slot={"target_slot": 4},
            attr={"is_optional": 1},
        )
        operation = _semantic_operation(
            kind="cost",
            code="tap_self_optional()",
            matched_text=body,
            runtime=runtime,
            notes={"optional": True, "target": "SELF"},
        )
        return operation, marker

    if match := _PLACE_ENERGY_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "PLACE_ENERGY_UNDER_MEMBER",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"place_energy({count})",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "state": "WAIT"},
        )
        return operation, marker

    if match := _CHOICE_PATTERN_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "SELECT_MODE",
            value=count,
            slot={},
        )
        operation = _semantic_operation(
            kind="selection",
            code=f"select_mode({count})",
            matched_text=body,
            runtime=runtime,
            notes={"choice_count": count},
        )
        return operation, marker

    if match := _ADD_TO_HAND_REMAINDER_RE.fullmatch(compact):
        count = int(match.group("count"))
        runtime = _semantic_runtime_frame(
            "ADD_TO_HAND",
            value=count,
            slot={"target_slot": 6},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"add_to_hand({count}, discard_remainder=true)",
            matched_text=body,
            runtime=runtime,
            notes={"count": count, "discard_remainder": True},
        )
        return operation, marker

    if match := _TARGET_OPPONENT_WAIT_RE.fullmatch(compact):
        cost = int(match.group("cost"))
        count = int(match.groupdict().get("count") or 1)
        runtime = _semantic_runtime_frame(
            "TAP_MEMBER",
            value=count,
            slot={"target": "OPPONENT"},
            params={"cost_filter": cost},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"tap_opponent(cost<={cost}, count={count})",
            matched_text=body,
            runtime=runtime,
            notes={"target": "OPPONENT", "cost_filter": cost, "count": count},
        )
        return operation, marker

    if match := _CONDITIONAL_EFFECT_RE.fullmatch(compact):
        condition = match.group(1)
        effect = match.group(2)
        condition_frames = _strip_trailing_return(_frames_for_text(condition))
        effect_frames = _strip_trailing_return(_frames_for_text(effect))
        if condition_frames and effect_frames:
            runtime = {
                "frames": condition_frames
                + [
                    {
                        "op": "JUMP_IF_FALSE",
                        "value": len(effect_frames) + 1,
                        "slot": {},
                        "params": {"condition": condition, "effect": effect},
                    }
                ]
                + effect_frames
            }
        else:
            runtime = _semantic_runtime_frame(
                "CONDITIONAL",
                value=0,
                slot={},
                params={"condition": condition, "effect": effect},
            )
        operation = _semantic_operation(
            kind="conditional",
            code=f"if({condition}, then={effect})",
            matched_text=body,
            runtime=runtime,
            notes={"condition": condition, "effect": effect},
        )
        return operation, marker

    if match := _DURATION_UNTIL_LIVE_END_RE.fullmatch(compact):
        effect = match.group(1)
        runtime = _semantic_runtime_frame(
            "DURATION",
            value=0,
            slot={},
            params={"duration": "LIVE_END", "effect": effect},
        )
        operation = _semantic_operation(
            kind="duration",
            code=f"duration(LIVE_END, {effect})",
            matched_text=body,
            runtime=runtime,
            notes={"duration": "LIVE_END", "effect": effect},
        )
        return operation, marker

    if match := _SEARCH_DECK_RE.fullmatch(compact):
        card_type = match.group(1)
        count = int(match.group("count"))
        action = match.group(2)
        runtime = _semantic_runtime_frame(
            "SEARCH_DECK",
            value=count,
            slot={"source_zone": "DECK"},
            params={"card_type": card_type, "action": action},
        )
        operation = _semantic_operation(
            kind="search",
            code=f"search_deck({card_type}, count={count}, action={action})",
            matched_text=body,
            runtime=runtime,
            notes={"card_type": card_type, "count": count, "action": action},
        )
        return operation, marker

    if match := _BOOST_SCORE_RE.fullmatch(compact):
        value = int(match.group("value"))
        runtime = _semantic_runtime_frame(
            "BOOST_SCORE",
            value=value,
            slot={},
        )
        operation = _semantic_operation(
            kind="effect",
            code=f"boost_score({value})",
            matched_text=body,
            runtime=runtime,
            notes={"value": value},
        )
        return operation, marker

    return None, marker


def extract_semantic_form_from_text(raw_text: str) -> dict[str, Any]:
    """Turn authored Japanese text into a semantic report plus leftover clauses."""
    source_text = str(raw_text or "")
    trigger_markers, clauses = _extract_trigger_and_clauses(source_text)
    operations: list[dict[str, Any]] = []
    clause_reports: list[dict[str, Any]] = []
    unmatched_clauses: list[dict[str, Any]] = []

    for index, clause in enumerate(clauses):
        operation, _ = _extract_semantic_operation(clause)

        clause_report: dict[str, Any] = {
            "index": index,
            "text": clause,
            "normalized_text": _normalize_authored_text(clause),
            "matched": operation is not None,
        }

        if operation is not None:
            operations.append(operation)
            clause_report["operation"] = operation
            clause_report["residual_text"] = ""
        else:
            clause_report["residual_text"] = clause
            unmatched_clauses.append(
                {
                    "index": index,
                    "text": clause,
                    "residual_text": clause,
                }
            )

        clause_reports.append(clause_report)

    coverage = {
        "clause_count": len(clauses),
        "matched_clause_count": sum(1 for item in clause_reports if item["matched"]),
        "unmatched_clause_count": len(unmatched_clauses),
    }

    return {
        "schema": "ability_semantic_form.v1",
        "source_text": source_text,
        "normalized_text": _normalize_authored_text(source_text),
        "trigger_markers": trigger_markers,
        "clauses": clause_reports,
        "operations": operations,
        "unmatched_clauses": unmatched_clauses,
        "coverage": coverage,
    }


def populate_semantic_from_text(abilities: list) -> None:
    """Populate a semantic form report directly from authored text."""
    for ab in abilities:
        raw_text = str(getattr(ab, "raw_text", "") or "")
        setattr(ab, "semantic_form", extract_semantic_form_from_text(raw_text))


def semantic_form_to_frame_program(semantic_form: dict[str, Any]) -> dict[str, Any]:
    """Convert a semantic form report into a minimal frame_program."""
    frames: list[dict[str, Any]] = []
    if not isinstance(semantic_form, dict):
        return {"frames": frames}

    for operation in semantic_form.get("operations", []):
        if not isinstance(operation, dict):
            continue
        runtime = operation.get("runtime")
        if isinstance(runtime, dict) and runtime:
            nested_frames = runtime.get("frames")
            if isinstance(nested_frames, list) and nested_frames:
                frames.extend([dict(frame) for frame in nested_frames if isinstance(frame, dict)])
            else:
                frames.append(dict(runtime))

    # Insert JUMP_IF_FALSE after SELECT_MEMBER when followed by effects that need a target
    # This handles cases like Q196 where the effect should be skipped if no member is selected
    i = 0
    while i < len(frames) - 1:
        frame = frames[i]
        next_frame = frames[i + 1]
        op = str(frame.get("op", frame.get("opcode", ""))).upper()
        next_op = str(next_frame.get("op", next_frame.get("opcode", ""))).upper()
        
        # If SELECT_MEMBER is followed by an effect that needs a target (ADD_BLADES, ADD_HEARTS, etc.)
        # insert JUMP_IF_FALSE to skip the effect if selection failed
        if op == "SELECT_MEMBER" and next_op in {"ADD_BLADES", "ADD_HEARTS", "ACTIVATE_MEMBER"}:
            # Insert JUMP_IF_FALSE that skips the next frame if selection failed
            jump_frame = {
                "op": "JUMP_IF_FALSE",
                "value": 1,  # Skip 1 frame (the next effect)
                "frame_index": i + 1,
            }
            frames.insert(i + 1, jump_frame)
            i += 1  # Skip the jump frame we just inserted
        i += 1

    if frames and str(frames[-1].get("op", frames[-1].get("opcode", ""))).upper() != "RETURN":
        frames.append({"op": "RETURN"})

    return {
        "schema": "ability_frame_program.v1",
        "frames": frames,
        "source": "semantic_form",
    }


def populate_semantic_from_frames(abilities: list) -> None:
    """Populate effects/conditions/costs from frame_program data."""
    for ab in abilities:
        frame_program = getattr(ab, "frame_program", None)
        if not isinstance(frame_program, dict):
            continue
        
        frames = frame_program.get("frames", [])
        if not isinstance(frames, list):
            continue
        
        # Clear and repopulate
        ab.effects = []
        ab.conditions = []
        ab.costs = []
        ability_text = str(getattr(ab, "raw_text", "") or "")
        inferred_area = extract_primary_area(ability_text)
        inferred_heart_color = extract_primary_heart_color(ability_text)
        saw_area_condition = False
        
        for frame in frames:
            if not isinstance(frame, dict):
                continue

            opcode = str(frame.get("opcode", frame.get("op", ""))).upper()
            if not opcode or opcode == "RETURN":
                continue
            semantic = frame.get("semantic", {})
            if not isinstance(semantic, dict):
                semantic = {}
            options = frame.get("options", {})
            if not isinstance(options, dict):
                options = {}

            value = semantic.get("value", frame.get("value", 0))
            filter_data = semantic.get("filter", frame.get("filter", {}))
            if not isinstance(filter_data, dict):
                filter_data = {}
            slot_data = semantic.get("slot", frame.get("slot", {}))
            if not isinstance(slot_data, dict):
                slot_data = {}
            params = semantic.get("params", frame.get("params", {}))
            if not isinstance(params, dict):
                params = {}
            attr_data = frame.get("attr", {})
            if not isinstance(attr_data, dict):
                attr_data = {}

            is_negated = bool(semantic.get("is_negated", False)) or bool(frame.get("is_negated", frame.get("negated", False)))
            is_cost = bool(semantic.get("is_cost", False)) or bool(frame.get("is_cost", False))
            is_optional = bool(semantic.get("is_optional", False)) or bool(frame.get("is_optional", frame.get("optional", False)))
            if isinstance(options, dict):
                is_cost = is_cost or bool(options.get("is_cost", False))
                is_optional = bool(options.get("optional", False))
                if not filter_data:
                    filter_data = options.get("filter", {})
                    if not isinstance(filter_data, dict):
                        filter_data = {}
                if not slot_data:
                    slot_data = options.get("slot", {})
                    if not isinstance(slot_data, dict):
                        slot_data = {}
            if not filter_data:
                filter_data = frame.get("filter", {})
                if not isinstance(filter_data, dict):
                    filter_data = {}
            if not slot_data:
                slot_data = frame.get("slot", {})
                if not isinstance(slot_data, dict):
                    slot_data = {}

            cond_type = _CONDITION_OPCODE_MAP.get(opcode, ConditionType.NONE)
            if cond_type != ConditionType.NONE:
                attr = 0
                if attr_data.get("group_enabled"):
                    attr |= 0x10
                    attr |= (_coerce_group_id(attr_data.get("group_id", 0)) & 0x7F) << 5

                if cond_type == ConditionType.HAS_KEYWORD:
                    keyword = str(params.get("keyword", "") or filter_data.get("keyword", ""))
                    keyword_energy = bool(attr_data.get("keyword_energy")) or keyword in _ENERGY_KEYWORDS
                    keyword_member = bool(attr_data.get("keyword_member")) or keyword in _MEMBER_KEYWORDS
                    group_enabled = bool(attr_data.get("group_enabled"))

                    if keyword_energy:
                        filter_data["keyword_energy"] = True
                    if keyword_member:
                        filter_data["keyword_member"] = True
                    if group_enabled:
                        filter_data["group_enabled"] = True
                        filter_data["group_id"] = attr_data.get("group_id", 0)

                    if keyword_energy and "keyword" not in params:
                        params["keyword"] = "DID_ACTIVATE_ENERGY"
                        if group_enabled:
                            params["group_id"] = filter_data["group_id"]
                    elif keyword_member and "keyword" not in params:
                        params["keyword"] = "DID_ACTIVATE_MEMBER"
                        if group_enabled:
                            params["group_id"] = filter_data["group_id"]

                if opcode == _RAW_UNIQUE_NAMES_OPCODE:
                    raw_params = dict(params)
                    raw_params.setdefault("raw_cond", "UNIQUE_NAMES_COUNT")
                    raw_params.setdefault("MIN", value)
                    ab.conditions.append(
                        Condition(
                            type=ConditionType.NONE,
                            value=value,
                            params=raw_params,
                            is_negated=is_negated,
                            attr=attr,
                        )
                    )
                else:
                    if cond_type in {ConditionType.AREA_CHECK, ConditionType.IS_CENTER}:
                        saw_area_condition = True
                    ab.conditions.append(
                        Condition(
                            type=cond_type,
                            value=value,
                            params=params,
                            is_negated=is_negated,
                            attr=attr,
                        )
                    )
                continue

            if is_cost:
                cost_type = _COST_OPCODE_MAP.get(opcode, AbilityCostType.NONE)
                if cost_type != AbilityCostType.NONE:
                    ab.costs.append(
                        Cost(
                            type=cost_type,
                            value=value,
                            params=params,
                            is_optional=is_optional,
                        )
                    )
                    continue

            eff_type = _EFFECT_OPCODE_MAP.get(opcode, EffectType.NONE)
            if eff_type != EffectType.NONE:
                effect_params = dict(params)
                if eff_type == EffectType.ADD_HEARTS and "color" not in effect_params:
                    # Frame data often omits heart color, so recover it from the authored text.
                    effect_color = inferred_heart_color
                    if effect_color is not None:
                        effect_params["color"] = effect_color
                        if effect_color == 6:
                            effect_params["all"] = True
                if eff_type == EffectType.LOOK_AND_CHOOSE and "choose_count" not in effect_params:
                    inferred_choose_count = 0
                    if ability_text:
                        normalized_text = unicodedata.normalize("NFKC", ability_text)
                        for pattern in _LOOK_AND_CHOOSE_COUNT_PATTERNS:
                            match = pattern.search(normalized_text)
                            if match:
                                try:
                                    inferred_choose_count = int(match.group(1))
                                except (TypeError, ValueError):
                                    inferred_choose_count = 0
                                break
                    if inferred_choose_count > 0:
                        effect_params["choose_count"] = inferred_choose_count
                        if isinstance(frame, dict):
                            frame_params = frame.get("params")
                            if not isinstance(frame_params, dict):
                                frame_params = {}
                                frame["params"] = frame_params
                            frame_params.setdefault("choose_count", inferred_choose_count)

                            frame_value = frame.get("value")
                            if isinstance(frame_value, dict):
                                frame_value.setdefault("choose_count", inferred_choose_count)

                            frame_semantic = frame.get("semantic")
                            if isinstance(frame_semantic, dict):
                                frame_semantic_params = frame_semantic.get("params")
                                if not isinstance(frame_semantic_params, dict):
                                    frame_semantic_params = {}
                                    frame_semantic["params"] = frame_semantic_params
                                frame_semantic_params.setdefault("choose_count", inferred_choose_count)

                target = TargetType.SELF
                if slot_data.get("is_opponent"):
                    target = TargetType.OPPONENT
                else:
                    target_slot = slot_data.get("target_slot", 0)
                    try:
                        target_slot = int(target_slot)
                    except (TypeError, ValueError):
                        target_slot = 0
                    target = _TARGET_SLOT_MAP.get(target_slot, TargetType.SELF)

                ab.effects.append(
                    Effect(
                        effect_type=eff_type,
                        value=value,
                        target=target,
                        params=effect_params,
                        is_optional=is_optional,
                    )
                )

        if inferred_area is not None and any(effect.effect_type == EffectType.ADD_HEARTS for effect in ab.effects):
            if not saw_area_condition:
                ab.conditions.append(
                    Condition(
                        type=ConditionType.AREA_CHECK,
                        value=inferred_area,
                        params={"value": inferred_area},
                    )
                )
