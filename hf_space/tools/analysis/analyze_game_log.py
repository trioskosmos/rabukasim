import re


def analyze_log(log_path):
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    p0_stats = {"play": 0, "discard": 0, "pass": 0, "live_set": 0, "ability": 0}
    p1_stats = {"play": 0, "discard": 0, "pass": 0, "live_set": 0, "ability": 0}

    current_game = 0

    for line in lines:
        if "=== Game" in line:
            current_game += 1
            # Reset or just track total? Let's track total for now or specifically Game 8
            # The user is interested in the "Best Game" behavior generally
            pass

        # Parse Actions
        # Action: P0 chooses 16
        m = re.search(r"Action: P(\d) chooses (\d+)", line)
        if m:
            pid = int(m.group(1))
            action = int(m.group(2))
            stats = p0_stats if pid == 0 else p1_stats

            if action == 0:
                stats["pass"] += 1
            elif 1 <= action <= 180:
                stats["play"] += 1
            elif 400 <= action <= 459:
                stats["live_set"] += 1
            elif action >= 600:
                stats["ability"] += 1

        # Parse Discards
        # Player 0 discarded 326
        m = re.search(r"Player (\d) discarded", line)
        if m:
            pid = int(m.group(1))
            stats = p0_stats if pid == 0 else p1_stats
            stats["discard"] += 1

    print("=== P0 (AbilityFocus) Stats ===")
    print(p0_stats)
    print("\n=== P1 (Random) Stats ===")
    print(p1_stats)


if __name__ == "__main__":
    analyze_log("ai_performance.log")
