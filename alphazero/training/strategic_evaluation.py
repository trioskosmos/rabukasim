from __future__ import annotations

from dataclasses import dataclass
from math import ceil, exp, lgamma, tanh
from typing import Any, Sequence


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_len(value: Any) -> int:
    try:
        return len(value)
    except TypeError:
        return 0


def _clip01(value: float) -> float:
    return float(max(0.0, min(1.0, value)))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = exp(-value)
        return float(1.0 / (1.0 + z))
    z = exp(value)
    return float(z / (1.0 + z))


def _log_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return float(lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1))


def _hypergeom_tail(population: int, success_states: int, draws: int, minimum_success: int) -> float:
    population = max(0, int(population))
    success_states = max(0, min(int(success_states), population))
    draws = max(0, min(int(draws), population))
    minimum_success = max(0, int(minimum_success))

    if minimum_success <= 0:
        return 1.0
    if population <= 0 or draws <= 0 or success_states <= 0:
        return 0.0
    if minimum_success > draws or minimum_success > success_states:
        return 0.0

    log_denom = _log_comb(population, draws)
    total = 0.0
    max_success = min(success_states, draws)
    for successes in range(minimum_success, max_success + 1):
        log_prob = (
            _log_comb(success_states, successes)
            + _log_comb(population - success_states, draws - successes)
            - log_denom
        )
        if log_prob > -745.0:
            total += exp(log_prob)
    return _clip01(total)


def _card_strength(card_id: int, card_lookup: dict[int, dict[str, Any]]) -> float:
    static = card_lookup.get(int(card_id), {}) if int(card_id) >= 0 else {}
    if not static:
        return 0.0
    primary = float(static.get("primary_value", 0.0))
    hearts = float(static.get("hearts_total", 0.0))
    aux = float(static.get("aux_icons", 0.0))
    groups = float(static.get("group_count", 0.0))
    return 0.35 * (primary / 20.0) + 0.45 * (hearts / 20.0) + 0.15 * (aux / 20.0) + 0.05 * (groups / 12.0)


COLOR_NAMES = ("Pink", "Red", "Yellow", "Green", "Blue", "Purple", "Any")


def _sum_hearts(card_ids: Sequence[int], card_lookup: dict[int, dict[str, Any]]) -> list[float]:
    totals = [0.0] * 7
    for raw_card_id in card_ids:
        card_id = _safe_int(raw_card_id, -1)
        if card_id < 0:
            continue
        static = card_lookup.get(card_id)
        if not static or static.get("type") != "member":
            continue
        hearts = [float(value) for value in static.get("hearts", [])[:7]]
        hearts += [0.0] * (7 - len(hearts))
        for idx, value in enumerate(hearts[:7]):
            totals[idx] += float(value)
    return totals


def _sum_live_requirements(card_ids: Sequence[int], card_lookup: dict[int, dict[str, Any]]) -> list[float]:
    totals = [0.0] * 7
    for raw_card_id in card_ids:
        card_id = _safe_int(raw_card_id, -1)
        if card_id < 0:
            continue
        static = card_lookup.get(card_id)
        if not static or static.get("type") != "live":
            continue
        hearts = [float(value) for value in static.get("hearts", [])[:7]]
        hearts += [0.0] * (7 - len(hearts))
        for idx, value in enumerate(hearts[:7]):
            totals[idx] += float(value)
    return totals


def _card_hearts_by_color(card_id: int, card_lookup: dict[int, dict[str, Any]]) -> list[float]:
    static = card_lookup.get(_safe_int(card_id, -1), {})
    if not static:
        return [0.0] * 7
    hearts = [float(value) for value in static.get("hearts", [])[:7]]
    hearts += [0.0] * (7 - len(hearts))
    return hearts[:7]


def _deck_card_counts(card_ids: Sequence[int]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for raw_card_id in card_ids:
        card_id = _safe_int(raw_card_id, -1)
        if card_id < 0:
            continue
        counts[card_id] = counts.get(card_id, 0) + 1
    return counts


def _useful_card_value(card_id: int, deficits: Sequence[float], card_lookup: dict[int, dict[str, Any]]) -> float:
    static = card_lookup.get(int(card_id), {})
    if not static:
        return 0.0
    hearts = [float(value) for value in static.get("hearts", [])[:7]]
    hearts += [0.0] * (7 - len(hearts))
    useful_hearts = 0.0
    for deficit, value in zip(deficits, hearts, strict=False):
        useful_hearts += min(max(float(deficit), 0.0), max(float(value), 0.0))
    aux = float(static.get("aux_icons", 0.0))
    primary = float(static.get("primary_value", 0.0))
    group_count = float(static.get("group_count", 0.0))
    return useful_hearts + 0.15 * aux + 0.07 * primary + 0.04 * group_count


def _useful_count_from_multiset(
    counts: dict[int, int],
    deficits: Sequence[float],
    card_lookup: dict[int, dict[str, Any]],
) -> tuple[int, float]:
    useful_count = 0
    weighted_sum = 0.0
    for card_id, count in counts.items():
        value = _useful_card_value(card_id, deficits, card_lookup)
        if value <= 0.15:
            continue
        useful_count += int(count)
        weighted_sum += float(value) * float(count)
    avg_value = weighted_sum / float(useful_count) if useful_count > 0 else 0.0
    return useful_count, avg_value


def _live_card_ids_from_hand(player_json: dict[str, Any], card_lookup: dict[int, dict[str, Any]]) -> list[int]:
    live_card_ids: list[int] = []
    for raw_card_id in player_json.get("hand", []):
        card_id = _safe_int(raw_card_id, -1)
        if card_id < 0:
            continue
        static = card_lookup.get(card_id, {})
        if static.get("type") == "live":
            live_card_ids.append(card_id)
    return live_card_ids


def _candidate_live_card_ids(player_json: dict[str, Any], card_lookup: dict[int, dict[str, Any]]) -> tuple[list[int], str]:
    active_live_ids = [
        _safe_int(card_id, -1)
        for card_id in player_json.get("live_zone", [])
        if _safe_int(card_id, -1) >= 0
    ]
    if active_live_ids:
        return active_live_ids, "live_zone"
    hand_live_ids = _live_card_ids_from_hand(player_json, card_lookup)
    if hand_live_ids:
        return hand_live_ids, "hand"
    return [], ""


def _card_name(card_id: int, card_lookup: dict[int, dict[str, Any]]) -> str:
    static = card_lookup.get(int(card_id), {})
    return str(static.get("name", static.get("display_name", f"card_{int(card_id)}")))


def live_card_fit_score(
    card_id: int,
    deficits_by_color: Sequence[float],
    card_lookup: dict[int, dict[str, Any]],
) -> float:
    static = card_lookup.get(_safe_int(card_id, -1), {})
    if not static or static.get("type") != "member":
        return 0.0

    hearts = _card_hearts_by_color(card_id, card_lookup)
    deficits = [max(float(value), 0.0) for value in deficits_by_color[:7]]
    deficit_total = float(sum(deficits))
    if deficit_total <= 0.0:
        return _clip01(float(static.get("hearts_total", 0.0)) / 10.0)

    captured = 0.0
    covered_colors = 0.0
    for deficit, heart_value in zip(deficits, hearts, strict=False):
        if deficit <= 0.0 or heart_value <= 0.0:
            continue
        captured += min(deficit, heart_value)
        covered_colors += 1.0

    total_hearts = float(sum(max(0.0, value) for value in hearts))
    aux = float(static.get("aux_icons", 0.0))
    primary = float(static.get("primary_value", 0.0))
    group_count = float(static.get("group_count", 0.0))
    coverage = captured / deficit_total
    color_diversity = covered_colors / float(max(1, sum(1 for deficit in deficits if deficit > 0.0)))
    breadth = _clip01(total_hearts / 12.0)
    support = _clip01((0.15 * aux + 0.10 * primary + 0.05 * group_count) / 6.0)
    return _clip01(0.58 * coverage + 0.18 * color_diversity + 0.16 * breadth + 0.08 * support)


@dataclass(frozen=True, slots=True)
class LiveCardClearabilityEstimate:
    card_id: int
    card_name: str
    source: str
    required_hearts: float
    stage_hearts: float
    heart_gap: float
    required_hearts_by_color: tuple[float, ...]
    stage_hearts_by_color: tuple[float, ...]
    deficit_by_color: tuple[float, ...]
    color_coverage: float
    useful_cards_remaining: int
    useful_card_density: float
    avg_useful_value: float
    draw_horizon: int
    clearability: float


def _live_card_clearability_estimate(
    card_id: int,
    *,
    stage_hearts: Sequence[float],
    remaining_counts: dict[int, int],
    hand_size: int,
    energy_size: int,
    yell_size: int,
    turn: int,
    max_turns: int,
    card_lookup: dict[int, dict[str, Any]],
    source: str,
) -> LiveCardClearabilityEstimate:
    required_hearts = _sum_live_requirements([card_id], card_lookup)
    live_required_total = float(sum(required_hearts))
    total_stage = float(sum(stage_hearts))
    heart_gap = max(live_required_total - total_stage, 0.0)
    deficits = [max(required - available, 0.0) for required, available in zip(required_hearts, stage_hearts, strict=False)]
    required_vector = tuple(float(value) for value in required_hearts[:7])
    stage_vector = tuple(float(value) for value in stage_hearts[:7])
    deficit_vector = tuple(float(value) for value in deficits[:7])
    weighted_required = float(sum(required_vector))
    weighted_coverage = 1.0
    if weighted_required > 0.0:
        color_coverages = []
        for required, available in zip(required_vector, stage_vector, strict=False):
            if required <= 0.0:
                continue
            color_coverages.append(_clip01(available / max(required, 1e-6)))
        weighted_coverage = float(sum(color_coverages) / len(color_coverages)) if color_coverages else 1.0
    useful_card_count, avg_useful_value = _useful_count_from_multiset(remaining_counts, deficits, card_lookup)
    useful_card_density = float(useful_card_count) / float(max(1, sum(remaining_counts.values())))
    draw_horizon = max(
        1,
        min(
            max(1, sum(remaining_counts.values())),
            max(1, int(max_turns) - int(turn) + 1 + int(hand_size) // 2 + int(energy_size) // 2 + int(yell_size) // 3),
        ),
    )

    if live_required_total <= 0.0:
        clearability = _clip01(
            0.25 * _clip01(total_stage / 12.0)
            + 0.25 * weighted_coverage
            + 0.45 * useful_card_density
            + 0.20 * (1.0 - _clip01(float(turn) / float(max(1, int(max_turns)))))
        )
    else:
        coverage = _clip01(total_stage / max(live_required_total, 1e-6))
        if heart_gap <= 0.0:
            future_prob = 1.0
        else:
            needed_cards = max(1, int(ceil(heart_gap / max(avg_useful_value, 0.5))))
            future_prob = _hypergeom_tail(sum(remaining_counts.values()), useful_card_count, draw_horizon, needed_cards)
        future_expectation = total_stage + draw_horizon * avg_useful_value + 0.25 * float(hand_size) + 0.15 * float(energy_size)
        future_margin = _sigmoid((future_expectation - live_required_total) / max(2.0, live_required_total * 0.15 + 1.0))
        clearability = _clip01(0.30 * coverage + 0.25 * weighted_coverage + 0.30 * future_prob + 0.15 * future_margin)

    return LiveCardClearabilityEstimate(
        card_id=int(card_id),
        card_name=_card_name(card_id, card_lookup),
        source=str(source),
        required_hearts=float(live_required_total),
        stage_hearts=float(total_stage),
        heart_gap=float(heart_gap),
        required_hearts_by_color=required_vector,
        stage_hearts_by_color=stage_vector,
        deficit_by_color=deficit_vector,
        color_coverage=float(weighted_coverage),
        useful_cards_remaining=int(useful_card_count),
        useful_card_density=float(useful_card_density),
        avg_useful_value=float(avg_useful_value),
        draw_horizon=int(draw_horizon),
        clearability=float(clearability),
    )


def evaluate_live_card_clearability_breakdown(
    state_json: dict[str, Any],
    current_player: int,
    card_lookup: dict[int, dict[str, Any]],
    *,
    max_turns: int,
) -> list[LiveCardClearabilityEstimate]:
    players = list(state_json.get("players", []))
    player_json = players[_safe_int(current_player, 0)] if _safe_int(current_player, 0) < len(players) else {}
    stage_hearts = _sum_hearts(player_json.get("stage", []), card_lookup)
    hand = _safe_len(player_json.get("hand", []))
    energy = _safe_len(player_json.get("energy_zone", []))
    yell = _safe_len(player_json.get("yell_cards", []))
    turn = _safe_int(state_json.get("turn", 0), 0)
    candidate_live_ids, source = _candidate_live_card_ids(player_json, card_lookup)
    remaining_counts = _deck_card_counts(player_json.get("deck", []))

    return [
        _live_card_clearability_estimate(
            card_id,
            stage_hearts=stage_hearts,
            remaining_counts=remaining_counts,
            hand_size=hand,
            energy_size=energy,
            yell_size=yell,
            turn=turn,
            max_turns=max_turns,
            card_lookup=card_lookup,
            source=source,
        )
        for card_id in candidate_live_ids
    ]


def _phase_role(state_json: dict[str, Any], current_player: int) -> str:
    phase = _safe_int(state_json.get("phase", 0), 0)
    pending_choice_type = str(state_json.get("pending_choice_type", "") or "").upper()
    interaction_stack = list(state_json.get("interaction_stack", []))
    if not pending_choice_type and interaction_stack:
        top = interaction_stack[-1]
        if isinstance(top, dict):
            pending_choice_type = str(top.get("choice_type", "") or top.get("choice", "") or "").upper()

    if "RPS" in pending_choice_type or "TURN_ORDER" in pending_choice_type:
        return "setup"
    if "MULLIGAN" in pending_choice_type:
        return "mulligan"
    if "SETLIVE" in pending_choice_type or "LIVESET" in pending_choice_type:
        return "liveset"
    if "LIVE_RESULT" in pending_choice_type or "RESULT" in pending_choice_type:
        return "resolution"
    if "DISCARD" in pending_choice_type or "TARGET" in pending_choice_type or "ABILITY" in pending_choice_type:
        return "prompt"
    if phase in {-3, -2, -1}:
        return "setup"
    if phase in {8, 10}:
        return "resolution"
    if phase in {4, 5}:
        return "main"
    return "main" if int(current_player) in (0, 1) else "setup"


@dataclass(frozen=True, slots=True)
class StateStrategicEvaluation:
    clearability: float
    strategic_utility: float
    phase_role: str
    active_live_count: int
    candidate_live_count: int
    candidate_live_source: str
    best_live_card_id: int
    best_live_clearability: float
    best_live_deficit_by_color: tuple[float, ...]
    best_live_color_coverage: float
    stage_hearts: float
    required_hearts: float
    heart_gap: float
    useful_cards_remaining: int
    useful_card_density: float
    draw_horizon: int
    score_margin: float
    live_margin: float
    energy_margin: float
    hand_margin: float
    turn_pressure: float


@dataclass(frozen=True, slots=True)
class MoveStrategicEvaluation:
    before: StateStrategicEvaluation
    after: StateStrategicEvaluation
    delta_clearability: float
    delta_utility: float
    resource_cost: float
    move_score: float


def evaluate_state_strategic_value(
    state_json: dict[str, Any],
    current_player: int,
    card_lookup: dict[int, dict[str, Any]],
    *,
    max_turns: int,
) -> StateStrategicEvaluation:
    players = list(state_json.get("players", []))
    player_json = players[_safe_int(current_player, 0)] if _safe_int(current_player, 0) < len(players) else {}
    opp_json = players[1 - _safe_int(current_player, 0)] if len(players) > 1 else {}
    role = _phase_role(state_json, current_player)

    stage_hearts = _sum_hearts(player_json.get("stage", []), card_lookup)
    opp_stage_hearts = _sum_hearts(opp_json.get("stage", []), card_lookup)
    total_stage = float(sum(stage_hearts))
    turn = _safe_int(state_json.get("turn", 0), 0)
    hand = _safe_len(player_json.get("hand", []))
    energy = _safe_len(player_json.get("energy_zone", []))
    yell = _safe_len(player_json.get("yell_cards", []))
    draw_horizon = max(
        1,
        min(
            max(1, len(player_json.get("deck", []))),
            max(1, _safe_int(max_turns, 10) - turn + 1 + hand // 2 + energy // 2 + yell // 3),
        ),
    )

    active_live_ids = [int(card_id) for card_id in player_json.get("live_zone", []) if _safe_int(card_id, -1) >= 0]
    active_live_count = len(active_live_ids)
    candidate_live_ids, candidate_live_source = _candidate_live_card_ids(player_json, card_lookup)
    remaining_counts = _deck_card_counts(player_json.get("deck", []))
    per_live_clearabilities: list[float] = []
    per_live_required_totals: list[float] = []
    per_live_gaps: list[float] = []
    per_live_useful_counts: list[int] = []
    per_live_densities: list[float] = []
    per_live_avg_values: list[float] = []

    for live_card_id in candidate_live_ids:
        estimate = _live_card_clearability_estimate(
            live_card_id,
            stage_hearts=stage_hearts,
            remaining_counts=remaining_counts,
            hand_size=hand,
            energy_size=energy,
            yell_size=yell,
            turn=turn,
            max_turns=max_turns,
            card_lookup=card_lookup,
            source=candidate_live_source,
        )
        per_live_clearabilities.append(float(estimate.clearability))
        per_live_required_totals.append(float(estimate.required_hearts))
        per_live_gaps.append(float(estimate.heart_gap))
        per_live_useful_counts.append(int(estimate.useful_cards_remaining))
        per_live_densities.append(float(estimate.useful_card_density))
        per_live_avg_values.append(float(estimate.avg_useful_value))

    if candidate_live_ids:
        clearability = _clip01(0.70 * float(min(per_live_clearabilities)) + 0.30 * float(sum(per_live_clearabilities) / len(per_live_clearabilities)))
        total_required = float(sum(per_live_required_totals))
        heart_gap = float(sum(per_live_gaps) / len(per_live_gaps)) if per_live_gaps else 0.0
        useful_card_count = int(max(per_live_useful_counts)) if per_live_useful_counts else 0
        useful_card_density = float(sum(per_live_densities) / len(per_live_densities)) if per_live_densities else 0.0
        avg_useful_value = float(sum(per_live_avg_values) / len(per_live_avg_values)) if per_live_avg_values else 0.0
    else:
        total_required = 0.0
        heart_gap = 0.0
        useful_card_count = 0
        useful_card_density = 0.0
        avg_useful_value = 0.0
        clearability = _clip01(
            0.35 * _clip01(total_stage / 12.0)
            + 0.45 * _clip01(float(hand) / 20.0)
            + 0.20 * (1.0 - _clip01(float(turn) / float(max(1, int(max_turns)))))
        )

    score_margin = float(tanh((float(player_json.get("score", 0)) - float(opp_json.get("score", 0))) / 12.0))
    live_margin = float(tanh((float(len(player_json.get("success_lives", []))) - float(len(opp_json.get("success_lives", [])))) / 3.0))
    energy_margin = float(tanh((float(len(player_json.get("energy_zone", []))) - float(len(opp_json.get("energy_zone", [])))) / 12.0))
    hand_margin = float(tanh((float(len(player_json.get("hand", []))) - float(len(opp_json.get("hand", [])))) / 20.0))
    stage_margin = float(tanh((total_stage - float(sum(opp_stage_hearts))) / 12.0))
    deck_quality = _clip01(float(useful_card_density))
    turn_pressure = _clip01(float(turn) / float(max(1, int(max_turns))))

    if role in {"setup", "mulligan"}:
        strategic_utility_raw = (
            0.75 * deck_quality
            + 0.40 * hand_margin
            + 0.35 * energy_margin
            + 0.20 * stage_margin
            - 0.70 * turn_pressure
        )
    elif role == "liveset":
        strategic_utility_raw = (
            0.60 * clearability
            + 0.45 * deck_quality
            + 0.30 * hand_margin
            + 0.30 * energy_margin
            + 0.20 * score_margin
            - 0.40 * turn_pressure
        )
    elif role == "resolution":
        strategic_utility_raw = (
            0.90 * score_margin
            + 0.75 * live_margin
            + 0.55 * stage_margin
            + 0.25 * hand_margin
            - 0.35 * turn_pressure
        )
    elif role == "prompt":
        strategic_utility_raw = (
            0.50 * clearability
            + 0.45 * deck_quality
            + 0.40 * hand_margin
            + 0.25 * energy_margin
            + 0.20 * stage_margin
            - 0.45 * turn_pressure
        )
    else:
        strategic_utility_raw = (
            0.95 * score_margin
            + 0.85 * live_margin
            + 0.60 * stage_margin
            + 0.40 * energy_margin
            + 0.35 * hand_margin
            + 0.45 * deck_quality
            + 0.30 * clearability
            - 0.85 * turn_pressure
        )
    strategic_utility = _clip01(_sigmoid(strategic_utility_raw))
    if per_live_clearabilities:
        best_live_index = max(range(len(per_live_clearabilities)), key=per_live_clearabilities.__getitem__)
        best_live_card_id = int(candidate_live_ids[best_live_index])
        best_live_clearability = float(per_live_clearabilities[best_live_index])
        best_estimate = _live_card_clearability_estimate(
            best_live_card_id,
            stage_hearts=stage_hearts,
            remaining_counts=remaining_counts,
            hand_size=hand,
            energy_size=energy,
            yell_size=yell,
            turn=turn,
            max_turns=max_turns,
            card_lookup=card_lookup,
            source=candidate_live_source,
        )
        best_live_deficit_by_color = tuple(float(value) for value in best_estimate.deficit_by_color)
        best_live_color_coverage = float(best_estimate.color_coverage)
    else:
        best_live_card_id = -1
        best_live_clearability = float(clearability)
        best_live_deficit_by_color = tuple([0.0] * 7)
        best_live_color_coverage = 0.0

    return StateStrategicEvaluation(
        clearability=float(clearability),
        strategic_utility=float(strategic_utility),
        phase_role=str(role),
        active_live_count=int(active_live_count),
        candidate_live_count=int(len(candidate_live_ids)),
        candidate_live_source=str(candidate_live_source),
        best_live_card_id=int(best_live_card_id),
        best_live_clearability=float(best_live_clearability),
        best_live_deficit_by_color=best_live_deficit_by_color,
        best_live_color_coverage=float(best_live_color_coverage),
        stage_hearts=total_stage,
        required_hearts=total_required,
        heart_gap=float(heart_gap),
        useful_cards_remaining=int(useful_card_count),
        useful_card_density=float(deck_quality),
        draw_horizon=int(draw_horizon),
        score_margin=float(score_margin),
        live_margin=float(live_margin),
        energy_margin=float(energy_margin),
        hand_margin=float(hand_margin),
        turn_pressure=float(turn_pressure),
    )


def evaluate_move_strategic_value(
    before_state_json: dict[str, Any],
    after_state_json: dict[str, Any],
    acting_player: int,
    card_lookup: dict[int, dict[str, Any]],
    *,
    max_turns: int,
    source_card_id: int = -1,
    family: str = "",
    policy_visible: bool = True,
) -> MoveStrategicEvaluation:
    before = evaluate_state_strategic_value(
        before_state_json,
        acting_player,
        card_lookup,
        max_turns=max_turns,
    )
    after = evaluate_state_strategic_value(
        after_state_json,
        acting_player,
        card_lookup,
        max_turns=max_turns,
    )

    family_lower = str(family).lower()
    resource_cost = _card_strength(source_card_id, card_lookup)
    if "discard" in family_lower:
        resource_cost += 0.25
    if "playmember" in family_lower or "setlive" in family_lower:
        resource_cost += 0.10 * _card_strength(source_card_id, card_lookup)
    if not policy_visible:
        resource_cost += 0.10

    delta_clearability = after.clearability - before.clearability
    delta_utility = after.strategic_utility - before.strategic_utility

    raw_score = (
        0.70 * delta_clearability
        + 1.05 * delta_utility
        + 0.25 * (after.score_margin - before.score_margin)
        + 0.15 * (after.energy_margin - before.energy_margin)
        + 0.10 * (after.hand_margin - before.hand_margin)
        + 0.10 * (after.useful_card_density - before.useful_card_density)
        - 0.20 * resource_cost
        - 0.08 * max(0.0, after.turn_pressure - before.turn_pressure)
    )
    move_score = float(tanh(raw_score))

    return MoveStrategicEvaluation(
        before=before,
        after=after,
        delta_clearability=float(delta_clearability),
        delta_utility=float(delta_utility),
        resource_cost=float(resource_cost),
        move_score=move_score,
    )
