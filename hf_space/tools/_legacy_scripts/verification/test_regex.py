import re

text = "自分の成功ライブカード置き場にあるカードを1枚手札に加える。"
regex = r"成功ライブカード置き場.*?手札に加"

match = re.search(regex, text)
print(f"Text: {text}")
print(f"Regex: {regex}")
if match:
    print(f"MATCH: {match.group(0)}")
else:
    print("NO MATCH")
