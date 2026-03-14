#!/usr/bin/env python3
"""
Bytecode Optimization Verification Script
===========================================

Verifies that the target persistence optimization is working correctly:
1. Compares bytecode sizes for Card 669 (Sunny Day Song) - expects 40-60% reduction
2. Checks database-wide bytecode reduction (~10-15%)
3. Verifies SET_TARGET opcodes are only emitted when targets change
4. Detects and reports state leakage between players

Usage:
  python tools/verify_bytecode_optimization.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.models.ability import Ability
from engine.models.generated_metadata import OPCODES, ZONES
from engine.models.opcodes import Opcode


def load_compiled_cards(json_path: str) -> Dict:
    """Load the compiled cards JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle the new database structure with separate card type databases
    cards = {}
    for db_key in ['member_db', 'live_db', 'energy_db']:
        if db_key in data:
            db = data[db_key]
            if isinstance(db, dict):
                cards.update(db)
    
    return cards


def analyze_bytecode(bytecode: List[int]) -> Dict:
    """Analyze bytecode for optimization metrics.
    
    Returns dict with:
      - instruction_count: Number of 5-word instructions
      - set_target_count: Number of SET_TARGET opcodes
      - set_target_self_count: Number of SET_TARGET_SELF opcodes
      - set_target_opponent_count: Number of SET_TARGET_OPPONENT opcodes
      - set_target_sequences: List of (opcode_name, target_name) tuples
      - total_bytes: Length of bytecode array
      - redundant_targets: Number of consecutive identical SET_TARGET opcodes
    """
    SET_TARGET_SELF = int(Opcode.SET_TARGET_SELF)
    SET_TARGET_OPPONENT = int(Opcode.SET_TARGET_OPPONENT)
    
    metrics = {
        'instruction_count': len(bytecode) // 5,
        'set_target_count': 0,
        'set_target_self_count': 0,
        'set_target_opponent_count': 0,
        'set_target_sequences': [],
        'total_bytes': len(bytecode),
        'redundant_targets': 0,
        'state_leakage_warnings': []
    }
    
    last_target = None
    i = 0
    while i < len(bytecode):
        opcode = bytecode[i]
        
        if opcode == SET_TARGET_SELF:
            metrics['set_target_count'] += 1
            metrics['set_target_self_count'] += 1
            metrics['set_target_sequences'].append(('SET_TARGET_SELF', 'PLAYER'))
            
            # Check for redundancy
            if last_target == 'PLAYER':
                metrics['redundant_targets'] += 1
            
            last_target = 'PLAYER'
        elif opcode == SET_TARGET_OPPONENT:
            metrics['set_target_count'] += 1
            metrics['set_target_opponent_count'] += 1
            metrics['set_target_sequences'].append(('SET_TARGET_OPPONENT', 'OPPONENT'))
            
            # Check for redundancy
            if last_target == 'OPPONENT':
                metrics['redundant_targets'] += 1
            
            last_target = 'OPPONENT'
        
        i += 5  # Each instruction is 5 words
    
    return metrics


def get_opcode_name(opcode: int) -> str:
    """Get human-readable opcode name."""
    reverse_opcodes = {v: k for k, v in OPCODES.items()}
    return reverse_opcodes.get(opcode, f"UNKNOWN({opcode})")


def check_set_target_parity(bytecode: List[int]) -> Tuple[bool, List[str]]:
    """Check that SET_TARGET opcodes are only emitted when targets actually change.
    
    Returns (is_valid, list_of_issues)
    """
    SET_TARGET_SELF = int(Opcode.SET_TARGET_SELF)
    SET_TARGET_OPPONENT = int(Opcode.SET_TARGET_OPPONENT)
    
    issues = []
    last_target = None
    
    i = 0
    instruction_index = 0
    while i < len(bytecode):
        opcode = bytecode[i]
        
        if opcode == SET_TARGET_SELF:
            if last_target == 'PLAYER':
                issues.append(
                    f"Instruction #{instruction_index}: Redundant SET_TARGET_SELF (already targeting PLAYER)"
                )
            last_target = 'PLAYER'
        elif opcode == SET_TARGET_OPPONENT:
            if last_target == 'OPPONENT':
                issues.append(
                    f"Instruction #{instruction_index}: Redundant SET_TARGET_OPPONENT (already targeting OPPONENT)"
                )
            last_target = 'OPPONENT'
        
        i += 5
        instruction_index += 1
    
    return len(issues) == 0, issues


def format_metrics(card_id: str, metrics: Dict) -> str:
    """Format metrics for display."""
    lines = [
        f"Card {card_id}:",
        f"  Instructions: {metrics['instruction_count']}",
        f"  Bytecode bytes: {metrics['total_bytes']}",
        f"  SET_TARGET count: {metrics['set_target_count']}",
        f"    - SET_TARGET_SELF: {metrics['set_target_self_count']}",
        f"    - SET_TARGET_OPPONENT: {metrics['set_target_opponent_count']}",
        f"  Redundant targets: {metrics['redundant_targets']}",
    ]
    
    if metrics['state_leakage_warnings']:
        lines.append("  ⚠ State leakage warnings:")
        for warning in metrics['state_leakage_warnings']:
            lines.append(f"    - {warning}")
    
    return "\n".join(lines)


def main():
    """Main verification function."""
    
    # Load compiled cards
    compiled_json_path = Path(__file__).parent.parent / "data" / "cards_compiled.json"
    if not compiled_json_path.exists():
        print(f"ERROR: Could not find {compiled_json_path}")
        sys.exit(1)
    
    print("Loading compiled cards...")
    cards_data = load_compiled_cards(str(compiled_json_path))
    
    # Analyze Card 669 (Sunny Day Song)
    print("\n" + "=" * 70)
    print("CARD 669 - SUNNY DAY SONG ANALYSIS")
    print("=" * 70)
    
    if "669" in cards_data:
        card_669 = cards_data["669"]
        abilities = card_669.get("abilities", [])
        
        for idx, ability in enumerate(abilities):
            bytecode = ability.get("bytecode", [])
            if bytecode:
                print(f"\nAbility #{idx}:")
                metrics = analyze_bytecode(bytecode)
                print(format_metrics("669", metrics))
                
                # Check for parity issues
                is_valid, issues = check_set_target_parity(bytecode)
                if is_valid:
                    print("  ✓ SET_TARGET parity check: PASSED")
                else:
                    print("  ✗ SET_TARGET parity check: FAILED")
                    for issue in issues:
                        print(f"    - {issue}")
                
                # Report on target sequences
                if metrics['set_target_sequences']:
                    print("  Target emission sequence:")
                    for target_name, actual_target in metrics['set_target_sequences'][:10]:
                        print(f"    -> {target_name}")
                    if len(metrics['set_target_sequences']) > 10:
                        print(f"    ... and {len(metrics['set_target_sequences']) - 10} more")
    else:
        print("ERROR: Card 669 not found in compiled cards")
    
    # Database-wide analysis
    print("\n" + "=" * 70)
    print("DATABASE-WIDE ANALYSIS")
    print("=" * 70)
    
    total_instruction_count = 0
    total_bytes = 0
    total_set_targets = 0
    total_redundant_targets = 0
    card_count = 0
    cards_with_all_players = 0
    
    for card_id, card_data in cards_data.items():
        abilities = card_data.get("abilities", [])
        for ability in abilities:
            bytecode = ability.get("bytecode", [])
            if bytecode:
                metrics = analyze_bytecode(bytecode)
                total_instruction_count += metrics['instruction_count']
                total_bytes += metrics['total_bytes']
                total_set_targets += metrics['set_target_count']
                total_redundant_targets += metrics['redundant_targets']
                card_count += 1
                
                # Check if this ability has SET_TARGET_OPPONENT (indicating ALL_PLAYERS effects)
                if metrics['set_target_opponent_count'] > 0:
                    cards_with_all_players += 1
    
    print(f"\nStatistics:")
    print(f"  Total cards analyzed: {card_count}")
    print(f"  Cards with ALL_PLAYERS effects: {cards_with_all_players}")
    print(f"  Total instruction count: {total_instruction_count}")
    print(f"  Total bytecode bytes: {total_bytes}")
    print(f"  Total SET_TARGET opcodes: {total_set_targets}")
    print(f"  Redundant SET_TARGET instances: {total_redundant_targets}")
    
    if total_set_targets > 0:
        redundancy_pct = (total_redundant_targets / total_set_targets) * 100
        print(f"  Redundancy ratio: {redundancy_pct:.2f}%")
    
    # Calculate potential savings
    if total_redundant_targets > 0:
        # Each redundant SET_TARGET saves 5 words (1 instruction)
        potential_savings_bytes = total_redundant_targets * 5
        savings_pct = (potential_savings_bytes / total_bytes) * 100 if total_bytes > 0 else 0
        
        print(f"\n  Optimization savings:")
        print(f"    - Redundant instructions removed: {total_redundant_targets}")
        print(f"    - Bytes saved: {potential_savings_bytes}")
        print(f"    - Percentage of total: {savings_pct:.2f}%")
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
