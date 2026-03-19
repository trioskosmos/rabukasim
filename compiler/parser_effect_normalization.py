from __future__ import annotations

from typing import Dict, Tuple

from engine.models.ability import TargetType


def normalize_select_hand_effect(name_up: str, params: Dict[str, object], target: TargetType) -> Tuple[str, TargetType]:
    params.setdefault("source", "HAND")
    dest_up = str(params.get("destination", "")).upper()

    if dest_up == "REVEAL":
        name_up = "REVEAL_CARDS"
        target = TargetType.CARD_HAND
        params["reveal_target"] = params.get("target", "OPPONENT_HIDDEN")
        params["target"] = "CARD_HAND"
        params.setdefault("selection_mode", "HIDDEN")
    elif dest_up in {"TARGET", "TARGET_VAL", "TARGETS"}:
        name_up = "SELECT_CARDS"
        target = TargetType.CARD_HAND
    elif dest_up in {"PLAY_STAGE_EMPTY", "STAGE_EMPTY"}:
        name_up = "PLAY_MEMBER_FROM_HAND"
        params["destination"] = "stage_empty"
        target = TargetType.PLAYER
    elif dest_up == "LIVE_PLAY":
        name_up = "PLAY_LIVE_FROM_DISCARD"
        params["destination"] = "live_play"
        target = TargetType.PLAYER

    return name_up, target