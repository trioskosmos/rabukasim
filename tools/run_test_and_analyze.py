import json
import subprocess


def main():
    print("--- Running Test ---")
    result = subprocess.run(
        ["cargo", "test", "--test", "repro_pb1_018_exhaustive", "--", "--nocapture"],
        cwd="engine_rust_src",
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    with open("reports/test_panic.txt", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    with open("reports/cost2_on_play.txt", "w", encoding="utf-8") as f:
        for cid, c in cards.items():
            if c.get("cost", 99) <= 2:
                for ab in c.get("abilities", []):
                    if ab.get("trigger") == 1 or "ON_PLAY" in ab.get("raw_text", ""):
                        f.write(
                            f"ID: {cid}, Name: {c['name']}, Cost: {c['cost']}, Text: {ab.get('raw_text')[:50]}...\n"
                        )
                        break


if __name__ == "__main__":
    main()
