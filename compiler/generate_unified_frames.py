#!/usr/bin/env python3
"""
Generate unified semantic JSON from compiled cards.

This script:
1. Loads cards_compiled.json
2. Recompiles abilities using semantic generator (no opcodes, no bit-packing)
3. Includes original Japanese text and translations
4. Outputs unified_semantic_frames.json
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from compiler.semantic_generator import SemanticGenerator, generate_semantic_frames
from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import Ability


def load_cards_compiled(path: str) -> Dict[str, Any]:
    """Load the compiled cards database."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_ability_text(text: str, parser: AbilityParserV2) -> List[Ability]:
    """Parse ability text into Ability objects."""
    if not text or not text.strip():
        return []
    try:
        return parser.parse(text)
    except Exception as e:
        print(f"Parse error: {e}")
        return []


def generate_unified_frames(cards_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate unified semantic frames for all cards."""
    parser = AbilityParserV2()
    generator = SemanticGenerator()
    
    unified = {
        "schema": "unified_semantic_frames.v1",
        "generated_at": "2026-03-29T00:00:00+00:00",
        "documentation": {
            "purpose": "Human-readable semantic frames preserving ability text",
            "note": "No opcodes, no bit-packing. Direct semantic representation.",
            "original_text": "Japanese card text as printed on cards",
            "translated_text": "English translation when available",
            "ability_text": "Specific text for this ability/effect"
        },
        "cards": []
    }
    
    member_db = cards_data.get('member_db', {})
    total_cards = len(member_db)
    
    print(f"Processing {total_cards} cards...")
    
    for idx, (card_id, card_data) in enumerate(member_db.items(), 1):
        if idx % 100 == 0:
            print(f"  Processed {idx}/{total_cards} cards...")
        
        original_text = card_data.get('original_text', '')
        translated_text = card_data.get('original_text_en', '')
        
        # Parse abilities from original text
        abilities = parse_ability_text(original_text, parser)
        
        # Generate semantic frames
        semantic_abilities = []
        if abilities:
            semantic_abilities = generate_semantic_frames(abilities, card_data)
        
        # Build LEAN card entry - only essential fields for ability execution
        card_entry = {
            "card_id": card_id,
            "card_no": card_data.get('card_no', ''),
            "original_text": original_text,
            "abilities": semantic_abilities
        }
        
        unified["cards"].append(card_entry)
    
    return unified


def save_unified_frames(data: Dict[str, Any], output_path: str):
    """Save unified frames to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved unified semantic frames to: {output_path}")


def save_minified_frames(data: Dict[str, Any], output_path: str):
    """Save minified version for runtime use."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"Saved minified unified frames to: {output_path}")


def main():
    """Main entry point."""
    input_path = project_root / "data" / "cards_compiled.json"
    output_path = project_root / "data" / "unified_semantic_frames.json"
    minified_path = project_root / "data" / "unified_semantic_frames.min.json"
    
    print("Loading cards database...")
    cards_data = load_cards_compiled(str(input_path))
    
    print("Generating unified semantic frames...")
    unified_data = generate_unified_frames(cards_data)
    
    # Add statistics
    total_abilities = sum(len(c.get('abilities', [])) for c in unified_data['cards'])
    total_effects = sum(
        len(a.get('effects', []))
        for c in unified_data['cards']
        for a in c.get('abilities', [])
    )
    
    unified_data['statistics'] = {
        "total_cards": len(unified_data['cards']),
        "total_abilities": total_abilities,
        "total_effects": total_effects
    }
    
    print(f"\nStatistics:")
    print(f"  Cards: {total_abilities}")
    print(f"  Abilities: {total_abilities}")
    print(f"  Effects: {total_effects}")
    
    save_unified_frames(unified_data, str(output_path))
    save_minified_frames(unified_data, str(minified_path))
    
    print("\nDone! Unified semantic frames generated.")
    print(f"\nExample output (first card):")
    if unified_data['cards']:
        first = unified_data['cards'][0]
        print(f"  Card: {first['card_no']}")
        print(f"  Original text: {first['original_text'][:80]}...")
        print(f"  Abilities: {len(first['abilities'])}")
        if first['abilities']:
            ab = first['abilities'][0]
            print(f"  First ability ({ab['trigger']}): {len(ab['effects'])} effects")


if __name__ == "__main__":
    main()
