import re
import json

# Atomic variable patterns - only game mechanics
ATOMIC_PATTERNS = {
    # Zones - pure game locations
    'ZONE': r'(ステージ|控え室|手札|デッキ|成功ライブカード置き場|エネルギーカード置き場|ライブカード置き場)',
    'ZONE_SIMPLE': r'(ステージ|控え室|手札|デッキ)',
    
    # Card types - pure game card types
    'CARD_TYPE': r'(メンバーカード|ライブカード|エネルギーカード)',
    'CARD_GENERAL': r'(メンバーカード|ライブカード|エネルギーカード|カード)',
    
    # Numbers - pure digits only
    'NUMBER': r'(\d+)',
    
    # Resources - pure game resources
    'RESOURCE': r'(ブレード)',
    'HEART': r'(heart\d+)',
    'ENERGY': r'(エネルギー)',
    
    # Groups - in quotes only
    'GROUP_SINGLE': r"『([^』]+)』",
    'GROUP_DOUBLE': r"「([^」]+)」",
    
    # Comparisons - pure game comparisons
    'COMPARISON': r'(以上|以下|より|未満)',
    
    # Actions - pure game actions
    'ACTION': r'(置く|得る|引く|選ぶ|加える|する|移動させる|発動させる|アクティブにする|ウェイトにする)',
    
    # States - pure game states
    'STATE': r'(待機|登場|ライブ開始時|ライブ成功時|起動|常時)',
    
    # Players - pure game players
    'PLAYER': r'(自分|相手)',
    
    # Attributes - pure game attributes
    'ATTRIBUTE': r'(コスト|スコア)',
    
    # Positions - pure positions
    'POSITION': r'(上|下|左|右|センター|サイド)',
    
    # Areas - pure areas
    'AREA': r'(エリア|ステージ|ライブエリア)',
    
    # Phases - pure phases
    'PHASE': r'(ターン|フェーズ)',
    
    # Events - pure events
    'EVENT': r'(ライブ|ターン)',
}

def create_replacement_mapping():
    """Create mapping from variable names to atomic patterns"""
    mapping = {
        # Zone mappings
        'ZONE': ATOMIC_PATTERNS['ZONE'],
        'ZONE1': ATOMIC_PATTERNS['ZONE'],
        'ZONE2': ATOMIC_PATTERNS['ZONE'],
        'ZONE3': ATOMIC_PATTERNS['ZONE'],
        'SOURCE_ZONE': ATOMIC_PATTERNS['ZONE'],
        'DESTINATION_ZONE': ATOMIC_PATTERNS['ZONE'],
        
        # Number mappings
        'NUMBER': ATOMIC_PATTERNS['NUMBER'],
        'NUMBER1': ATOMIC_PATTERNS['NUMBER'],
        'NUMBER2': ATOMIC_PATTERNS['NUMBER'],
        'NUMBER3': ATOMIC_PATTERNS['NUMBER'],
        
        # Resource mappings
        'RESOURCE': ATOMIC_PATTERNS['RESOURCE'],
        'RESOURCE1': ATOMIC_PATTERNS['RESOURCE'],
        'RESOURCE2': ATOMIC_PATTERNS['RESOURCE'],
        'RESOURCE3': ATOMIC_PATTERNS['RESOURCE'],
        'HEART': ATOMIC_PATTERNS['HEART'],
        'HEART1': ATOMIC_PATTERNS['HEART'],
        'HEART2': ATOMIC_PATTERNS['HEART'],
        'ENERGY': ATOMIC_PATTERNS['ENERGY'],
        
        # Card type mappings
        'CARD_TYPE': ATOMIC_PATTERNS['CARD_TYPE'],
        'CARD_TYPE2': ATOMIC_PATTERNS['CARD_TYPE'],
        'CARD': ATOMIC_PATTERNS['CARD_GENERAL'],
        'CARD1': ATOMIC_PATTERNS['CARD_GENERAL'],
        'CARD2': ATOMIC_PATTERNS['CARD_GENERAL'],
        
        # Group mappings
        'GROUP': ATOMIC_PATTERNS['GROUP_SINGLE'],
        'GROUP1': ATOMIC_PATTERNS['GROUP_SINGLE'],
        'GROUP2': ATOMIC_PATTERNS['GROUP_SINGLE'],
        'GROUP3': ATOMIC_PATTERNS['GROUP_SINGLE'],
        
        # Action mappings
        'ACTION': ATOMIC_PATTERNS['ACTION'],
        'ACTION2': ATOMIC_PATTERNS['ACTION'],
        
        # State mappings
        'STATE': ATOMIC_PATTERNS['STATE'],
        'STATE1': ATOMIC_PATTERNS['STATE'],
        'STATE2': ATOMIC_PATTERNS['STATE'],
        
        # Player mappings
        'PLAYER': ATOMIC_PATTERNS['PLAYER'],
        'PLAYER1': ATOMIC_PATTERNS['PLAYER'],
        'PLAYER2': ATOMIC_PATTERNS['PLAYER'],
        
        # Attribute mappings
        'ATTRIBUTE': ATOMIC_PATTERNS['ATTRIBUTE'],
        'ATTRIBUTE1': ATOMIC_PATTERNS['ATTRIBUTE'],
        
        # Position mappings
        'POSITION': ATOMIC_PATTERNS['POSITION'],
        
        # Area mappings
        'AREA': ATOMIC_PATTERNS['AREA'],
        
        # Phase mappings
        'PHASE': ATOMIC_PATTERNS['PHASE'],
        
        # Event mappings
        'EVENT': ATOMIC_PATTERNS['EVENT'],
    }
    return mapping

def analyze_pattern_for_atomic_replacement(pattern):
    """Analyze a pattern to identify which capture groups can be replaced"""
    regex = pattern['regex']
    template = pattern['template']
    
    # Extract variable names from template
    template_vars = re.findall(r'⟦([^⟧]+)⟧', template)
    
    # Find corresponding capture groups in regex
    capture_groups = re.findall(r'\(([^?][^)]*)\)', regex)
    
    replacements = []
    
    for i, (var_name, capture_group) in enumerate(zip(template_vars, capture_groups)):
        # Check if this is a broad capture that should be atomic
        if capture_group == '[^。]+':
            if var_name in create_replacement_mapping():
                replacements.append({
                    'variable': var_name,
                    'old_capture': capture_group,
                    'new_capture': create_replacement_mapping()[var_name],
                    'position': i
                })
    
    return replacements

def main():
    print("=" * 80)
    print("ATOMIC VARIABLE PATTERN DEFINITION")
    print("=" * 80)
    
    print("\nAtomic Patterns Defined:")
    for name, pattern in ATOMIC_PATTERNS.items():
        print(f"  {name}: {pattern}")
    
    print(f"\nTotal atomic patterns: {len(ATOMIC_PATTERNS)}")
    
    # Create replacement mapping
    mapping = create_replacement_mapping()
    print(f"\nVariable to atomic pattern mappings: {len(mapping)}")
    
    # Save to file
    output = {
        'atomic_patterns': ATOMIC_PATTERNS,
        'replacement_mapping': mapping
    }
    
    with open('../data/atomic_variable_patterns.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nAtomic patterns saved to ../data/atomic_variable_patterns.json")

if __name__ == "__main__":
    main()
