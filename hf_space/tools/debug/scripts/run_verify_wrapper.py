import subprocess
import sys


def main():
    print("Running verify_abilities.py...")
    result = subprocess.run(
        [sys.executable, "tools/verify_abilities.py"],
        capture_output=True,
        text=True,
        cwd=r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy",
    )

    with open("log.clean.txt", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)

    print("Done. log.clean.txt created.")


if __name__ == "__main__":
    main()
