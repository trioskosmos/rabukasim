def repair_log(input_path, output_path):
    with open(input_path, "rb") as f:
        content = f.read()

    # Try different decodings
    decodings = ["utf-16", "utf-16-le", "utf-16-be", "utf-8"]
    repaired = None
    for enc in decodings:
        try:
            repaired = content.decode(enc)
            print(f"Decoded with {enc}")
            break
        except:
            continue

    if repaired:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(repaired)
        print(f"Repaired log written to {output_path}")
    else:
        print("Failed to decode log file")


if __name__ == "__main__":
    repair_log("tournament_round_robin.txt", "tournament_results_utf8.txt")
