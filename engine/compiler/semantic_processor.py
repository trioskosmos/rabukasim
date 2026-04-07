"""
Semantic Frame Processor

Converts frame_program frames into semantic effects, conditions, and costs.
"""

import re
import unicodedata

from ..models.ability import Ability, Effect, Condition, Cost
from ..models.generated_enums import EffectType, ConditionType, AbilityCostType, TargetType


_LOOK_AND_CHOOSE_COUNT_PATTERNS = (
    re.compile(r"([0-9]+)枚まで"),
    re.compile(r"choose(?: up to)?\s*([0-9]+)", re.IGNORECASE),
)

_GROUP_ID_MAP = {
    "MUSE": 0,
    "MUS": 0,
    "Μ'S": 0,
    "M'S": 0,
    "U'S": 0,
    "AQOURS": 1,
    "AQUOURS": 1,
    "NIJIGASAKI": 2,
    "NIJIGAKU": 2,
    "NIJI": 2,
    "LIELLA": 3,
    "HASUNOSORA": 4,
    "HASU": 4,
    "ARISE": 10,
    "SAINT_SNOW": 11,
    "SUNNY_PASSION": 12,
    "MUSICAL": 13,
}

_EFFECT_OPCODE_MAP = {
    "DRAW": EffectType.DRAW,
    "RECOVER_MEMBER": EffectType.RECOVER_MEMBER,
    "RECOVER_LIVE": EffectType.RECOVER_LIVE,
    "BOOST_SCORE": EffectType.BOOST_SCORE,
    "ADD_BLADES": EffectType.ADD_BLADES,
    "ADD_HEARTS": EffectType.ADD_HEARTS,
    "MOVE_MEMBER": EffectType.MOVE_MEMBER,
    "MOVE_TO_DISCARD": EffectType.MOVE_TO_DISCARD,
    "MOVE_TO_DECK": EffectType.MOVE_TO_DECK,
    "TAP_MEMBER": EffectType.TAP_MEMBER,
    "TAP_OPPONENT": EffectType.TAP_OPPONENT,
    "SET_TAPPED": EffectType.SET_TAPPED,
    "ENERGY_CHARGE": EffectType.ENERGY_CHARGE,
    "ACTIVATE_MEMBER": EffectType.ACTIVATE_MEMBER,
    "SEARCH_DECK": EffectType.SEARCH_DECK,
    "LOOK_AND_CHOOSE": EffectType.LOOK_AND_CHOOSE,
    "LOOK_DECK": EffectType.LOOK_DECK,
    "ORDER_DECK": EffectType.ORDER_DECK,
    "SELECT_MEMBER": EffectType.SELECT_MEMBER,
    "SELECT_CARDS": EffectType.SELECT_CARDS,
    "PLAY_MEMBER_FROM_HAND": EffectType.PLAY_MEMBER_FROM_HAND,
    "PLAY_MEMBER_FROM_DISCARD": EffectType.PLAY_MEMBER_FROM_DISCARD,
    "REDUCE_COST": EffectType.REDUCE_COST,
    "REDUCE_HEART_REQ": EffectType.REDUCE_HEART_REQ,
    "TRANSFORM_COLOR": EffectType.TRANSFORM_COLOR,
    "META_RULE": EffectType.META_RULE,
    "REVEAL_UNTIL": EffectType.REVEAL_UNTIL,
    "REVEAL_CARDS": EffectType.REVEAL_CARDS,
    "SWAP_CARDS": EffectType.SWAP_CARDS,
    "SWAP_AREA": EffectType.SWAP_AREA,
    "PREVENT_BATON_TOUCH": EffectType.PREVENT_BATON_TOUCH,
    "PREVENT_ACTIVATE": EffectType.PREVENT_ACTIVATE,
    "GRANT_ABILITY": EffectType.GRANT_ABILITY,
    "INCREASE_COST": EffectType.INCREASE_COST,
    "SET_HEART_COST": EffectType.SET_HEART_COST,
    "MODIFY_SCORE_RULE": EffectType.MODIFY_SCORE_RULE,
    "SELECT_MODE": EffectType.SELECT_MODE,
    "COLOR_SELECT": EffectType.COLOR_SELECT,
    "BATON_TOUCH_MOD": EffectType.BATON_TOUCH_MOD,
    "BUFF_POWER": EffectType.BUFF_POWER,
    "PLAY_LIVE_FROM_DISCARD": EffectType.PLAY_LIVE_FROM_DISCARD,
    "ADD_TO_HAND": EffectType.ADD_TO_HAND,
    "DRAW_UNTIL": EffectType.DRAW_UNTIL,
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

_CONDITION_OPCODE_MAP = {
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

