import json

def check_atomic_results():
    """Check the results of atomic variable replacement"""
    
    # Load the processed data
    with open('../data/abilities_extracted_atomic.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("ATOMIC VARIABLE REPLACEMENT RESULTS")
    print("=" * 80)
    
    # Define atomic patterns
    atomic_patterns = {
        'NUMBER': r'^\d+$',
        'ZONE': r'^(ステージ|控え室|手札|デッキ|成功ライブカード置き場|エネルギーカード置き場|ライブカード置き場|エリア|センターエリア|右サイドエリア|左サイドエリア|エネルギー置き場)$',
        'CARD_TYPE': r'^(メンバーカード|ライブカード|エネルギーカード|カード)$',
        'PLAYER': r'^(自分|相手)$',
        'ICON': r'^\{\{[^}]+\|[^}]+\}\}?$',
        'GROUP': r'^「([^」]+)」$|^『([^』]+)』$|^\'[^\']+\'$|^[^\']+\'$',
        'GROUP_WITH_OR': r'^「([^」]+)」か「([^」]+)」(か「([^」]+)」)*$|^『([^』]+)』か『([^』]+)』(か『([^』]+)』)*$',
        'GROUP_NAME': r'^(A-RISE|Aqours|BiBi|CatChu!|DOLLCHESTRA|EdelNote|KALEIDOSCORE|Liella!|SaintSnow|SunnyPassion|lilywhite)$',
        'GROUP_JAPANESE': r'^(μ\'s|蓮ノ空|虹ヶ咲)$',
        'ACTION': r'^(置く|得る|引く|選ぶ|加える|する|移動させる|発動させる|アクティブにする|ウェイトにする|公開する|移動|発動|見る|行う|成功させる|支払え)$',
        'COST': r'^コスト$',
        'CONDITION': r'^場合$|^とき$',
        'DURATION': r'^まで$',
        'TARGET': r'^このメンバー$|^そのカード$|^そのハート$',
        'TRIGGER_NAME': r'^(登場|起動|常時|ライブ開始時|ライブ成功時|自動)$',
        'STATE': r'^(アクティブ|ウェイト|アクティブフェイズ|ウェイト状態)$',
        'RESOURCE': r'^(エネルギー|ハート|エール|ブレード)$',
        'RESOURCE_WITH_BRACKETS': r'^\[([^\]]+)\]$',
        'SINGLE_CHAR': r'^.$',
        'GROUP_SIMPLE': r'^[^\']+\'$',
        'GROUP_INCOMPLETE': r'^「([^」]*)$|^『([^』]*)$',
        'CONTEXT_PARTICLE': r'^(ある|いる|すべてある|それぞれ|それら|この|その|これ|それ|元々|同じ|異なる)$',
    }
    
    import re
    nonatomic_count = 0
    atomic_count = 0
    nonatomic_examples = []
    nonatomic_list = []
    
    for ability in data['abilities']:
        if 'pattern_matches' in ability:
            for match in ability['pattern_matches']:
                if 'extracted_variables_atomic' in match:
                    for var_value in match['extracted_variables_atomic']:
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
                            nonatomic_list.append(var_value)
    
    # Get unique non-atomic entries
    unique_nonatomic = list(set(nonatomic_list))
    
    print(f"\nAtomic variable analysis:")
    print(f"Atomic variables: {atomic_count}")
    print(f"Non-atomic variables: {nonatomic_count}")
    print(f"Total variables: {atomic_count + nonatomic_count}")
    print(f"Percentage atomic: {atomic_count / (atomic_count + nonatomic_count) * 100:.1f}%")
    
    print(f"\nUnique non-atomic entries: {len(unique_nonatomic)}")
    print(f"Total non-atomic occurrences: {nonatomic_count}")
    
    print(f"\n--- All Non-Atomic Variables ({len(unique_nonatomic)} unique) ---")
    for i, var in enumerate(sorted(unique_nonatomic)):
        count = nonatomic_list.count(var)
        print(f"{i+1}. {var} (occurs {count} times)")
    
    # Save to JSON file for examination
    nonatomic_data = {
        'unique_count': len(unique_nonatomic),
        'total_occurrences': nonatomic_count,
        'nonatomic_variables': [{'value': var, 'count': nonatomic_list.count(var)} for var in sorted(unique_nonatomic)]
    }
    
    with open('../data/nonatomic_variables_list.json', 'w', encoding='utf-8') as f:
        json.dump(nonatomic_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nNon-atomic variables saved to ../data/nonatomic_variables_list.json")
    
    # Compare with original
    print(f"\n--- Comparison with Original ---")
    original_nonatomic = 1578
    original_atomic = 1226
    original_total = 2804
    
    print(f"Original: {original_atomic} atomic ({original_atomic/original_total*100:.1f}%), {original_nonatomic} non-atomic ({original_nonatomic/original_total*100:.1f}%)")
    print(f"New: {atomic_count} atomic ({atomic_count/(atomic_count+nonatomic_count)*100:.1f}%), {nonatomic_count} non-atomic ({nonatomic_count/(atomic_count+nonatomic_count)*100:.1f}%)")
    print(f"Improvement: {(atomic_count - original_atomic)} more atomic variables")
    print(f"Reduction in non-atomic: {(original_nonatomic - nonatomic_count)} fewer non-atomic variables")

if __name__ == "__main__":
    check_atomic_results()
