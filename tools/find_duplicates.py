def find_dupes(path, query):
    print(f"Scanning {path} for {query}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if query in line:
                    print(f"Found at line {i + 1}: {line.strip()}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    find_dupes("reports/semantic_truth.json", "PL!N-PR-005-PR")
