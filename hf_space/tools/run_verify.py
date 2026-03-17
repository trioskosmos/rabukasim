import subprocess


def main():
    print("Running verify_attention_extractor.py...")
    try:
        result = subprocess.run(
            ["uv", "run", "python", "tools/verify_attention_extractor.py"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        print("--- STDOUT ---")
        print(result.stdout)
        print("--- STDERR ---")
        print(result.stderr)

        with open("verify_log.txt", "w") as f:
            f.write(result.stdout)
            f.write("\n--- STDERR ---\n")
            f.write(result.stderr)

    except Exception as e:
        print(f"Failed to run: {e}")


if __name__ == "__main__":
    main()
