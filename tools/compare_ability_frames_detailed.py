import json
from pathlib import Path
from typing import Dict, Any, List, Optional

def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_matching_ability(ability: Dict, abilities_list: List[Dict]) -> Dict:
    """Find matching ability in list by card_refs."""
    if not ability.get('card_refs'):
        return None
    
    for ref in ability['card_refs']:
        card_no = ref.get('card_no', ref.get('card', ''))
        ability_idx = ref.get('ability_index', ref.get('index', 0))
        
        for other_ability in abilities_list:
            if not other_ability.get('card_refs'):
                continue
            for other_ref in other_ability['card_refs']:
                other_card_no = other_ref.get('card_no', other_ref.get('card', ''))
                other_ability_idx = other_ref.get('ability_index', other_ref.get('index', 0))
                if card_no == other_card_no and ability_idx == other_ability_idx:
                    return other_ability
    return None

def find_matching_semantic(card_no: str, ability_idx: int, semantic_abilities: List[Dict]) -> Optional[Dict]:
    """Find matching semantic ability by card number and ability index."""
    for semantic in semantic_abilities:
        cards = semantic.get('cards', [])
        for card_entry in cards:
            # Parse "PL!SP-pb1-023-L | Card Name (ab#0)" format
            if '|' in card_entry:
                parts = card_entry.split('|')
                semantic_card = parts[0].strip()
                ability_part = parts[1].strip() if len(parts) > 1 else ''
                
                # Extract ability index from (ab#N)
                semantic_idx = 0
                if '(ab#' in ability_part:
                    idx_str = ability_part.split('(ab#')[1].split(')')[0]
                    try:
                        semantic_idx = int(idx_str)
                    except ValueError:
                        pass
                
                if semantic_card == card_no and semantic_idx == ability_idx:
                    return semantic
    return None

def format_semantic_cost(semantic: Dict) -> str:
    """Format semantic cost as readable string."""
    cost = semantic.get('cost')
    if not cost:
        return "None"
    
    cost_type = cost.get('type', 'unknown')
    parts = [f"type={cost_type}"]
    
    if 'source' in cost:
        parts.append(f"source={cost['source']}")
    if 'destination' in cost:
        parts.append(f"dest={cost['destination']}")
    if 'count' in cost:
        parts.append(f"count={cost['count']}")
    if 'target' in cost:
        parts.append(f"target={cost['target']}")
    if 'optional' in cost and cost['optional']:
        parts.append("optional")
    if 'text' in cost:
        parts.append(f"text='{cost['text'][:50]}...'")
    
    return " | ".join(parts)

def format_semantic_effect(semantic: Dict) -> str:
    """Format semantic effect as readable string."""
    effect = semantic.get('effect')
    if not effect:
        return "None"
    
    parts = []
    
    # Handle single action
    if 'action' in effect:
        parts.append(f"action={effect['action']}")
        for key in ['count', 'card_type', 'source', 'destination', 'remainder_zone']:
            if key in effect:
                parts.append(f"{key}={effect[key]}")
    
    # Handle multiple actions
    if 'actions' in effect:
        actions = effect['actions']
        parts.append(f"actions[{len(actions)}]:")
        for i, action in enumerate(actions):
            action_parts = [f"  [{i}] action={action.get('action', 'unknown')}"]
            for key in ['count', 'card_type', 'source', 'destination', 'remainder_zone']:
                if key in action:
                    action_parts.append(f"{key}={action[key]}")
            parts.append(" | ".join(action_parts))
    
    return " | ".join(parts) if parts else json.dumps(effect, ensure_ascii=False, indent=2)[:200]

def compare_abilities_detailed(authored_path: Path, automated_path: Path, output_path: Path, semantic_path: Path = None):
    """Compare abilities with full text, semantic, and frame outputs."""
    authored = load_json(authored_path)
    automated = load_json(automated_path)
    
    # Load semantic data if available
    semantic_abilities = []
    if semantic_path and semantic_path.exists():
        semantic_data = load_json(semantic_path)
        semantic_abilities = semantic_data.get('unique_abilities', [])
    
    authored_abilities = authored.get('abilities', [])
    automated_abilities = automated.get('abilities', [])
    
    lines = []
    lines.append("=" * 120)
    lines.append("DETAILED ABILITY FRAME COMPARISON (with Semantic Data)")
    lines.append("=" * 120)
    lines.append("")
    lines.append(f"Authored abilities: {len(authored_abilities)}")
    lines.append(f"Automated abilities: {len(automated_abilities)}")
    if semantic_abilities:
        lines.append(f"Semantic abilities: {len(semantic_abilities)}")
    lines.append("")
    
    # Track which automated abilities we've seen
    seen_automated = set()
    
    # Compare authored abilities
    for idx, auth_ability in enumerate(authored_abilities):
        lines.append("=" * 120)
        lines.append(f"AUTHORED ABILITY #{idx + 1}")
        lines.append("=" * 120)
        
        # Get primary text
        primary_text = auth_ability.get('primary_text_jp', auth_ability.get('primary_text_en', ''))
        lines.append(f"Primary Text: {primary_text}")
        lines.append("")
        
        # Get card refs
        card_refs = auth_ability.get('card_refs', [])
        primary_card_no = None
        primary_ability_idx = 0
        if card_refs:
            lines.append("Card References:")
            for ref in card_refs:
                card_no = ref.get('card_no', ref.get('card', 'unknown'))
                name = ref.get('name', 'unknown')
                ability_idx = ref.get('ability_index', ref.get('index', 0))
                lines.append(f"  - {card_no} | {name} (ab#{ability_idx})")
                if primary_card_no is None:
                    primary_card_no = card_no
                    primary_ability_idx = ability_idx
        else:
            lines.append("Card References: None")
        lines.append("")
        
        # Find and display semantic data
        if semantic_abilities and primary_card_no:
            semantic = find_matching_semantic(primary_card_no, primary_ability_idx, semantic_abilities)
            if semantic:
                lines.append("SEMANTIC DATA (from abilities_extracted_from_cards.json):")
                lines.append(f"  Trigger: {semantic.get('triggers', 'None')}")
                lines.append(f"  Use Limit: {semantic.get('use_limit', 'None')}")
                lines.append(f"  Cost: {format_semantic_cost(semantic)}")
                lines.append(f"  Effect: {format_semantic_effect(semantic)}")
                lines.append("")
        
        # Find matching automated ability
        auto_ability = find_matching_ability(auth_ability, automated_abilities)
        
        if auto_ability:
            # Mark as seen
            for ref in auto_ability.get('card_refs', []):
                card_no = ref.get('card_no', ref.get('card', ''))
                ability_idx = ref.get('ability_index', ref.get('index', 0))
                seen_automated.add(f"{card_no}_{ability_idx}")
            
            lines.append("AUTHORED FRAMES:")
            auth_frames = auth_ability.get('frames', [])
            for frame in auth_frames:
                lines.append(f"  {json.dumps(frame, ensure_ascii=False, indent=2)}")
            lines.append("")
            
            lines.append("AUTOMATED FRAMES:")
            auto_frames = auto_ability.get('frames', [])
            for frame in auto_frames:
                lines.append(f"  {json.dumps(frame, ensure_ascii=False, indent=2)}")
            lines.append("")
            
            # Compare frames
            if auth_frames != auto_frames:
                lines.append("FRAME DIFFERENCES: YES")
                lines.append("")
            else:
                lines.append("FRAME DIFFERENCES: NO (identical)")
                lines.append("")
        else:
            lines.append("STATUS: NOT FOUND in automated")
            lines.append("")
            lines.append("AUTHORED FRAMES:")
            auth_frames = auth_ability.get('frames', [])
            for frame in auth_frames:
                lines.append(f"  {json.dumps(frame, ensure_ascii=False, indent=2)}")
            lines.append("")
        
        lines.append("")
    
    # Show abilities only in automated
    lines.append("=" * 120)
    lines.append("ABILITIES ONLY IN AUTOMATED")
    lines.append("=" * 120)
    lines.append("")
    
    for idx, auto_ability in enumerate(automated_abilities):
        # Check if this ability was already matched
        is_seen = False
        for ref in auto_ability.get('card_refs', []):
            card_no = ref.get('card_no', ref.get('card', ''))
            ability_idx = ref.get('ability_index', ref.get('index', 0))
            if f"{card_no}_{ability_idx}" in seen_automated:
                is_seen = True
                break
        
        if is_seen:
            continue
        
        lines.append("=" * 120)
        lines.append(f"AUTOMATED ABILITY #{idx + 1} (NOT IN AUTHORED)")
        lines.append("=" * 120)
        
        primary_text = auto_ability.get('primary_text_jp', auto_ability.get('primary_text_en', ''))
        lines.append(f"Primary Text: {primary_text}")
        lines.append("")
        
        card_refs = auto_ability.get('card_refs', [])
        if card_refs:
            lines.append("Card References:")
            for ref in card_refs:
                card_no = ref.get('card_no', ref.get('card', 'unknown'))
                name = ref.get('name', 'unknown')
                lines.append(f"  - {card_no} | {name}")
        else:
            lines.append("Card References: None")
        lines.append("")
        
        lines.append("AUTOMATED FRAMES:")
        auto_frames = auto_ability.get('frames', [])
        for frame in auto_frames:
            lines.append(f"  {json.dumps(frame, ensure_ascii=False, indent=2)}")
        lines.append("")
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"Detailed comparison saved to {output_path}")

if __name__ == "__main__":
    base_path = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data")
    authored_path = base_path / "ability_frame_source_authored.json"
    automated_path = base_path / "ability_frame_source.json"
    semantic_path = base_path / "abilities_extracted_from_cards.json"
    output_path = base_path / "frame_comparison_detailed.txt"
    
    compare_abilities_detailed(authored_path, automated_path, output_path, semantic_path)
