import re


def parse_failures():
    log_path = "test_results.log"
    # Try different encodings
    content = ""
    try:
        with open(log_path, "r", encoding="utf-16") as f:
            content = f.read()
    except:
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
        except:
            print("Could not read file")
            return

    # Look for FAILED ...::test_strict_...
    failures = re.findall(r"FAILED .*?::(test_strict_\w+)", content)
    unique_failures = sorted(list(set(failures)))

    print(f"Found {len(unique_failures)} failing strict tests.")
    for f in unique_failures[:20]:
        print(f)


if __name__ == "__main__":
    parse_failures()
