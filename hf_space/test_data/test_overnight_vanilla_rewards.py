from alphazero.training.overnight_reward import (
    competitive_fast_win_reward,
    seed_certified,
    summarize_seed_certification,
)


def test_draw_reward_is_zero() -> None:
    breakdown = competitive_fast_win_reward(
        winner=-1,
        turns=10,
        max_turns=10,
        final_scores=(2, 2),
        final_lives=(2, 2),
        fast_win_turn_threshold=6,
    )
    assert breakdown.reward == 0.0
    assert breakdown.is_draw is True


def test_fast_win_beats_slow_win() -> None:
    fast = competitive_fast_win_reward(
        winner=0,
        turns=4,
        max_turns=10,
        final_scores=(3, 0),
        final_lives=(3, 0),
        fast_win_turn_threshold=6,
    )
    slow = competitive_fast_win_reward(
        winner=0,
        turns=9,
        max_turns=10,
        final_scores=(3, 0),
        final_lives=(3, 0),
        fast_win_turn_threshold=6,
    )
    assert fast.reward > slow.reward
    assert fast.speed_bonus > slow.speed_bonus


def test_reward_uses_margin_not_total_progress() -> None:
    dominant = competitive_fast_win_reward(
        winner=0,
        turns=6,
        max_turns=10,
        final_scores=(3, 0),
        final_lives=(3, 0),
        fast_win_turn_threshold=6,
    )
    mutual_progress = competitive_fast_win_reward(
        winner=0,
        turns=6,
        max_turns=10,
        final_scores=(3, 2),
        final_lives=(3, 2),
        fast_win_turn_threshold=6,
    )
    assert dominant.reward > mutual_progress.reward


def test_certification_requires_fast_decisive_results() -> None:
    summary = summarize_seed_certification(
        [
            {"winner": 0, "turns": 5, "p0_score": 3, "p1_score": 0, "p0_lives": 3, "p1_lives": 0},
            {"winner": 1, "turns": 6, "p0_score": 0, "p1_score": 3, "p0_lives": 0, "p1_lives": 3},
            {"winner": 0, "turns": 6, "p0_score": 3, "p1_score": 1, "p0_lives": 3, "p1_lives": 1},
            {"winner": 1, "turns": 5, "p0_score": 0, "p1_score": 3, "p0_lives": 0, "p1_lives": 3},
        ],
        max_turns=10,
        fast_win_turn_threshold=6,
    )
    assert seed_certified(
        summary,
        target_reward=0.75,
        target_decisive_rate=1.0,
        target_fast_win_rate=1.0,
        target_avg_turns=6.0,
    )


def test_certification_rejects_draw_heavy_results() -> None:
    summary = summarize_seed_certification(
        [
            {"winner": -1, "turns": 10, "p0_score": 2, "p1_score": 2, "p0_lives": 2, "p1_lives": 2},
            {"winner": 0, "turns": 8, "p0_score": 3, "p1_score": 2, "p0_lives": 3, "p1_lives": 2},
        ],
        max_turns=10,
        fast_win_turn_threshold=6,
    )
    assert not seed_certified(
        summary,
        target_reward=0.75,
        target_decisive_rate=1.0,
        target_fast_win_rate=0.9,
        target_avg_turns=6.0,
    )