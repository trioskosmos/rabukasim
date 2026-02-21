def search_parser():
    with open("compiler/parser.py", "r", encoding="utf-8") as f:
        lines = f.readlines()

    keywords = ["移動", "HAS_MOVED", "移動している場合"]

    for i, line in enumerate(lines):
        line_no = i + 1
        for kw in keywords:
            if kw in line:
                print(f"{line_no}: {line.strip()}")
                break


if __name__ == "__main__":
    search_parser()
