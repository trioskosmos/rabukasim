#!/usr/bin/env python3
"""
Test the batontouch regex against actual batontouch text samples.
"""

import re

# The regex pattern I created
pattern = re.compile(r"([^。]*?)バトンタッチ([^。]*?)場合、([^。]+)")

# Test samples from the earlier analysis
test_samples = [
    "バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える",
    "このメンバーよりコストが低い『スリーズブーケ』のメンバーからバトンタッチして登場した場合、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える",
    "自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを",
    "このメンバーはバトンタッチで控え室に置けない",
    "その後、このメンバーが『Printemps』のメンバーからバトンタッチして登場していないかぎり、手札を1枚控え室に置く",
]

print("Testing batontouch regex pattern:")
print(f"Pattern: {pattern.pattern}")
print()

for i, sample in enumerate(test_samples):
    match = pattern.search(sample)
    if match:
        print(f"Sample {i+1}: MATCHED")
        print(f"  Text: {sample}")
        print(f"  Groups: {match.groups()}")
    else:
        print(f"Sample {i+1}: NOT MATCHED")
        print(f"  Text: {sample}")
    print()
