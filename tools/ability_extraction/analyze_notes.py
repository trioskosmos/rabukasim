"""Analyze all abilities with 'note' actions to understand why they parse as notes."""
import json
import re
from collections import Counter, defaultdict

def find_note_actions(data):
    """Find all abilities with note actions."""
    note_abilities = []
    
    for ability in data.get('unique_abilities', []):
        full_text = ability.get('full_text', '')
        triggerless_text = ability.get('triggerless_text', '')
        effect = ability.get('effect')
        
        if not effect:
            continue
            
        # Check if effect has actions
        actions = effect.get('actions', [])
        if not actions:
            continue
            
        # Check if any action is a "note"
        note_actions = []
        for action in actions:
            if isinstance(action, dict) and action.get('action') == 'note':
                note_actions.append(action)
        
        if note_actions:
            note_abilities.append({
                'full_text': full_text,
                'triggerless_text': triggerless_text,
                'costless_text': ability.get('costless_text', ''),
                'effect_text': effect.get('text', ''),
                'note_actions': note_actions,
                'cost': ability.get('cost'),
                'triggers': ability.get('triggers'),
                'card_count': ability.get('card_count', 0)
            })
    
    return note_abilities

def categorize_notes(note_abilities):
    """Categorize note actions by their text patterns."""
    categories = defaultdict(list)
    
    for ability in note_abilities:
        for note_action in ability['note_actions']:
            note_text = note_action.get('text', '')
            
            # Categorize based on patterns
            if 'ウェイトにする' in note_text:
                categories['wait_tap'].append(ability)
            elif '引く' in note_text or '手札に加える' in note_text:
                categories['draw_add'].append(ability)
            elif '控え室に置く' in note_text:
                categories['discard'].append(ability)
            elif '登場' in note_text:
                categories['deploy'].append(ability)
            elif 'アクティブ' in note_text:
                categories['activate'].append(ability)
            elif '(' in note_text or '（' in note_text:
                categories['parenthetical'].append(ability)
            elif '場合' in note_text or 'とき' in note_text:
                categories['conditional'].append(ability)
            else:
                categories['other'].append(ability)
            break  # Only categorize once per ability
    
    return categories

def main():
    with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    note_abilities = find_note_actions(data)
    categories = categorize_notes(note_abilities)
    
    print(f"Total abilities with note actions: {len(note_abilities)}")
    print(f"Total unique abilities: {len(data.get('unique_abilities', []))}")
    print(f"Percentage: {len(note_abilities) / len(data.get('unique_abilities', [])) * 100:.1f}%")
    print()
    
    print("Categories:")
    for category, abilities in categories.items():
        print(f"  {category}: {len(abilities)}")
    print()
    
    # Show examples from each category
    print("=" * 80)
    print("EXAMPLES BY CATEGORY")
    print("=" * 80)
    
    for category, abilities in categories.items():
        print(f"\n{category.upper()} ({len(abilities)} abilities):")
        print("-" * 80)
        
        # Show first 3 examples
        for i, ability in enumerate(abilities[:3]):
            print(f"\nExample {i+1}:")
            print(f"  Full text: {ability['full_text'][:200]}...")
            print(f"  Note text: {ability['note_actions'][0].get('text', '')[:200]}...")
            print(f"  Card count: {ability['card_count']}")
            print(f"  Cost: {ability['cost']}")
    
    # Save full list to file
    with open('note_abilities_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(note_abilities, f, indent=2, ensure_ascii=False)
    
    print(f"\nFull analysis saved to: note_abilities_analysis.json")

if __name__ == '__main__':
    main()
