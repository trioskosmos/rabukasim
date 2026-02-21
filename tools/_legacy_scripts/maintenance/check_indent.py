import sys


def check_indentation(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped:
                continue

            indent = len(line) - len(stripped)
            if indent % 4 != 0:
                print(f"Line {i + 1}: Potential indentation issue ({indent} spaces): {line.strip()[:40]}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_indentation(sys.argv[1])
    else:
        print("Usage: python check_indent.py <filepath>")
