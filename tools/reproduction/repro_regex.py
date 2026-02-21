import re

text = "自分のデッキの上からカードを3枚見る"
pattern = r"(?:デッキ|山札).*?(\d+)枚.*?(?:見る|見て)"

match = re.search(pattern, text)
print(f"Text: '{text}'")
print(f"Pattern: '{pattern}'")
if match:
    print(f"MATCH: {match.group(0)}")
    print(f"Group 1: {match.group(1)}")
else:
    print("NO MATCH")
