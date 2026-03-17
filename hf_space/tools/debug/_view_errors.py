import json
import subprocess


def main():
    result = subprocess.run(
        ["cargo", "test", "--no-run", "--message-format=json"],
        capture_output=True,
        cwd=r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src",
    )
    output = result.stdout.decode("utf-8", errors="ignore")
    errors = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
            if msg.get("reason") == "compiler-message" and msg.get("message", {}).get("level") == "error":
                m = msg["message"]
                spans = m.get("spans", [])
                if spans:
                    span = spans[0]
                    errors.append(f"{span['file_name']}:{span['line_start']} - {m['message']}")
                else:
                    errors.append(m["message"])
        except Exception:
            pass

    with open(
        "c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/errors.txt", "w", encoding="utf-8"
    ) as f:
        for e in errors:
            f.write(e + "\n")
    print(f"Wrote {len(errors)} errors to errors.txt")


if __name__ == "__main__":
    main()
