#!/usr/bin/env python3
"""
Show what structured cost breakdown would look like for ability extraction.
"""

import json
from pathlib import Path


def parse_cost_structure(cost_text):
    """Parse cost text into structured format."""
    cost = {}
    
    # Energy cost
    energy_count = cost_text.count('{icon_energy.png|E}')
    if energy_count > 0:
        cost['energy'] = energy_count
    
    # Card discard
    if '控え室に置く' in cost_text or '控え室に置いてもよい' in cost_text:
        discard_info = {}
        if '手札' in cost_text:
            discard_info['source'] = 'hand'
        elif 'デッキ' in cost_text:
            discard_info['source'] = 'deck'
        elif 'ステージから' in cost_text:
            discard_info['source'] = 'stage'
        
        # Card type
        if 'ライブカード' in cost_text:
            discard_info['card_type'] = 'live'
        elif 'メンバーカード' in cost_text:
            discard_info['card_type'] = 'member'
        elif 'カード' in cost_text:
            discard_info['card_type'] = 'any'
        
        # Group/character restrictions
        if 'Liella' in cost_text:
            discard_info['group'] = 'Liella'
        elif "μ's" in cost_text:
            discard_info['group'] = "μ's"
        elif 'Aqours' in cost_text:
            discard_info['group'] = 'Aqours'
        elif '虹ヶ咲' in cost_text:
            discard_info['group'] = '虹ヶ咲'
        
        # Cost condition
        if 'コスト' in cost_text and '以下' in cost_text:
            discard_info['cost_condition'] = '<=4'  # simplified example
        elif 'コスト' in cost_text:
            discard_info['cost_condition'] = 'specific'
        
        # Optional
        if 'でもよい' in cost_text or '支払ってもよい' in cost_text:
            discard_info['optional'] = True
        
        if discard_info:
            cost['card_discard'] = discard_info
    
    # Member movement
    if 'ウェイトにする' in cost_text or 'ウェイトにしてもよい' in cost_text:
        member_info = {}
        if 'このメンバー' in cost_text:
            member_info['target'] = 'this_member'
        elif 'メンバー' in cost_text:
            member_info['target'] = 'member'
        
        if 'でもよい' in cost_text:
            member_info['optional'] = True
        
        if member_info:
            cost['member_to_wait'] = member_info
    
    # Card reveal
    if '公開' in cost_text:
        reveal_info = {}
        if '手札' in cost_text:
            reveal_info['source'] = 'hand'
        
        if 'でもよい' in cost_text:
            reveal_info['optional'] = True
        
        if reveal_info:
            cost['card_reveal'] = reveal_info
    
    return cost


def show_structured_examples():
    """Show examples of structured cost breakdown."""
    
    # Load abilities
    abilities_file = Path("data/abilities_extracted_from_cards.json")
    with open(abilities_file, encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data["unique_abilities"]
    
    # Find abilities with interesting cost structures
    examples = []
    
    for ability in abilities:
        triggerless = ability["triggerless_text"]
        if '：' in triggerless:
            cost_text = triggerless.split('：')[0].strip()
            if cost_text and len(cost_text) > 10:  # meaningful cost
                structured_cost = parse_cost_structure(cost_text)
                if structured_cost:
                    examples.append({
                        "cost_text": cost_text,
                        "structured_cost": structured_cost,
                        "full_text": ability["full_text"],
                        "card_count": ability["card_count"]
                    })
        
        if len(examples) >= 10:
            break
    
    print("=== Structured Cost Breakdown Examples ===\n")
    
    for i, example in enumerate(examples[:5]):
        print(f"Example {i+1}:")
        print(f"  Cost text: {example['cost_text']}")
        print(f"  Structured cost: {json.dumps(example['structured_cost'], ensure_ascii=False, indent=4)}")
        print(f"  Full ability: {example['full_text']}")
        print(f"  Card count: {example['card_count']}")
        print()
    
    # Show what the final ability structure would look like
    print("=== Final Ability Structure Example ===\n")
    
    example_ability = {
        "full_text": "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：自分の控え室から『Liella!』のライブカードを1枚手札に加える。",
        "triggerless_text": "{{icon_energy.png|E}}{{icon_energy.png|E}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：自分の控え室から『Liella!』のライブカードを1枚手札に加える。",
        "cost": {
            "energy": 2,
            "card_discard": {
                "source": "hand",
                "card_type": "member",
                "group": "Liella",
                "cost_condition": "<=4",
                "count": 1
            }
        },
        "effect_text": "自分の控え室から『Liella!』のライブカードを1枚手札に加える。",
        "triggers": ["起動"],
        "use_limit": None,
        "card_count": 4,
        "card_examples": ["PL!SP-bp1-003-R+ | 嵐 千砂都 (ab#0)"]
    }
    
    print(json.dumps(example_ability, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    show_structured_examples()
