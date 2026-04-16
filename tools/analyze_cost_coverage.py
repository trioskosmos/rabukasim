#!/usr/bin/env python3
"""
Analyze cost extraction coverage.
Compares structured cost outputs to raw cost text to see how general the extraction is.

This script reads: ../data/abilities_extracted_from_cards.json
"""

import json
from collections import defaultdict

def get_raw_cost(text):
    """Extract raw cost text before colon."""
    if '：' not in text and ':' not in text:
        return None
    raw = text.split('：')[0] if '：' in text else text.split(':')[0]
    return raw.strip() if raw.strip() else None

def main():
    with open('../data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    categories = {
        'structured': [],
        'raw_fallback': [],
        'no_cost': [],
        'null_cost': []
    }
    
    for ab in data['unique_abilities']:
        raw_cost = get_raw_cost(ab['triggerless_text'])
        cost = ab.get('cost')
        
        if raw_cost is None:
            categories['no_cost'].append({
                'full_text': ab['full_text'],
                'triggerless_text': ab['triggerless_text'],
                'card_count': ab['card_count']
            })
        elif cost is None:
            categories['null_cost'].append({
                'full_text': ab['full_text'],
                'triggerless_text': ab['triggerless_text'],
                'raw_cost': raw_cost,
                'card_count': ab['card_count']
            })
        elif isinstance(cost, str):
            categories['raw_fallback'].append({
                'full_text': ab['full_text'],
                'triggerless_text': ab['triggerless_text'],
                'raw_cost': raw_cost,
                'cost': cost,
                'card_count': ab['card_count']
            })
        elif isinstance(cost, dict):
            categories['structured'].append({
                'full_text': ab['full_text'],
                'triggerless_text': ab['triggerless_text'],
                'raw_cost': raw_cost,
                'cost': cost,
                'card_count': ab['card_count']
            })
    
    total = len(data['unique_abilities'])
    
    print("=== Cost Extraction Coverage Analysis ===\n")
    print(f"Total abilities: {total}")
    print(f"\nStructured costs: {len(categories['structured'])} ({len(categories['structured'])/total*100:.1f}%)")
    print(f"Raw fallback costs: {len(categories['raw_fallback'])} ({len(categories['raw_fallback'])/total*100:.1f}%)")
    print(f"Null costs (has raw): {len(categories['null_cost'])} ({len(categories['null_cost'])/total*100:.1f}%)")
    print(f"No cost (no colon): {len(categories['no_cost'])} ({len(categories['no_cost'])/total*100:.1f}%)")
    
    print("\n=== Structured Cost Examples (first 10) ===")
    for i, item in enumerate(categories['structured'][:10]):
        print(f"\n{i+1}. Raw: {item['raw_cost']}")
        print(f"   Structured: {item['cost']}")
        print(f"   Cards: {item['card_count']}")
    
    print("\n=== Raw Fallback Examples (first 10) ===")
    for i, item in enumerate(categories['raw_fallback'][:10]):
        print(f"\n{i+1}. Raw: {item['raw_cost']}")
        print(f"   Fallback: {item['cost']}")
        print(f"   Cards: {item['card_count']}")
    
    print("\n=== Null Cost Examples (first 10) ===")
    for i, item in enumerate(categories['null_cost'][:10]):
        print(f"\n{i+1}. Raw: {item['raw_cost']}")
        print(f"   Cost: null")
        print(f"   Cards: {item['card_count']}")
    
    # Count cost types
    cost_types = defaultdict(int)
    for item in categories['structured']:
        for key in item['cost'].keys():
            cost_types[key] += 1
    
    print("\n=== Cost Type Distribution ===")
    for cost_type, count in sorted(cost_types.items(), key=lambda x: -x[1]):
        print(f"{cost_type}: {count}")

if __name__ == "__main__":
    main()
