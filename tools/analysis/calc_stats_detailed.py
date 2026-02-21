import sys

try:
    with open("bench_results.txt", "rb") as f:
        data = f.read().decode("utf-16", "ignore")
except FileNotFoundError:
    print("Error: bench_results.txt not found")
    sys.exit(1)

lines = [l for l in data.splitlines() if "|" in l and "-" not in l and "Game" not in l]

for l in lines:
    parts = [p.strip() for p in l.split("|") if p.strip()]
    if len(parts) >= 5:
        try:
            game_idx = parts[0]
            p_steps = float(parts[1])
            r_steps = float(parts[2])
            p_time = float(parts[3])
            r_time = float(parts[4])

            p_avg = p_time / p_steps if p_steps > 0 else 0
            r_avg = r_time / r_steps if r_steps > 0 else 0
            speedup = p_avg / r_avg if r_avg > 0 else 0

            print(f"Game {game_idx}: P {p_avg:.4f} ms/step, R {r_avg:.4f} ms/step, Speedup {speedup:.1f}x")
        except ValueError:
            continue
