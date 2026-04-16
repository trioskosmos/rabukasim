#!/usr/bin/env python3
"""
Analyze colon patterns in ability triggerless_text.
Categorize patterns before and after the colon.
"""

import json
from collections import defaultdict, Counter
from pathlib import Path


def analyze_colon_patterns():
    """Analyze patterns before and after colons in abilities."""
    
    # Load abilities
    abilities_file = Path("data/abilities_extracted_from_cards.json")
    with open(abilities_file, encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data["unique_abilities"]
    
    # Filter abilities with colons
    with_colon = []
    without_colon = []
    
    for ability in abilities:
        triggerless = ability["triggerless_text"]
        if '：' in triggerless:
            with_colon.append(ability)
        else:
            without_colon.append(ability)
    
    print(f"=== Colon Analysis ===")
    print(f"Total abilities: {len(abilities)}")
    print(f"With colon: {len(with_colon)}")
    print(f"Without colon: {len(without_colon)}")
    print()
    
    # Analyze before colon patterns
    before_colon_patterns = Counter()
    before_colon_examples = defaultdict(list)
    
    for ability in with_colon:
        triggerless = ability["triggerless_text"]
        before = triggerless.split('：')[0].strip()
        
        # Extract key patterns
        if '支払ってもよい' in before:
            pattern = 'may_pay'
        elif '支払う' in before:
            pattern = 'must_pay'
        elif '置く' in before:
            pattern = 'place'
        elif '控え室に置く' in before:
            pattern = 'send_to_waitroom'
        elif '手札に加える' in before:
            pattern = 'add_to_hand'
        elif '引く' in before:
            pattern = 'draw'
        elif '捨てる' in before:
            pattern = 'discard'
        elif '選ぶ' in before:
            pattern = 'choose'
        elif '公開する' in before:
            pattern = 'reveal'
        elif 'シャッフル' in before:
            pattern = 'shuffle'
        elif 'アクティブにする' in before:
            pattern = 'activate'
        elif 'ウェイトにする' in before:
            pattern = 'wait'
        elif '得る' in before:
            pattern = 'gain'
        elif '失う' in before:
            pattern = 'lose'
        elif before.startswith('{{icon_energy'):
            pattern = 'energy_only'
        elif before.startswith('{{heart'):
            pattern = 'heart_only'
        elif before.startswith('{{icon_blade'):
            pattern = 'blade_only'
        elif before.startswith('{{icon_score'):
            pattern = 'score_only'
        else:
            pattern = 'other'
        
        before_colon_patterns[pattern] += 1
        if len(before_colon_examples[pattern]) < 3:
            before_colon_examples[pattern].append({
                "before": before,
                "full": triggerless,
                "card_count": ability["card_count"]
            })
    
    print("=== Before Colon Patterns ===")
    for pattern, count in before_colon_patterns.most_common():
        print(f"{pattern}: {count}")
        examples = before_colon_examples[pattern]
        for ex in examples[:2]:
            print(f"  Example: {ex['before']}")
    print()
    
    # Analyze after colon patterns
    after_colon_patterns = Counter()
    after_colon_examples = defaultdict(list)
    
    for ability in with_colon:
        triggerless = ability["triggerless_text"]
        after = triggerless.split('：')[1].strip()
        
        # Extract key patterns
        if 'カードを' in after and '引く' in after:
            pattern = 'draw_cards'
        elif '手札に加える' in after:
            pattern = 'add_to_hand'
        elif '控え室に置く' in after:
            pattern = 'send_to_waitroom'
        elif 'ステージに置く' in after:
            pattern = 'place_on_stage'
        elif '得る' in after:
            pattern = 'gain'
        elif '失う' in after:
            pattern = 'lose'
        elif 'アクティブにする' in after:
            pattern = 'activate'
        elif 'ウェイトにする' in after:
            pattern = 'wait'
        elif '選ぶ' in after:
            pattern = 'choose'
        elif '見る' in after:
            pattern = 'look_at'
        elif '場合' in after:
            pattern = 'conditional'
        elif 'とき' in after:
            pattern = 'timing'
        elif 'ライブ終了時まで' in after:
            pattern = 'until_live_end'
        elif 'このターン' in after:
            pattern = 'this_turn'
        elif '得る。」を得る' in after:
            pattern = 'gain_ability'
        else:
            pattern = 'other'
        
        after_colon_patterns[pattern] += 1
        if len(after_colon_examples[pattern]) < 3:
            after_colon_examples[pattern].append({
                "after": after,
                "full": triggerless,
                "card_count": ability["card_count"]
            })
    
    print("=== After Colon Patterns ===")
    for pattern, count in after_colon_patterns.most_common():
        print(f"{pattern}: {count}")
        examples = after_colon_examples[pattern]
        for ex in examples[:2]:
            print(f"  Example: {ex['after']}")
    print()
    
    # Analyze abilities without colons
    without_colon_patterns = Counter()
    without_colon_examples = defaultdict(list)
    
    for ability in without_colon:
        triggerless = ability["triggerless_text"]
        
        # Extract key patterns
        if 'カードを' in triggerless and '引く' in triggerless:
            pattern = 'draw_cards'
        elif '手札に加える' in triggerless:
            pattern = 'add_to_hand'
        elif '控え室に置く' in triggerless:
            pattern = 'send_to_waitroom'
        elif 'ステージに置く' in triggerless:
            pattern = 'place_on_stage'
        elif '得る' in triggerless:
            pattern = 'gain'
        elif '失う' in triggerless:
            pattern = 'lose'
        elif 'アクティブにする' in triggerless:
            pattern = 'activate'
        elif 'ウェイトにする' in triggerless:
            pattern = 'wait'
        elif '場合' in triggerless:
            pattern = 'conditional'
        elif 'とき' in triggerless:
            pattern = 'timing'
        elif 'ライブ終了時まで' in triggerless:
            pattern = 'until_live_end'
        else:
            pattern = 'other'
        
        without_colon_patterns[pattern] += 1
        if len(without_colon_examples[pattern]) < 3:
            without_colon_examples[pattern].append({
                "text": triggerless,
                "card_count": ability["card_count"]
            })
    
    print("=== Without Colon Patterns ===")
    for pattern, count in without_colon_patterns.most_common():
        print(f"{pattern}: {count}")
        examples = without_colon_examples[pattern]
        for ex in examples[:2]:
            print(f"  Example: {ex['text']}")
    print()
    
    # Save detailed analysis
    output = {
        "statistics": {
            "total": len(abilities),
            "with_colon": len(with_colon),
            "without_colon": len(without_colon)
        },
        "before_colon_patterns": dict(before_colon_patterns),
        "before_colon_examples": dict(before_colon_examples),
        "after_colon_patterns": dict(after_colon_patterns),
        "after_colon_examples": dict(after_colon_examples),
        "without_colon_patterns": dict(without_colon_patterns),
        "without_colon_examples": dict(without_colon_examples)
    }
    
    output_file = Path("data/colon_pattern_analysis.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Detailed analysis saved to {output_file}")


if __name__ == "__main__":
    analyze_colon_patterns()
