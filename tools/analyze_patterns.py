#!/usr/bin/env python3
"""
Analyze pattern overlap and identify structures needing more breaking down.
"""
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    data_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    analysis = data.get("analysis", {})
    dsl_analysis = analysis.get("dsl_pattern_analysis", {})
    
    pattern_counts = dsl_analysis.get("pattern_counts", {})
    text_matches = dsl_analysis.get("text_matches", [])
    
    # Sort patterns by count
    sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
    
    print("PATTERN OVERLAP ANALYSIS")
    print("="*80)
    print(f"Total patterns: {len(pattern_counts)}")
    print(f"Total abilities: {dsl_analysis.get('total_texts', 0)}")
    print(f"Average coverage: {dsl_analysis.get('average_coverage', 0):.2%}")
    print()
    
    # Show top patterns by count
    print("TOP 20 PATTERNS BY MATCH COUNT")
    print("-"*80)
    for pattern, count in sorted_patterns[:20]:
        print(f"{pattern:40} {count:5d} matches")
    print()
    
    # Identify fragment patterns (likely overlapping)
    fragment_keywords = ["fragment", "generic", "atomic"]
    fragment_patterns = [p for p in pattern_counts.keys() if any(k in p for k in fragment_keywords)]
    
    print(f"FRAGMENT/ATOMIC PATTERNS (likely overlapping): {len(fragment_patterns)}")
    print("-"*80)
    for pattern in sorted(fragment_patterns):
        print(f"  {pattern:40} {pattern_counts[pattern]:5d} matches")
    print()
    
    # Identify semantic patterns (complete structures)
    semantic_keywords = ["cost_effect", "look_select_add", "gain_hearts", "conditional", "trigger", "discard_then", "place_to", "state_change"]
    semantic_patterns = [p for p in pattern_counts.keys() if any(k in p for k in semantic_keywords)]
    
    print(f"SEMANTIC PATTERNS (complete structures): {len(semantic_patterns)}")
    print("-"*80)
    for pattern in sorted(semantic_patterns):
        print(f"  {pattern:40} {pattern_counts[pattern]:5d} matches")
    print()
    
    # Analyze overlap by checking how many patterns match per ability
    matches_per_ability = [len(m.get("matches", [])) for m in text_matches]
    avg_matches = sum(matches_per_ability) / len(matches_per_ability) if matches_per_ability else 0
    
    print(f"AVERAGE PATTERNS PER ABILITY: {avg_matches:.1f}")
    print(f"MAX PATTERNS IN ONE ABILITY: {max(matches_per_ability) if matches_per_ability else 0}")
    print()
    
    # Show abilities with most pattern matches (likely high overlap)
    print("ABILITIES WITH MOST PATTERN MATCHES (high overlap)")
    print("-"*80)
    sorted_matches = sorted(text_matches, key=lambda x: len(x.get("matches", [])), reverse=True)
    for i, match in enumerate(sorted_matches[:10]):
        original = match.get("original", "")
        matches = match.get("matches", [])
        pattern_names = [m.get("pattern_name", "") for m in matches]
        print(f"Ability #{i+1}: {len(matches)} matches")
        print(f"  Original: {original[:80]}...")
        print(f"  Patterns: {', '.join(pattern_names[:5])}...")
        print()
    
    # Identify patterns that appear together frequently (overlap detection)
    co_occurrence = defaultdict(Counter)
    for match in text_matches:
        pattern_names = [m.get("pattern_name", "") for m in match.get("matches", [])]
        for i, p1 in enumerate(pattern_names):
            for p2 in pattern_names[i+1:]:
                co_occurrence[p1][p2] += 1
    
    print("PATTERN CO-OCCURRENCE (patterns that frequently overlap)")
    print("-"*80)
    top_cooccur = []
    for p1, cooccur in co_occurrence.items():
        for p2, count in cooccur.most_common(3):
            top_cooccur.append((count, p1, p2))
    
    top_cooccur.sort(reverse=True)
    for count, p1, p2 in top_cooccur[:15]:
        print(f"  {p1:30} <-> {p2:30} ({count} times)")
    print()
    
if __name__ == "__main__":
    main()
