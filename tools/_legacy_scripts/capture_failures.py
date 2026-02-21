import subprocess


def run_tests():
    print("Running pytest for Batch 2...")
    with open("batch2_failures.log", "w", encoding="utf-8") as f:
        # Run pytest and redirect stdout/stderr to the file
        result = subprocess.run(
            ["uv", "run", "pytest", "engine/tests/cards/batches/test_easy_wins_batch_2.py", "--tb=short"],
            stdout=f,
            stderr=subprocess.STDOUT,
        )
    print(f"Finished with exit code {result.returncode}. Log saved to batch2_failures.log")


if __name__ == "__main__":
    run_tests()
