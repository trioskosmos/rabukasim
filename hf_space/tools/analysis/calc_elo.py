def expected(ra, rb):
    return 1 / (1 + 10 ** ((rb - ra) / 400))


smart = 1077
random_elo = 981
true = 940

print("ELO Predictions (what each matchup should produce):")
print(f"Smart(1077) vs Random(981): {expected(smart, random_elo) * 100:.1f}% expected win for Smart")
print(f"Smart(1077) vs True(940): {expected(smart, true) * 100:.1f}% expected win for Smart")
print(f"Random(981) vs True(940): {expected(random_elo, true) * 100:.1f}% expected win for Random")
print()
print("Overall win rates:")
print("Smart: 45.1% (plays 50% vs each opponent)")
print("Random: 16.4%")
print("TrueRandom: 21.2%")
