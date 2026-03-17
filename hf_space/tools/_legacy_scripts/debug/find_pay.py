with open("card_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("払")
if idx != -1:
    start = max(0, idx - 20)
    end = min(len(text), idx + 20)
    print(f"Context: ...{text[start:end]}...")
    print(f"At index: {idx}")
else:
    print("Not found")
