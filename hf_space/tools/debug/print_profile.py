def print_profile():
    with open("profile_results_2.txt", "r", encoding="utf-16") as f:
        lines = f.readlines()

    # Find the header
    start_idx = 0
    for i, line in enumerate(lines):
        if "ncalls" in line and "tottime" in line:
            start_idx = i
            break

    with open("profile_summary.txt", "w", encoding="utf-8") as out:
        for line in lines[start_idx : start_idx + 60]:
            out.write(line)


if __name__ == "__main__":
    print_profile()
