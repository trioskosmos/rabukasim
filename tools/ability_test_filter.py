import json
import os
import subprocess
import sys

# Paths
RESULT_FILE = "tests/ability_test_results.json"
TEST_FILE = "engine/tests/cards/test_all_abilities.py"


def load_results():
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "r") as f:
            return json.load(f)
    return {}


def save_results(results):
    with open(RESULT_FILE, "w") as f:
        json.dump(results, f, indent=2)


def run_tests(parallel=True):
    results = load_results()

    # We want to run tests with -n auto if parallel
    cmd = ["uv", "run", "pytest", TEST_FILE, "--json-report", "--json-report-file=tests/report.json"]
    if parallel:
        cmd += ["-n", "auto"]

    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd)

    # Parse report.json
    if os.path.exists("tests/report.json"):
        with open("tests/report.json", "r") as f:
            report = json.load(f)

        for test in report.get("tests", []):
            nodeid = test.get("nodeid")
            outcome = test.get("outcome")
            results[nodeid] = outcome

        save_results(results)
        print(f"Updated results in {RESULT_FILE}")


def print_summary():
    results = load_results()
    passed = sum(1 for v in results.values() if v == "passed")
    failed = sum(1 for v in results.values() if v == "failed")
    skipped = sum(1 for v in results.values() if v == "skipped")
    print(f"Summary: {passed} passed, {failed} failed, {skipped} skipped.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        print_summary()
    else:
        run_tests()
