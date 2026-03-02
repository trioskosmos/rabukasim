import json
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding="utf-8")

# We want to check the neighborhood of Shizuku to see if indices slipped
# Index of PL!N-bp4-018-N in cards.json is ~361
TARGET_ID = "PL!N-bp4-018-N"


def compare_neighborhood():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)
    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        pseudo = json.load(f)

    keys = list(cards.keys())
    try:
        idx = keys.index(TARGET_ID)
    except ValueError:
        print(f"Error: {TARGET_ID} not found in cards.json")
        return

    # Check 5 cards before and after
    range_indices = range(max(0, idx - 5), min(len(keys), idx + 6))

    with open("shizuku_comparison.txt", "w", encoding="utf-8") as out:
        out.write(f"--- COMPARISON AROUND {TARGET_ID} ---\n\n")
        for i in range_indices:
            cid = keys[i]
            card_text = cards[cid].get("ability", "N/A")
            p_data = pseudo.get(cid, {})
            p_text = p_data.get("pseudocode", "NONE")

            out.write(f"[{cid}]\n")
            out.write(f"TEXT:   {card_text}\n")
            out.write(f"PSEUDO: {p_text}\n")
            out.write("-" * 50 + "\n")

    print("Comparison written to shizuku_comparison.txt")


if __name__ == "__main__":
    compare_neighborhood()
