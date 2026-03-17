import math


def calculate_expected_elo_for_winrate(win_rate, opponent_avg_elo):
    """Calculate what ELO a player should have given their win rate against opponents."""
    if win_rate >= 1.0:
        return float("inf")
    if win_rate <= 0.0:
        return float("-inf")

    elo_diff = -400 * math.log10((1 / win_rate) - 1)
    return opponent_avg_elo + elo_diff


# Actual stats from 100-game tournament
stats = {
    "Smart": {"wins": 62, "games": 66, "current_elo": 1064},
    "TrueRandom": {"wins": 22, "games": 70, "current_elo": 975},
    "Random": {"wins": 18, "games": 64, "current_elo": 959},
}

# Calculate win rates
for agent, data in stats.items():
    data["winrate"] = data["wins"] / data["games"]

print("=== CURRENT STATE (Zero-Sum Constrained) ===")
for agent, data in stats.items():
    print(f"{agent:12}: {data['current_elo']:4} ELO, {data['winrate'] * 100:5.1f}% win rate")
print(f"Total: {sum(d['current_elo'] for d in stats.values())}")
print()

# Calculate expected ELOs (iteratively, since they depend on each other)
# Start with current ELOs as opponent averages, then iterate
print("=== EXPECTED STATE (Unconstrained) ===")
for iteration in range(5):  # Iterate to converge
    expected = {}
    for agent, data in stats.items():
        # Calculate average opponent ELO
        opponent_elos = [
            stats[opp]["current_elo"] if iteration == 0 else expected.get(opp, stats[opp]["current_elo"])
            for opp in stats
            if opp != agent
        ]
        opponent_avg = sum(opponent_elos) / len(opponent_elos)

        expected[agent] = calculate_expected_elo_for_winrate(data["winrate"], opponent_avg)

    # Update current_elo for next iteration
    for agent in stats:
        stats[agent]["current_elo"] = expected[agent]

for agent, elo in expected.items():
    actual = stats[agent]["current_elo"]
    print(
        f"{agent:12}: {elo:7.0f} ELO (should be), currently {1064 if agent == 'Smart' else 975 if agent == 'TrueRandom' else 959}"
    )

print(f"\nExpected Total: {sum(expected.values()):.0f} (not 3000!)")
print()

# Calculate the adjustment needed
print("=== ZERO-SUM FORCES ALL RATINGS TOWARD 1000 ===")
expected_total = sum(expected.values())
compression_factor = 3000 / expected_total

for agent, expected_elo in expected.items():
    actual = 1064 if agent == "Smart" else 975 if agent == "TrueRandom" else 959
    compressed = (expected_elo - 1000) * compression_factor + 1000
    print(f"{agent:12}: Expected {expected_elo:5.0f} → Compressed to ~{compressed:4.0f} (Actual: {actual})")
