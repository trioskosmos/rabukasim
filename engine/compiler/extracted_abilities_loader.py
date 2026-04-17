"""Loader for auto-generated abilities_extracted_from_cards.json.

This module loads abilities from the new extracted format and converts them
to the Python Ability model without going through frame conversion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.ability import (
    Ability,
    AbilityCostType,
    Condition,
    ConditionType,
    Cost,
    Effect,
    EffectType,
    TargetType,
    TriggerType,
)


# Japanese trigger names to internal TriggerType enum mapping
JAPANESE_TRIGGER_MAP: Dict[str, TriggerType] = {
    "起動": TriggerType.ACTIVATED,
    "登場": TriggerType.ON_PLAY,
    "ライブ開始時": TriggerType.ON_LIVE_START,
    "ライブ成功時": TriggerType.ON_LIVE_SUCCESS,
    "常時": TriggerType.CONSTANT,
    "ターン開始時": TriggerType.TURN_START,
    "ターン終了時": TriggerType.TURN_END,
    "控え室に置かれた時": TriggerType.ON_MOVE_TO_DISCARD,
    "公開された時": TriggerType.ON_REVEAL,
    "メンバータップ時": TriggerType.ON_MEMBER_TAP,
    "能力解決時": TriggerType.ON_ABILITY_RESOLVE,
    "能力成功時": TriggerType.ON_ABILITY_SUCCESS,
    "ポジション変更時": TriggerType.ON_POSITION_CHANGE,
    "離脱時": TriggerType.ON_LEAVES,
}


# Semantic action names to EffectType enum mapping
SEMANTIC_ACTION_TO_EFFECT: Dict[str, EffectType] = {
    "draw_cards": EffectType.DRAW,
    "add_to_hand": EffectType.ADD_TO_HAND,
    "gain_resource": EffectType.ADD_BLADES,  # Default, will check resource type
    "look_at_cards": EffectType.LOOK_DECK,
    "discard_to_waitroom": EffectType.MOVE_TO_DISCARD,
    "member_to_wait": EffectType.MOVE_TO_DISCARD,
    "place_on_deck": EffectType.MOVE_TO_DECK,
    "select_from_looked_at_cards": EffectType.LOOK_AND_CHOOSE,
    "note": EffectType.FLAVOR_ACTION,
}


# Cost type mapping
COST_TYPE_TO_ABILITY_COST: Dict[str, AbilityCostType] = {
    "pay_energy": AbilityCostType.ENERGY,
    "move_cards": AbilityCostType.DISCARD_HAND,  # Default, will refine based on source/dest
}


def parse_card_reference(card_ref: str) -> Dict[str, Any]:
    """Parse card reference string like 'PL!-sd1-005-SD | 星空 凛 (ab#0)'.

    Returns:
        Dict with card_no, name, ability_index
    """
    try:
        # Format: "SET-sd1-005-Rarity | Name (ab#index)"
        parts = card_ref.split(" | ")
        if len(parts) != 2:
            return {"card_no": "", "name": "", "ability_index": 0}

        card_no = parts[0].strip()
        name_part = parts[1].strip()

        # Extract ability index from "(ab#0)"
        ability_index = 0
        if "(ab#" in name_part:
            idx_start = name_part.index("(ab#") + 4
            idx_end = name_part.index(")", idx_start)
            ability_index = int(name_part[idx_start:idx_end])
            name = name_part[:name_part.index("(ab#")].strip()
        else:
            name = name_part

        return {
            "card_no": card_no,
            "name": name,
            "ability_index": ability_index,
        }
    except Exception:
        return {"card_no": card_ref, "name": "", "ability_index": 0}


def map_trigger(japanese_trigger: str) -> TriggerType:
    """Map Japanese trigger string to TriggerType enum."""
    # Handle comma-separated multiple triggers
    if "," in japanese_trigger:
        # For multiple triggers, use the first one for now
        # This needs refinement for abilities with multiple triggers
        japanese_trigger = japanese_trigger.split(",")[0].strip()

    return JAPANESE_TRIGGER_MAP.get(japanese_trigger.strip(), TriggerType.NONE)


def map_cost_type(cost_data: Dict[str, Any]) -> Optional[Cost]:
    """Convert cost data from extracted format to Cost object."""
    if not cost_data:
        return None

    cost_type = cost_data.get("type", "")
    base_cost_type = COST_TYPE_TO_ABILITY_COST.get(cost_type, AbilityCostType.NONE)

    # Refine cost type based on source/destination
    source = cost_data.get("source", "")
    destination = cost_data.get("destination", "")

    if cost_type == "move_cards":
        if source == "stage" and destination == "waitroom":
            base_cost_type = AbilityCostType.SACRIFICE_SELF
        elif source == "hand" and destination == "waitroom":
            base_cost_type = AbilityCostType.DISCARD_HAND
        elif source == "hand" and destination == "deck":
            base_cost_type = AbilityCostType.RETURN_HAND

    value = cost_data.get("count", 0) or cost_data.get("energy", 0)
    is_optional = cost_data.get("optional", False)

    params = {
        "source": source,
        "destination": destination,
        "target": cost_data.get("target", ""),
        "card_type": cost_data.get("card_type", ""),
    }

    return Cost(
        type=base_cost_type,
        value=value,
        params=params,
        is_optional=is_optional,
    )


def map_semantic_action(action_data: Dict[str, Any]) -> Effect:
    """Convert semantic action data to Effect object."""
    # Handle case where action_data might be the action name directly
    if isinstance(action_data, str):
        action_name = action_data
    elif isinstance(action_data, dict):
        action_name = action_data.get("action", "")
        # If action field is still a dict, skip this action
        if isinstance(action_name, dict):
            return Effect(effect_type=EffectType.NONE, value=0)
    else:
        return Effect(effect_type=EffectType.NONE, value=0)

    base_effect_type = SEMANTIC_ACTION_TO_EFFECT.get(action_name, EffectType.NONE)

    # Special handling for gain_resource to distinguish blades/hearts
    if action_name == "gain_resource":
        resource = action_data.get("resource", "")
        if resource == "heart":
            base_effect_type = EffectType.ADD_HEARTS
        elif resource == "blade":
            base_effect_type = EffectType.ADD_BLADES

    value = action_data.get("count", 0) or action_data.get("blade_count", 0) or action_data.get("resource_count", 0)

    params = {
        "source": action_data.get("source", ""),
        "destination": action_data.get("destination", ""),
        "card_type": action_data.get("card_type", ""),
        "text": action_data.get("text", ""),
    }

    return Effect(
        effect_type=base_effect_type,
        value=value,
        params=params,
    )


def load_extracted_abilities(path: Path | str) -> Dict[str, Ability]:
    """Load abilities from abilities_extracted_from_cards.json.

    Returns:
        Dict mapping card reference strings to Ability objects
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    unique_abilities = data.get("unique_abilities", [])
    abilities_map: Dict[str, Ability] = {}

    for extracted_ability in unique_abilities:
        full_text = extracted_ability.get("full_text", "")
        triggerless_text = extracted_ability.get("triggerless_text", "")
        triggers = extracted_ability.get("triggers", "")
        cost_data = extracted_ability.get("cost")
        effect_data = extracted_ability.get("effect", {})
        use_limit = extracted_ability.get("use_limit")

        # Map trigger
        trigger = map_trigger(triggers)

        # Map cost
        costs = []
        if cost_data:
            cost_obj = map_cost_type(cost_data)
            if cost_obj:
                costs.append(cost_obj)

        # Map effect actions
        effects = []
        actions = effect_data.get("actions", [])
        for action in actions:
            if action.get("action") != "note":  # Skip flavor notes
                effect_obj = map_semantic_action(action)
                if effect_obj.effect_type != EffectType.NONE:
                    effects.append(effect_obj)

        # Handle use limit
        is_once_per_turn = use_limit == "turn1"

        # Create Ability object
        ability = Ability(
            raw_text=full_text,
            trigger=trigger,
            effects=effects,
            costs=costs,
            conditions=[],  # Conditions not yet extracted
            is_once_per_turn=is_once_per_turn,
        )

        # Map to all card references
        card_refs = extracted_ability.get("cards", [])
        for card_ref in card_refs:
            parsed = parse_card_reference(card_ref)
            key = f"{parsed['card_no']} (ab#{parsed['ability_index']})"
            abilities_map[key] = ability

    return abilities_map


def get_ability_for_card(card_no: str, ability_index: int, abilities_map: Dict[str, Ability]) -> Optional[Ability]:
    """Get ability for a specific card and ability index."""
    key = f"{card_no} (ab#{ability_index})"
    return abilities_map.get(key)
