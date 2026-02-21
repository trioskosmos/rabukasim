import re

text = "自分の成功ライブカード置き場にあるカードを1枚手札に加える"
regex = r"成功ライブカード.*?手札に加"

match = re.search(regex, text)
print(f"Text: {text}")
print(f"Regex: {regex}")
print(f"Match: {match}")
if match:
    print(f"Matched: {match.group(0)}")
