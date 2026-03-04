import json
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from engine.models.generated_metadata import OPCODES, CONDITIONS, COSTS

def get_inverse_mapping(mapping: Dict[str, int]) -> Dict[int, str]:
    return {v: k for k, v in mapping.items()}

INV_OPCODES = get_inverse_mapping(OPCODES)
INV_CONDITIONS = get_inverse_mapping(CONDITIONS)
INV_COSTS = get_inverse_mapping(COSTS)

# --- Documentation Templates and Reference ---

BITWISE_REFERENCE = """
## Bitwise Mapping Reference

### 64-bit Filter Attribute (Attr)
Used by most opcodes for target selection and filtering.
- **Bits 0-1**: Target Player (1=Player, 2=Opponent)
- **Bits 2-3**: Card Type (1=Member, 2=Live)
- **Bit 4**: Group Filter Enable
- **Bits 5-11**: Group ID
- **Bit 12**: Tapped Mask (0=Any, 1=Tapped Only)
- **Bit 13**: Has Blade Heart Mask (True)
- **Bit 14**: Has Blade Heart Mask (False)
- **Bit 15**: Unique Names Flag
- **Bit 16**: Unit Filter Enable
- **Bits 17-23**: Unit ID
- **Bits 25-29**: Value Threshold (0-31)
- **Bit 30**: Value Mode (0=GE, 1=LE)
- **Bit 31**: Value/Cost Type Flag (0=Heart, 1=Cost)
- **Bits 32-38**: Color Mask (Bit 0=Pink, 1=Red, 2=Yellow, 3=Green, 4=Blue, 5=Purple, 6=Any)
- **Bits 39-45**: Character ID 1
- **Bits 46-52**: Character ID 2
- **Bits 53-55**: Zone Bitmask (4=Stage, 6=Hand, 7=Discard)
- **Bits 56-58**: Special ID
- **Bit 59**: Setsuna / Dynamic Value Flag
- **Bit 60**: Compare Accumulated Flag
- **Bit 61**: Optional Flag
- **Bit 62**: Keyword: Activated Energy
- **Bit 63**: Keyword: Activated Member

### Slot Field (S) - Effect Layout
- **Bits 0-7**: Target Type / Zone ID (0=Stage, 6=Hand, 7=Discard, 8=Deck, 15=Yell)
- **Bits 8-15**: Remainder Destination Zone or Multiplier Type
- **Bits 16-23**: Source Zone ID
- **Bit 24**: Target Opponent Flag
- **Bit 25**: Reveal Until Is Live Flag
- **Bit 26**: Empty Slot Only Flag
- **Bit 27**: Wait Flag (for Energy Charge)
- **Bits 28-30**: Area Filter (1=Left, 2=Center, 3=Right)

### Slot Field (S) - Condition Layout
- **Bits 0-3**: Zone/Slot ID (0=Stage, 1=Live Zone, 2=Excess, 15=Yell)
- **Bits 4-7**: Comparison Operator (0=EQ, 1=GT, 2=LT, 3=GE, 4=LE)
- **Bits 28-30**: Area Filter (1=Left, 2=Center, 3=Right)
"""

SPECIAL_TEMPLATES = {
    41: { # LOOK_AND_CHOOSE
        "Value": "Bits 0-7: Look Count, Bits 8-15: Pick Count, Bits 23-29: Color Mask, Bit 30: Reveal Flag",
        "Attr": "Standard Filter Attribute (Target selection)",
        "Slot": "Bits 0-7: Target Zone, Bits 8-15: Remainder Destination Zone, Bits 16-23: Source Zone"
    },
    83: { # SET_HEART_COST
        "Value": "Color Counts (6 Nibbles: Pink, Red, Yellow, Green, Blue, Purple)",
        "Attr": "Added Requirements (8 Nibbles: P/R/Y/G/B/P/Any)",
        "Slot": "Standard Slot Flags"
    },
    29: { # META_RULE
        "Attr": "Meta Type (0=Cheer, 1=HeartRule, 2=Live, 3=Shuffle, 4=OppTrigger, 5=LoseBladeHeart, 6=ReCheer, 7=Alias, 8=ScoreRule, 9=PreventSuccess, 10=Mulligan, 11=YellAgain, 12=MoveSuccess, 13=ResetYell)",
        "Value": "Specific parameters based on Meta Type (e.g. HeartRule source subtype)",
        "Slot": "N/A"
    },
    30: { # SELECT_MODE
        "Value": "Number of Options",
        "Attr": "N/A",
        "Slot": "Target Flags (e.g. Bit 24 for Opponent)",
        "Note": "Followed by a Jump Table for each option"
    }
}

class OpcodeStats:
    def __init__(self, name: str, code: int, type_name: str):
        self.name = name
        self.code = code
        self.type_name = type_name
        self.cards: Set[str] = set() # Store "card_no (Name)"
        self.count = 0
        self.dynamic_modifiers: Dict[int, Set[str]] = defaultdict(set) # value_cond -> Set of cards

def generate_opcode_docs(compiled_data: dict, output_path: str = "reports/opcode_reference.md"):
    """
    Analyzes compiled card database to generate automatic documentation for opcodes.
    """
    print(f"Generating opcode documentation to {output_path}...")
    
    # Initialize trackers
    effect_stats: Dict[int, OpcodeStats] = {code: OpcodeStats(name, code, "Effect") for name, code in OPCODES.items()}
    condition_stats: Dict[int, OpcodeStats] = {code: OpcodeStats(name, code, "Condition") for name, code in CONDITIONS.items()}
    
    # Analyze bytecode in member_db and live_db
    for db_key in ["member_db", "live_db"]:
        for cid_str, card_data in compiled_data.get(db_key, {}).items():
            card_no = card_data.get("card_no", cid_str)
            card_name = card_data.get("name", "Unknown")
            card_label = f"`{card_no}` ({card_name})"
            
            for ab in card_data.get("abilities", []):
                bc = ab.get("bytecode", [])
                
                # Iterate through bytecode chunks (size 5)
                for i in range(0, len(bc), 5):
                    if i + 4 >= len(bc):
                        break # Incomplete chunk
                        
                    op = bc[i]
                    v = bc[i+1]
                    v_cond = bc[i+2]
                    p1 = bc[i+3]
                    p2 = bc[i+4]
                    
                    # Handle negated conditions (1000+)
                    is_negated = op >= 1000
                    real_op = op - 1000 if is_negated else op
                    
                    if real_op in effect_stats:
                        stats = effect_stats[real_op]
                        stats.count += 1
                        stats.cards.add(card_label)
                        if v_cond != 0 and v_cond in INV_CONDITIONS:
                             stats.dynamic_modifiers[v_cond].add(card_label)
                    
                    elif real_op in condition_stats:
                        stats = condition_stats[real_op]
                        stats.count += 1
                        stats.cards.add(card_label)

    # Format Markdown
    md_lines = [
        "# LovecaSim Opcode Reference",
        "",
        "This document is automatically generated by the compiler. It details the opcodes used in the engine, their parameters, and the cards that utilize them.",
        "",
        BITWISE_REFERENCE,
        "",
        "---",
        ""
    ]
    
    def format_section(title: str, stats_dict: Dict[int, OpcodeStats], is_condition: bool = False):
        md_lines.append(f"## {title}")
        md_lines.append("")
        
        # Sort by opcode number
        sorted_stats = sorted(stats_dict.values(), key=lambda s: s.code)
        
        for stats in sorted_stats:
            md_lines.append(f"### {stats.name} ({stats.code})")
            md_lines.append(f"- **Usage Count**: {stats.count}")
            
            # --- Detailed Parameter Explanation ---
            if stats.code in SPECIAL_TEMPLATES:
                template = SPECIAL_TEMPLATES[stats.code]
                md_lines.append(f"- **Parameters (Special)**:")
                md_lines.append(f"  - `Value`: {template['Value']}")
                md_lines.append(f"  - `Attr`: {template['Attr']}")
                md_lines.append(f"  - `Slot`: {template['Slot']}")
                if "Note" in template:
                    md_lines.append(f"  - *Note: {template['Note']}*")
            elif is_condition:
                md_lines.append(f"- **Parameters (Condition)**:")
                md_lines.append(f"  - `Value`: Comparison threshold or specific ID.")
                md_lines.append(f"  - `Attr`: Standard Filter Attribute (Filter requirements).")
                md_lines.append(f"  - `Slot`: Packed Condition Slot (Zone + Comparison Operator).")
            else:
                md_lines.append(f"- **Parameters (Effect)**:")
                md_lines.append(f"  - `Value`: Fixed amount or amount-base.")
                md_lines.append(f"  - `Attr`: Standard Filter Attribute (Target requirements / Flags).")
                md_lines.append(f"  - `Slot`: Standard Effect Slot (Zones / Flags).")

            if stats.dynamic_modifiers:
                md_lines.append("- **Dynamic Modifiers Used** (Value adjusted by):")
                for mod_code, cards in stats.dynamic_modifiers.items():
                    mod_name = INV_CONDITIONS.get(mod_code, "UNKNOWN")
                    md_lines.append(f"  - `{mod_name}` ({mod_code}) -> Used by: {', '.join(sorted(list(cards))[:3])}{'...' if len(cards)>3 else ''}")
            
            if stats.cards:
                # Show up to 10 cards to keep it readable
                card_list = sorted(list(stats.cards))
                display_cards = card_list[:10]
                hidden_count = len(card_list) - 10
                
                md_lines.append(f"- **Used By**: {', '.join(display_cards)}")
                if hidden_count > 0:
                    md_lines.append(f"  - *...and {hidden_count} more cards.*")
            else:
                 md_lines.append("- *Currently unused.*")
                 
            md_lines.append("")
            
    format_section("Effect Opcodes", effect_stats, is_condition=False)
    md_lines.append("---")
    format_section("Condition Opcodes", condition_stats, is_condition=True)
    
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    print(f"Documentation written to {output_path}")

if __name__ == "__main__":
    # Test script standalone
    import sys, os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    try:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        generate_opcode_docs(data)
    except FileNotFoundError:
        print("Error: Could not find data/cards_compiled.json")
