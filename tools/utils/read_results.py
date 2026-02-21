with open("final_output.txt", "rb") as f:
    data = f.read().decode("utf-16", errors="ignore")
    # Remove lines that contain '\r' without '\n' (progress bar lines)
    lines = [line for line in data.splitlines() if not line.endswith("\r")]
    for line in lines:
        if any(
            keyword in line
            for keyword in ["BENCHMARK RESULTS:", "CPU Total:", "GPU Total:", "Speedup:", "ELO Table", "=="]
        ):
            print(line)
        if "|" in line and any(x in line for x in ["Agent", "ELO", "NN"]):
            print(line)
