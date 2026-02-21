import json

with open("card_dump.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    text = data[0]["ability"]

with open("card_text.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("Saved text to card_text.txt")
