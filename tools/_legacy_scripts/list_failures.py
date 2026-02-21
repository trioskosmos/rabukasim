import sys
import re


def list_failures(filepath):
    content = ""
    # Try all typical encodings for Windows redirection
    for enc in ["utf-16", "utf-8", "cp1252"]:
        try:
            with open(filepath, "r", encoding=enc) as f:
                content = f.read()
            break
        except Exception:
            continue

    if not content:
        print("Error: Could not read file.")
        return

    # Find the last 'failures:' section
    sections = list(re.finditer(r"^failures:\s*$", content, re.MULTILINE))
    if not sections:
        print("No 'failures:' section found.")
        return

    last_section = sections[-1]
    # The list of tests follows until the next double newline or 'test result:'
    rest = content[last_section.end() :]
    end_match = re.search(r"\n\n|test result:", rest)
    if end_match:
        failed_block = rest[: end_match.start()]
    else:
        failed_block = rest

    for line in failed_block.split("\n"):
        name = line.strip()
        if name:
            print(name)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        list_failures(sys.argv[1])
    else:
        print("Usage: python list_failures.py <logfile>")
