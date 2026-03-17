with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("LL-PR-004-PR")
if idx != -1:
    print(f"Found at index {idx}")
    start = max(0, idx - 100)
    end = min(len(text), idx + 1000)
    print("--- CONTEXT ---")
    print(text[start:end])
else:
    print("Likely encoding mismatch or file sync issue. Not found in raw text.")
