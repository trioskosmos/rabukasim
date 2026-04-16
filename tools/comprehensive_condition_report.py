#!/usr/bin/env python3
"""
Comprehensive examination of all conditions with detailed explanations.
"""
import json
from collections import defaultdict

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

conditions_by_type = defaultdict(list)
total_conditions = 0

def extract_conditions(obj, ability_index, costless_text, triggers):
    global total_conditions
    if isinstance(obj, dict):
        if 'condition' in obj:
            cond = obj['condition']
            cond_type = cond.get('type', 'unknown')
            conditions_by_type[cond_type].append({
                'index': ability_index,
                'condition': cond,
                'action': obj.get('action'),
                'costless_text': costless_text,
                'triggers': triggers
            })
            total_conditions += 1
        for key, value in obj.items():
            extract_conditions(value, ability_index, costless_text, triggers)
    elif isinstance(obj, list):
        for item in obj:
            extract_conditions(item, ability_index, costless_text, triggers)

for i, ability in enumerate(data['unique_abilities'], 1):
    effect = ability.get('effect')
    if not effect:
        continue
    extract_conditions(effect, i, ability['costless_text'], ability['triggers'])

# Generate detailed report
with open('data/comprehensive_condition_report.txt', 'w', encoding='utf-8') as f:
    f.write("="*100 + "\n")
    f.write("COMPREHENSIVE CONDITION EXAMINATION REPORT\n")
    f.write("="*100 + "\n")
    f.write(f"Total conditions found: {total_conditions}\n")
    f.write(f"Unique condition types: {len(conditions_by_type)}\n")
    f.write("="*100 + "\n\n")
    
    # Process each condition type
    for cond_type in sorted(conditions_by_type.keys()):
        conditions = conditions_by_type[cond_type]
        
        f.write("="*100 + "\n")
        f.write(f"CONDITION TYPE: {cond_type}\n")
        f.write(f"Total abilities: {len(conditions)}\n")
        f.write("="*100 + "\n\n")
        
        # Write each condition with detailed explanation
        for item in conditions:
            f.write("-"*100 + "\n")
            f.write(f"Ability #{item['index']}\n")
            f.write(f"Triggers: {item['triggers']}\n")
            f.write(f"Original text: {item['costless_text']}\n")
            f.write(f"Extracted condition: {json.dumps(item['condition'], indent=2, ensure_ascii=False)}\n")
            if item['action']:
                f.write(f"Extracted action: {json.dumps(item['action'], indent=2, ensure_ascii=False)}\n")
            else:
                f.write(f"Extracted action: None\n")
            
            # Generate explanation
            f.write(f"\nEXPLANATION:\n")
            
            cond = item['condition']
            text = item['costless_text']
            
            # Explain based on condition type
            if cond_type == 'energy':
                f.write(f"  - This is an energy threshold condition.\n")
                f.write(f"  - The pattern 'エネルギーが{{value}}枚以上' matches the energy requirement.\n")
                f.write(f"  - Extracted value: {cond.get('value')} cards with operator '{cond.get('operator')}'.\n")
                f.write(f"  - This works because the regex 'エネルギーが(\\d+)枚以上' captures the number.\n")
            
            elif cond_type == 'card_count':
                f.write(f"  - This is a card count condition.\n")
                f.write(f"  - The pattern '{{value}}枚以上' matches the count requirement.\n")
                f.write(f"  - Extracted value: {cond.get('value')} cards with operator '{cond.get('operator')}'.\n")
                if 'location' in cond:
                    f.write(f"  - Location extracted: {cond.get('location')}.\n")
                    f.write(f"  - This works by checking for keywords like 'ライブカード置き場', '成功ライブカード置き場', '控え室'.\n")
                if 'card_type' in cond:
                    f.write(f"  - Card type extracted: {cond.get('card_type')}.\n")
            
            elif cond_type == 'member_count':
                f.write(f"  - This is a member count condition.\n")
                f.write(f"  - The pattern '{{value}}人以上' matches the member requirement.\n")
                f.write(f"  - Extracted value: {cond.get('value')} members with operator '{cond.get('operator')}'.\n")
                if 'different_name' in cond:
                    f.write(f"  - Modifier: different_name = {cond.get('different_name')} (members must have different names).\n")
                if 'different_cost' in cond:
                    f.write(f"  - Modifier: different_cost = {cond.get('different_cost')} (members must have different costs).\n")
                f.write(f"  - This works by checking for '名前とコストが両方ともそれぞれ異なる' pattern.\n")
            
            elif cond_type == 'member_presence':
                f.write(f"  - This is a member presence/absence condition.\n")
                f.write(f"  - Extracted presence: {cond.get('presence')} (members must be present or absent).\n")
                f.write(f"  - Extracted target: {cond.get('target')} (self, opponent, or both).\n")
                if 'cost' in cond:
                    f.write(f"  - Cost requirement: {cond.get('cost')} or higher.\n")
                if 'exclusion' in cond:
                    f.write(f"  - Exclusion: {cond.get('exclusion')} (this_member or other).\n")
                f.write(f"  - This works by matching patterns like '自分のステージに.*?メンバーが(いる|いない)'.\n")
            
            elif cond_type == 'per_unit':
                f.write(f"  - This is a per-unit multiplier condition.\n")
                f.write(f"  - Extracted value: {cond.get('value')} with operator '{cond.get('operator')}'.\n")
                if 'unit_type' in cond:
                    f.write(f"  - Unit type: {cond.get('unit_type')}.\n")
                if 'target' in cond:
                    f.write(f"  - Target: {cond.get('target')}.\n")
                f.write(f"  - This works by matching the '～につき' pattern.\n")
            
            elif cond_type == 'group':
                f.write(f"  - This is a group condition.\n")
                f.write(f"  - Extracted group: {cond.get('value')}.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by extracting text between 『』 brackets.\n")
            
            elif cond_type == 'baton_touch_deploy':
                f.write(f"  - This is a baton touch deployment condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                if 'source_member' in cond:
                    f.write(f"  - Source member: {cond.get('source_member')}.\n")
                f.write(f"  - This works by matching 'バトンタッチして登場した' pattern.\n")
            
            elif cond_type == 'position':
                f.write(f"  - This is a position condition.\n")
                f.write(f"  - Extracted position: {cond.get('value')}.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by matching position keywords like 'センターエリア', '左サイドエリア', '右サイドエリア'.\n")
            
            elif cond_type == 'answer':
                f.write(f"  - This is an answer condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                if 'answers' in cond:
                    f.write(f"  - Valid answers: {cond.get('answers')}.\n")
                f.write(f"  - This works by extracting text between '回答が' and 'の場合'.\n")
            
            elif cond_type == 'live_success_trigger':
                f.write(f"  - This is a live success trigger condition.\n")
                f.write(f"  - Trigger type: {cond.get('trigger_type')}.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by matching 'ライブ成功時能力が解決するたび' pattern.\n")
            
            elif cond_type == 'opponent_live_cards':
                f.write(f"  - This is an opponent live cards location condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by matching '相手のライブカード置き場にあるすべてのライブカードは' pattern.\n")
            
            elif cond_type == 'stage_members_target':
                f.write(f"  - This is a stage members target condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by matching '自分のステージにいるメンバーを' pattern.\n")
            
            elif cond_type == 'blade_count':
                f.write(f"  - This is a blade count condition.\n")
                f.write(f"  - Extracted value: {cond.get('value')} with operator '{cond.get('operator')}'.\n")
                f.write(f"  - This works by matching 'ブレード.*?合計が(\\d+)以上' pattern.\n")
            
            elif cond_type == 'heart_count':
                f.write(f"  - This is a heart count condition.\n")
                f.write(f"  - Extracted value: {cond.get('value')} with operator '{cond.get('operator')}'.\n")
                f.write(f"  - This works by matching 'ハート.*?(\\d+)つ以上' pattern.\n")
            
            elif cond_type == 'state':
                f.write(f"  - This is a state condition.\n")
                f.write(f"  - Extracted state: {cond.get('value')}.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by matching state keywords like 'アクティブ状態', 'ウェイト状態'.\n")
            
            elif cond_type == 'card_score':
                f.write(f"  - This is a card score condition.\n")
                f.write(f"  - Extracted score: {cond.get('value')} with operator '{cond.get('operator')}'.\n")
                f.write(f"  - This works by matching 'このカードのスコアが(\\d+)' pattern.\n")
            
            elif cond_type == 'combined_location_count':
                f.write(f"  - This is a combined location count condition.\n")
                f.write(f"  - Extracted value: {cond.get('value')} with operator '{cond.get('operator')}'.\n")
                if 'location' in cond:
                    f.write(f"  - Location: {cond.get('location')}.\n")
                f.write(f"  - This works by matching '自分と相手の.*?合計(\\d+)枚以上' pattern.\n")
            
            elif cond_type == 'comparison':
                f.write(f"  - This is a comparison condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                if 'compares' in cond:
                    f.write(f"  - Compares: {cond.get('compares')}.\n")
                if 'location' in cond:
                    f.write(f"  - Location: {cond.get('location')}.\n")
                f.write(f"  - This works by matching '～より～' pattern and extracting what's being compared.\n")
            
            elif cond_type == 'hand_card_count':
                f.write(f"  - This is a hand card count comparison condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by matching '手札の枚数が.*?より' pattern.\n")
            
            elif cond_type == 'energy_comparison':
                f.write(f"  - This is an energy comparison condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by matching 'エネルギーが.*?より' pattern.\n")
            
            elif cond_type == 'score_sum':
                f.write(f"  - This is a score sum condition.\n")
                f.write(f"  - Extracted value: {cond.get('value')} with operator '{cond.get('operator')}'.\n")
                if 'location' in cond:
                    f.write(f"  - Location: {cond.get('location')}.\n")
                f.write(f"  - This works by matching 'スコアの合計が(\\d+)以上' pattern.\n")
            
            elif cond_type == 'card_presence':
                f.write(f"  - This is a card presence condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                if 'location' in cond:
                    f.write(f"  - Location: {cond.get('location')}.\n")
                f.write(f"  - This works by matching '～カードがある' pattern.\n")
            
            elif cond_type == 'opponent_live_cards_location':
                f.write(f"  - This is an opponent live cards location condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by matching '相手のライブカード置き場にある' pattern.\n")
            
            elif cond_type == 'waitroom_location':
                f.write(f"  - This is a waitroom location condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by matching '自分の控え室にある' pattern.\n")
            
            elif cond_type == 'choice':
                f.write(f"  - This is a choice condition.\n")
                f.write(f"  - Operator: {cond.get('operator')}.\n")
                f.write(f"  - This works by matching '～か' pattern indicating alternatives.\n")
            
            elif cond_type == 'raw':
                f.write(f"  - WARNING: This condition could not be parsed.\n")
                f.write(f"  - Raw text: {cond.get('text')}.\n")
                f.write(f"  - This needs a pattern added to handle this specific text.\n")
            
            else:
                f.write(f"  - Condition type: {cond_type}.\n")
                f.write(f"  - Extracted parameters: {list(cond.keys())}.\n")
            
            f.write("\n")
    
    f.write("="*100 + "\n")
    f.write("END OF REPORT\n")
    f.write("="*100 + "\n")

print(f"Comprehensive report generated: data/comprehensive_condition_report.txt")
print(f"Total conditions examined: {total_conditions}")
print(f"Unique condition types: {len(conditions_by_type)}")
