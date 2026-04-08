from __future__ import annotations

import re
from typing import Any, Sequence

import numpy as np

from alphazero.training.vanilla_action_codec import ACTION_SPACE


ACTION_FAMILY_PASS = 0
ACTION_FAMILY_RPS = 1
ACTION_FAMILY_TURN_ORDER = 2
ACTION_FAMILY_MULLIGAN = 3
ACTION_FAMILY_LIVESET = 4
ACTION_FAMILY_PLAY_MEMBER = 5
ACTION_FAMILY_LIVE_RESULT = 6
ACTION_FAMILY_ABILITY = 7
ACTION_FAMILY_UNKNOWN = 8

ACTION_FAMILY_COUNT = 9
ACTION_FEATURE_DIM = 50

_LABEL_PATTERN = re.compile(r"^(?P<family>[A-Za-z0-9_]+)(?:\s*\{(?P<body>.*)\})?$")
_PAIR_PATTERN = re.compile(r"(?P<key>[A-Za-z0-9_]+):\s*(?P<value>[^,]+)")


def _norm(value: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    return float(np.clip(value / scale, -1.0, 1.0))


def _pos_norm(value: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    return float(np.clip(value / scale, 0.0, 1.0))


def _safe_int(value: Any, default: int = -1) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_verbose_action_label(label: str) -> tuple[str, dict[str, Any]]:
    match = _LABEL_PATTERN.match(label.strip())
    if not match:
        return "Unknown", {}

    family = str(match.group("family") or "Unknown")
    body = match.group("body") or ""
    params: dict[str, Any] = {}
    for pair in _PAIR_PATTERN.finditer(body):
        key = str(pair.group("key"))
        raw_value = str(pair.group("value")).strip()
        if raw_value in {"None", "null"}:
            params[key] = None
            continue
        if raw_value in {"true", "True"}:
            params[key] = True
            continue
        if raw_value in {"false", "False"}:
            params[key] = False
            continue
        if raw_value.startswith("Some(") and raw_value.endswith(")"):
            inner_value = raw_value[5:-1].strip()
            if inner_value in {"None", "null", ""}:
                params[key] = None
                continue
            try:
                params[key] = int(inner_value)
                continue
            except ValueError:
                params[key] = inner_value.strip("\"'")
                continue
        try:
            params[key] = int(raw_value)
            continue
        except ValueError:
            pass
        params[key] = raw_value.strip("\"'")
    return family, params


def _family_bucket(family: str) -> int:
    family_lower = family.lower()
    if family_lower == "pass":
        return ACTION_FAMILY_PASS
    if family_lower == "rps":
        return ACTION_FAMILY_RPS
    if "turn" in family_lower and "order" in family_lower:
        return ACTION_FAMILY_TURN_ORDER
    if "mulligan" in family_lower:
        return ACTION_FAMILY_MULLIGAN
    if "live" in family_lower and "set" in family_lower:
        return ACTION_FAMILY_LIVESET
    if "playmember" in family_lower or "play_member" in family_lower:
        return ACTION_FAMILY_PLAY_MEMBER
    if "result" in family_lower and "live" in family_lower:
        return ACTION_FAMILY_LIVE_RESULT
    if "ability" in family_lower or "trigger" in family_lower or "target" in family_lower:
        return ACTION_FAMILY_ABILITY
    return ACTION_FAMILY_UNKNOWN


def _static_card_features(card_id: int, card_lookup: dict[int, dict[str, Any]]) -> tuple[np.ndarray, int, int]:
    static = card_lookup.get(int(card_id), {}) if card_id >= 0 else {}
    features = np.zeros(14, dtype=np.float32)
    if not static:
        return features, 0, 0

    kind = str(static.get("type", ""))
    is_member = 1 if kind == "member" else 0
    is_live = 1 if kind == "live" else 0
    features[0] = float(is_member)
    features[1] = float(is_live)
    features[2] = _pos_norm(float(static.get("primary_value", 0.0)), 20.0)
    features[3] = _pos_norm(float(static.get("hearts_total", 0.0)), 20.0)
    features[4] = _pos_norm(float(static.get("aux_icons", 0.0)), 20.0)
    features[5] = _pos_norm(float(static.get("group_count", 0.0)), 12.0)

    hearts = [float(x) for x in static.get("hearts", [])[:7]]
    hearts += [0.0] * (7 - len(hearts))
    features[6:13] = np.asarray([_pos_norm(value, 12.0) for value in hearts], dtype=np.float32)
    features[13] = _pos_norm(float(card_id), 20000.0)
    return features, is_member, is_live


def candidate_action_feature_vector(
    record: dict[str, Any],
    card_lookup: dict[int, dict[str, Any]],
) -> np.ndarray:
    features = np.zeros(ACTION_FEATURE_DIM, dtype=np.float32)

    family_bucket = _family_bucket(str(record.get("family", "Unknown")))
    features[family_bucket] = 1.0
    features[9] = 1.0 if bool(record.get("policy_visible", False)) else 0.0
    features[10] = _norm(float(record.get("engine_action", -1)), 30000.0)
    features[11] = _norm(float(record.get("mapped_policy_id", -1)), float(ACTION_SPACE))
    features[12] = _pos_norm(float(record.get("turn", 0)), 20.0)
    features[13] = _pos_norm(float(record.get("phase", 0)) + 10.0, 20.0)
    features[14] = float(int(record.get("current_player", 0)))

    params = dict(record.get("params", {}) or {})
    features[15] = _pos_norm(float(_safe_int(params.get("hand_idx"), -1)), 20.0)
    features[16] = _pos_norm(float(_safe_int(params.get("slot_idx"), -1)), 3.0)
    features[17] = _pos_norm(float(_safe_int(params.get("other_slot"), -1)), 3.0)
    features[18] = _pos_norm(float(_safe_int(params.get("choice_idx"), -1)), 8.0)
    features[19] = _pos_norm(float(_safe_int(params.get("card_idx"), -1)), 20.0)
    features[20] = _pos_norm(float(_safe_int(params.get("target_idx"), -1)), 20.0)

    features[21] = _pos_norm(float(record.get("source_hand_card_id", -1)), 20000.0)
    features[22] = _pos_norm(float(record.get("source_stage_card_id", -1)), 20000.0)

    source_static, source_is_member, source_is_live = _static_card_features(
        _safe_int(record.get("source_hand_card_id", -1)),
        card_lookup,
    )
    target_static, target_is_member, target_is_live = _static_card_features(
        _safe_int(record.get("target_stage_card_id", -1)),
        card_lookup,
    )

    features[23] = float(source_is_member)
    features[24] = float(source_is_live)
    features[25:39] = source_static

    features[39] = _pos_norm(float(record.get("target_stage_card_id", -1)), 20000.0)
    features[40] = float(target_is_member)
    features[41] = float(target_is_live)
    features[42:50] = target_static[:8]
    return features


def build_candidate_action_features(
    records: Sequence[dict[str, Any]],
    card_lookup: dict[int, dict[str, Any]],
) -> np.ndarray:
    if not records:
        return np.zeros((0, ACTION_FEATURE_DIM), dtype=np.float32)
    return np.asarray([candidate_action_feature_vector(record, card_lookup) for record in records], dtype=np.float32)


def resolve_card_context_for_action(
    state_json: dict[str, Any],
    current_player: int,
    label: str,
    engine_action: int,
    mapped_policy_id: int,
    policy_visible: bool,
    turn: int,
    phase: int,
) -> dict[str, Any]:
    family, params = parse_verbose_action_label(label)
    player_json = state_json["players"][int(current_player)]
    hand = list(player_json.get("hand", []))
    stage = list(player_json.get("stage", []))
    live_zone = list(player_json.get("live_zone", []))
    source_hand_idx = _safe_int(
        params.get("hand_idx"),
        _safe_int(params.get("selected_hand_idx"), _safe_int(params.get("card_idx"), -1)),
    )
    source_stage_idx = _safe_int(params.get("stage_idx"), -1)
    source_live_idx = _safe_int(params.get("live_idx"), -1)
    target_stage_idx = _safe_int(
        params.get("slot_idx"),
        _safe_int(params.get("selected_target_idx"), _safe_int(params.get("target_idx"), -1)),
    )

    source_hand_card_id = hand[source_hand_idx] if 0 <= source_hand_idx < len(hand) else -1
    source_stage_card_id = stage[source_stage_idx] if 0 <= source_stage_idx < len(stage) else -1
    source_live_card_id = live_zone[source_live_idx] if 0 <= source_live_idx < len(live_zone) else -1

    if source_hand_card_id < 0 and _safe_int(params.get("ability_card_id"), -1) >= 0:
        source_hand_card_id = _safe_int(params.get("ability_card_id"), -1)

    source_card_id = source_hand_card_id
    if source_card_id < 0:
        source_card_id = source_stage_card_id if source_stage_card_id >= 0 else source_live_card_id

    target_stage_card_id = stage[target_stage_idx] if 0 <= target_stage_idx < len(stage) else -1

    return {
        "engine_action": int(engine_action),
        "label": str(label),
        "family": family,
        "params": params,
        "mapped_policy_id": int(mapped_policy_id),
        "policy_visible": bool(policy_visible),
        "turn": int(turn),
        "phase": int(phase),
        "current_player": int(current_player),
        "source_hand_idx": source_hand_idx,
        "source_stage_idx": source_stage_idx,
        "source_live_idx": source_live_idx,
        "target_stage_idx": target_stage_idx,
        "source_hand_card_id": int(source_card_id),
        "source_stage_card_id": int(source_stage_card_id),
        "source_live_card_id": int(source_live_card_id),
        "target_stage_card_id": int(target_stage_card_id),
    }
