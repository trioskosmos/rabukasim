import json
from collections import defaultdict

def analyze_nonatomic_variables():
    """Analyze non-atomic variables in detail"""
    
    # Load variable counts analysis
    with open('../data/variable_counts_analysis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Load abilities_extracted_simple.json for context
    with open('../data/abilities_extracted_simple.json', 'r', encoding='utf-8') as f:
        simple_data = json.load(f)
    
    print("=" * 80)
    print("NON-ATOMIC VARIABLE ANALYSIS")
    print("=" * 80)
    
    # Define atomic game mechanic categories
    atomic_categories = {
        'zones': ['ZONE', 'ZONE1', 'ZONE2', 'ZONE3'],
        'numbers': ['NUMBER', 'NUMBER1', 'NUMBER2', 'NUMBER3'],
        'resources': ['RESOURCE', 'RESOURCE1', 'RESOURCE2', 'RESOURCE3'],
        'card_types': ['CARD_TYPE', 'CARD_TYPE2', 'CARD1', 'CARD2'],
        'actions': ['ACTION', 'ACTION2'],
        'states': ['STATE', 'STATE1', 'STATE2'],
        'players': ['PLAYER', 'PLAYER1', 'PLAYER2'],
        'attributes': ['ATTRIBUTE', 'ATTRIBUTE1'],
        'costs': ['COST', 'COST_TARGET'],
        'groups': ['GROUP', 'GROUP1', 'GROUP2', 'GROUP3'],
        'members': ['MEMBER', 'MEMBER2'],
        'positions': ['POSITION'],
        'comparisons': ['COMPARISON', 'COMPARISON_TARGET'],
    }
    
    # Variables that are likely non-atomic
    nonatomic_variables = [
        'SOURCE', 'SOURCE1', 'SOURCE2',  # Capture full context/trigger phrases
        'DESTINATION', 'DESTINATION1', 'DESTINATION2',  # Capture full destination phrases
        'SUBJECT',  # Capture sentence subjects with context
        'CONDITION',  # Capture conditional phrases
        'CONTEXT',  # Capture contextual information
        'TRIGGER',  # Capture trigger information
        'CLAUSE',  # Capture clause information
        'ICON',  # Capture icon references
        'MODIFIER',  # Capture modifier phrases
        'PLACED',  # Capture placement context
        'SELECTED',  # Capture selection context
        'EFFECT',  # Capture effect descriptions
        'ORIGINAL',  # Capture original state
        'CURRENT',  # Capture current state
        'NEW_TARGET',  # Capture target changes
        'SUMMONED',  # Capture summoning context
        'REVEALED',  # Capture revelation context
        'CALCULATED',  # Capture calculation context
        'OPERATION',  # Capture operation descriptions
        'PROCEDURE',  # Capture procedure descriptions
        'TRANSFORM',  # Capture transformation context
        'SUPERLATIVE',  # Capture superlative phrases
        'LIMITATION',  # Capture limitation phrases
        'EXACT',  # Capture exact specifications
        'DIFFERENT',  # Capture difference specifications
        'OTHER',  # Capture other specifications
        'ALTERNATIVE',  # Capture alternative specifications
        'TIME',  # Capture time specifications
        'EVENT',  # Capture event descriptions
        'RESULT',  # Capture result descriptions
        'DRAW',  # Capture draw context
        'LOSE',  # Capture loss context
        'GAINED',  # Capture gain context
        'PERFORM',  # Capture performance context
        'ACTIVATE',  # Capture activation context
        'REPEAT',  # Capture repetition context
        'PREFIX',  # Capture prefix information
        'SUFFIX',  # Capture suffix information
        'NEGATION',  # Capture negation phrases
        'REDUCTION',  # Capture reduction phrases
        'LOCATION',  # Capture location context
        'AREA',  # Capture area specifications
        'TOTAL',  # Capture total specifications
        'COUNT',  # Capture count specifications
        'EACH',  # Capture each specifications
        'ALL',  # Capture all specifications
        'THEY',  # Capture they specifications
        'SELF',  # Capture self specifications
        'OPPONENT',  # Capture opponent specifications
        'TARGET_PLAYER', 'TARGET_PLAYER2',  # Capture player target context
        'DESTINATION_ZONE', 'SOURCE_ZONE',  # Capture zone context
        'EXCEPT_CARD', 'EXCEPT_GROUP', 'EXCEPT_MEMBER',  # Capture exception context
        'HEART_TYPE',  # Capture heart type context
        'COLOR',  # Capture color specifications
        'LIVE',  # Capture live context
        'SCORE',  # Capture score specifications
        'ENERGY',  # Capture energy context
        'TURN',  # Capture turn context
        'PHASE',  # Capture phase context
        'DURATION',  # Capture duration context
        'PAYMENT',  # Capture payment context
        'QUESTION',  # Capture question context
    ]
    
    print(f"\n--- Non-Atomic Variables Analysis ---")
    print(f"Total variables analyzed: {len(data['variable_counts'])}")
    print(f"Variables classified as non-atomic: {len(nonatomic_variables)}")
    
    # Analyze non-atomic variables
    nonatomic_analysis = {}
    for var_name in nonatomic_variables:
        if var_name in data['variable_counts']:
            count = data['variable_counts'][var_name]
            examples = data['variable_examples'].get(var_name, [])
            nonatomic_analysis[var_name] = {
                'count': count,
                'examples': examples,
                'is_truly_nonatomic': len([e for e in examples if len(e) > 20]) > len(examples) / 2
            }
    
    # Sort by count
    sorted_nonatomic = sorted(nonatomic_analysis.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print(f"\n--- Top Non-Atomic Variables by Count ---")
    for var_name, analysis in sorted_nonatomic[:20]:
        print(f"\n{var_name}: {analysis['count']} occurrences")
        print(f"  Examples:")
        for example in analysis['examples'][:5]:
            print(f"    - {example}")
        print(f"  Truly non-atomic: {analysis['is_truly_nonatomic']}")
    
    # Analyze specific problematic patterns
    print("\n--- Specific Problematic Variable Examples ---")
    
    problematic_examples = {
        'SOURCE': data['variable_examples'].get('SOURCE', [])[:5],
        'SUBJECT': data['variable_examples'].get('SUBJECT', [])[:5],
        'CONDITION': data['variable_examples'].get('CONDITION', [])[:5],
        'CONTEXT': data['variable_examples'].get('CONTEXT', [])[:5],
    }
    
    for var_name, examples in problematic_examples.items():
        if examples:
            print(f"\n{var_name} examples (showing non-atomic capture):")
            for example in examples:
                print(f"  - {example}")
                # Analyze why it's non-atomic
                if len(example) > 30:
                    print(f"    → Too long, captures full phrases")
                if any(trigger in example for trigger in ['png', '}}', '時', '場合', 'とき']):
                    print(f"    → Contains trigger/context markers")
                if any(word in example for word in ['自分', '相手', 'この', 'その']):
                    print(f"    → Contains contextual pronouns")
    
    # Calculate impact
    total_nonatomic_occurrences = sum(analysis['count'] for var_name, analysis in nonatomic_analysis.items())
    total_occurrences = sum(data['variable_counts'].values())
    
    print(f"\n--- Impact Analysis ---")
    print(f"Total variable occurrences: {total_occurrences}")
    print(f"Non-atomic variable occurrences: {total_nonatomic_occurrences}")
    print(f"Percentage non-atomic: {total_nonatomic_occurrences / total_occurrences * 100:.1f}%")
    
    # Save results
    results = {
        'nonatomic_variables': nonatomic_analysis,
        'total_nonatomic_occurrences': total_nonatomic_occurrences,
        'total_occurrences': total_occurrences,
        'percentage_nonatomic': total_nonatomic_occurrences / total_occurrences * 100
    }
    
    output_file = '../data/nonatomic_variable_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to {output_file}")
    
    return results

if __name__ == "__main__":
    results = analyze_nonatomic_variables()
