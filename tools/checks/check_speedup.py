# Read parallel tournament output
try:
    with open("tournament_parallel_output.txt", "r", encoding="utf-16le") as f:
        content = f.read()

    # Find timing info
    if "Tournament Complete" in content:
        # Extract the time
        import re

        match = re.search(r"Tournament Complete in ([\d.]+)s", content)
        if match:
            parallel_time = float(match.group(1))
            print(f"Parallel execution time: {parallel_time:.2f}s")

            # Compare with sequential (10.39s from earlier)
            sequential_time = 10.39
            speedup = sequential_time / parallel_time
            print(f"Sequential execution time: {sequential_time:.2f}s")
            print(f"Speedup: {speedup:.2f}x faster!")
            print(f"Time saved: {sequential_time - parallel_time:.2f}s")

        # Find worker count
        worker_match = re.search(r"Running \d+ games using (\d+) workers", content)
        if worker_match:
            print(f"Workers used: {worker_match.group(1)}")

    # Show results section
    if "=====" in content:
        results_start = content.find("=====")
        print("\nResults preview:")
        print(content[results_start : results_start + 800])

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
