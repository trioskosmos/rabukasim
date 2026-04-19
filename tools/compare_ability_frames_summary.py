import json
from pathlib import Path
from typing import Dict, Any, Set

def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_ability_identifiers(abilities: list) -> Set[str]:
    """Extract unique identifiers from abilities list."""
    identifiers = set()
    for idx, ability in enumerate(abilities):
        # Try to create a unique identifier from card_refs or primary_text
        if 'card_refs' in ability and ability['card_refs']:
            for ref in ability['card_refs']:
                if isinstance(ref, dict):
                    card_no = ref.get('card_no', ref.get('card', 'unknown'))
                    ability_idx = ref.get('ability_index', ref.get('index', 0))
                    identifiers.add(f"{card_no}_{ability_idx}")
        elif 'primary_text_jp' in ability:
            # Use a hash of the text as identifier if no card_refs
            text_hash = hash(ability['primary_text_jp'][:100])
            identifiers.add(f"text_{text_hash}")
        else:
            # Fallback to index
            identifiers.add(f"index_{idx}")
    return identifiers

def compare_abilities(authored: list, automated: list) -> Dict[str, Any]:
    """Compare two ability lists."""
    authored_ids = get_ability_identifiers(authored)
    automated_ids = get_ability_identifiers(automated)
    
    only_authored = authored_ids - automated_ids
    only_automated = automated_ids - authored_ids
    common = authored_ids & automated_ids
    
    return {
        "authored_count": len(authored),
        "automated_count": len(automated),
        "only_authored_count": len(only_authored),
        "only_automated_count": len(only_automated),
        "common_count": len(common),
        "only_authored_sample": list(only_authored)[:10],
        "only_automated_sample": list(only_automated)[:10],
    }

def main():
    base_path = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data")
    authored_path = base_path / "ability_frame_source_authored.json"
    automated_path = base_path / "ability_frame_source.json"
    
    authored = load_json(authored_path)
    automated = load_json(automated_path)
    
    print("=" * 80)
    print("ABILITY FRAME COMPARISON SUMMARY")
    print("=" * 80)
    print()
    
    # Top-level keys
    authored_keys = set(authored.keys())
    automated_keys = set(automated.keys())
    
    print("TOP-LEVEL STRUCTURE:")
    print(f"  Authored keys: {sorted(authored_keys)}")
    print(f"  Automated keys: {sorted(automated_keys)}")
    print()
    
    # Compare each top-level key
    for key in sorted(authored_keys | automated_keys):
        print(f"\n{'=' * 80}")
        print(f"KEY: {key}")
        print(f"{'=' * 80}")
        
        if key not in authored:
            print(f"  Status: MISSING in authored")
            print(f"  Type in automated: {type(automated[key]).__name__}")
            if isinstance(automated[key], list):
                print(f"  Length: {len(automated[key])}")
        elif key not in automated:
            print(f"  Status: MISSING in automated")
            print(f"  Type in authored: {type(authored[key]).__name__}")
            if isinstance(authored[key], list):
                print(f"  Length: {len(authored[key])}")
        elif authored[key] == automated[key]:
            print(f"  Status: IDENTICAL")
            print(f"  Type: {type(authored[key]).__name__}")
        else:
            print(f"  Status: DIFFERENT")
            print(f"  Authored type: {type(authored[key]).__name__}")
            print(f"  Automated type: {type(automated[key]).__name__}")
            
            # Special handling for abilities list
            if key == "abilities" and isinstance(authored[key], list) and isinstance(automated[key], list):
                comparison = compare_abilities(authored[key], automated[key])
                print()
                print(f"  ABILITY COUNTS:")
                print(f"    Authored:  {comparison['authored_count']}")
                print(f"    Automated: {comparison['automated_count']}")
                print(f"    Difference: {comparison['automated_count'] - comparison['authored_count']}")
                print()
                print(f"  OVERLAP:")
                print(f"    Common abilities: {comparison['common_count']}")
                print(f"    Only in authored: {comparison['only_authored_count']}")
                print(f"    Only in automated: {comparison['only_automated_count']}")
                print()
                if comparison['only_authored_sample']:
                    print(f"  SAMPLE of abilities ONLY in authored (showing first {len(comparison['only_authored_sample'])}):")
                    for aid in comparison['only_authored_sample']:
                        print(f"    - {aid}")
                    if comparison['only_authored_count'] > 10:
                        print(f"    ... and {comparison['only_authored_count'] - 10} more")
                print()
                if comparison['only_automated_sample']:
                    print(f"  SAMPLE of abilities ONLY in automated (showing first {len(comparison['only_automated_sample'])}):")
                    for aid in comparison['only_automated_sample']:
                        print(f"    - {aid}")
                    if comparison['only_automated_count'] > 10:
                        print(f"    ... and {comparison['only_automated_count'] - 10} more")
            elif isinstance(authored[key], str) and isinstance(automated[key], str):
                print()
                print(f"  Authored value:")
                print(f"    {authored[key][:200]}")
                if len(authored[key]) > 200:
                    print(f"    ... ({len(authored[key])} total chars)")
                print()
                print(f"  Automated value:")
                print(f"    {automated[key][:200]}")
                if len(automated[key]) > 200:
                    print(f"    ... ({len(automated[key])} total chars)")
            else:
                print(f"  (Full comparison available in detailed output)")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total top-level keys: {len(authored_keys | automated_keys)}")
    print(f"Keys only in authored: {len(authored_keys - automated_keys)}")
    print(f"Keys only in automated: {len(automated_keys - authored_keys)}")
    print(f"Keys with differences: {len([k for k in (authored_keys & automated_keys) if authored[k] != automated[k]])}")

if __name__ == "__main__":
    main()
