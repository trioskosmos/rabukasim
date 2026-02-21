import math


def calculate_expected_elo_for_winrate(win_rate, opponent_avg_elo=1000):
    """
    Given a win rate, calculate what ELO difference would predict that rate
    ELO formula: expected = 1 / (1 + 10^((opponent - player) / 400))

    Solving for player ELO:
    win_rate = 1 / (1 + 10^((opponent - player) / 400))
    1 + 10^((opponent - player) / 400) = 1 / win_rate
    10^((opponent - player) / 400) = (1 / win_rate) - 1
    (opponent - player) / 400 = log10((1 / win_rate) - 1)
    player = opponent - 400 * log10((1 / win_rate) - 1)
    """
    if win_rate >= 1.0:
        return float("inf")
    if win_rate <= 0.0:
        return float("-inf")

    elo_diff = -400 * math.log10((1 / win_rate) - 1)
    return opponent_avg_elo + elo_diff


# Smart's stats
smart_wins = 62
smart_games = 66
smart_winrate = smart_wins / smart_games

# Opponent average (TrueRandom 975 + Random 959) / 2
opponent_avg = (975 + 959) / 2

expected_smart_elo = calculate_expected_elo_for_winrate(smart_winrate, opponent_avg)

print(f"Smart's Win Rate: {smart_winrate * 100:.1f}%")
print(f"Opponent Average ELO: {opponent_avg:.0f}")
print(f"Expected Smart ELO for {smart_winrate * 100:.1f}% win rate: {expected_smart_elo:.0f}")
print("Actual Smart ELO: 1064")
print(f"Difference: {expected_smart_elo - 1064:.0f} points SHORT")
print()
print("Zero-Sum Constraint:")
print(f"Total ELO in system: {1064 + 975 + 959} (should be 3000)")
print(f"Average ELO: {(1064 + 975 + 959) / 3:.1f}")
