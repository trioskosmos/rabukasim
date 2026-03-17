#!/usr/bin/env python3
"""Analyze deck composition and show card statistics."""

import sys
import json
from pathlib import Path
from collections import Counter

def load_deck_file(deck_path):
    """Load a deck file and parse it."""
    with open(deck_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    cards = []
    for line in lines:
        if line:
            cards.append(int(line))
    return cards

def load_card_database(db_path="data/cards_vanilla_compiled.json"):
    """Load vanilla card database."""
    with open(db_path, 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def analyze_deck(deck_path, db):
    """Analyze deck composition."""
    cards = load_deck_file(deck_path)
    card_counts = Counter(cards)
    
    members = []
    lives = []
    
    for cid, count in sorted(card_counts.items()):
        card = db.get(cid, {})
        card_type = card.get('type', 'unknown')
        name = card.get('name', f'Card {cid}')
        
        if card_type == 'member':
            hearts = card.get('blade_hearts', [0]*7)
            hearts_str = ','.join(str(h) for h in hearts[:6]) if hearts else 'None'
            members.append({
                'id': cid,
                'name': name,
                'count': count,
                'hearts': hearts_str,
                'cost': card.get('cost', 0),
                'blades': card.get('blades', 0),
            })
        elif card_type == 'live':
            required = card.get('required_hearts', [0]*7)
            req_str = ','.join(str(h) for h in required[:6]) if required else 'None'
            lives.append({
                'id': cid,
                'name': name,
                'count': count,
                'score': card.get('score', 0),
                'required': req_str,
            })
    
    return {
        'deck_file': str(deck_path),
        'total_cards': len(cards),
        'unique_cards': len(card_counts),
        'members': members,
        'lives': lives,
    }

def print_deck_analysis(analysis):
    """Print deck analysis in human-readable format."""
    print(f"\n{'='*80}")
    print(f"DECK ANALYSIS: {analysis['deck_file']}")
    print(f"{'='*80}")
    print(f"Total Cards: {analysis['total_cards']} | Unique: {analysis['unique_cards']}")
    
    print(f"\n{'-'*80}")
    print("MEMBERS:")
    print(f"{'ID':<6} {'Name':<30} {'Qty':<3} {'Hearts (RGBPWCY)':<20} {'Cost':<5} {'Blades':<5}")
    print(f"{'-'*80}")
    for m in analysis['members']:
        print(f"{m['id']:<6} {m['name'][:30]:<30} {m['count']:<3} {m['hearts']:<20} {m['cost']:<5} {m['blades']:<5}")
    
    print(f"\n{'-'*80}")
    print("LIVE CARDS (Requirements):")
    print(f"{'ID':<6} {'Name':<30} {'Qty':<3} {'Score':<6} {'Required Hearts (RGBPWCY)':<25}")
    print(f"{'-'*80}")
    for l in analysis['lives']:
        print(f"{l['id']:<6} {l['name'][:30]:<30} {l['count']:<3} {l['score']:<6} {l['required']:<25}")
    print(f"{'-'*80}\n")

if __name__ == '__main__':
    # Default deck path
    deck_path = Path("ai/decks/liella_cup.txt")
    
    # Load database
    try:
        db = load_card_database()
    except FileNotFoundError:
        print(f"ERROR: Cannot find card database at data/cards_vanilla_compiled.json")
        sys.exit(1)
    
    # Analyze and print
    try:
        analysis = analyze_deck(deck_path, db)
        print_deck_analysis(analysis)
        
        # Print summary statistics
        member_hearts_by_color = [0] * 6
        for m in analysis['members']:
            hearts = [int(h) for h in m['hearts'].split(',')]
            for i, h in enumerate(hearts):
                member_hearts_by_color[i] += h * m['count']
        
        print(f"Total Member Hearts by Color (R/G/B/P/W/C):")
        for i, h in enumerate(member_hearts_by_color):
            colors = ['Red', 'Green', 'Blue', 'Purple', 'White', 'Colorless']
            print(f"  {colors[i]}: {h}")
        
        print(f"\nTotal Lives: {len(analysis['lives'])} types, {sum(l['count'] for l in analysis['lives'])} cards")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
