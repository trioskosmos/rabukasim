#!/usr/bin/env python3
"""
Ability Phrase Miner - Data-Driven Frame Verification

Instead of hand-written regex patterns, this tool:
1. Takes abilities marked as CORRECT from the audit
2. Extracts fixed phrases and their corresponding frames
3. Builds a phrase → frame mapping dictionary
4. Matches new abilities against known phrases
5. Flags unknown phrases for manual review

Usage:
    python ability_phrase_miner.py build <audit_file> <abilities_json>  # Build phrase dictionary
    python ability_phrase_miner.py verify <abilities_json> <phrase_dict>   # Verify abilities
    python ability_phrase_miner.py learn <abilities_json> <corrections>  # Learn from fixes
"""

import json
import re
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
import difflib


@dataclass
class PhraseTemplate:
    """A phrase template with variable slots"""
    fixed_parts: List[str]  # The fixed text segments
    variable_slots: List[str]  # Types: NUMBER, GROUP, CARD_TYPE, etc.
    frames: List[Dict]  # The frame sequence
    source_ability: int  # Which ability this came from
    confidence: float = 1.0  # How many times we've seen this


def tokenize_japanese(text: str) -> List[str]:
    """Tokenize Japanese text into meaningful segments"""
    # Split on numbers first
    tokens = []
    current = ""
    
    for char in text:
        if char.isdigit():
            if current:
                tokens.append(current)
                current = ""
            tokens.append(f"__NUM__")
        else:
            current += char
    
    if current:
        tokens.append(current)
    
    # Further split on common boundaries
    result = []
    for token in tokens:
        if token == "__NUM__":
            result.append(token)
            continue
        
        # Split on punctuation and particles that often indicate clause boundaries
        parts = re.split(r'(。|:|：|、|！|？|してもよい|そうした場合|場合)', token)
        for p in parts:
            if p:
                result.append(p)
    
    return result


def extract_variables(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Extract variable parts from text, return template + variable mapping
    
    Example: "カードを3枚引く" -> "カードを__NUM__枚引く", {"__NUM__": "3"}
    """
    variables = {}
    counter = 0
    
    # Replace numbers
    def replace_num(match):
        nonlocal counter
        key = f"__NUM{counter}__"
        variables[key] = match.group(0)
        counter += 1
        return key
    
    template = re.sub(r'\d+', replace_num, text)
    
    # Replace group names (can be expanded)
    group_names = ["μ's", "Aqours", "Liella", "虹ヶ咲", "SaintSnow", "Hasunosora", 
                   "BiBi", "Printemps", "Lily White", "Guilty Kiss", "AZALEA", "CYaRon!"]
    for group in group_names:
        if group in template:
            key = f"__GROUP{counter}__"
            variables[key] = group
            template = template.replace(group, key, 1)
            counter += 1
    
    return template, variables


class PhraseDictionary:
    """Dictionary of known phrases and their frames"""
    
    def __init__(self):
        self.phrases: Dict[str, List[Dict]] = {}  # template -> frames
        self.source_abilities: Dict[str, List[int]] = defaultdict(list)
        self.confidence: Dict[str, int] = defaultdict(int)
    
    def add_phrase(self, template: str, frames: List[Dict], ability_idx: int):
        """Add or update a phrase in the dictionary"""
        if template in self.phrases:
            # Verify frames match existing
            if self._frames_match(self.phrases[template], frames):
                self.confidence[template] += 1
            else:
                # Frame mismatch - mark as ambiguous
                print(f"Warning: Phrase '{template[:50]}...' has conflicting frames")
        else:
            self.phrases[template] = frames
            self.confidence[template] = 1
        
        self.source_abilities[template].append(ability_idx)
    
    def _frames_match(self, frames1: List[Dict], frames2: List[Dict]) -> bool:
        """Check if two frame sequences are equivalent"""
        if len(frames1) != len(frames2):
            return False
        
        for f1, f2 in zip(frames1, frames2):
            if f1.get("op") != f2.get("op"):
                return False
            # Could add more detailed comparison here
        
        return True
    
    def find_best_match(self, text: str, threshold: float = 0.85) -> Optional[Tuple[str, float, Dict]]:
        """
        Find best matching phrase for given text.
        Returns (template, similarity_score, extracted_variables)
        """
        template, variables = extract_variables(text)
        
        best_match = None
        best_score = 0.0
        
        for known_template in self.phrases.keys():
            # Exact match first
            if template == known_template:
                return known_template, 1.0, variables
            
            # Fuzzy match using sequence similarity
            matcher = difflib.SequenceMatcher(None, template, known_template)
            score = matcher.ratio()
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = known_template
        
        if best_match:
            return best_match, best_score, variables
        
        return None
    
    def save(self, filepath: str):
        """Save dictionary to JSON"""
        data = {
            "phrases": self.phrases,
            "confidence": dict(self.confidence),
            "source_abilities": dict(self.source_abilities),
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> "PhraseDictionary":
        """Load dictionary from JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pd = cls()
        pd.phrases = data.get("phrases", {})
        pd.confidence = defaultdict(int, data.get("confidence", {}))
        pd.source_abilities = defaultdict(list, data.get("source_abilities", {}))
        return pd


class AuditParser:
    """Parse audit findings to extract correct abilities"""
    
    CORRECT_MARKER = "CORRECT"
    
    def parse_correct_abilities(self, audit_text: str) -> List[int]:
        """Extract indices of abilities marked as correct from audit markdown"""
        correct_indices = []
        
        # Look for patterns like "Ability #5: ... ✓ CORRECT"
        for match in re.finditer(r'Ability\s*#(\d+)\s*.*?(?:Status|status)[：:\s].*?(?:✓|CORRECT|Correct)', audit_text, re.DOTALL):
            try:
                idx = int(match.group(1))
                correct_indices.append(idx)
            except ValueError:
                continue
        
        # Also match simpler format
        for match in re.finditer(r'Ability\s*#(\d+)\s*.*?(?:✓|CORRECT|Correct)', audit_text):
            try:
                idx = int(match.group(1))
                if idx not in correct_indices:
                    correct_indices.append(idx)
            except ValueError:
                continue
        
        return sorted(set(correct_indices))


def build_phrase_dictionary(abilities_json: str, audit_file: str, output_file: str):
    """Build phrase dictionary from correct abilities"""
    
    # Load audit file
    with open(audit_file, 'r', encoding='utf-8') as f:
        audit_text = f.read()
    
    parser = AuditParser()
    correct_indices = parser.parse_correct_abilities(audit_text)
    print(f"Found {len(correct_indices)} abilities marked as CORRECT in audit")
    
    # Load abilities JSON
    with open(abilities_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data.get("abilities", [])
    
    # Build dictionary
    phrase_dict = PhraseDictionary()
    
    for idx in correct_indices:
        if idx >= len(abilities):
            print(f"Warning: Ability index {idx} out of range")
            continue
        
        ability = abilities[idx]
        text = ability.get("primary_text_jp", "")
        frames = ability.get("frames", [])
        
        if not text or not frames:
            continue
        
        # Extract template and add to dictionary
        template, variables = extract_variables(text)
        phrase_dict.add_phrase(template, frames, idx)
        
        print(f"Added ability #{idx}: {template[:60]}...")
    
    # Save dictionary
    phrase_dict.save(output_file)
    print(f"\nSaved {len(phrase_dict.phrases)} unique phrases to {output_file}")
    
    # Print high-confidence phrases
    print("\nHigh-confidence phrases (>1 occurrence):")
    for phrase, count in sorted(phrase_dict.confidence.items(), key=lambda x: -x[1]):
        if count > 1:
            print(f"  [{count}x] {phrase[:60]}...")


def verify_abilities(abilities_json: str, phrase_dict_file: str, output_report: str):
    """Verify all abilities against phrase dictionary"""
    
    # Load phrase dictionary
    phrase_dict = PhraseDictionary.load(phrase_dict_file)
    print(f"Loaded {len(phrase_dict.phrases)} known phrases")
    
    # Load all abilities
    with open(abilities_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data.get("abilities", [])
    
    results = {
        "matched": [],
        "partial": [],
        "unknown": [],
        "total": len(abilities),
    }
    
    for idx, ability in enumerate(abilities):
        text = ability.get("primary_text_jp", "")
        frames = ability.get("frames", [])
        card = ability.get("card_refs", [{}])[0]
        
        if not text:
            continue
        
        # Try to match
        match = phrase_dict.find_best_match(text, threshold=0.85)
        
        if match:
            template, score, variables = match
            expected_frames = phrase_dict.phrases[template]
            
            # Check if frames match
            if phrase_dict._frames_match(expected_frames, frames):
                results["matched"].append({
                    "ability": idx,
                    "card": card.get("name"),
                    "card_no": card.get("card_no"),
                    "match_score": score,
                })
            else:
                # Similar text but different frames - potential mismatch
                results["partial"].append({
                    "ability": idx,
                    "card": card.get("name"),
                    "card_no": card.get("card_no"),
                    "template": template,
                    "match_score": score,
                    "expected_frames": expected_frames,
                    "actual_frames": frames,
                })
        else:
            # No match found
            results["unknown"].append({
                "ability": idx,
                "card": card.get("name"),
                "card_no": card.get("card_no"),
                "text": text[:100],
            })
    
    # Save report
    with open(output_report, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"\n=== VERIFICATION SUMMARY ===")
    print(f"Total abilities: {results['total']}")
    print(f"Fully matched: {len(results['matched'])} ({100*len(results['matched'])/results['total']:.1f}%)")
    print(f"Partial match (text similar, frames differ): {len(results['partial'])} ({100*len(results['partial'])/results['total']:.1f}%)")
    print(f"Unknown (new phrases): {len(results['unknown'])} ({100*len(results['unknown'])/results['total']:.1f}%)")
    
    if results["partial"]:
        print("\n=== PARTIAL MATCHES (Potential Issues) ===")
        for item in results["partial"][:10]:
            print(f"  Ability #{item['ability']}: {item['card']} ({item['card_no']})")
            print(f"    Similarity: {item['match_score']:.2%}")
            print(f"    Template: {item['template'][:50]}...")
    
    if results["unknown"]:
        print(f"\n=== UNKNOWN PHRASES (First 5) ===")
        for item in results["unknown"][:5]:
            print(f"  Ability #{item['ability']}: {item['card']} ({item['card_no']})")
            print(f"    Text: {item['text'][:60]}...")


def interactive_learning(abilities_json: str, phrase_dict_file: str):
    """Interactive mode to teach new phrases"""
    
    phrase_dict = PhraseDictionary.load(phrase_dict_file)
    
    with open(abilities_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data.get("abilities", [])
    
    print("\n=== Interactive Learning Mode ===")
    print("Reviewing unknown abilities and adding new phrases...")
    print("Commands: y = yes (add), n = no (skip), s = similar (find similar), q = quit\n")
    
    added = 0
    skipped = 0
    
    for idx, ability in enumerate(abilities):
        text = ability.get("primary_text_jp", "")
        frames = ability.get("frames", [])
        
        if not text:
            continue
        
        # Skip if already known
        match = phrase_dict.find_best_match(text, threshold=0.95)
        if match and match[1] > 0.95:
            continue
        
        print(f"\n--- Ability #{idx} ---")
        print(f"Text: {text[:80]}...")
        print(f"Frames: {len(frames)} frames")
        
        # Check for similar phrases
        similar = phrase_dict.find_best_match(text, threshold=0.70)
        if similar:
            template, score, _ = similar
            print(f"\nMost similar known phrase ({score:.0%}):")
            print(f"  {template[:60]}...")
        
        cmd = input("\nAdd this phrase? (y/n/s/q): ").strip().lower()
        
        if cmd == 'q':
            break
        elif cmd == 'y':
            template, _ = extract_variables(text)
            phrase_dict.add_phrase(template, frames, idx)
            added += 1
            print("  -> Added to dictionary")
        elif cmd == 's':
            # Show all similar phrases
            print("\nAll similar phrases (70%+ match):")
            for template in phrase_dict.phrases.keys():
                matcher = difflib.SequenceMatcher(None, text, template)
                score = matcher.ratio()
                if score >= 0.70:
                    print(f"  [{score:.0%}] {template[:50]}...")
        else:
            skipped += 1
    
    # Save updated dictionary
    phrase_dict.save(phrase_dict_file)
    print(f"\nSaved dictionary. Added {added} new phrases, skipped {skipped}.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "build":
        if len(sys.argv) < 5:
            print("Usage: python ability_phrase_miner.py build <audit.md> <abilities.json> <output_phrases.json>")
            sys.exit(1)
        build_phrase_dictionary(sys.argv[3], sys.argv[2], sys.argv[4])
    
    elif command == "verify":
        if len(sys.argv) < 5:
            print("Usage: python ability_phrase_miner.py verify <abilities.json> <phrases.json> <report.json>")
            sys.exit(1)
        verify_abilities(sys.argv[2], sys.argv[3], sys.argv[4])
    
    elif command == "learn":
        if len(sys.argv) < 4:
            print("Usage: python ability_phrase_miner.py learn <abilities.json> <phrases.json>")
            sys.exit(1)
        interactive_learning(sys.argv[2], sys.argv[3])
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
