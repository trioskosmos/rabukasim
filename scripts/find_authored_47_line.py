#!/usr/bin/env python3
"""Find the line number of card 47 in authored frame source"""
with open('data/ability_frame_source_authored.json', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'PL!-bp3-024-L' in line:
            print(f"Line {i}: {line.strip()}")
