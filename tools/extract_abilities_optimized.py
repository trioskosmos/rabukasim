# Optimized atomic pattern system for ability extraction
# Variables are limited to pure game mechanics only

# Atomic variable patterns - only game mechanics
ATOMIC_VARIABLES = {
    # Zones
    "ZONE": r"(ステージ|控え室|手札|デッキ|成功ライブカード置き場|エネルギーカード置き場|ライブカード置き場|エール置き場)",
    "ZONE_GENERAL": r"(ステージ|控え室|手札|デッキ|置き場)",
    
    # Card types
    "CARD_TYPE": r"(メンバーカード|ライブカード|エネルギーカード|カード)",
    
    # Numbers
    "NUMBER": r"(\d+)",
    
    # Resources
    "RESOURCE": r"(ブレード|heart\d+|icon_all\.png\|ハート)",
    "RESOURCE_SPECIFIC": r"(ブレード|heart01|heart02|heart03|heart04|heart05|heart06)",
    
    # Groups (in quotes)
    "GROUP": r"『([^』]+)』",
    "GROUP_ALT": r"「([^」]+)」",
    
    # Comparisons
    "COMPARISON": r"(以上|以下|より|未満)",
    "COMPARISON_INCLUSIVE": r"(以上|以下)",
    
    # Actions
    "ACTION": r"(置く|得る|引く|選ぶ|加える|する)",
    
    # States
    "STATE": r"(待機|登場|ライブ開始時|ライブ成功時|起動|常時)",
    
    # Players
    "PLAYER": r"(自分|相手)",
    
    # Attributes
    "ATTRIBUTE": r"(コスト|スコア)",
}

# Trigger patterns (separated from game mechanics)
TRIGGER_PATTERNS = {
    "ICON_TRIGGER": r"(\{?\{[^}]+\.png\|[^}]+\}\}?)",
    "TEXT_TRIGGER": r"(\{\{(toujyou|live_start|live_success|kidou|jidou|jyouji)\.png\|[^}]+\}\})",
}

# Optimized pattern system with atomic variables
OPTIMIZED_PATTERNS = [
    {
        "name": "zone_to_zone_add_atomic",
        "regex": r"\{?\{[^}]+\.png\|[^}]+\}\}?(自分の)?{ZONE_GENERAL}から{CARD_TYPE}を{NUMBER}枚{ZONE_GENERAL}に(加える|置く)",
        "template": "⟦TRIGGER⟧⟦PLAYER⟧{ZONE_GENERAL}から{CARD_TYPE}を{NUMBER}枚{ZONE_GENERAL}に⟦ACTION⟧",
        "structure": "Zone to zone add (atomic)",
        "atomic_vars": ["TRIGGER", "PLAYER", "ZONE_GENERAL", "CARD_TYPE", "NUMBER", "ACTION"]
    },
    {
        "name": "cost_zone_to_zone_add_atomic", 
        "regex": r"\{?\{[^}]+\.png\|[^}]+\}\}?{ZONE_GENERAL}にある{CARD_TYPE}を{NUMBER}枚{ZONE_GENERAL}に(加える|置く)",
        "template": "⟦TRIGGER⟧{ZONE_GENERAL}にある{CARD_TYPE}を{NUMBER}枚{ZONE_GENERAL}に⟦ACTION⟧",
        "structure": "Cost zone to zone add (atomic)",
        "atomic_vars": ["TRIGGER", "ZONE_GENERAL", "CARD_TYPE", "NUMBER", "ACTION"]
    },
    {
        "name": "resource_gain_atomic",
        "regex": r"\{?\{[^}]+\.png\|[^}]+\}\}?{RESOURCE}を{NUMBER}(つ|枚)得る",
        "template": "⟦TRIGGER⟧{RESOURCE}を{NUMBER}つ得る",
        "structure": "Resource gain (atomic)",
        "atomic_vars": ["TRIGGER", "RESOURCE", "NUMBER"]
    },
    {
        "name": "conditional_resource_gain_atomic",
        "regex": r"{ZONE_GENERAL}に{CARD_TYPE}が{NUMBER}枚以上ある場合、{RESOURCE}を得る",
        "template": "{ZONE_GENERAL}に{CARD_TYPE}が{NUMBER}枚以上ある場合、{RESOURCE}を得る",
        "structure": "Conditional resource gain (atomic)",
        "atomic_vars": ["ZONE_GENERAL", "CARD_TYPE", "NUMBER", "RESOURCE"]
    },
]

def format_atomic_pattern(pattern_dict):
    """Format pattern with atomic variable placeholders"""
    regex = pattern_dict["regex"]
    for var_name, var_pattern in ATOMIC_VARIABLES.items():
        regex = regex.replace(f"{{{var_name}}}", f"(?P<{var_name}>{var_pattern})")
    return regex

# Example usage
if __name__ == "__main__":
    print("Atomic Variable Patterns:")
    for var_name, pattern in ATOMIC_VARIABLES.items():
        print(f"{var_name}: {pattern}")
    
    print("\nOptimized Patterns:")
    for pattern in OPTIMIZED_PATTERNS:
        formatted = format_atomic_pattern(pattern)
        print(f"{pattern['name']}: {formatted}")
