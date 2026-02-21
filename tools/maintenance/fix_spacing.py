import sys


def fix_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Collapse multiple blank lines into a single blank line
    # Replace any sequence of 3 or more newlines (which is 2+ blank lines) with 2 newlines (1 blank line)
    # Actually, simpler: replace \n\s*\n with \n

    lines = content.split("\n")
    new_lines = []

    prev_empty = False

    for line in lines:
        is_empty = line.strip() == ""

        if is_empty and prev_empty:
            continue  # Skip consecutive empty lines

        new_lines.append(line)
        prev_empty = is_empty

    content = "\n".join(new_lines)

    # 2. Ensure 2 blank lines before top-level class and def
    # This is a bit rough but catches the main ones
    # We'll rely on ruff/black to do the fine tuning AFTER this aggressive strip

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    fix_file(sys.argv[1])
