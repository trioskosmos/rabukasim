import re
import subprocess


def run_tests():
    cmd = ["uv", "run", "pytest", "engine/tests/cards/batches/test_auto_generated_strict_v2.py", "--tb=no", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

    failures = []
    # Q output with failures looks like:
    # FAILED engine/tests/cards/batches/test_auto_generated_strict_v2.py::test_strict_... - AssertionError: ...
    for line in result.stdout.splitlines():
        if "::test_strict_" in line:
            match = re.search(r"::(test_strict_[\w!+-]+)", line)
            if match:
                failures.append(match.group(1))

    print(f"Total Failures: {len(failures)}")
    for f in failures:
        print(f)


if __name__ == "__main__":
    run_tests()
