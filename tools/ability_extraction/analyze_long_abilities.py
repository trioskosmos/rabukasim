#!/usr/bin/env python3
"""
Script to display the top 20 longest abilities for manual analysis.
Outputs abilities with space for manual assessment of structural patterns.
"""

import json
from pathlib import Path

def load_abilities():
    """Load abilities from the extracted abilities JSON file."""
    abilities_file = Path("data/abilities_extracted_from_cards.json")
    with open(abilities_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['unique_abilities']

def get_top_longest_abilities(abilities, n=20):
    """Get the n longest abilities by effect text length."""
    # Sort by effect text length (descending)
    sorted_abilities = sorted(
        abilities,
        key=lambda x: len(x.get('effect', '')),
        reverse=True
    )
    return sorted_abilities[:n]

def analyze_ability_structure(effect_text):
    """
    Analyze the structure of an ability effect.
    Returns a structured breakdown.
    """
    structure = {
        'has_cost': '：' in effect_text,
        'has_periods': '。' in effect_text,
        'has_commas': '、' in effect_text,
        'has_parentheses': '（' in effect_text or '(' in effect_text,
        'has_conditions': '場合' in effect_text or '時' in effect_text,
        'has_optional': 'てもよい' in effect_text or 'まで' in effect_text,
        'has_choices': '選ぶ' in effect_text or '好きな' in effect_text,
        'period_count': effect_text.count('。'),
        'comma_count': effect_text.count('、'),
        'length': len(effect_text)
    }
    return structure

def display_ability_with_analysis(ability, index):
    """Display an ability with structural analysis and space for manual assessment."""
    effect = ability.get('effect', '')
    full_text = ability.get('full_text', '')
    triggers = ability.get('triggers', [])
    card_count = ability.get('card_count', 0)
    
    structure = analyze_ability_structure(effect)
    
    print(f"\n{'='*80}")
    print(f"ABILITY #{index + 1}")
    print(f"{'='*80}")
    print(f"Full Text: {full_text}")
    print(f"Triggers: {triggers}")
    print(f"Card Count: {card_count}")
    print(f"Effect Length: {structure['length']} characters")
    print(f"\nEffect: {effect}")
    print(f"\n--- AUTOMATED STRUCTURE ANALYSIS ---")
    print(f"Has Cost (：): {structure['has_cost']}")
    print(f"Has Periods (。): {structure['has_periods']} (count: {structure['period_count']})")
    print(f"Has Commas (、): {structure['has_commas']} (count: {structure['comma_count']})")
    print(f"Has Parentheses: {structure['has_parentheses']}")
    print(f"Has Conditions (場合/時): {structure['has_conditions']}")
    print(f"Has Optional (てもよい/まで): {structure['has_optional']}")
    print(f"Has Choices (選ぶ/好きな): {structure['has_choices']}")
    print(f"\n--- MANUAL ASSESSMENT ---")
    print(f"[Break points: _________________]")
    print(f"[Action sequence: _________________]")
    print(f"[Conditions: _________________]")
    print(f"[Player decisions: _________________]")
    print(f"[Automatic actions: _________________]")
    print(f"[Notes: _________________]")

def main():
    """Main function to display top 20 longest abilities."""
    output_file = Path("ability_analysis_output.txt")
    
    print("Loading abilities...")
    abilities = load_abilities()
    
    print(f"Total abilities: {len(abilities)}")
    print("Finding top 20 longest abilities by effect text length...")
    
    top_abilities = get_top_longest_abilities(abilities, 20)
    
    print(f"\nWriting analysis to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"TOP {len(top_abilities)} LONGEST ABILITIES - MANUAL ANALYSIS\n")
        f.write(f"{'='*80}\n\n")
        
        for i, ability in enumerate(top_abilities):
            # Capture the output
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            display_ability_with_analysis(ability, i)
            sys.stdout = old_stdout
            output = buffer.getvalue()
            f.write(output + "\n")
        
        f.write(f"\n{'='*80}\n")
        f.write("Analysis complete. Review the manual assessment sections above.\n")
        f.write(f"{'='*80}\n")
    
    print(f"Analysis complete. Output written to {output_file}")

if __name__ == "__main__":
    main()
