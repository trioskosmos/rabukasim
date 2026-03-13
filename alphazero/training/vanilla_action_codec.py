from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from alphazero.training.vanilla_observation import MAX_HAND_SLOTS, MAX_INITIAL_DECK, OBS_DIM

ACTION_BASE_PASS = 0
ACTION_BASE_MULLIGAN = 300
ACTION_BASE_LIVESET = 400
ACTION_BASE_TURN_ORDER = 5000
ACTION_BASE_LIVE_RESULT = 600
ACTION_BASE_HAND = 1000
ACTION_BASE_RPS_P1 = 20000
ACTION_BASE_RPS_P2 = 21000

ACTION_PASS_ID = 0
ACTION_RPS_OFFSET = 1
ACTION_TURN_CHOICE_OFFSET = 4
ACTION_MULLIGAN_OFFSET = 6
MAIN_PLAY_ACTIONS = MAX_HAND_SLOTS * 3
ACTION_LIVESET_OFFSET = ACTION_MULLIGAN_OFFSET + MAX_HAND_SLOTS
ACTION_MAIN_PLAY_OFFSET = ACTION_LIVESET_OFFSET + MAX_HAND_SLOTS
ACTION_LIVE_RESULT_OFFSET = ACTION_MAIN_PLAY_OFFSET + MAIN_PLAY_ACTIONS
ACTION_SPACE = ACTION_LIVE_RESULT_OFFSET + 3


@dataclass(frozen=True)
class VanillaActionSpaceSpec:
    num_actions: int = ACTION_SPACE
    rps_offset: int = ACTION_RPS_OFFSET
    turn_choice_offset: int = ACTION_TURN_CHOICE_OFFSET
    mulligan_offset: int = ACTION_MULLIGAN_OFFSET
    liveset_offset: int = ACTION_LIVESET_OFFSET
    main_play_offset: int = ACTION_MAIN_PLAY_OFFSET
    live_result_offset: int = ACTION_LIVE_RESULT_OFFSET


def _build_occurrence_positions(initial_deck: Sequence[int]) -> Dict[int, List[int]]:
    positions: Dict[int, List[int]] = {}
    for deck_idx, card_id in enumerate(initial_deck[:MAX_INITIAL_DECK]):
        positions.setdefault(card_id, []).append(deck_idx)
    return positions


def assign_hand_positions(hand: Sequence[int], initial_deck: Sequence[int]) -> List[Optional[int]]:
    positions_by_card = _build_occurrence_positions(initial_deck)
    used_counts: Dict[int, int] = {}
    assignments: List[Optional[int]] = []

    for card_id in hand:
        card_positions = positions_by_card.get(card_id, [])
        use_idx = used_counts.get(card_id, 0)
        if use_idx < len(card_positions):
            assignments.append(card_positions[use_idx])
            used_counts[card_id] = use_idx + 1
        else:
            assignments.append(None)

    return assignments


def engine_action_to_policy_id(
    _player_json: dict,
    engine_action: int,
    _initial_deck: Sequence[int],
    _phase: Optional[int] = None,
) -> int:
    if engine_action == ACTION_BASE_PASS:
        return ACTION_PASS_ID
    if ACTION_BASE_RPS_P1 <= engine_action <= ACTION_BASE_RPS_P1 + 2:
        return ACTION_RPS_OFFSET + (engine_action - ACTION_BASE_RPS_P1)
    if ACTION_BASE_RPS_P2 <= engine_action <= ACTION_BASE_RPS_P2 + 2:
        return ACTION_RPS_OFFSET + (engine_action - ACTION_BASE_RPS_P2)
    if ACTION_BASE_TURN_ORDER <= engine_action <= ACTION_BASE_TURN_ORDER + 1:
        return ACTION_TURN_CHOICE_OFFSET + (engine_action - ACTION_BASE_TURN_ORDER)
    if ACTION_BASE_MULLIGAN <= engine_action < ACTION_BASE_MULLIGAN + MAX_HAND_SLOTS:
        return ACTION_MULLIGAN_OFFSET + (engine_action - ACTION_BASE_MULLIGAN)
    if ACTION_BASE_LIVESET <= engine_action < ACTION_BASE_LIVESET + MAX_HAND_SLOTS:
        return ACTION_LIVESET_OFFSET + (engine_action - ACTION_BASE_LIVESET)
    if ACTION_BASE_HAND <= engine_action < ACTION_BASE_HAND + 100:
        hand_idx = (engine_action - ACTION_BASE_HAND) // 10
        slot_idx = (engine_action - ACTION_BASE_HAND) % 10
        if 0 <= hand_idx < MAX_HAND_SLOTS and 0 <= slot_idx < 3:
            return ACTION_MAIN_PLAY_OFFSET + hand_idx * 3 + slot_idx
        return -1
    if ACTION_BASE_LIVE_RESULT <= engine_action <= ACTION_BASE_LIVE_RESULT + 2:
        return ACTION_LIVE_RESULT_OFFSET + (engine_action - ACTION_BASE_LIVE_RESULT)
    return -1


def policy_id_to_engine_action(
    state,
    player_idx: int,
    policy_id: int,
    phase: int,
    _initial_deck: Sequence[int],
) -> Optional[int]:
    if policy_id == ACTION_PASS_ID:
        return ACTION_BASE_PASS
    if ACTION_RPS_OFFSET <= policy_id < ACTION_RPS_OFFSET + 3:
        base = ACTION_BASE_RPS_P1 if player_idx == 0 else ACTION_BASE_RPS_P2
        return base + (policy_id - ACTION_RPS_OFFSET)
    if ACTION_TURN_CHOICE_OFFSET <= policy_id < ACTION_TURN_CHOICE_OFFSET + 2:
        return ACTION_BASE_TURN_ORDER + (policy_id - ACTION_TURN_CHOICE_OFFSET)
    if ACTION_MULLIGAN_OFFSET <= policy_id < ACTION_MULLIGAN_OFFSET + MAX_HAND_SLOTS:
        return ACTION_BASE_MULLIGAN + (policy_id - ACTION_MULLIGAN_OFFSET)
    if ACTION_LIVESET_OFFSET <= policy_id < ACTION_LIVESET_OFFSET + MAX_HAND_SLOTS:
        return ACTION_BASE_LIVESET + (policy_id - ACTION_LIVESET_OFFSET)
    if ACTION_MAIN_PLAY_OFFSET <= policy_id < ACTION_MAIN_PLAY_OFFSET + MAIN_PLAY_ACTIONS:
        rel = policy_id - ACTION_MAIN_PLAY_OFFSET
        hand_idx = rel // 3
        slot_idx = rel % 3
        return ACTION_BASE_HAND + hand_idx * 10 + slot_idx
    if ACTION_LIVE_RESULT_OFFSET <= policy_id < ACTION_LIVE_RESULT_OFFSET + 3:
        return ACTION_BASE_LIVE_RESULT + (policy_id - ACTION_LIVE_RESULT_OFFSET)
    return None


def build_legal_policy_mask(
    state,
    player_idx: int,
    initial_deck: Sequence[int],
    phase: int,
    legal_engine_actions: Optional[Iterable[int]] = None,
) -> np.ndarray:
    player_json = json.loads(state.to_json())["players"][player_idx]
    if legal_engine_actions is None:
        legal_engine_actions = state.get_legal_action_ids()

    mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
    for engine_action in legal_engine_actions:
        policy_id = engine_action_to_policy_id(player_json, engine_action, initial_deck, phase)
        if 0 <= policy_id < ACTION_SPACE:
            mask[policy_id] = True
    return mask


def build_policy_engine_mapping(
    player_json: dict,
    legal_engine_actions: Iterable[int],
    initial_deck: Sequence[int],
    phase: int,
) -> Dict[int, int]:
    mapping: Dict[int, int] = {}
    for engine_action in legal_engine_actions:
        policy_id = engine_action_to_policy_id(player_json, engine_action, initial_deck, phase)
        if 0 <= policy_id < ACTION_SPACE and policy_id not in mapping:
            mapping[policy_id] = engine_action
    return mapping


def sparse_policy_from_engine_visits(
    player_json: dict,
    suggestions: Sequence[Tuple[int, float, int]],
    initial_deck: Sequence[int],
    phase: int,
) -> np.ndarray:
    dense = np.zeros(ACTION_SPACE, dtype=np.float32)
    total_visits = sum(visits for _, _, visits in suggestions)
    if total_visits <= 0:
        return dense

    for engine_action, _score, visits in suggestions:
        policy_id = engine_action_to_policy_id(player_json, engine_action, initial_deck, phase)
        if 0 <= policy_id < ACTION_SPACE:
            dense[policy_id] += visits / total_visits

    total_prob = dense.sum()
    if total_prob > 0:
        dense /= total_prob
    return dense


def dense_to_sparse(policy: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    indices = np.flatnonzero(policy > 0).astype(np.uint16)
    values = policy[indices].astype(np.float16)
    if len(indices) == 0:
        return np.array([0], dtype=np.uint16), np.array([0.0], dtype=np.float16)
    return indices, values


def legal_policy_ids(mask: np.ndarray) -> np.ndarray:
    return np.flatnonzero(mask)
