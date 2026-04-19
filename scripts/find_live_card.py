#!/usr/bin/env python3
"""Find live card in compiled data"""
import json

with open('data/cards_compiled.json', encoding='utf-8') as f:
    data = json.load(f)

live_db = data.get('live_db', {})
for card_no, card_data in live_db.items():
    if 'PL!-bp3-024-L' in card_no or '夏色えがおで1,2,Jump!' in str(card_data):
        print(f"Card: {card_no}")
        print(json.dumps(card_data, ensure_ascii=False, indent=2))
        break
