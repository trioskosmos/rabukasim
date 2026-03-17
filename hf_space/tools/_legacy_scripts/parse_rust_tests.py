import re
import sys


def parse_test_results(filepath):
    content = ""
    encodings = ["utf-16", "utf-8", "cp1252", "latin-1"]
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc) as f:
                content = f.read()
            break
        except Exception:
            continue

    if not content:
        print("Could not read file with any encoding")
        return

    # 1. Find the failures list at the end
    # failures:
    #    test_a
    #    test_b
    failures_match = re.search(r"failures:\n(.*?)\n\ntest result:", content, re.DOTALL)
    if not failures_match:
        # Try finding the list at the very end if it's truncated or slightly different
        failures_match = re.search(r"failures:\n(.*)", content, re.DOTALL)

    if not failures_match:
        print("No failures list found")
        return

    # Extract test names
    raw_list = failures_match.group(1).strip()
    fail_names = []
    for line in raw_list.split("\n"):
        line = line.strip()
        if line and not line.startswith("----"):
            # Sometimes it has ' - result: FAILED'
            name = line.split(" ")[0]
            fail_names.append(name)

    print(f"Total failures identified: {len(fail_names)}")

    # 2. Extract panic messages for each failure
    for name in fail_names:
        # Search for the block starting with "---- name stdout ----"
        pattern = rf"---- {re.escape(name)} stdout ----(.*?)(?=----|$)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            stdout = match.group(1)
            # Find the line that looks like 'panicked at ...'
            panic_lines = [l.strip() for l in stdout.split("\n") if "panicked at" in l]
            panic_msg = panic_lines[-1] if panic_lines else "Panic message not found in stdout block"
            print(f"[{name}]\n  {panic_msg}")
        else:
            print(f"[{name}]\n  Stdout block not found")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        parse_test_results(sys.argv[1])
    else:
        print("Usage: python parse_tests.py <logfile>")
