import os, time

results = []
# Check benchmark results 
results.append("=== BENCHMARK RESULTS ===")
with open("alphazero/logs/benchmark_results.txt", "rb") as f:
    text = f.read().decode("utf-8", errors="replace")
results.append(text)

# Check for new loops  
results.append("\n=== LOOP LOG ANALYSIS ===")
d = "alphazero/logs/loops"
files = os.listdir(d)
now = time.time()
recent = [(f, os.path.getsize(os.path.join(d, f)), os.path.getmtime(os.path.join(d, f))) for f in files if now - os.path.getmtime(os.path.join(d, f)) < 900]
results.append("Total loop files: " + str(len(files)))
results.append("New loop files (last 15min): " + str(len(recent)))
for f, size, mtime in sorted(recent, key=lambda x: -x[2]):
    age_min = (now - mtime) / 60
    results.append("  " + f + "  (" + str(size) + "b, " + str(round(age_min, 1)) + "min ago)")

with open("reports/fix_verification.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))
print("Written to reports/fix_verification.txt")
