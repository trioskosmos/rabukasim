from typing import Any, Dict, List

from .ability_descriptions import (
    EFFECT_DESCRIPTIONS,
    EFFECT_DESCRIPTIONS_JP,
    TRIGGER_DESCRIPTIONS,
    TRIGGER_DESCRIPTIONS_JP,
)
from .ability_filter import format_filter_attr
from .generated_enums import AbilityCostType, ConditionType, TargetType


def build_semantic_form(ability: Any) -> Dict[str, Any]:
    semantic_effects: List[Dict[str, Any]] = []
    for eff in ability.effects:
        try:
            params_copy = eff.params.copy() if hasattr(eff.params, "copy") else dict(eff.params or {})
        except (AttributeError, TypeError, ValueError):
            params_copy = {}

        semantic_effects.append(
            {
                "type": eff.effect_type.name if hasattr(eff.effect_type, "name") else str(eff.effect_type),
                "value": eff.value,
                "target": eff.target.name if hasattr(eff.target, "name") else str(eff.target),
                "params": params_copy,
                "optional": eff.is_optional,
            }
        )

    semantic_conditions: List[Dict[str, Any]] = []
    for cond in ability.conditions:
        try:
            params_upper = {k.upper(): v for k, v in cond.params.items() if isinstance(k, str)}
        except (AttributeError, TypeError):
            params_upper = {}

        comp_str = str(cond.params.get("comparison") or params_upper.get("COMPARISON") or "GE").upper() if cond.params else "GE"
        filter_summary = ""
        if hasattr(cond, "attr") and cond.attr:
            try:
                filter_summary = format_filter_attr(cond.attr)
            except (AttributeError, TypeError, ValueError):
                filter_summary = ""

        semantic_conditions.append(
            {
                "type": cond.type.name if hasattr(cond.type, "name") else str(cond.type),
                "value": cond.value if hasattr(cond, "value") else 0,
                "comparison": comp_str,
                "filter": filter_summary,
                "area": str(cond.params.get("area", "")).upper() if cond.params else "",
                "negated": cond.is_negated if hasattr(cond, "is_negated") else False,
            }
        )

    semantic_costs: List[Dict[str, Any]] = []
    for cost in ability.costs:
        semantic_costs.append(
            {
                "type": cost.type.name if hasattr(cost.type, "name") else str(cost.type),
                "value": cost.value,
                "optional": cost.is_optional,
            }
        )

    instructions_summary = ""
    if ability.instructions:
        parts = []
        from .ability import Condition, Cost, Effect

        for instr in ability.instructions:
            if isinstance(instr, Effect):
                parts.append(f"Effect({instr.effect_type.name})")
            elif isinstance(instr, Condition):
                parts.append(f"Condition({instr.type.name})")
            elif isinstance(instr, Cost):
                parts.append(f"Cost({instr.type.name})")
        instructions_summary = " -> ".join(parts)

    ability.semantic_form = {
        "semantic_version": 1,
        "trigger": ability.trigger.name if hasattr(ability.trigger, "name") else str(ability.trigger),
        "effects": semantic_effects,
        "conditions": semantic_conditions,
        "costs": semantic_costs,
        "once_per_turn": ability.is_once_per_turn,
        "description": ability.pseudocode or ability.raw_text,
        "instructions_summary": instructions_summary,
    }
    return ability.semantic_form


def reconstruct_text(ability: Any, lang: str = "en") -> str:
    parts: List[str] = []
    is_jp = lang == "jp"
    effect_descriptions = EFFECT_DESCRIPTIONS_JP if is_jp else EFFECT_DESCRIPTIONS
    trigger_descriptions = TRIGGER_DESCRIPTIONS_JP if is_jp else TRIGGER_DESCRIPTIONS

    trigger_name = getattr(ability.trigger, "name", str(ability.trigger))
    parts.append(trigger_descriptions.get(ability.trigger, f"[{trigger_name}]"))

    for cost in ability.costs:
        if is_jp:
            if cost.type == AbilityCostType.ENERGY:
                parts.append(f"(繧ｳ繧ｹ繝・ 繧ｨ繝阪Ν繧ｮ繝ｼ{cost.value})")
            elif cost.type == AbilityCostType.TAP_SELF:
                parts.append("(繧ｳ繧ｹ繝・ 閾ｪ蛻・ｒ繝ｬ繧ｹ繝・")
            elif cost.type == AbilityCostType.DISCARD_HAND:
                parts.append(f"(繧ｳ繧ｹ繝・ 謇区惆 {cost.value} 譫壽昏縺ｦ繧・")
            elif cost.type == AbilityCostType.SACRIFICE_SELF:
                parts.append("(繧ｳ繧ｹ繝・ 閾ｪ蛻・ｒ騾蝣ｴ)")
            else:
                parts.append(f"(繧ｳ繧ｹ繝・ {cost.type.name} {cost.value})")
        else:
            if cost.type == AbilityCostType.ENERGY:
                parts.append(f"(Cost: Pay {cost.value} Energy)")
            elif cost.type == AbilityCostType.TAP_SELF:
                parts.append("(Cost: Rest Self)")
            elif cost.type == AbilityCostType.DISCARD_HAND:
                parts.append(f"(Cost: Discard {cost.value} from hand)")
            elif cost.type == AbilityCostType.SACRIFICE_SELF:
                parts.append("(Cost: Sacrifice Self)")
            else:
                parts.append(f"(Cost: {cost.type.name} {cost.value})")

    for cond in ability.conditions:
        neg = "NOT " if getattr(cond, "is_negated", False) and not is_jp else ""
        cond_desc = f"{neg}{cond.type.name}"
        if cond.params.get("group") is not None:
            cond_desc += f"({cond.params['group']})"
        if cond.params.get("unit") is not None:
            cond_desc += f" ({cond.params['unit']})"
        if cond.params.get("zone"):
            cond_desc += f" (in {cond.params['zone']})" if not is_jp else f" ({cond.params['zone']})"
        if cond.type == ConditionType.HAS_KEYWORD:
            cond_desc += f" ({cond.params.get('keyword', '?')})"
        parts.append(cond_desc)

    for eff in ability.effects:
        template = effect_descriptions.get(eff.effect_type, getattr(eff.effect_type, "name", str(eff.effect_type)))
        context = eff.params.copy()
        context["value"] = eff.value
        try:
            desc = template.format(**context)
        except KeyError:
            desc = template

        if eff.params.get("per_energy"):
            desc += " per Energy" if not is_jp else " / 繧ｨ繝阪Ν繧ｮ繝ｼ縺斐→"
        if eff.params.get("per_member"):
            desc += " per Member" if not is_jp else " / 繝｡繝ｳ繝舌・縺斐→"
        if eff.params.get("per_live"):
            desc += " per Live" if not is_jp else " / 繝ｩ繧､繝悶＃縺ｨ"
        if eff.target == TargetType.MEMBER_SELECT:
            desc += " (Choose member)" if not is_jp else " (蟇ｾ雎｡繧帝∈縺ｶ)"
        if eff.target in (TargetType.OPPONENT, getattr(TargetType, "OPPONENT_HAND", TargetType.OPPONENT)):
            if "opponent" not in desc.lower():
                desc += " (Opponent)" if not is_jp else " (相手)"
        parts.append(desc)

        if eff.modal_options:
            for index, option in enumerate(eff.modal_options, start=1):
                option_descs = []
                for sub_eff in option:
                    option_template = effect_descriptions.get(sub_eff.effect_type, sub_eff.effect_type.name)
                    option_context = sub_eff.params.copy()
                    option_context["value"] = sub_eff.value
                    try:
                        option_descs.append(option_template.format(**option_context))
                    except KeyError:
                        option_descs.append(option_template)
                label = f"Option {index}" if not is_jp else f"驕ｸ謚櫁い{index}"
                parts.append(f"[{label}: {' + '.join(option_descs)}]")

    return " ".join(parts)


__all__ = ["build_semantic_form", "reconstruct_text"]
