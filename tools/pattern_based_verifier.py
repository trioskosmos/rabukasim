#!/usr/bin/env python3
"""
Pattern-Based Ability Verifier

Instead of naive keyword matching, this tool:
1. Extracts patterns from verified CORRECT abilities
2. Matches new abilities against these known-good patterns
3. Only flags deviations from verified patterns (reduces false positives)
4. Focuses on known bug patterns (copy-paste errors, trigger mismatches)

Usage:
    python pattern_based_verifier.py build    # Extract patterns from verified abilities
    python pattern_based_verifier.py verify   # Check all abilities against patterns
"""

import json
import re
import sys
from difflib import SequenceMatcher
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


def normalize_text(text: str) -> str:
    """Normalize text for pattern matching"""
    # Replace numbers with placeholders
    text = re.sub(r'\d+', '{N}', text)
    # Replace group names
    groups = ["μ's", "Aqours", "Liella", "虹ヶ咲", "SaintSnow", "Hasunosora", 
              "BiBi", "Printemps", "Lily White", "Guilty Kiss", "AZALEA", "CYaRon!",
              "Mira-cra Park", "EdelNote", "Cerise Bouquet", "DOLLCHESTRA"]
    for group in groups:
        text = text.replace(group, '{GROUP}')
    # Replace card names (simplified - between quotes)
    text = re.sub(r'『(.+?)』', '{CARD}', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text


def extract_frame_signature(frames: List[Dict]) -> str:
    """Extract a signature of frame opcodes and key attributes"""
    parts = []
    for frame in frames:
        op = frame.get("op", "NOP")
        attrs = []
        
        # Add key attributes that affect behavior
        if frame.get("attr", {}).get("is_optional"):
            attrs.append("opt")
        if frame.get("slot", {}).get("source_zone"):
            attrs.append(f"src:{frame['slot']['source_zone']}")
        if frame.get("slot", {}).get("dest_zone"):
            attrs.append(f"dst:{frame['slot']['dest_zone']}")
        if frame.get("attr", {}).get("char_id_1"):
            attrs.append(f"grp:{frame['attr']['char_id_1']}")
        
        if attrs:
            parts.append(f"{op}({','.join(attrs)})")
        else:
            parts.append(op)
    
    return "->".join(parts)


def build_patterns(abilities_json: str, verified_json: str) -> Dict:
    """Build pattern library from verified correct abilities"""
    
    with open(abilities_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(verified_json, 'r', encoding='utf-8') as f:
        verified = json.load(f)
    
    abilities = data.get("abilities", [])
    verified_indices = {v['index'] for v in verified.get('verified_abilities', [])}
    
    patterns = defaultdict(list)
    
    for idx in verified_indices:
        if idx >= len(abilities):
            continue
        
        ability = abilities[idx]
        text = ability.get("primary_text_jp", "")
        frames = ability.get("frames", [])
        
        if not text or not frames:
            continue
        
        # Normalize and extract pattern
        normalized = normalize_text(text)
        signature = extract_frame_signature(frames)
        
        # Store pattern
        pattern = {
            "index": idx,
            "name": ability.get("card_refs", [{}])[0].get("name", "Unknown"),
            "normalized_text": normalized,
            "frame_signature": signature,
            "trigger": ability.get("trigger", "UNKNOWN"),
            "frame_count": len(frames)
        }
        
        # Index by frame signature for lookup
        patterns[signature].append(pattern)
    
    return dict(patterns)


def find_best_pattern_match(text: str, frames: List[Dict], patterns: Dict) -> Optional[Dict]:
    """Find best matching pattern for given ability"""
    normalized = normalize_text(text)
    signature = extract_frame_signature(frames)
    
    # First try exact signature match
    if signature in patterns:
        candidates = patterns[signature]
        # Find best text match among candidates
        best = None
        best_score = 0
        for candidate in candidates:
            score = SequenceMatcher(None, normalized, candidate["normalized_text"]).ratio()
            if score > best_score:
                best_score = score
                best = candidate
        return {
            "match_type": "exact_signature",
            "score": best_score,
            "candidate": best
        }
    
    # Try frame count match with text similarity
    frame_count = len(frames)
    best = None
    best_score = 0
    
    for sig, candidates in patterns.items():
        for candidate in candidates:
            # Score based on text similarity and frame count proximity
            text_score = SequenceMatcher(None, normalized, candidate["normalized_text"]).ratio()
            count_diff = abs(frame_count - candidate["frame_count"])
            count_penalty = count_diff * 0.1  # Penalty for frame count mismatch
            score = text_score - count_penalty
            
            if score > best_score and score > 0.5:  # Threshold
                best_score = score
                best = candidate
    
    if best:
        return {
            "match_type": "fuzzy",
            "score": best_score,
            "candidate": best
        }
    
    return None


def detect_specific_bugs(ability: Dict, idx: int) -> List[Dict]:
    """Detect specific known bug patterns"""
    bugs = []
    text = ability.get("primary_text_jp", "")
    frames = ability.get("frames", [])
    trigger = ability.get("trigger", "UNKNOWN")
    
    # Bug 1: Copy-paste from Ability #5 pattern
    # Text says simple draw, but frames have "discard up to 3, draw that many"
    if re.search(r'カードを1枚引く[。]?$', text) or re.search(r'カードを1枚引く[。]', text):
        # Check for the discard-up-to-3 pattern
        if len(frames) >= 2:
            f0 = frames[0]
            f1 = frames[1]
            if (f0.get("op") == "MOVE_TO_DISCARD" and 
                f0.get("attr", {}).get("is_optional") and
                f0.get("value") == 3 and
                f1.get("op") == "DRAW" and
                f1.get("value") == 0):
                bugs.append({
                    "type": "COPY_PASTE_ERROR",
                    "severity": "CRITICAL",
                    "message": "Text says simple 'draw 1' but frames implement 'discard up to 3, draw that many' - likely copy-paste from Ability #5",
                    "fix": "Replace frames with simple DRAW 1"
                })
    
    # Bug 2: Trigger mismatch - text says LIVE_START but frames say ON_PLAY
    if "ライブ開始時" in text and trigger == "ON_PLAY":
        bugs.append({
            "type": "TRIGGER_MISMATCH",
            "severity": "CRITICAL",
            "message": f"Text says LIVE_START but frames have {trigger}",
            "fix": "Change trigger to LIVE_START"
        })
    
    # Bug 3: Zone confusion - text says deck but frames use hand
    if "デッキの上から" in text or "デッキの上" in text:
        for frame in frames:
            if frame.get("op") == "MOVE_TO_DISCARD":
                slot = frame.get("slot", {})
                if slot.get("source_zone") == "HAND" and "手札" not in text[:text.find("デッキ")]:
                    bugs.append({
                        "type": "WRONG_SOURCE_ZONE",
                        "severity": "MAJOR",
                        "message": "Text says mill from DECK but frame uses HAND as source",
                        "fix": "Change source_zone from HAND to DECK"
                    })
                    break
    
    # Bug 4: SUM_VALUE no-op (empty SUM_VALUE frames)
    for i, frame in enumerate(frames):
        if frame.get("op") == "SUM_VALUE":
            # Check if SUM_VALUE has no meaningful parameters
            params = frame.get("params", {})
            attr = frame.get("attr", {})
            if not params and not attr.get("value"):
                bugs.append({
                    "type": "SUM_VALUE_NOOP",
                    "severity": "WARNING",
                    "message": f"SUM_VALUE at frame {i} has no parameters - likely placeholder/no-op",
                    "fix": "Verify if SUM_VALUE is necessary or remove"
                })
    
    # Bug 5: Group filter mismatch
    group_mentions = re.findall(r'『(.+?)』', text)
    for group in group_mentions:
        # Check if any frame has this group filter
        has_filter = False
        for frame in frames:
            attr = frame.get("attr", {})
            if attr.get("char_id_1") == group or attr.get("group_id") == group:
                has_filter = True
                break
        if not has_filter:
            bugs.append({
                "type": "MISSING_GROUP_FILTER",
                "severity": "MAJOR",
                "message": f"Text mentions group '{group}' but no frame has this filter",
                "fix": f"Add group filter for '{group}' to appropriate frame"
            })
    
    return bugs


def verify_all(abilities_json: str, verified_json: str):
    """Verify all abilities against patterns and known bugs"""
    
    print("Building pattern library from verified abilities...")
    patterns = build_patterns(abilities_json, verified_json)
    print(f"  Extracted {len(patterns)} unique frame signatures from verified abilities")
    
    with open(abilities_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data.get("abilities", [])
    
    results = {
        "matched": [],
        "unmatched": [],
        "bugs_found": []
    }
    
    print(f"\nAnalyzing {len(abilities)} abilities...")
    
    for idx, ability in enumerate(abilities):
        text = ability.get("primary_text_jp", "")
        frames = ability.get("frames", [])
        
        if not text:
            continue
        
        # Find pattern match
        match = find_best_pattern_match(text, frames, patterns)
        
        # Detect specific bugs
        bugs = detect_specific_bugs(ability, idx)
        
        card = ability.get("card_refs", [{}])[0]
        result = {
            "index": idx,
            "name": card.get("name", "Unknown"),
            "card_no": card.get("card_no", "N/A"),
            "trigger": ability.get("trigger", "UNKNOWN"),
            "text": text[:80],
            "frame_count": len(frames)
        }
        
        if bugs:
            result["bugs"] = bugs
            results["bugs_found"].append(result)
        elif match and match["score"] > 0.8:
            result["match"] = match
            results["matched"].append(result)
        else:
            result["match"] = match
            results["unmatched"].append(result)
    
    # Print summary
    print(f"\n{'='*70}")
    print("VERIFICATION RESULTS")
    print(f"{'='*70}")
    print(f"Total abilities: {len(abilities)}")
    print(f"Matched known patterns: {len(results['matched'])} ({100*len(results['matched'])/len(abilities):.1f}%)")
    print(f"Unmatched (new patterns): {len(results['unmatched'])} ({100*len(results['unmatched'])/len(abilities):.1f}%)")
    print(f"Bugs detected: {len(results['bugs_found'])} ({100*len(results['bugs_found'])/len(abilities):.1f}%)")
    
    # Show bugs by type
    if results["bugs_found"]:
        bug_types = defaultdict(int)
        for ability in results["bugs_found"]:
            for bug in ability["bugs"]:
                bug_types[bug["type"]] += 1
        
        print(f"\nBug breakdown:")
        for btype, count in sorted(bug_types.items(), key=lambda x: -x[1]):
            print(f"  {btype}: {count}")
        
        # Show specific bug examples
        print(f"\n{'='*70}")
        print("BUG EXAMPLES")
        print(f"{'='*70}")
        
        for ability in results["bugs_found"][:10]:
            print(f"\n--- Ability #{ability['index']}: {ability['name']} ({ability['card_no']}) ---")
            print(f"  Text: {ability['text']}...")
            for bug in ability["bugs"][:2]:
                print(f"  >> [{bug['severity']}] {bug['type']}: {bug['message']}")
                print(f"     Fix: {bug['fix']}")
    
    # Save report
    report_path = abilities_json.replace('.json', '_pattern_verification.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nFull report saved to: {report_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "verify":
        verify_all(
            "C:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\data\\ability_frame_source.json",
            "C:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\data\\verified_correct_abilities.json"
        )
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
