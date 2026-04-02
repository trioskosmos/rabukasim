"""
Semantic Frame Processor

Converts frame_program instructions into semantic effects, conditions, and costs.
"""

import re
import unicodedata

from ..models.ability import Ability, Effect, Condition, Cost
from ..models.generated_enums import EffectType, ConditionType, AbilityCostType, TargetType


_LOOK_AND_CHOOSE_COUNT_PATTERNS = (
    re.compile(r"([0-9]+)枚まで"),
    re.compile(r"choose(?: up to)?\s*([0-9]+)", re.IGNORECASE),
)


def _opcode_to_effect_type(opcode: str) -> EffectType:
    """Map opcode name to EffectType."""
    mapping = {
        "DRAW": EffectType.DRAW, "RECOVER_MEMBER": EffectType.RECOVER_MEMBER,
        "RECOVER_LIVE": EffectType.RECOVER_LIVE, "BOOST_SCORE": EffectType.BOOST_SCORE,
        "ADD_BLADES": EffectType.ADD_BLADES, "ADD_HEARTS": EffectType.ADD_HEARTS,
        "MOVE_MEMBER": EffectType.MOVE_MEMBER, "MOVE_TO_DISCARD": EffectType.MOVE_TO_DISCARD,
        "MOVE_TO_DECK": EffectType.MOVE_TO_DECK, "TAP_MEMBER": EffectType.TAP_MEMBER,
        "TAP_OPPONENT": EffectType.TAP_OPPONENT, "SET_TAPPED": EffectType.SET_TAPPED,
        "ENERGY_CHARGE": EffectType.ENERGY_CHARGE, "ACTIVATE_MEMBER": EffectType.ACTIVATE_MEMBER,
        "SEARCH_DECK": EffectType.SEARCH_DECK, "LOOK_AND_CHOOSE": EffectType.LOOK_AND_CHOOSE,
        "LOOK_DECK": EffectType.LOOK_DECK, "ORDER_DECK": EffectType.ORDER_DECK,
        "SELECT_MEMBER": EffectType.SELECT_MEMBER, "SELECT_CARDS": EffectType.SELECT_CARDS,
        "PLAY_MEMBER_FROM_HAND": EffectType.PLAY_MEMBER_FROM_HAND,
        "PLAY_MEMBER_FROM_DISCARD": EffectType.PLAY_MEMBER_FROM_DISCARD,
        "REDUCE_COST": EffectType.REDUCE_COST, "REDUCE_HEART_REQ": EffectType.REDUCE_HEART_REQ,
        "TRANSFORM_COLOR": EffectType.TRANSFORM_COLOR, "META_RULE": EffectType.META_RULE,
        "REVEAL_UNTIL": EffectType.REVEAL_UNTIL, "REVEAL_CARDS": EffectType.REVEAL_CARDS,
        "SWAP_CARDS": EffectType.SWAP_CARDS, "SWAP_AREA": EffectType.SWAP_AREA,
        "PREVENT_BATON_TOUCH": EffectType.PREVENT_BATON_TOUCH,
        "PREVENT_ACTIVATE": EffectType.PREVENT_ACTIVATE,
        "GRANT_ABILITY": EffectType.GRANT_ABILITY, "INCREASE_COST": EffectType.INCREASE_COST,
        "SET_HEART_COST": EffectType.SET_HEART_COST, "MODIFY_SCORE_RULE": EffectType.MODIFY_SCORE_RULE,
        "SELECT_MODE": EffectType.SELECT_MODE, "COLOR_SELECT": EffectType.COLOR_SELECT,
        "BATON_TOUCH_MOD": EffectType.BATON_TOUCH_MOD, "BUFF_POWER": EffectType.BUFF_POWER,
        "PLAY_LIVE_FROM_DISCARD": EffectType.PLAY_LIVE_FROM_DISCARD,
        "ADD_TO_HAND": EffectType.ADD_TO_HAND, "DRAW_UNTIL": EffectType.DRAW_UNTIL,
        "ACTIVATE_ENERGY": EffectType.ACTIVATE_ENERGY,
        "CALC_SUM_COST": EffectType.CALC_SUM_COST,
        "DIV_VALUE": EffectType.DIV_VALUE,
        "LOOK_REORDER_DISCARD": EffectType.LOOK_REORDER_DISCARD,
        "OPPONENT_CHOOSE": EffectType.OPPONENT_CHOOSE,
        "PAY_ENERGY_DYNAMIC": EffectType.PAY_ENERGY_DYNAMIC,
        "PAY_ENERGY": EffectType.PAY_ENERGY,
        "PLACE_ENERGY_UNDER_MEMBER": EffectType.PLACE_ENERGY_UNDER_MEMBER,
        "PREVENT_PLAY_TO_SLOT": EffectType.PREVENT_PLAY_TO_SLOT,
        "PREVENT_SET_TO_SUCCESS_PILE": EffectType.PREVENT_SET_TO_SUCCESS_PILE,
        "REDUCE_LIVE_SET_LIMIT": EffectType.REDUCE_LIVE_SET_LIMIT,
        "REDUCE_SCORE": EffectType.REDUCE_SCORE,
        "REPEAT_ABILITY": EffectType.REPEAT_ABILITY,
        "SET_TARGET_SELF": EffectType.SET_TARGET_SELF,
        "SET_TARGET_OPPONENT": EffectType.SET_TARGET_OPPONENT,
        "SKIP_ACTIVATE_PHASE": EffectType.SKIP_ACTIVATE_PHASE,
        "TRANSFORM_BLADES": EffectType.TRANSFORM_BLADES,
        "TRANSFORM_HEART": EffectType.TRANSFORM_HEART,
        "LOOK_DECK_DYNAMIC": EffectType.LOOK_DECK_DYNAMIC,
        "INCREASE_HEART_COST": EffectType.INCREASE_HEART_COST,
        "NEGATE_EFFECT": EffectType.NEGATE_EFFECT,
        "RESTRICTION": EffectType.RESTRICTION,
        "SELECT_LIVE": EffectType.SELECT_LIVE,
        "SELECT_PLAYER": EffectType.SELECT_PLAYER,
        "SET_SCORE": EffectType.SET_SCORE,
        "TRIGGER_REMOTE": EffectType.TRIGGER_REMOTE,
        "FORMATION_CHANGE": EffectType.FORMATION_CHANGE,
        "REDUCE_YELL_COUNT": EffectType.REDUCE_YELL_COUNT,
    }
    return mapping.get(opcode.upper(), EffectType.NONE)


def _opcode_to_condition_type(opcode: str) -> ConditionType:
    """Map condition-like opcode names to ConditionType."""
    mapping = {
        "HAS_MEMBER": ConditionType.HAS_MEMBER,
        "COUNT_STAGE": ConditionType.COUNT_STAGE,
        "COUNT_HAND": ConditionType.COUNT_HAND,
        "COUNT_DISCARD": ConditionType.COUNT_DISCARD,
        "COUNT_ENERGY": ConditionType.COUNT_ENERGY,
        "COUNT_HEARTS": ConditionType.COUNT_HEARTS,
        "COUNT_BLADES": ConditionType.COUNT_BLADES,
        "COUNT_LIVE_ZONE": ConditionType.COUNT_LIVE_ZONE,
        "COUNT_SUCCESS_LIVE": ConditionType.COUNT_SUCCESS_LIVE,
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
        "CHECK_UNIQUE_NAMES": ConditionType.UNIQUE_NAMES_COUNT,
    }
    return mapping.get(opcode.upper(), ConditionType.NONE)


def _encode_keyword_filter(params: dict, filter_data: dict, attr_data: dict = None) -> dict:
    """Encode keyword conditions into filter flags for Rust compatibility.
    
    Rust expects either:
    - filter.keyword_energy = True (for activated energy)
    - filter.keyword_member = True (for activated member)
    - OR raw_attr with bits 62/63 set
    """
    result = {}
    # Check params first, then filter, then attr
    keyword = params.get("keyword", "")
    if not keyword and filter_data:
        keyword = filter_data.get("keyword", "")
    if not keyword and attr_data:
        # Check for keyword flags in attr
        if attr_data.get("keyword_energy"):
            result["keyword_energy"] = True
        if attr_data.get("keyword_member"):
            result["keyword_member"] = True
        # Also extract group info if present
        if attr_data.get("group_enabled"):
            result["group_enabled"] = True
            result["group_id"] = attr_data.get("group_id", 0)
        return result
    
    if keyword in ("activated_energy", "DID_ACTIVATE_ENERGY", "DID_ACTIVATE_ENERGY_BY_GROUP"):
        result["keyword_energy"] = True
    elif keyword in ("activated_member", "DID_ACTIVATE_MEMBER", "DID_ACTIVATE_MEMBER_BY_GROUP"):
        result["keyword_member"] = True
    return result


def _encode_attr_from_frame(attr_data: dict) -> int:
    """Encode attr field from frame's attr data.
    
    Bit layout (matching Rust filter.rs):
    - Bit 4: Group Enable flag
    - Bits 5-11: Group ID (7 bits)
    """
    attr = 0
    if not attr_data:
        return attr
    
    # Group filter encoding
    if attr_data.get("group_enabled"):
        attr |= 0x10  # Bit 4: Group Enable
        group_id = attr_data.get("group_id", 0)
        attr |= (group_id & 0x7F) << 5  # Bits 5-11: Group ID
    
    return attr


def _opcode_to_cost_type(opcode: str, is_cost: bool) -> AbilityCostType:
    """Map opcode to AbilityCostType if marked as cost."""
    if not is_cost:
        return AbilityCostType.NONE
    mapping = {
        "PAY_ENERGY": AbilityCostType.ENERGY, "SET_TAPPED": AbilityCostType.TAP_SELF,
        "TAP_MEMBER": AbilityCostType.TAP_MEMBER, "MOVE_TO_DISCARD": AbilityCostType.DISCARD_HAND,
        "SELECT_CARDS": AbilityCostType.SELECT_CARDS, "SELECT_MEMBER": AbilityCostType.SELECT_MEMBER,
    }
    return mapping.get(opcode.upper(), AbilityCostType.NONE)


def _extract_frame_data(frame: dict) -> dict:
    """Extract all relevant data from a frame."""
    result = {"opcode": "", "value": 0, "filter": {}, "attr": {}, "slot": {}, "params": {},
              "is_cost": False, "is_negated": False, "is_optional": False}
    
    if not isinstance(frame, dict):
        return result
    
    result["opcode"] = str(frame.get("opcode", frame.get("op", ""))).upper()
    result["value"] = frame.get("value", 0)
    result["attr"] = frame.get("attr", {})  # Extract attr field for keyword flags
    
    # Check semantic data first
    semantic = frame.get("semantic", {})
    if isinstance(semantic, dict):
        result["value"] = semantic.get("value", result["value"])
        result["filter"] = semantic.get("filter", {})
        result["slot"] = semantic.get("slot", {})
        result["params"] = semantic.get("params", {})
        result["is_negated"] = semantic.get("is_negated", False)
        result["is_cost"] = semantic.get("is_cost", False)
        result["is_optional"] = semantic.get("is_optional", result["is_optional"])
    result["is_negated"] = result["is_negated"] or bool(frame.get("is_negated", frame.get("negated", False)))
    result["is_optional"] = result["is_optional"] or bool(frame.get("is_optional", frame.get("optional", False)))
    result["is_cost"] = result["is_cost"] or bool(frame.get("is_cost", False))
    
    # Check options field
    options = frame.get("options", {})
    if isinstance(options, dict):
        result["is_cost"] = result["is_cost"] or options.get("is_cost", False)
        result["is_optional"] = options.get("optional", False)
        if not result["filter"]: result["filter"] = options.get("filter", {})
        if not result["slot"]: result["slot"] = options.get("slot", {})
    
    # Direct frame fields as fallback
    if not result["filter"]: result["filter"] = frame.get("filter", {})
    if not result["slot"]: result["slot"] = frame.get("slot", {})
    
    return result


def _determine_target(slot_data: dict) -> TargetType:
    """Determine target type from slot data."""
    if not slot_data:
        return TargetType.SELF
    if slot_data.get("is_opponent"):
        return TargetType.OPPONENT
    target_slot = slot_data.get("target_slot", 0)
    if target_slot == 6: return TargetType.CARD_HAND
    if target_slot == 7: return TargetType.CARD_DISCARD
    if target_slot == 4: return TargetType.MEMBER_SELF
    return TargetType.SELF


def _infer_look_and_choose_count(ability_text: str) -> int:
    """Infer LOOK_AND_CHOOSE choose_count from authored card text."""
    if not ability_text:
        return 0

    normalized = unicodedata.normalize("NFKC", ability_text)
    for pattern in _LOOK_AND_CHOOSE_COUNT_PATTERNS:
        match = pattern.search(normalized)
        if match:
            try:
                return int(match.group(1))
            except (TypeError, ValueError):
                return 0
    return 0


def populate_semantic_from_frames(abilities: list, card_no: str = "") -> None:
    """Populate effects/conditions/costs from frame_program data."""
    for ab in abilities:
        frame_program = getattr(ab, "frame_program", None)
        if not isinstance(frame_program, dict):
            continue
        
        instructions = frame_program.get("instructions", [])
        if not isinstance(instructions, list):
            continue
        
        # Clear and repopulate
        ab.effects = []
        ab.conditions = []
        ab.costs = []
        ability_text = str(getattr(ab, "raw_text", "") or "")
        
        for frame in instructions:
            data = _extract_frame_data(frame)
            opcode = data["opcode"]
            
            if not opcode or opcode == "RETURN":
                continue
            
            # Handle conditions
            cond_type = _opcode_to_condition_type(opcode)
            if cond_type != ConditionType.NONE:
                # For HAS_KEYWORD conditions, encode keyword into filter for Rust compatibility
                filter_data = data.get("filter", {})
                params = dict(data.get("params", {}))  # Copy params
                if cond_type == ConditionType.HAS_KEYWORD:
                    # Get attr data which contains keyword_energy/keyword_member flags
                    attr_data = data.get("attr", {})
                    keyword_filter = _encode_keyword_filter(params, filter_data, attr_data)
                    filter_data.update(keyword_filter)
                    # Also ensure keyword is in params for Rust check_condition
                    if keyword_filter.get("keyword_energy") and "keyword" not in params:
                        params["keyword"] = "DID_ACTIVATE_ENERGY"
                        # Add group_id if present
                        if keyword_filter.get("group_enabled"):
                            params["group_id"] = keyword_filter.get("group_id", 0)
                    elif keyword_filter.get("keyword_member") and "keyword" not in params:
                        params["keyword"] = "DID_ACTIVATE_MEMBER"
                        # Add group_id if present
                        if keyword_filter.get("group_enabled"):
                            params["group_id"] = keyword_filter.get("group_id", 0)
                
                # Encode attr from frame data
                attr_data = data.get("attr", {})
                attr = _encode_attr_from_frame(attr_data)
                
                ab.conditions.append(Condition(
                    type=cond_type, value=data["value"], params=params,
                    is_negated=data["is_negated"],
                    attr=attr
                ))
                continue
            
            # Handle costs
            cost_type = _opcode_to_cost_type(opcode, data["is_cost"])
            if cost_type != AbilityCostType.NONE:
                ab.costs.append(Cost(
                    type=cost_type, value=data["value"], params=data["params"],
                    is_optional=data["is_optional"]
                ))
                continue
            
            # Handle effects
            eff_type = _opcode_to_effect_type(opcode)
            if eff_type != EffectType.NONE:
                params = dict(data["params"])
                if eff_type == EffectType.LOOK_AND_CHOOSE and "choose_count" not in params:
                    inferred_choose_count = _infer_look_and_choose_count(ability_text)
                    if inferred_choose_count > 0:
                        params["choose_count"] = inferred_choose_count

                ab.effects.append(Effect(
                    effect_type=eff_type, value=data["value"],
                    target=_determine_target(data["slot"]),
                    params=params, is_optional=data["is_optional"]
                ))


# Backwards compatibility alias
_populate_semantic_from_frames = populate_semantic_from_frames
