import json
import os


def find_longest_abilities():
    file_path = "data/cards_compiled.json"
    if not os.path.exists(file_path):
        print("Error: data/cards_compiled.json not found")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    # Process members
    for m_id, m in data.get("member_db", {}).items():
        text = m.get("ability_text", "")
        if text:
            results.append(
                {
                    "card_no": m.get("card_no", "Unknown"),
                    "name": m.get("name", "Unknown"),
                    "text": text,
                    "length": len(text),
                    "lines": len(text.split("\n")),
                }
            )

    # Process lives
    for l_id, l in data.get("live_db", {}).items():
        text = l.get("ability_text", "")
        if text:
            results.append(
                {
                    "card_no": l.get("card_no", "Unknown"),
                    "name": l.get("name", "Unknown"),
                    "text": text,
                    "length": len(text),
                    "lines": len(text.split("\n")),
                }
            )

    # Sort by character length
    results.sort(key=lambda x: x["length"], reverse=True)

    with open("tools/longest_abilities.txt", "w", encoding="utf-8") as out:
        out.write("Top 10 Longest Abilities (by char length):\n\n")
        for i, r in enumerate(results[:10]):
            out.write(f"{i + 1}. Card: {r['card_no']} ({r['name']})\n")
            out.write(f"   Length: {r['length']} chars, {r['lines']} lines\n")
            out.write(f"   Text:\n{r['text']}\n---\n\n")


if __name__ == "__main__":
    find_longest_abilities()
