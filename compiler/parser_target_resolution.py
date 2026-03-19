from __future__ import annotations

from typing import Dict, Tuple

from engine.models.ability import EffectType, TargetType


def resolve_target_type(target_name: str, fallback_target: TargetType, params: Dict[str, object]) -> Tuple[TargetType, bool]:
    target = fallback_target
    is_chained = False

    if target_name:
        target_name = target_name.strip().upper()
        if hasattr(EffectType, target_name):
            is_chained = True
        elif target_name in {"SELF", "MEMBER_SELF"}:
            target = TargetType.MEMBER_SELF
        elif target_name == "PLAYER":
            target = TargetType.PLAYER
        elif target_name == "OPPONENT":
            target = TargetType.OPPONENT
        elif target_name in {"ALL_PLAYERS", "PLAYER_AND_OPPONENT"}:
            target = TargetType.ALL_PLAYERS
        elif target_name == "CARD_HAND":
            target = TargetType.CARD_HAND
        elif "MEMBER_" in target_name:
            target = TargetType.MEMBER_SELECT
        else:
            try:
                target = TargetType[target_name]
            except KeyError:
                params["destination"] = target_name.lower()
                target = fallback_target

    return target, is_chained