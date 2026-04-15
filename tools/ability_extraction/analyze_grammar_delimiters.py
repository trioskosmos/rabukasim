#!/usr/bin/env python3
"""
Analyze grammar delimiter usage patterns in abilities.
"""

import json
import re
from collections import Counter, defaultdict

# Load the raw cards data
with open('data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Collect all ability texts
ability_texts = []
for card_id, card_data in cards.items():
    if 'ability' in card_data and card_data['ability']:
        ability_texts.append(card_data['ability'])

print(f"Total abilities found: {len(ability_texts)}")

# Analyze delimiter usage
delimiters = {
    '：': 'colon',
    '、': 'comma', 
    '。': 'period',
    '（': 'open_paren',
    '）': 'close_paren',
    '「': 'open_quote',
    '」': 'close_quote'
}

# Count delimiter occurrences
delimiter_counts = Counter()
for text in ability_texts:
    for delim in delimiters:
        delimiter_counts[delim] += text.count(delim)

print("\nDelimiter counts:")
for delim, name in delimiters.items():
    print(f"  {delim} ({name}): {delimiter_counts[delim]}")

# Analyze context around each delimiter
delimiter_contexts = defaultdict(list)

for text in ability_texts:
    for delim in delimiters:
        # Find all occurrences and capture context
        for match in re.finditer(re.escape(delim), text):
            start = max(0, match.start() - 10)
            end = min(len(text), match.end() + 10)
            context = text[start:end]
            delimiter_contexts[delim].append(context)

print("\n\n=== DELIMITER CONTEXT ANALYSIS ===\n")

for delim, name in delimiters.items():
    print(f"\n{delim} ({name}) - {delimiter_counts[delim]} occurrences:")
    print(f"  Sample contexts:")
    for i, ctx in enumerate(delimiter_contexts[delim][:10], 1):
        print(f"    {i}. ...{ctx}...")
    if len(delimiter_contexts[delim]) > 10:
        print(f"    ... and {len(delimiter_contexts[delim]) - 10} more")

# Analyze quote patterns specifically
print("\n\n=== QUOTE PATTERN ANALYSIS ===\n")

quote_patterns = []
for text in ability_texts:
    if '「' in text and '」' in text:
        # Find quoted content
        matches = re.findall(r'「(.*?)」', text)
        for match in matches:
            quote_patterns.append(match)

print(f"Total quoted segments: {len(quote_patterns)}")
print(f"\nSample quoted content:")
for i, quote in enumerate(quote_patterns[:20], 1):
    print(f"  {i}. 「{quote}」")

# Categorize quote content
quote_categories = {
    'character_name': 0,
    'ability': 0,
    'other': 0
}

for quote in quote_patterns:
    if re.match(r'^[^\s]+$', quote) and len(quote) <= 10:
        # Likely a character name (short, no spaces)
        quote_categories['character_name'] += 1
    elif any(keyword in quote for keyword in ['ライブ', 'スコア', 'アクティブ', 'ウェイト', '引く', '加える']):
        # Contains ability keywords
        quote_categories['ability'] += 1
    else:
        quote_categories['other'] += 1

print(f"\nQuote content categories:")
for category, count in quote_categories.items():
    print(f"  {category}: {count}")

# Analyze parenthetical patterns
print("\n\n=== PARENTHETICAL PATTERN ANALYSIS ===\n")

paren_patterns = []
for text in ability_texts:
    if '（' in text and '）' in text:
        matches = re.findall(r'（(.*?)）', text)
        for match in matches:
            paren_patterns.append(match)

print(f"Total parenthetical segments: {len(paren_patterns)}")
print(f"\nSample parenthetical content:")
for i, paren in enumerate(paren_patterns[:20], 1):
    print(f"  {i}. （{paren}）")

# Analyze colon patterns
print("\n\n=== COLON PATTERN ANALYSIS ===\n")

colon_contexts = []
for text in ability_texts:
    if '：' in text:
        matches = re.finditer(r'：', text)
        for match in matches:
            # Get 20 chars before and after
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end]
            colon_contexts.append(context)

print(f"Total colon occurrences: {len(colon_contexts)}")
print(f"\nSample colon contexts:")
for i, ctx in enumerate(colon_contexts[:15], 1):
    print(f"  {i}. ...{ctx}...")

# Check what comes before colons
before_colon = []
for ctx in colon_contexts:
    colon_idx = ctx.find('：')
    before = ctx[:colon_idx].strip()
    if before:
        before_colon.append(before[-20:] if len(before) > 20 else before)

print(f"\nWhat comes before colons (last 20 chars):")
from collections import Counter
before_counter = Counter(before_colon)
for item, count in before_counter.most_common(10):
    print(f"  {count}x: ...{item}")

# Check what comes after colons
after_colon = []
for ctx in colon_contexts:
    colon_idx = ctx.find('：')
    after = ctx[colon_idx+1:].strip()
    if after:
        after_colon.append(after[:20] if len(after) > 20 else after)

print(f"\nWhat comes after colons (first 20 chars):")
after_counter = Counter(after_colon)
for item, count in after_counter.most_common(10):
    print(f"  {count}x: {item}...")
