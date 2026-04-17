"""Analyze overflattening issues in abilities_extracted_from_cards.json."""

import json
import re
from collections import defaultdict

def extract_japanese_keywords(text):
    """Extract meaningful Japanese keywords from text."""
    # Remove image tags
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    # Remove punctuation
    text = re.sub(r'[。、：:（）\(\)「」『』]', ' ', text)
    # Split into words
    words = text.split()
    # Filter out empty strings and very short words
    words = [w for w in words if len(w) > 0]
    return words

def analyze_text_coverage(ability):
    """Analyze how much of the text is covered by the parsed structure."""
    full_text = ability['full_text']
    triggerless_text = ability['triggerless_text']
    cost = ability.get('cost')
    effect = ability.get('effect')
    
    issues = []
    
    # Extract keywords from full text
    full_keywords = set(extract_japanese_keywords(full_text))
    
    # Keywords that should be captured by cost
    cost_keywords = set()
    if cost:
        if isinstance(cost, dict):
            # Check for common cost-related keywords
            if cost.get('source'):
                cost_keywords.add('控え室' if cost['source'] == 'waitroom' else '')
                cost_keywords.add('手札' if cost['source'] == 'hand' else '')
                cost_keywords.add('ステージ' if cost['source'] == 'stage' else '')
                cost_keywords.add('デッキ' if 'deck' in cost.get('source', '') else '')
            if cost.get('destination'):
                cost_keywords.add('控え室' if cost['destination'] == 'waitroom' else '')
                cost_keywords.add('手札' if cost['destination'] == 'hand' else '')
                cost_keywords.add('ステージ' if cost['destination'] == 'stage' else '')
                cost_keywords.add('デッキ' if 'deck' in cost.get('destination', '') else '')
            if cost.get('card_type'):
                cost_keywords.add('ライブカード' if cost['card_type'] == 'live_card' else '')
                cost_keywords.add('メンバーカード' if cost['card_type'] == 'member_card' else '')
    
    # Keywords that should be captured by effect
    effect_keywords = set()
    def extract_from_effect(effect_dict):
        if isinstance(effect_dict, dict):
            if effect_dict.get('source'):
                effect_keywords.add('控え室' if effect_dict['source'] == 'waitroom' else '')
                effect_keywords.add('手札' if effect_dict['source'] == 'hand' else '')
                effect_keywords.add('ステージ' if effect_dict['source'] == 'stage' else '')
                effect_keywords.add('デッキ' if 'deck' in effect_dict.get('source', '') else '')
            if effect_dict.get('destination'):
                effect_keywords.add('控え室' if effect_dict['destination'] == 'waitroom' else '')
                effect_keywords.add('手札' if effect_dict['destination'] == 'hand' else '')
                effect_keywords.add('ステージ' if effect_dict['destination'] == 'stage' else '')
                effect_keywords.add('デッキ' if 'deck' in effect_dict.get('destination', '') else '')
            if effect_dict.get('card_type'):
                effect_keywords.add('ライブカード' if effect_dict['card_type'] == 'live_card' else '')
                effect_keywords.add('メンバーカード' if effect_dict['card_type'] == 'member_card' else '')
            for key, value in effect_dict.items():
                if isinstance(value, dict):
                    extract_from_effect(value)
                elif isinstance(value, list):
                    for item in value:
                        extract_from_effect(item)
    
    if effect:
        extract_from_effect(effect)
    
    # Combine captured keywords
    captured_keywords = cost_keywords.union(effect_keywords)
    captured_keywords.discard('')  # Remove empty strings
    
    # Find keywords in full text that weren't captured
    uncaptured_keywords = []
    for keyword in full_keywords:
        if keyword and keyword not in captured_keywords:
            uncaptured_keywords.append(keyword)
    
    # Check for specific overflattening patterns
    overflattening_issues = []
    
    # Check for raw_text in effect
    def check_raw_text(effect_dict, path=''):
        if isinstance(effect_dict, dict):
            if 'raw_text' in effect_dict:
                overflattening_issues.append({
                    'type': 'raw_text',
                    'path': path,
                    'text': effect_dict['raw_text']
                })
            for key, value in effect_dict.items():
                check_raw_text(value, f"{path}.{key}" if path else key)
        elif isinstance(effect_dict, list):
            for i, item in enumerate(effect_dict):
                check_raw_text(item, f"{path}[{i}]")
    
    if effect:
        check_raw_text(effect)
    
    # Check for missing trigger information
    if ability.get('triggers'):
        def has_trigger_field(effect_dict):
            if isinstance(effect_dict, dict):
                if 'trigger' in effect_dict:
                    return True
                for value in effect_dict.values():
                    if has_trigger_field(value):
                        return True
            elif isinstance(effect_dict, list):
                for item in effect_dict:
                    if has_trigger_field(item):
                        return True
            return False
        
        if effect and not has_trigger_field(effect):
            overflattening_issues.append({
                'type': 'missing_trigger',
                'trigger': ability['triggers']
            })
    
    # Check for missing use_limit in parsed structure
    if ability.get('use_limit'):
        if effect:
            def check_use_limit(effect_dict):
                if isinstance(effect_dict, dict):
                    if 'use_limit' not in effect_dict and 'turn_limit' not in effect_dict:
                        pass  # Could be missing
                    for value in effect_dict.values():
                        check_use_limit(value)
                elif isinstance(effect_dict, list):
                    for item in effect_dict:
                        check_use_limit(item)
            check_use_limit(effect)
    
    return {
        'uncaptured_keywords': uncaptured_keywords,
        'overflattening_issues': overflattening_issues,
        'full_text': full_text,
        'triggerless_text': triggerless_text
    }

def main():
    with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data['unique_abilities']
    
    # Analyze each ability
    all_issues = defaultdict(list)
    raw_text_count = 0
    missing_trigger_count = 0
    keyword_coverage_issues = []
    
    for i, ability in enumerate(abilities):
        analysis = analyze_text_coverage(ability)
        
        if analysis['overflattening_issues']:
            for issue in analysis['overflattening_issues']:
                if issue['type'] == 'raw_text':
                    raw_text_count += 1
                    all_issues['raw_text'].append({
                        'index': i,
                        'card': ability['cards'][0] if ability['cards'] else 'Unknown',
                        'text': issue['text'],
                        'full_text': analysis['full_text']
                    })
                elif issue['type'] == 'missing_trigger':
                    missing_trigger_count += 1
                    all_issues['missing_trigger'].append({
                        'index': i,
                        'card': ability['cards'][0] if ability['cards'] else 'Unknown',
                        'trigger': issue['trigger'],
                        'full_text': analysis['full_text']
                    })
        
        if analysis['uncaptured_keywords']:
            keyword_coverage_issues.append({
                'index': i,
                'card': ability['cards'][0] if ability['cards'] else 'Unknown',
                'uncaptured': analysis['uncaptured_keywords'],
                'full_text': analysis['full_text']
            })
    
    # Write report
    with open('overflattening_report.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("OVERFLATTENING ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total abilities analyzed: {len(abilities)}\n\n")
        
        f.write(f"Raw text issues: {raw_text_count}\n")
        f.write(f"Missing trigger issues: {missing_trigger_count}\n")
        f.write(f"Keyword coverage issues: {len(keyword_coverage_issues)}\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("RAW TEXT ISSUES\n")
        f.write("=" * 80 + "\n\n")
        
        for issue in all_issues['raw_text']:
            f.write(f"[{issue['index']}] {issue['card']}\n")
            f.write(f"Raw text: {issue['text']}\n")
            f.write(f"Full text: {issue['full_text']}\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("MISSING TRIGGER ISSUES\n")
        f.write("=" * 80 + "\n\n")
        
        for issue in all_issues['missing_trigger']:
            f.write(f"[{issue['index']}] {issue['card']}\n")
            f.write(f"Trigger: {issue['trigger']}\n")
            f.write(f"Full text: {issue['full_text']}\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("KEYWORD COVERAGE ISSUES (Top 50)\n")
        f.write("=" * 80 + "\n\n")
        
        for issue in keyword_coverage_issues[:50]:
            f.write(f"[{issue['index']}] {issue['card']}\n")
            f.write(f"Uncaptured keywords: {', '.join(issue['uncaptured'])}\n")
            f.write(f"Full text: {issue['full_text']}\n\n")
    
    print(f"Analysis complete. Report saved to overflattening_report.txt")
    print(f"Raw text issues: {raw_text_count}")
    print(f"Missing trigger issues: {missing_trigger_count}")
    print(f"Keyword coverage issues: {len(keyword_coverage_issues)}")

if __name__ == '__main__':
    main()
