import json
import re

def analyze_ideal_atomic_state():
    """Analyze what ideal atomic variable extraction would look like"""
    
    # Load current data
    with open('../data/abilities_extracted_simple.json', 'r', encoding='utf-8') as f:
        simple_data = json.load(f)
    
    with open('../data/nonatomic_variable_analysis.json', 'r', encoding='utf-8') as f:
        nonatomic_data = json.load(f)
    
    print("=" * 80)
    print("IDEAL ATOMIC VARIABLE EXTRACTION ANALYSIS")
    print("=" * 80)
    
    # Define truly atomic game mechanics
    ATOMIC_GAME_MECHANICS = {
        'ZONES': ['ステージ', '控え室', '手札', 'デッキ', '成功ライブカード置き場', 'エネルギーカード置き場', 'ライブカード置き場'],
        'CARD_TYPES': ['メンバーカード', 'ライブカード', 'エネルギーカード'],
        'NUMBERS': ['\\d+'],  # Only digits
        'RESOURCES': ['ブレード'],
        'HEARTS': ['heart\\d+'],  # heart followed by digits
        'ACTIONS': ['置く', '得る', '引く', '選ぶ', '加える', 'する', '移動させる', '発動させる', 'アクティブにする', 'ウェイトにする'],
        'STATES': ['待機', '登場', 'ライブ開始時', 'ライブ成功時', '起動', '常時', 'アクティブ', 'ウェイト'],
        'PLAYERS': ['自分', '相手'],
        'ATTRIBUTES': ['コスト', 'スコア'],
        'POSITIONS': ['上', '下', '左', '右', 'センター', 'サイド'],
        'AREAS': ['エリア', 'ステージ', 'ライブエリア'],
        'COMPARISONS': ['以上', '以下', 'より', '未満'],
        'GROUPS': ['『([^』]+)』', '「([^」]+)」'],  # In quotes
    }
    
    print("\n--- Ideal Atomic Game Mechanics ---")
    for category, mechanics in ATOMIC_GAME_MECHANICS.items():
        print(f"{category}: {mechanics}")
    
    print(f"\nTotal atomic categories: {len(ATOMIC_GAME_MECHANICS)}")
    
    # Analyze current vs ideal
    print("\n--- Current State Analysis ---")
    print(f"Total variable occurrences: {nonatomic_data['total_occurrences']}")
    print(f"Non-atomic occurrences: {nonatomic_data['total_nonatomic_occurrences']}")
    print(f"Percentage non-atomic: {nonatomic_data['percentage_nonatomic']:.1f}%")
    
    # Show examples of current vs ideal extraction
    print("\n--- Current vs Ideal Variable Extraction Examples ---")
    
    # Find a specific example ability
    example_ability = None
    for ability in simple_data['abilities']:
        if ability['pattern_matches']:
            example_ability = ability
            break
    
    if example_ability:
        print(f"\nExample Ability:")
        print(f"Original: {example_ability['jp']}")
        
        for match in example_ability['pattern_matches']:
            print(f"\nPattern: {match['pattern_name']}")
            print(f"Current extracted variables: {match['extracted_variables']}")
            
            # Show what ideal extraction would look like
            print(f"Ideal extracted variables (atomic only):")
            template_vars = re.findall(r'⟦([^⟧]+)⟧', match['template'])
            for var_name in template_vars:
                if var_name in ['ZONE', 'ZONE1', 'ZONE2']:
                    print(f"  {var_name}: (ステージ|控え室|手札|デッキ|成功ライブカード置き場)")
                elif var_name in ['NUMBER', 'NUMBER1', 'NUMBER2']:
                    print(f"  {var_name}: (\\d+)")
                elif var_name in ['CARD_TYPE', 'CARD1', 'CARD2']:
                    print(f"  {var_name}: (メンバーカード|ライブカード|エネルギーカード)")
                elif var_name in ['RESOURCE', 'RESOURCE1', 'RESOURCE2']:
                    print(f"  {var_name}: (ブレード)")
                elif var_name in ['GROUP', 'GROUP1', 'GROUP2']:
                    print(f"  {var_name}: 『([^』]+)』")
                elif var_name in ['ACTION']:
                    print(f"  {var_name}: (置く|得る|引く|選ぶ|加える)")
                elif var_name in ['STATE']:
                    print(f"  {var_name}: (待機|登場|ライブ開始時|ライブ成功時|起動|常時)")
                elif var_name in ['PLAYER']:
                    print(f"  {var_name}: (自分|相手)")
                else:
                    print(f"  {var_name}: [needs specific atomic pattern]")
    
    # Analyze what changes would be needed
    print("\n--- Required Changes for Atomic Extraction ---")
    
    # Count patterns that would need modification
    pattern_modifications = 0
    total_patterns = 0
    
    for ability in simple_data['abilities']:
        if ability['pattern_matches']:
            for match in ability['pattern_matches']:
                total_patterns += 1
                template_vars = re.findall(r'⟦([^⟧]+)⟧', match['template'])
                # Check if any variables are non-atomic
                if any(var not in ['NUMBER', 'NUMBER1', 'NUMBER2', 'ZONE', 'ZONE1', 'ZONE2', 
                                 'CARD_TYPE', 'RESOURCE', 'GROUP', 'ACTION', 'STATE', 'PLAYER'] 
                       for var in template_vars):
                    pattern_modifications += 1
    
    print(f"Total pattern matches: {total_patterns}")
    print(f"Patterns needing atomic modification: {pattern_modifications}")
    print(f"Percentage needing modification: {pattern_modifications / total_patterns * 100:.1f}%")
    
    # Calculate impact on pattern count
    print("\n--- Impact Analysis ---")
    print(f"Current unique patterns: 282")
    print(f"Estimated patterns after atomic expansion: 400-600 (to handle all variations)")
    print(f"Reason: Each current pattern would need multiple variants to handle:")
    print(f"  - Different trigger contexts (登場, ライブ開始時, etc.)")
    print(f"  - Different contextual phrases (自分の, 相手の, etc.)")
    print(f"  - Different grammatical structures")
    print(f"  - Icon references vs text references")
    
    # Save analysis
    analysis = {
        'atomic_game_mechanics': ATOMIC_GAME_MECHANICS,
        'current_state': {
            'total_occurrences': nonatomic_data['total_occurrences'],
            'nonatomic_occurrences': nonatomic_data['total_nonatomic_occurrences'],
            'percentage_nonatomic': nonatomic_data['percentage_nonatomic']
        },
        'required_changes': {
            'total_pattern_matches': total_patterns,
            'patterns_needing_modification': pattern_modifications,
            'percentage_needing_modification': pattern_modifications / total_patterns * 100
        },
        'impact': {
            'current_patterns': 282,
            'estimated_patterns_after_atomic': '400-600',
            'reason': 'Multiple variants needed for trigger contexts, contextual phrases, grammatical structures, and icon references'
        }
    }
    
    with open('../data/ideal_atomic_state_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalysis saved to ../data/ideal_atomic_state_analysis.json")

if __name__ == "__main__":
    analyze_ideal_atomic_state()
