#!/usr/bin/env python3
"""Test group_id mapping"""
import sys
sys.path.insert(0, 'tools')

from semantic_to_frame_converter import _group_or_char_id, _group_id

# Test cases
test_cases = [
    ("μ's", "unit"),
    ("μs", "unit"),
    ("Aqours", "unit"),
    ("Liella!", "unit"),
]

for name, group_type in test_cases:
    result = _group_or_char_id(name, group_type)
    print(f"_group_or_char_id({name!r}, {group_type!r}) = {result!r}")

print("\nDirect _group_id tests:")
for name, _ in test_cases:
    result = _group_id(name)
    print(f"_group_id({name!r}) = {result!r}")
