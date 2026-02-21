import os

path = "evaluation_results.txt"
if os.path.exists(path):
    with open(path, "rb") as f:
        data = f.read()
    content = ""
    for enc in ["utf-16", "utf-8"]:
        try:
            content = data.decode(enc)
            break
        except:
            continue
    lines = [
        l for l in content.splitlines() if any(k in l for k in ["Win Rate", "Avg Reward", "Avg Score", "Conclusion"])
    ]
    with open("metrics_fixed.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
else:
    print("File not found.")
