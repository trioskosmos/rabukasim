import os
import subprocess
import sys


def run_suite():
    print("============================================================")
    print("Lovecasim Ability Test Suite")
    print("============================================================")

    repro_dir = os.path.dirname(__file__)
    test_files = [f for f in os.listdir(repro_dir) if f.startswith("test_") and f.endswith(".py")]
    test_files.sort()

    results = []

    for test_file in test_files:
        test_path = os.path.join(repro_dir, test_file)
        print(f"\nRunning {test_file}...")

        try:
            # Run test as a subprocess to avoid state pollution between tests
            process = subprocess.run([sys.executable, test_path], capture_output=True, text=True, timeout=30)

            if process.returncode == 0:
                print(f"PASS: {test_file}")
                results.append((test_file, "PASS"))
            else:
                print(f"FAIL: {test_file}")
                print("--- STDOUT ---")
                print(process.stdout)
                print("--- STDERR ---")
                print(process.stderr)
                results.append((test_file, "FAIL"))

        except subprocess.TimeoutExpired:
            print(f"TIMEOUT: {test_file}")
            results.append((test_file, "TIMEOUT"))
        except Exception as e:
            print(f"ERROR running {test_file}: {e}")
            results.append((test_file, f"ERROR: {e}"))

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    passed = 0
    for test, status in results:
        print(f"{test:<30} | {status}")
        if status == "PASS":
            passed += 1

    print(f"\nSummary: {passed}/{len(results)} passed")

    if passed < len(results):
        sys.exit(1)


if __name__ == "__main__":
    run_suite()
