import re


def find_type_11():
    with open("compiler/parser.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Search for all Condition creation
    matches = re.finditer(r"Condition\(([^,\)]+)", content)
    for match in matches:
        expr = match.group(1).strip()
        line_no = content.count("\n", 0, match.start()) + 1
        print(f"Line {line_no}: Condition({expr})")


if __name__ == "__main__":
    find_type_11()
