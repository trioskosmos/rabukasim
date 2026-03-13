from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

MAX_INITIAL_DECK = 60
MAX_HAND_SLOTS = 20
MAX_STAGE_SLOTS = 3
MAX_LIVE_SLOTS = 3

PHASE_FEATURE_ORDER = (-3, -2, -1, 0, 4, 5, 8, 10)

GLOBAL_FEATURES = 40
CARD_FEATURES = 20
OBS_DIM = GLOBAL_FEATURES + MAX_INITIAL_DECK * CARD_FEATURES

ZONE_DECK = 0
ZONE_HAND = 1
ZONE_STAGE = 2
ZONE_ENERGY = 3
ZONE_DISCARD = 4
ZONE_SUCCESS = 5
ZONE_YELL = 6
ZONE_LIVE = 7


@dataclass(frozen=True)
class VanillaObservationSpec:
    global_features: int = GLOBAL_FEATURES
    card_features: int = CARD_FEATURES
    total_cards: int = MAX_INITIAL_DECK
    obs_dim: int = OBS_DIM
    max_hand_slots: int = MAX_HAND_SLOTS
    max_stage_slots: int = MAX_STAGE_SLOTS
    max_live_slots: int = MAX_LIVE_SLOTS


OBSERVATION_SPEC = VanillaObservationSpec()


def _norm(value: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    return float(np.clip(value / scale, 0.0, 1.0))


def _build_occurrence_positions(initial_deck: Sequence[int]) -> dict[int, list[int]]:
    positions: dict[int, list[int]] = {}
    for deck_idx, card_id in enumerate(initial_deck[:MAX_INITIAL_DECK]):
        positions.setdefault(int(card_id), []).append(deck_idx)
    return positions


def _claim_card_occurrence(
    card_id: int,
    positions_by_card: dict[int, list[int]],
    next_occurrence: dict[int, int],
) -> int | None:
    positions = positions_by_card.get(int(card_id), [])
    use_idx = next_occurrence.get(int(card_id), 0)
    if use_idx >= len(positions):
        return None
    next_occurrence[int(card_id)] = use_idx + 1
    return positions[use_idx]


def build_card_feature_lookup(full_db: dict[str, Any]) -> dict[int, dict[str, Any]]:
    lookup: dict[int, dict[str, Any]] = {}

    for raw in full_db.get("member_db", {}).values():
        card_id = int(raw.get("card_id", -1))
        if card_id < 0:
            continue
        hearts = [float(value) for value in raw.get("hearts", [0] * 7)[:7]]
        hearts += [0.0] * (7 - len(hearts))
        lookup[card_id] = {
            "type": "member",
            "primary_value": float(raw.get("cost", 0)),
            "hearts": hearts,
            "aux_icons": float(raw.get("blades", 0)) + float(raw.get("volume_icons", 0)),
            "group_count": float(len(raw.get("groups", []) or [])),
        }

    for raw in full_db.get("live_db", {}).values():
        card_id = int(raw.get("card_id", -1))
        if card_id < 0:
            continue
        hearts = [float(value) for value in raw.get("required_hearts", [0] * 7)[:7]]
        hearts += [0.0] * (7 - len(hearts))
        lookup[card_id] = {
            "type": "live",
            "primary_value": float(raw.get("score", 0)),
            "hearts": hearts,
            "aux_icons": float(raw.get("draw_icons", 0)) + float(raw.get("volume_icons", 0)),
            "group_count": float(len(raw.get("groups", []) or [])),
        }

    return lookup


def _sum_stage_hearts(player_json: dict[str, Any], card_lookup: dict[int, dict[str, Any]]) -> list[float]:
    totals = [0.0] * 7
    for card_id in player_json.get("stage", []):
        if int(card_id) < 0:
            continue
        static = card_lookup.get(int(card_id))
        if not static or static["type"] != "member":
            continue
        for color_idx, value in enumerate(static["hearts"]):
            totals[color_idx] += float(value)
    return totals


def _sum_live_requirements(player_json: dict[str, Any], card_lookup: dict[int, dict[str, Any]]) -> list[float]:
    totals = [0.0] * 7
    for card_id in player_json.get("live_zone", []):
        if int(card_id) < 0:
            continue
        static = card_lookup.get(int(card_id))
        if not static or static["type"] != "live":
            continue
        for color_idx, value in enumerate(static["hearts"]):
            totals[color_idx] += float(value)
    return totals


def build_vanilla_observation(
    state_json: dict[str, Any],
    current_player: int,
    initial_deck: Sequence[int],
    card_lookup: dict[int, dict[str, Any]],
) -> np.ndarray:
    player_json = state_json["players"][current_player]
    opp_json = state_json["players"][1 - current_player]

    phase = int(state_json.get("phase", -4))
    stage_hearts = _sum_stage_hearts(player_json, card_lookup)
    live_requirements = _sum_live_requirements(player_json, card_lookup)
    live_deficits = [max(required - available, 0.0) for required, available in zip(live_requirements, stage_hearts)]

    tapped_energy_mask = int(player_json.get("tapped_energy_mask", 0))
    energy_total = len(player_json.get("energy_zone", []))
    energy_untapped = max(0, energy_total - tapped_energy_mask.bit_count())
    stage_count = sum(1 for card_id in player_json.get("stage", []) if int(card_id) >= 0)

    global_features = [0.0] * GLOBAL_FEATURES
    phase_offset = 0
    for idx, phase_id in enumerate(PHASE_FEATURE_ORDER):
        global_features[phase_offset + idx] = 1.0 if phase == phase_id else 0.0

    scalar_offset = len(PHASE_FEATURE_ORDER)
    scalar_values = [
        _norm(float(state_json.get("turn", 0)), 20.0),
        1.0 if int(state_json.get("first_player", 0)) == current_player else 0.0,
        _norm(float(player_json.get("score", 0)), 20.0),
        _norm(float(opp_json.get("score", 0)), 20.0),
        _norm(float(len(player_json.get("hand", []))), float(MAX_HAND_SLOTS)),
        _norm(float(len(player_json.get("deck", []))), 60.0),
        _norm(float(len(player_json.get("discard", []))), 20.0),
        _norm(float(len(player_json.get("success_lives", []))), 3.0),
        _norm(float(sum(1 for card_id in player_json.get("live_zone", []) if int(card_id) >= 0)), 3.0),
        _norm(float(stage_count), 3.0),
        _norm(float(len(player_json.get("yell_cards", []))), 12.0),
        _norm(float(energy_total), 12.0),
        _norm(float(energy_untapped), 12.0),
        _norm(float(len(opp_json.get("success_lives", []))), 3.0),
        _norm(float(sum(1 for card_id in opp_json.get("stage", []) if int(card_id) >= 0)), 3.0),
        _norm(float(player_json.get("play_count_this_turn", 0)), 6.0),
        _norm(float(player_json.get("cost_reduction", 0)), 6.0),
        _norm(float(player_json.get("baton_touch_count", 0)), 3.0),
    ]
    for idx, value in enumerate(scalar_values):
        global_features[scalar_offset + idx] = value

    stage_heart_offset = scalar_offset + len(scalar_values)
    for idx, value in enumerate(stage_hearts):
        global_features[stage_heart_offset + idx] = _norm(value, 10.0)

    deficit_offset = stage_heart_offset + 7
    for idx, value in enumerate(live_deficits):
        global_features[deficit_offset + idx] = _norm(value, 10.0)

    positions_by_card = _build_occurrence_positions(initial_deck)
    next_occurrence: dict[int, int] = {}
    zone_by_pos = [ZONE_DECK] * MAX_INITIAL_DECK
    hand_pos_by_pos = [-1] * MAX_INITIAL_DECK
    stage_slot_by_pos = [-1] * MAX_INITIAL_DECK
    live_slot_by_pos = [-1] * MAX_INITIAL_DECK

    for hand_idx, card_id in enumerate(player_json.get("hand", [])[:MAX_HAND_SLOTS]):
        deck_pos = _claim_card_occurrence(int(card_id), positions_by_card, next_occurrence)
        if deck_pos is None:
            continue
        zone_by_pos[deck_pos] = ZONE_HAND
        hand_pos_by_pos[deck_pos] = hand_idx

    for slot_idx, card_id in enumerate(player_json.get("stage", [])[:MAX_STAGE_SLOTS]):
        if int(card_id) < 0:
            continue
        deck_pos = _claim_card_occurrence(int(card_id), positions_by_card, next_occurrence)
        if deck_pos is None:
            continue
        zone_by_pos[deck_pos] = ZONE_STAGE
        stage_slot_by_pos[deck_pos] = slot_idx

    for slot_idx, card_id in enumerate(player_json.get("live_zone", [])[:MAX_LIVE_SLOTS]):
        if int(card_id) < 0:
            continue
        deck_pos = _claim_card_occurrence(int(card_id), positions_by_card, next_occurrence)
        if deck_pos is None:
            continue
        zone_by_pos[deck_pos] = ZONE_LIVE
        live_slot_by_pos[deck_pos] = slot_idx

    for zone_name, zone_id in (("success_lives", ZONE_SUCCESS), ("yell_cards", ZONE_YELL), ("discard", ZONE_DISCARD)):
        for card_id in player_json.get(zone_name, []):
            deck_pos = _claim_card_occurrence(int(card_id), positions_by_card, next_occurrence)
            if deck_pos is None:
                continue
            zone_by_pos[deck_pos] = zone_id

    revealed_cards = {int(card_id) for card_id in player_json.get("revealed_cards", [])}
    stage_energy_count = [int(value) for value in player_json.get("stage_energy_count", [0] * MAX_STAGE_SLOTS)]

    card_features: list[float] = []
    for deck_pos in range(MAX_INITIAL_DECK):
        card_id = int(initial_deck[deck_pos]) if deck_pos < len(initial_deck) else -1
        if card_id < 0:
            card_features.extend([0.0] * CARD_FEATURES)
            continue

        static = card_lookup.get(card_id, None)
        zone_id = zone_by_pos[deck_pos]
        hand_idx = hand_pos_by_pos[deck_pos]
        stage_slot = stage_slot_by_pos[deck_pos]
        live_slot = live_slot_by_pos[deck_pos]
        stage_energy = stage_energy_count[stage_slot] if 0 <= stage_slot < len(stage_energy_count) else 0

        is_member = 1.0 if static and static.get("type") == "member" else 0.0
        is_live = 1.0 if static and static.get("type") == "live" else 0.0
        primary_value = float(static.get("primary_value", 0.0)) if static else 0.0
        hearts = [float(value) for value in static.get("hearts", [0.0] * 7)] if static else [0.0] * 7
        aux_icons = float(static.get("aux_icons", 0.0)) if static else 0.0
        group_count = float(static.get("group_count", 0.0)) if static else 0.0

        playable_now = 1.0 if zone_id == ZONE_HAND and is_member and phase == 4 and stage_count < MAX_STAGE_SLOTS and primary_value <= energy_untapped else 0.0
        settable_now = 1.0 if zone_id == ZONE_HAND and is_live and phase == 5 else 0.0
        revealed_now = 1.0 if zone_id == ZONE_LIVE and card_id in revealed_cards else 0.0

        token = [
            _norm(float(zone_id), 7.0),
            _norm(float(hand_idx + 1), float(MAX_HAND_SLOTS)) if hand_idx >= 0 else 0.0,
            _norm(float(stage_slot + 1), float(MAX_STAGE_SLOTS)) if stage_slot >= 0 else 0.0,
            _norm(float(live_slot + 1), float(MAX_LIVE_SLOTS)) if live_slot >= 0 else 0.0,
            _norm(float(stage_energy), 6.0),
            playable_now,
            settable_now,
            revealed_now,
            is_member,
            is_live,
            _norm(primary_value, 10.0),
            _norm(hearts[0], 5.0),
            _norm(hearts[1], 5.0),
            _norm(hearts[2], 5.0),
            _norm(hearts[3], 5.0),
            _norm(hearts[4], 5.0),
            _norm(hearts[5], 5.0),
            _norm(hearts[6], 5.0),
            _norm(aux_icons, 10.0),
            _norm(group_count, 4.0),
        ]
        card_features.extend(token)

    obs = np.asarray(global_features + card_features, dtype=np.float32)
    if obs.shape[0] != OBS_DIM:
        raise RuntimeError(f"Vanilla observation size mismatch: expected {OBS_DIM}, got {obs.shape[0]}")
    return obs