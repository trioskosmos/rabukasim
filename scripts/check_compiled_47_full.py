#!/usr/bin/env python3
"""Check full compiled card 47 data"""
import json

with open('data/cards_compiled.json', encoding='utf-8') as f:
    compiled = json.load(f)

live_db = compiled.get('live_db', {})
card_47 = live_db.get('47')
if card_47:
    print("Card 47 full data:")
    print(json.dumps(card_47, ensure_ascii=False, indent=2))
