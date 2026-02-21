import collections
import re


def analyze(filename):
    print(f"Analyzing {filename}...")
    try:
        with open(filename, "r", encoding="utf-16") as f:
            content = f.read()
    except:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Could not read file: {e}")
            return

    failures = []
    # Pytest failure pattern usually:
    # ________________________________ test_name _________________________________
    # ...
    # E   AssertionError: ...
    # or
    # E   IndexError: ...

    chunks = re.split(r"_{10,} test_", content)
    print(f"Found {len(chunks)} chunks")

    errors = []
    for chunk in chunks[1:]:  # Skip first preamble
        # Find the exception
        match = re.search(r"^E \s+(.+?)$", chunk, re.MULTILINE)
        if match:
            err = match.group(1).strip()
            # Normalize error slightly (remove specific counts or IDs if obvious)
            err_norm = re.sub(r"card \d+", "card <ID>", err)
            err_norm = re.sub(r"id=\d+", "id=<ID>", err_norm)
            errors.append(err_norm)
        else:
            # Fallback checks
            if "FAILED" in chunk:
                errors.append("Unknown FAILURE")

    counter = collections.Counter(errors)
    print("\nTop Failures:")
    for err, count in counter.most_common(10):
        print(f"{count}: {err}")
        # Find examples
        examples = []
        for chunk in chunks:
            if err in chunk:
                # Extract test name
                m = re.search(r"test_([A-Za-z0-9_]+)", chunk)
                if m:
                    examples.append(m.group(1))
                if len(examples) >= 3:
                    break
        print(f"   Examples: {', '.join(examples)}")


if __name__ == "__main__":
    analyze("test_failures.log")
    print("-" * 20)
    analyze("test_failure.log")
