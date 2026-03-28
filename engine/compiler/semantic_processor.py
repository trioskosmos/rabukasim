"""
Semantic Frame Processor

Converts frame_program instructions into semantic effects, conditions, and costs.
"""

from ..models.ability import Ability, Effect, Condition, Cost
from ..models.generated_enums import EffectType, ConditionType, AbilityCostType, TargetType


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
    }
    return mapping.get(opcode.upper(), EffectType.NONE)


def _opcode_to_condition_type(opcode: str) -> ConditionType:
    """Map CHECK_* opcode to ConditionType."""
    mapping = {
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
    result = {"opcode": "", "value": 0, "filter": {}, "slot": {}, "params": {},
              "is_cost": False, "is_negated": False, "is_optional": False}
    
    if not isinstance(frame, dict):
        return result
    
    result["opcode"] = str(frame.get("opcode", frame.get("op", ""))).upper()
    result["value"] = frame.get("value", 0)
    
    # Check semantic data first
    semantic = frame.get("semantic", {})
    if isinstance(semantic, dict):
        result["value"] = semantic.get("value", result["value"])
        result["filter"] = semantic.get("filter", {})
        result["slot"] = semantic.get("slot", {})
        result["params"] = semantic.get("params", {})
        result["is_negated"] = semantic.get("is_negated", False)
        result["is_cost"] = semantic.get("is_cost", False)
    
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
        
        for frame in instructions:
            data = _extract_frame_data(frame)
            opcode = data["opcode"]
            
            if not opcode or opcode == "RETURN":
                continue
            
            # Handle conditions
            if opcode.startswith("CHECK_"):
                cond_type = _opcode_to_condition_type(opcode)
                if cond_type != ConditionType.NONE:
                    ab.conditions.append(Condition(
                        type=cond_type, value=data["value"], params=data["params"],
                        is_negated=data["is_negated"], target_slot=data["slot"].get("target_slot", 0)
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
                ab.effects.append(Effect(
                    effect_type=eff_type, value=data["value"],
                    target=_determine_target(data["slot"]),
                    params=data["params"], is_optional=data["is_optional"]
                ))


# Backwards compatibility alias
_populate_semantic_from_frames = populate_semantic_from_frames
