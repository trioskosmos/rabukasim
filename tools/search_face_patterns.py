import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Search for face up/face down patterns
print("Searching for face up/face down patterns:")
count = 0
for skeleton in data.get('skeletons', []):
    for example in skeleton.get('jp_examples', []):
        if '表にする' in example or '裏にする' in example or '表向き' in example or '裏向き' in example:
            print(f"\n{example}")
            count += 1
            if count >= 5:
                break
    if count >= 5:
        break

print(f"\nTotal face patterns found: {count}")

print("\n" + "="*80 + "\n")

# Search for pay energy patterns
print("Searching for pay energy patterns:")
count = 0
for skeleton in data.get('skeletons', []):
    for example in skeleton.get('jp_examples', []):
        if '支払う' in example or '払う' in example:
            print(f"\n{example}")
            count += 1
            if count >= 5:
                break
    if count >= 5:
        break

print(f"\nTotal pay patterns found: {count}")

print("\n" + "="*80 + "\n")

# Search for swap patterns
print("Searching for swap patterns:")
count = 0
for skeleton in data.get('skeletons', []):
    for example in skeleton.get('jp_examples', []):
        if '入れ替える' in example or '交換' in example:
            print(f"\n{example}")
            count += 1
            if count >= 5:
                break
    if count >= 5:
        break

print(f"\nTotal swap patterns found: {count}")

print("\n" + "="*80 + "\n")

# Search for card count comparison patterns
print("Searching for card count comparison patterns:")
count = 0
for skeleton in data.get('skeletons', []):
    for example in skeleton.get('jp_examples', []):
        if '枚以上' in example or '枚以下' in example:
            print(f"\n{example}")
            count += 1
            if count >= 5:
                break
    if count >= 5:
        break

print(f"\nTotal card count comparison patterns found: {count}")
