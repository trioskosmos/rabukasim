import json
import re

def decompose_variable(variable_text, var_name):
    """Decompose a variable into atomic components"""
    atomic_components = {}
    
    # Extract icon references as atomic units
    icon_pattern = r'\{\{[^}]+\|[^}]+\}\}'
    icons = re.findall(icon_pattern, variable_text)
    if icons:
        atomic_components['ICON'] = icons
    
    # Extract trigger (if present)
    trigger_pattern = r'\{\{[^}]+\.png\|[^}]+\}\}'
    triggers = re.findall(trigger_pattern, variable_text)
    
    # Fix missing opening brackets in triggers
    broken_trigger_pattern = r'([^{\}]+\.png\|[^}]+\})'
    broken_triggers = re.findall(broken_trigger_pattern, variable_text)
    
    # Combine triggers - prefer proper triggers, fall back to fixed broken ones
    all_triggers = triggers if triggers else (['{{' + t for t in broken_triggers] if broken_triggers else [])
    if all_triggers:
        atomic_components['TRIGGER'] = all_triggers
    
    # Extract player
    if '自分' in variable_text:
        atomic_components['PLAYER'] = '自分'
    elif '相手' in variable_text:
        atomic_components['PLAYER'] = '相手'
    
    # Extract zone
    zones = ['ステージ', '控え室', '手札', 'デッキ', '成功ライブカード置き場', 'エネルギーカード置き場', 'ライブカード置き場', 'エリア', 'センターエリア', '右サイドエリア', '左サイドエリア', 'エネルギー置き場']
    for zone in zones:
        if zone in variable_text:
            atomic_components['ZONE'] = zone
            break
    
    # Extract number
    numbers = re.findall(r'\d+', variable_text)
    if numbers:
        atomic_components['NUMBER'] = numbers[0]
    
    # Extract card type
    card_types = ['メンバーカード', 'ライブカード', 'エネルギーカード', 'カード']
    for card_type in card_types:
        if card_type in variable_text:
            atomic_components['CARD_TYPE'] = card_type
            break
    
    # Extract resource (non-icon)
    resources = ['エネルギー', 'ハート', 'エール', 'ブレード']
    for resource in resources:
        if resource in variable_text and not icons:
            atomic_components['RESOURCE'] = resource
            break
    
    # Extract group (in quotes) including names with 'or' particles
    group_pattern = r"「([^」]+)」|『([^』]+)』"
    groups = re.findall(group_pattern, variable_text)
    if groups:
        # Flatten the tuple results
        flat_groups = [g for group_tuple in groups for g in group_tuple if g]
        if flat_groups:
            atomic_components['GROUP'] = flat_groups
    
    # Extract group names with 'or' particles
    group_or_pattern = r"「([^」]+)」か「([^」]+)」(か「([^」]+)」)*|『([^』]+)』か『([^』]+)』(か『([^』]+)』)*"
    group_or = re.findall(group_or_pattern, variable_text)
    if group_or:
        atomic_components['GROUP_OR'] = group_or
    
    # Extract condition
    if '場合' in variable_text:
        atomic_components['CONDITION'] = '場合'
    if 'まで' in variable_text:
        atomic_components['DURATION'] = 'まで'
    if 'とき' in variable_text:
        atomic_components['CONDITION'] = 'とき'
    
    # Extract action
    actions = ['置く', '得る', '引く', '選ぶ', '加える', 'する', '移動させる', '発動させる', 'アクティブにする', 'ウェイトにする', '公開する', '移動', '発動', '見る', '行う', '成功させる', '支払え']
    for action in actions:
        if action in variable_text:
            atomic_components['ACTION'] = action
            break
    
    # Extract state
    states = ['アクティブ', 'ウェイト', 'アクティブフェイズ', 'ウェイト状態']
    for state in states:
        if state in variable_text:
            atomic_components['STATE'] = state
            break
    
    # Extract target/context
    if 'このメンバー' in variable_text:
        atomic_components['TARGET'] = 'このメンバー'
    if 'そのカード' in variable_text:
        atomic_components['TARGET'] = 'そのカード'
    if 'そのハート' in variable_text:
        atomic_components['TARGET'] = 'そのハート'
    
    # Extract cost
    if 'コスト' in variable_text:
        atomic_components['COST'] = 'コスト'
    
    # Handle grammar particles - split poorly parsed segments
    # "いるエリ" should be split into "いる" (verb) + "エリア" (zone)
    if 'エリ' in variable_text and 'エリア' not in variable_text:
        # This is likely a poorly parsed "エリア"
        atomic_components['ZONE'] = 'エリア'
    
    # Handle context phrases with duration
    if 'ライブ終了時まで' in variable_text:
        atomic_components['DURATION_CONTEXT'] = 'ライブ終了時まで'
    
    return atomic_components

def post_process_abilities():
    """Post-process extracted variables to replace with atomic components"""
    
    # Load abilities_extracted_simple.json
    with open('../data/abilities_extracted_simple.json', 'r', encoding='utf-8') as f:
        simple_data = json.load(f)
    
    print("=" * 80)
    print("POST-PROCESSING VARIABLE DECOMPOSITION")
    print("=" * 80)
    
    # Process each ability
    for ability in simple_data['abilities']:
        if 'pattern_matches' in ability:
            for match in ability['pattern_matches']:
                if 'extracted_variables' in match:
                    original_vars = match['extracted_variables']
                    template = match['template']
                    
                    # Extract variable names from template
                    template_vars = re.findall(r'⟦([^⟧]+)⟧', template)
                    
                    # Decompose each variable and replace with atomic components
                    atomic_vars = []
                    for i, (var_name, var_value) in enumerate(zip(template_vars, original_vars)):
                        if i < len(original_vars):
                            decomposition = decompose_variable(var_value, var_name)
                            if decomposition:
                                # Replace with most atomic component available (preserve icon references as requested)
                                if 'ICON' in decomposition:
                                    atomic_vars.append(decomposition['ICON'][0])
                                elif 'TRIGGER' in decomposition:
                                    atomic_vars.append(decomposition['TRIGGER'][0])
                                elif 'NUMBER' in decomposition:
                                    atomic_vars.append(decomposition['NUMBER'])
                                elif 'PLAYER' in decomposition:
                                    atomic_vars.append(decomposition['PLAYER'])
                                elif 'ZONE' in decomposition:
                                    atomic_vars.append(decomposition['ZONE'])
                                elif 'CARD_TYPE' in decomposition:
                                    atomic_vars.append(decomposition['CARD_TYPE'])
                                elif 'ACTION' in decomposition:
                                    atomic_vars.append(decomposition['ACTION'])
                                elif 'GROUP' in decomposition:
                                    atomic_vars.append(decomposition['GROUP'][0])
                                else:
                                    # Fallback to original if no atomic component found
                                    atomic_vars.append(var_value)
                            else:
                                # Keep original if no decomposition
                                atomic_vars.append(var_value)
                        else:
                            atomic_vars.append(var_value)
                    
                    # Replace original variables with atomic ones
                    match['extracted_variables_atomic'] = atomic_vars
                    # Keep original for reference
                    match['extracted_variables_original'] = original_vars
    
    # Save the processed data
    output_file = '../data/abilities_extracted_atomic.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(simple_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nProcessed {len(simple_data['abilities'])} abilities")
    print(f"Saved atomic variables to {output_file}")
    
    # Show examples
    print("\n--- Example Transformations ---")
    for i, ability in enumerate(simple_data['abilities'][:5]):
        if 'pattern_matches' in ability:
            print(f"\nAbility {i+1}:")
            print(f"Original: {ability['jp'][:80]}...")
            for match in ability['pattern_matches']:
                if 'extracted_variables_atomic' in match:
                    print(f"Pattern: {match['pattern_name']}")
                    print(f"Original variables: {match['extracted_variables_original']}")
                    print(f"Atomic variables: {match['extracted_variables_atomic']}")

if __name__ == "__main__":
    post_process_abilities()
