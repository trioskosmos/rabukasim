import subprocess
import sys


def main():
    print("Running tests/test_card_bp1_019.py...")
    result = subprocess.run(
        [sys.executable, "tests/test_card_bp1_019.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy",
    )

    with open("test_bp1_019_log.clean.txt", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n")
        f.write(result.stdout or "")
        f.write("\nSTDERR:\n")
        f.write(result.stderr or "")

    print("Done. test_bp1_019_log.clean.txt created.")


if __name__ == "__main__":
    main()
