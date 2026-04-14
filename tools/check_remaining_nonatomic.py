import json
import re

def check_remaining_nonatomic():
    """Check if there are still non-atomic parts in variables after decomposition"""
    
    # Load the processed data
    with open('../data/abilities_extracted_with_atomic.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("CHECKING REMAINING NON-ATOMIC VARIABLES")
    print("=" * 80)
    
    # Define atomic patterns
    atomic_patterns = {
        'NUMBER': r'^\d+$',
        'ZONE': r'^(ステージ|控え室|手札|デッキ|成功ライブカード置き場|エネルギーカード置き場|ライブカード置き場)$',
        'CARD_TYPE': r'^(メンバーカード|ライブカード|エネルギーカード|カード)$',
        'PLAYER': r'^(自分|相手)$',
        'ICON': r'^\{\{[^}]+\|[^}]+\}\}$',
        'GROUP': r'^「([^」]+)」$|^『([^』]+)』$',
    }
    
    nonatomic_count = 0
    atomic_count = 0
    nonatomic_examples = []
    
    for ability in data['abilities']:
        if 'pattern_matches' in ability:
            for match in ability['pattern_matches']:
                if 'extracted_variables' in match:
                    for var_value in match['extracted_variables']:
                        # Check if variable is atomic
                        is_atomic = False
                        for atomic_name, atomic_pattern in atomic_patterns.items():
                            if re.match(atomic_pattern, var_value):
                                is_atomic = True
                                break
                        
                        if is_atomic:
                            atomic_count += 1
                        else:
                            nonatomic_count += 1
                            if len(nonatomic_examples) < 10:
                                nonatomic_examples.append(var_value)
    
    print(f"\nOriginal variable analysis:")
    print(f"Atomic variables: {atomic_count}")
    print(f"Non-atomic variables: {nonatomic_count}")
    print(f"Total variables: {atomic_count + nonatomic_count}")
    print(f"Percentage atomic: {atomic_count / (atomic_count + nonatomic_count) * 100:.1f}%")
    
    print(f"\nNon-atomic examples:")
    for example in nonatomic_examples:
        print(f"  {example}")
    
    # Check atomic decomposition coverage
    print(f"\n--- Atomic Decomposition Coverage ---")
    fully_decomposed = 0
    partially_decomposed = 0
    not_decomposed = 0
    
    for ability in data['abilities']:
        if 'pattern_matches' in ability:
            for match in ability['pattern_matches']:
                if 'atomic_variables' in match and match['atomic_variables']:
                    atomic_vars = match['atomic_variables']
                    original_vars = match['extracted_variables']
                    
                    # Check if all original vars have atomic decomposition
                    all_decomposed = len(atomic_vars) == len(original_vars)
                    some_decomposed = len(atomic_vars) > 0
                    
                    if all_decomposed:
                        fully_decomposed += 1
                    elif some_decomposed:
                        partially_decomposed += 1
                    else:
                        not_decomposed += 1
                else:
                    not_decomposed += 1
    
    print(f"Fully decomposed: {fully_decomposed}")
    print(f"Partially decomposed: {partially_decomposed}")
    print(f"Not decomposed: {not_decomposed}")
    
    # Check what non-atomic parts remain
    print(f"\n--- Remaining Non-Atomic Components ---")
    remaining_patterns = {
        'trigger_context': r'\{\{[^}]+\}\}.*自分',
        'condition_context': r'.*場合.*',
        'action_context': r'.*する.*',
        'mixed_context': r'自分.*相手',
    }
    
    for pattern_name, pattern in remaining_patterns.items():
        count = 0
        for ability in data['abilities']:
            if 'pattern_matches' in ability:
                for match in ability['pattern_matches']:
                    if 'extracted_variables' in match:
                        for var_value in match['extracted_variables']:
                            if re.search(pattern, var_value):
                                count += 1
        print(f"{pattern_name}: {count} occurrences")

if __name__ == "__main__":
    check_remaining_nonatomic()
