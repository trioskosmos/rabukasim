from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class CompetitiveGameRewardBreakdown:
    winner: int
    turns: int
    max_turns: int
    fast_win_turn_threshold: int
    decisive_bonus: float
    speed_bonus: float
    live_margin_bonus: float
    score_margin_bonus: float
    reward: float
    is_draw: bool
    is_fast_win: bool


@dataclass(frozen=True)
class SeedCertificationSummary:
    games: int
    avg_reward: float
    min_reward: float
    max_reward: float
    decisive_rate: float
    fast_win_rate: float
    avg_turns: float
    avg_decisive_turns: float
    avg_abs_live_margin: float
    avg_abs_score_margin: float


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def competitive_fast_win_reward(
    *,
    winner: int,
    turns: int,
    max_turns: int,
    final_scores: tuple[int, int],
    final_lives: tuple[int, int],
    fast_win_turn_threshold: int,
) -> CompetitiveGameRewardBreakdown:
    turns = int(turns)
    max_turns = max(1, int(max_turns))
    fast_win_turn_threshold = max(1, min(int(fast_win_turn_threshold), max_turns))

    if int(winner) == -1:
        return CompetitiveGameRewardBreakdown(
            winner=-1,
            turns=turns,
            max_turns=max_turns,
            fast_win_turn_threshold=fast_win_turn_threshold,
            decisive_bonus=0.0,
            speed_bonus=0.0,
            live_margin_bonus=0.0,
            score_margin_bonus=0.0,
            reward=0.0,
            is_draw=True,
            is_fast_win=False,
        )

    winner_idx = int(winner)
    loser_idx = 1 - winner_idx
    live_margin = max(0, int(final_lives[winner_idx]) - int(final_lives[loser_idx]))
    score_margin = max(0, int(final_scores[winner_idx]) - int(final_scores[loser_idx]))

    decisive_bonus = 1.0
    speed_bonus = 0.75 * _clip01((fast_win_turn_threshold + 1 - min(turns, max_turns)) / fast_win_turn_threshold)
    live_margin_bonus = 0.35 * float(live_margin)
    score_margin_bonus = 0.12 * float(score_margin)
    reward = float(decisive_bonus + speed_bonus + live_margin_bonus + score_margin_bonus)

    return CompetitiveGameRewardBreakdown(
        winner=winner_idx,
        turns=turns,
        max_turns=max_turns,
        fast_win_turn_threshold=fast_win_turn_threshold,
        decisive_bonus=decisive_bonus,
        speed_bonus=speed_bonus,
        live_margin_bonus=live_margin_bonus,
        score_margin_bonus=score_margin_bonus,
        reward=reward,
        is_draw=False,
        is_fast_win=turns <= fast_win_turn_threshold,
    )


def perspective_fast_win_value(
    *,
    player: int,
    winner: int,
    turns: int,
    max_turns: int,
    final_scores: tuple[int, int],
    final_lives: tuple[int, int],
    fast_win_turn_threshold: int,
) -> float:
    breakdown = competitive_fast_win_reward(
        winner=winner,
        turns=turns,
        max_turns=max_turns,
        final_scores=final_scores,
        final_lives=final_lives,
        fast_win_turn_threshold=fast_win_turn_threshold,
    )
    if breakdown.is_draw:
        return 0.0
    return float(breakdown.reward if int(player) == int(winner) else -breakdown.reward)


def summarize_seed_certification(
    games: Sequence[Mapping[str, int | float]],
    *,
    max_turns: int,
    fast_win_turn_threshold: int,
) -> SeedCertificationSummary:
    if not games:
        return SeedCertificationSummary(
            games=0,
            avg_reward=0.0,
            min_reward=0.0,
            max_reward=0.0,
            decisive_rate=0.0,
            fast_win_rate=0.0,
            avg_turns=0.0,
            avg_decisive_turns=0.0,
            avg_abs_live_margin=0.0,
            avg_abs_score_margin=0.0,
        )

    breakdowns = [
        competitive_fast_win_reward(
            winner=int(game["winner"]),
            turns=int(game["turns"]),
            max_turns=max_turns,
            final_scores=(int(game["p0_score"]), int(game["p1_score"])),
            final_lives=(int(game["p0_lives"]), int(game["p1_lives"])),
            fast_win_turn_threshold=fast_win_turn_threshold,
        )
        for game in games
    ]
    decisive_turns = [float(item.turns) for item in breakdowns if not item.is_draw]
    turn_values = [float(item.turns) for item in breakdowns]
    live_margins = [abs(int(game["p0_lives"]) - int(game["p1_lives"])) for game in games]
    score_margins = [abs(int(game["p0_score"]) - int(game["p1_score"])) for game in games]
    reward_values = [float(item.reward) for item in breakdowns]

    return SeedCertificationSummary(
        games=len(games),
        avg_reward=sum(reward_values) / len(reward_values),
        min_reward=min(reward_values),
        max_reward=max(reward_values),
        decisive_rate=sum(0 if item.is_draw else 1 for item in breakdowns) / len(breakdowns),
        fast_win_rate=sum(1 if item.is_fast_win and not item.is_draw else 0 for item in breakdowns) / len(breakdowns),
        avg_turns=sum(turn_values) / len(turn_values),
        avg_decisive_turns=(sum(decisive_turns) / len(decisive_turns)) if decisive_turns else float(max_turns),
        avg_abs_live_margin=sum(float(value) for value in live_margins) / len(live_margins),
        avg_abs_score_margin=sum(float(value) for value in score_margins) / len(score_margins),
    )


def seed_certified(
    summary: SeedCertificationSummary,
    *,
    target_reward: float,
    target_decisive_rate: float,
    target_fast_win_rate: float,
    target_avg_turns: float,
) -> bool:
    if summary.games <= 0:
        return False
    return (
        float(summary.avg_reward) >= float(target_reward)
        and float(summary.decisive_rate) >= float(target_decisive_rate)
        and float(summary.fast_win_rate) >= float(target_fast_win_rate)
        and float(summary.avg_turns) <= float(target_avg_turns)
    )