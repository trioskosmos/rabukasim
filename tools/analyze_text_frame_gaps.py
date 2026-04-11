#!/usr/bin/env python3
"""
Analyze abilities where text mentions effects not covered by frames.

This tool:
1. Parses Japanese ability text to extract mentioned effects
2. Compares against actual frame opcodes
3. Reports gaps where text mentions things frames don't implement
"""

import json
import re
import sys
from typing import List, Dict, Set, Tuple, Optional

# Keywords that indicate specific frame types should exist
TEXT_TO_OPCODE_MAPPING = {
    # Draw effects
    "引く": "DRAW",
    "ドロー": "DRAW",
    
    # Discard/Mill
    "控え室に置く": "MOVE_TO_DISCARD",
    "控え室に置いて": "MOVE_TO_DISCARD",
    "控え室に": "MOVE_TO_DISCARD",
    
    # Recovery (from discard to hand)
    "手札に加える": "RECOVER",
    "手札に加え": "RECOVER",
    "手札に戻す": "RECOVER",
    
    # Energy
    "エネルギー": "ENERGY",
    "エネルギーを": "ENERGY",
    
    # Blades/Hearts
    "ブレード": "ADD_BLADES",
    "ハート": "ADD_HEARTS",
    
    # Tap/Untap
    "リラックス": "TAP",
    "アクティブ": "ACTIVATE_ENERGY",
    
    # Baton
    "バトン": "BATON",
    
    # Modal/Choice
    "するか、": "SELECT_MODE",
    "するか": "SELECT_MODE",
    "のいずれか": "SELECT_MODE",
    
    # Position
    "【センター】": "IS_CENTER",
    "【左サイド】": "HAS_KEYWORD",
    "【右サイド】": "HAS_KEYWORD",
    
    # Negate
    "無効": "NEGATE_EFFECT",
    
    # Deck manipulation
    "デッキの": "DECK",
    "デッキに": "DECK",
    "デッキの上": "DECK_TOP",
    "デッキの下": "DECK_BOTTOM",
    "デッキの一番上": "DECK_TOP",
    "デッキの一番下": "DECK_BOTTOM",
    
    # Look/Choose
    "見て": "LOOK",
    "選び": "SELECT",
    "選ん": "SELECT",
    
    # Swap/Move
    "入れ替": "SWAP",
    "移動": "MOVE",
    
    # Play from zones
    "登場させる": "PLAY",
    "ステージに": "PLAY",
}


def extract_mentioned_effects(text: str) -> Set[str]:
    """Extract what effects are mentioned in the ability text"""
    effects = set()
    
    for keyword, effect_type in TEXT_TO_OPCODE_MAPPING.items():
        if keyword in text:
            effects.add(effect_type)
    
    return effects


def extract_frame_effects(frames: List[Dict]) -> Set[str]:
    """Extract what effects are implemented in frames"""
    effects = set()
    
    for frame in frames:
        op = frame.get("op", "")
        
        # Map opcodes to effect categories
        if op == "DRAW":
            effects.add("DRAW")
        elif op in ["MOVE_TO_DISCARD", "DISCARDED_CARDS"]:
            effects.add("MOVE_TO_DISCARD")
        elif op in ["RECOVER_MEMBER", "RECOVER_LIVE"]:
            effects.add("RECOVER")
        elif op in ["PAY_ENERGY", "ENERGY_CHARGE", "ACTIVATE_ENERGY", "COUNT_ENERGY"]:
            effects.add("ENERGY")
        elif op == "ADD_BLADES":
            effects.add("ADD_BLADES")
        elif op == "ADD_HEARTS":
            effects.add("ADD_HEARTS")
        elif op in ["SET_TAPPED", "TAP_OPPONENT"]:
            effects.add("TAP")
        elif op == "BATON":
            effects.add("BATON")
        elif op == "SELECT_MODE":
            effects.add("SELECT_MODE")
        elif op in ["HAS_KEYWORD", "IS_CENTER"]:
            effects.add(op)
        elif op == "NEGATE_EFFECT":
            effects.add("NEGATE_EFFECT")
        elif op in ["LOOK_AND_CHOOSE", "LOOK_DECK", "LOOK_REORDER_DISCARD"]:
            effects.add("LOOK")
        elif op in ["SELECT_CARDS", "SELECT_MEMBER"]:
            effects.add("SELECT")
        elif op == "SWAP_ZONE":
            effects.add("SWAP")
        elif op in ["PLAY_MEMBER_FROM_HAND", "PLAY_MEMBER_FROM_DISCARD"]:
            effects.add("PLAY")
        elif op == "MOVE_MEMBER":
            effects.add("MOVE")
        elif op in ["MOVE_TO_DECK", "ORDER_DECK"]:
            effects.add("DECK")
    
    return effects


def analyze_ability(ability: Dict, idx: int) -> Dict:
    """Analyze a single ability for text/frame gaps"""
    text = ability.get("primary_text_jp", "")
    frames = ability.get("frames", [])
    card = ability.get("card_refs", [{}])[0]
    trigger = ability.get("trigger", "UNKNOWN")
    
    if not text:
        return None
    
    mentioned = extract_mentioned_effects(text)
    implemented = extract_frame_effects(frames)
    
    # Find gaps
    not_implemented = mentioned - implemented
    extra_implemented = implemented - mentioned
    
    return {
        "index": idx,
        "name": card.get("name", "Unknown"),
        "card_no": card.get("card_no", "N/A"),
        "trigger": trigger,
        "text_preview": text[:80],
        "mentioned_effects": sorted(mentioned),
        "implemented_effects": sorted(implemented),
        "not_implemented": sorted(not_implemented),
        "extra_implemented": sorted(extra_implemented),
        "frame_count": len(frames),
    }


def analyze_nuanced_gaps(ability: Dict, idx: int) -> Optional[Dict]:
    """Look for nuanced gaps like missing costs, wrong zones, missing filters"""
    text = ability.get("primary_text_jp", "")
    frames = ability.get("frames", [])
    
    if not text:
        return None
    
    issues = []
    
    # Check for cost-payment text without PAY_ENERGY frame
    cost_patterns = [
        (r"エネルギー[^\\n]{0,10}支払", "PAY_ENERGY", "Text mentions paying energy but no PAY_ENERGY frame"),
        (r"手札[^\\n]{0,10}枚[^\\n]{0,10}控え室", "MOVE_TO_DISCARD cost", "Text mentions discarding hand as cost but no discard frame"),
        (r"リラックスしてもよい", "SET_TAPPED cost", "Text mentions optional tap as cost but no SET_TAPPED frame"),
    ]
    
    for pattern, expected_op, message in cost_patterns:
        if re.search(pattern, text) and not any(f.get("op") == expected_op for f in frames):
            # Check if it's actually missing (some may be conditional)
            issues.append({
                "type": "missing_cost",
                "expected_opcode": expected_op,
                "message": message
            })
    
    # Check for deck mill vs hand discard confusion
    if "デッキの上から" in text or "デッキの上" in text:
        discard_frames = [f for f in frames if f.get("op") == "MOVE_TO_DISCARD"]
        for frame in discard_frames:
            slot = frame.get("slot", {})
            if slot.get("source_zone") == "HAND":
                issues.append({
                    "type": "wrong_source_zone",
                    "message": "Text says mill from DECK but frame uses HAND as source",
                    "frame": frame
                })
    
    # Check for conditional "if done" effects missing the check
    if "そうした場合" in text or "それを行った場合" in text:
        has_conditional_jump = any(f.get("op") == "JUMP_IF_FALSE" for f in frames)
        if not has_conditional_jump:
            issues.append({
                "type": "missing_conditional",
                "message": "Text has conditional 'if done' but no JUMP_IF_FALSE frame"
            })
    
    # Check for group filters mentioned but not implemented
    group_mentions = re.findall(r'『(.+?)』', text)
    if group_mentions:
        for group in group_mentions:
            # Check if any frame has this group filter
            has_filter = False
            for frame in frames:
                attr = frame.get("attr", {})
                if attr.get("char_id_1") == group or attr.get("group_id") == group:
                    has_filter = True
                    break
            if not has_filter:
                issues.append({
                    "type": "missing_group_filter",
                    "group": group,
                    "message": f"Text mentions group '{group}' but no frame has this filter"
                })
    
    if issues:
        card = ability.get("card_refs", [{}])[0]
        return {
            "index": idx,
            "name": card.get("name", "Unknown"),
            "card_no": card.get("card_no", "N/A"),
            "text_preview": text[:80],
            "issues": issues,
            "issue_count": len(issues)
        }
    
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_text_frame_gaps.py <ability_frame_source.json>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data.get("abilities", [])
    
    # Analyze all abilities
    results = []
    gaps_found = []
    nuanced_issues = []
    
    for idx, ability in enumerate(abilities):
        result = analyze_ability(ability, idx)
        if result:
            results.append(result)
            if result["not_implemented"]:
                gaps_found.append(result)
        
        # Also check nuanced gaps
        nuanced = analyze_nuanced_gaps(ability, idx)
        if nuanced:
            nuanced_issues.append(nuanced)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"TEXT/FRAME GAP ANALYSIS")
    print(f"{'='*70}")
    print(f"Total abilities analyzed: {len(results)}")
    print(f"Abilities with missing effects: {len(gaps_found)} ({100*len(gaps_found)/len(results):.1f}%)")
    print(f"Abilities with nuanced issues: {len(nuanced_issues)} ({100*len(nuanced_issues)/len(results):.1f}%)")
    
    # Show gaps by category
    gap_categories = {}
    for gap in gaps_found:
        for effect in gap["not_implemented"]:
            gap_categories[effect] = gap_categories.get(effect, 0) + 1
    
    print(f"\n{'='*70}")
    print("GAP CATEGORIES (effects mentioned in text but missing from frames)")
    print(f"{'='*70}")
    for effect, count in sorted(gap_categories.items(), key=lambda x: -x[1])[:15]:
        print(f"  {effect}: {count} abilities")
    
    # Show nuanced issues
    if nuanced_issues:
        print(f"\n{'='*70}")
        print("NUANCED ISSUES (costs, wrong zones, missing filters)")
        print(f"{'='*70}")
        
        # Group by issue type
        by_type = {}
        for issue in nuanced_issues:
            for detail in issue["issues"]:
                itype = detail["type"]
                by_type[itype] = by_type.get(itype, 0) + 1
        
        for itype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"  {itype}: {count} occurrences")
        
        # Show specific examples
        print(f"\n--- Examples of nuanced issues ---")
        for issue in nuanced_issues[:10]:
            print(f"\nAbility #{issue['index']}: {issue['name']} ({issue['card_no']})")
            print(f"  Text: {issue['text_preview']}...")
            for detail in issue["issues"][:2]:  # Show first 2 issues
                print(f"  >> [{detail['type']}] {detail['message']}")
    
    # Show specific examples of effect gaps
    print(f"\n{'='*70}")
    print("EXAMPLES OF MISSING EFFECTS")
    print(f"{'='*70}")
    
    for gap in gaps_found[:10]:
        print(f"\n--- Ability #{gap['index']}: {gap['name']} ({gap['card_no']}) ---")
        print(f"  Text: {gap['text_preview']}...")
        print(f"  Mentioned: {', '.join(gap['mentioned_effects'])}")
        print(f"  Implemented: {', '.join(gap['implemented_effects']) if gap['implemented_effects'] else 'NONE'}")
        print(f"  >> MISSING: {', '.join(gap['not_implemented'])}")
    
    # Save detailed report
    report_path = json_path.replace('.json', '_gap_analysis.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total": len(results),
                "with_gaps": len(gaps_found),
                "gap_rate": f"{100*len(gaps_found)/len(results):.1f}%",
                "with_nuanced_issues": len(nuanced_issues),
                "nuanced_rate": f"{100*len(nuanced_issues)/len(results):.1f}%"
            },
            "gap_categories": gap_categories,
            "nuanced_issue_types": by_type if nuanced_issues else {},
            "gaps": gaps_found,
            "nuanced_issues": nuanced_issues
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Full report saved to: {report_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
