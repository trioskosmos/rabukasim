import os


def search_japanese(file_path, keyword):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Searching for '{keyword}' in {file_path}:")
    for i, line in enumerate(lines):
        if keyword in line:
            print(f"{i + 1}: {line.strip()}")


if __name__ == "__main__":
    import sys

    file = sys.argv[1] if len(sys.argv) > 1 else "compiler/parser.py"
    kw = sys.argv[2] if len(sys.argv) > 2 else "相手"
    search_japanese(file, kw)
