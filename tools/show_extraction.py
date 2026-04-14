#!/usr/bin/env python3
"""
Quick script to show template vs matched_text extraction results.
Shows what text is correctly extracted vs not extracted.
"""
import json
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    data_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # The structure is nested under analysis.dsl_pattern_analysis
    analysis = data.get("analysis", {})
    dsl_analysis = analysis.get("dsl_pattern_analysis", {})
    
    text_matches = dsl_analysis.get("text_matches", [])
    
    print(f"Total abilities: {dsl_analysis.get('total_texts', 0)}")
    print(f"Full coverage: {dsl_analysis.get('full_coverage', 0)}")
    print(f"Partial coverage: {dsl_analysis.get('partial_coverage', 0)}")
    print(f"No coverage: {dsl_analysis.get('no_coverage', 0)}")
    print(f"Average coverage: {dsl_analysis.get('average_coverage', 0):.2%}")
    print(f"\n{'='*80}\n")
    
    for i, match in enumerate(text_matches[:30]):  # Show first 30
        original = match.get("original", "")
        matches = match.get("matches", [])
        coverage = match.get("coverage", 0.0)
        match_count = match.get("match_count", 0)
        
        print(f"Ability #{i+1} (Coverage: {coverage:.1%}, Matches: {match_count})")
        print(f"Original: {original[:100]}..." if len(original) > 100 else f"Original: {original}")
        
        if matches:
            for m in matches:
                pattern_name = m.get("pattern_name", "")
                template = m.get("template", "")
                matched_text = m.get("matched_text", "")
                print(f"  [{pattern_name}]")
                print(f"    Template: {template}")
                print(f"    Matched:  {matched_text}")
        else:
            print("  NO MATCHES")
        
        print()
    
if __name__ == "__main__":
    main()
