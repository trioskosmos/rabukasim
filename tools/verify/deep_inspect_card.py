import json
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

CARD_IDS = [
    "PL!N-bp1-003-R＋", "PL!N-bp1-003-P＋", "PL!N-bp1-003-SEC",
    "PL!N-sd1-001-SD", "PL!N-sd1-009-SD",
    "PL!HS-bp1-003-R＋", "PL!HS-bp1-003-P＋", "PL!HS-bp1-003-SEC",
    "PL!N-pb1-003-R", "PL!N-pb1-003-P＋",
    "PL!N-bp1-012-P＋", "PL!N-bp1-012-SEC",
    "PL!HS-PR-014-PR", "PL!SP-bp1-010-R", "PL!N-pb1-002-R"
]

def deep_inspect():
    with open("deep_inspect_dump.txt", "w", encoding="utf-8") as out:
        for cid in CARD_IDS:
            out.write(f"=== {cid} ===\n")
            # 1. Source Text
            out.write("--- 📜 SOURCE TEXT ---\n")
            try:
                with open("data/cards.json", "r", encoding="utf-8") as f:
                    cards = json.load(f)
                    card_data = cards.get(cid, {})
                    out.write(card_data.get("ability", "N/A"))
            except Exception as e:
                out.write(f"Error: {e}")
            out.write("\n\n")

            # 2. Manual Pseudocode
            out.write("--- ✍️ MANUAL PSEUDOCODE ---\n")
            try:
                with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
                    pseudo = json.load(f)
                    p_entry = pseudo.get(cid, {})
                    out.write(p_entry.get("pseudocode", "N/A"))
            except Exception as e:
                out.write(f"Error: {e}")
            out.write("\n\n\n")

            # 3. Compiled Logic
            out.write("--- ⚙️ COMPILED BYTECODE ---\n")
            try:
                with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
                    compiled = json.load(f)
                    c_entry = compiled.get(cid, {})
                    out.write(json.dumps(c_entry.get("ability"), indent=2, ensure_ascii=False))
            except Exception as e:
                out.write(f"Error: {e}")
            out.write("\n\n")

    print("Dump written to deep_inspect_dump.txt")

if __name__ == "__main__":
    deep_inspect()
