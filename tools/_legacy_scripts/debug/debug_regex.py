import re

with open("card_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

print(f"Original Text Length: {len(text)}")
text = text.replace("<br>", "\n")
blocks = re.split(r"\\n|\n", text)
print(f"Blocks: {len(blocks)}")

block = blocks[0].strip()
print(f"Block 0 Length: {len(block)}")

sentences = [s.strip() for s in re.split(r"。\s*", block) if s.strip()]
print(f"Sentences: {len(sentences)}")

line = sentences[0]
print(f"Sentence 0: ...{line[-30:]}...")  # End of sentence

full_content = re.sub(r"（.*?）|\(.*?\)", "", line)
print(f"Full Content: ...{full_content[-30:]}...")

print(f"Pay in Line: {'払' in line}")
print(f"Pay in Full Content: {'払' in full_content}")
