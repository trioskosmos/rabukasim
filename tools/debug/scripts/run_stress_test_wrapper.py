import subprocess


def run_stress_test():
    cmd = [
        "uv",
        "run",
        "python",
        "ai/headless_runner.py",
        "--agent",
        "ability_focus",
        "--agent_p2",
        "ability_focus",
        "--max_turns",
        "1000",
        "--log_file",
        "stress_test_log.txt",
        "--num_games",
        "100",
    ]

    print(f"Running: {' '.join(cmd)}")
    with (
        open("stress_stdout.txt", "w", encoding="utf-8") as out,
        open("stress_stderr.txt", "w", encoding="utf-8") as err,
    ):
        result = subprocess.run(cmd, stdout=out, stderr=err, text=True)

    print(f"Stress test finished with exit code {result.returncode}")
    if result.returncode != 0:
        print("Check stress_stderr.txt for errors.")


if __name__ == "__main__":
    run_stress_test()
