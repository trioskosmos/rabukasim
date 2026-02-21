import subprocess
import sys


def main():
    print("Running compiler/main.py...")
    result = subprocess.run(
        [sys.executable, "compiler/main.py", "--input", "data/cards.json", "--output", "data/cards_compiled.json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy",
    )

    with open("compile_log.clean.txt", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)

    print("Done. compile_log.clean.txt created.")


if __name__ == "__main__":
    main()
