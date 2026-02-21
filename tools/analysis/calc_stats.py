import sys

try:
    with open("bench_results.txt", "rb") as f:
        data = f.read().decode("utf-16", "ignore")
except FileNotFoundError:
    print("Error: bench_results.txt not found")
    sys.exit(1)

lines = [l for l in data.splitlines() if "|" in l and "-" not in l and "Game" not in l]
p_steps, r_steps, p_times, r_times = 0, 0, 0, 0

for l in lines:
    parts = [p.strip() for p in l.split("|") if p.strip()]
    if len(parts) >= 5:
        try:
            p0 = float(parts[1])
            r0 = float(parts[2])
            pt = float(parts[3])
            rt = float(parts[4])
            p_steps += p0
            r_steps += r0
            p_times += pt
            r_times += rt
        except ValueError:
            continue

if p_steps == 0 or r_steps == 0:
    print("No valid steps found in results.")
    sys.exit(0)

py_avg = p_times / p_steps
rust_py_avg = r_times / r_steps

print("--- Benchmark Comparison ---")
print(f"Python Engine: {p_steps:.0f} steps, {p_times:.2f}ms total")
print(f"  Avg: {py_avg:.4f} ms/step")
print(f"Rust Engine (via Python): {r_steps:.0f} steps, {r_times:.2f}ms total")
print(f"  Avg: {rust_py_avg:.4f} ms/step")
print(f"Speedup Ratio (Bindings): {py_avg / rust_py_avg:.1f}x")

# Pure Rust baseline (from benchmark_pure.rs)
rust_native_avg = 0.0015
print(f"Rust Engine (Native Pure): {rust_native_avg:.4f} ms/step (Baseline)")
print(f"Speedup Ratio (Native): {py_avg / rust_native_avg:.1f}x")
print(f"Binding Overhead: {rust_py_avg / rust_native_avg:.1f}x longer than native")
