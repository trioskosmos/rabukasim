text = "好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。"
keyword = "下に置"
print(f"Text: {text}")
print(f"Keyword: {keyword}")
print(f"Match: {keyword in text}")

text2 = "デッキの一番下に置く"
print(f"Control Text: {text2}")
print(f"Control Match: {keyword in text2}")
