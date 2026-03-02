import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.curdir))

from compiler.parser_v2 import AbilityParserV2
# from compiler.main import parse_live
from engine.models.ability import Ability

def targeted_compile(card_no):
    print(f"--- Targeted Compilation for {card_no} ---")
    
    # Load raw data
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards_data = json.load(f)
    
    if card_no not in cards_data:
        print(f"Error: Card {card_no} not found in cards.json")
        return
    
    data = cards_data[card_no]
    print(f"Name: {data.get('name')}")
    
    # Mimic compiler.main.parse_live logic
    print("\n--- Step 1: Parsing Pseudocode ---")
    parser = AbilityParserV2()
    
    # Load consolidated data to check what the compiler actually sees
    consolidated_path = "compiler/_consolidated_abilities.json" # Best guess for the name based on main.py imports usually
    # From main.py: raw_jp in _consolidated_abilities: entry = _consolidated_abilities[raw_jp]
    # Let's see if we can just replicate the mapping logic from data
    raw_jp = str(data.get("ability", ""))
    print(f"Raw JP: {raw_jp[:50]}...")
    
    # We'll just force the pseudocode for targeted repro
    raw_pseudocode = data.get("pseudocode", raw_jp)
    print(f"Raw Pseudocode: {raw_pseudocode[:50]}...")
    abilities = parser.parse(raw_pseudocode)
    
    print(f"Parsed {len(abilities)} abilities.")
    
    for idx, ab in enumerate(abilities):
        print(f"\nAbility #{idx}:")
        print(f"  Trigger: {ab.trigger.name}")
        print(f"  Instructions ({len(ab.instructions)}):")
        for i_idx, instr in enumerate(ab.instructions):
            print(f"    [{i_idx}] {type(instr).__name__} {getattr(instr, 'type', getattr(instr, 'effect_type', 'N/A'))}")
        
        print("\n--- Step 2: Compiling Bytecode ---")
        ab.card_no = card_no # My injected field
        try:
            bytecode = ab.compile()
            print(f"  Result Bytecode: {bytecode}")
        except Exception as e:
            print(f"  FAILED to compile: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import io
    # Force captured output to file with UTF-8
    with open("reports/targeted_repro_fixed.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        targeted_compile("PL!-bp4-020-L")
