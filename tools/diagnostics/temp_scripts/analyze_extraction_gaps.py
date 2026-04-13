#!/usr/bin/env python3
"""Analyze what parts of abilities are extracted vs what's missed."""

import json
import re
import sys
from pathlib import Path

# Add parent to path to import extract module
sys.path.insert(0, str(Path(__file__).parent))
from extract_abilities_to_template import jp_to_logic, translate_extracted_text

def analyze_ability_extraction(jp_text, logic, card_id=""):
    """Analyze what was extracted vs what remains in the Japanese text."""
    
    results = {
        'card_id': card_id,
        'jp_original': jp_text,
        'logic_extracted': logic,
        'extracted_operations': [],
        'untranslated_fragments': [],
        'coverage_percent': 0
    }
    
    if not jp_text or not jp_text.strip():
        return results
    
    # Split JP text by common delimiters to find segments
    # Keep track of which parts were matched
    remaining_text = jp_text
    
    # Common patterns that should be extracted
    extraction_patterns = [
        (r'カードを(\d+)枚引[くき]', 'draw cards'),
        (r'控え室に置く', 'discard'),
        (r'手札に加', 'add to hand'),
        (r'手札から', 'from hand'),
        (r'デッキの上から', 'from top of deck'),
        (r'デッキの下に置く', 'to bottom of deck'),
        (r'エネルギー', 'energy'),
        (r'ウェイトにする', 'tap'),
        (r'アクティブにする', 'activate'),
        (r'スコア', 'score'),
        (r'ハート', 'hearts'),
        (r'ブレード', 'blades'),
        (r'メンバーカード', 'member cards'),
        (r'ライブカード', 'live cards'),
        (r'自分の', 'player\'s'),
        (r'相手の', 'opponent\'s'),
        (r'ステージ', 'stage'),
        (r'控え室', 'discard'),
        (r'「(.+?)」', 'character name'),
        (r'『(.+?)』', 'group name'),
        (r'支払', 'pay'),
        (r'引く', 'draw'),
        (r'置く', 'place'),
        (r'得る', 'gain'),
        (r'選ぶ', 'choose'),
        (r'見る', 'look at'),
        (r'公開', 'reveal'),
        (r'バトンタッチ', 'baton touch'),
        (r'てもよい', 'optional'),
        (r'場合', 'if condition'),
        (r'のとき', 'when'),
        (r'まで', 'until'),
        (r'すべて', 'all'),
        (r'以下から', 'choose one from'),
        (r'・', 'bullet option'),
    ]
    
    # Check which patterns are present in the Japanese text
    matched_patterns = []
    for pattern, description in extraction_patterns:
        matches = list(re.finditer(pattern, jp_text))
        for match in matches:
            matched_text = match.group(0)
            # Check if this was translated to logic
            translated = False
            
            # Simple heuristic: if logic contains related English, consider it translated
            if description == 'draw cards' and 'draw' in logic:
                translated = True
            elif description == 'discard' and 'discard' in logic:
                translated = True
            elif description == 'add to hand' and 'add' in logic and 'hand' in logic:
                translated = True
            elif description == 'character name':
                # Check if character name appears in logic
                char_name = match.group(1)
                if char_name.upper() in logic.upper():
                    translated = True
            elif description == 'group name':
                group_name = match.group(1)
                if group_name.upper() in logic.upper():
                    translated = True
            elif description == 'optional' and 'optional' in logic:
                translated = True
            elif description == 'pay' and 'pay' in logic:
                translated = True
            elif description == 'hearts' and 'heart' in logic:
                translated = True
            elif description == 'blades' and 'blade' in logic:
                translated = True
            elif description == 'energy' and 'energy' in logic:
                translated = True
            elif description == 'tap' and 'tap' in logic:
                translated = True
            
            matched_patterns.append({
                'jp_text': matched_text,
                'description': description,
                'translated': translated,
                'position': match.start()
            })
    
    # Sort by position
    matched_patterns.sort(key=lambda x: x['position'])
    
    # Find gaps between matched patterns
    last_end = 0
    gaps = []
    for pattern in matched_patterns:
        if pattern['position'] > last_end:
            gap_text = jp_text[last_end:pattern['position']]
            # Clean up the gap text
            gap_text = gap_text.strip('・。、\n ')
            if gap_text and len(gap_text) > 2:
                gaps.append(gap_text)
        last_end = max(last_end, pattern['position'] + len(pattern['jp_text']))
    
    # Check for trailing text
    if last_end < len(jp_text):
        trailing = jp_text[last_end:].strip('・。、\n ')
        if trailing and len(trailing) > 2:
            gaps.append(trailing)
    
    results['extracted_operations'] = [p for p in matched_patterns if p['translated']]
    results['untranslated_fragments'] = gaps
    
    # Calculate coverage
    total_chars = len(jp_text)
    covered_chars = sum(len(p['jp_text']) for p in matched_patterns if p['translated'])
    if total_chars > 0:
        results['coverage_percent'] = (covered_chars / total_chars) * 100
    
    return results


def main():
    # Load extracted abilities
    with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Analyze abilities with gaps
    abilities_with_gaps = []
    
    for ability in data['abilities']:
        source = ability['source_ability_texts'][0]
        jp = source['jp']
        logic = source['logic']
        cards = source['cards']
        card_id = cards[0] if cards else 'UNKNOWN'
        
        analysis = analyze_ability_extraction(jp, logic, card_id)
        
        # Only report if there are untranslated fragments or low coverage
        if analysis['untranslated_fragments'] or analysis['coverage_percent'] < 50:
            abilities_with_gaps.append(analysis)
    
    # Sort by number of gaps (most problematic first)
    abilities_with_gaps.sort(key=lambda x: len(x['untranslated_fragments']), reverse=True)
    
    # Print report
    print("=" * 80)
    print("ABILITY EXTRACTION GAP ANALYSIS")
    print("=" * 80)
    print(f"\nTotal abilities analyzed: {len(data['abilities'])}")
    print(f"Abilities with extraction gaps: {len(abilities_with_gaps)}")
    
    # Show top 10 most problematic
    print("\n" + "=" * 80)
    print("TOP 10 ABILITIES WITH MOST EXTRACTION GAPS")
    print("=" * 80)
    
    for i, analysis in enumerate(abilities_with_gaps[:10], 1):
        print(f"\n{i}. Card: {analysis['card_id']}")
        print(f"   Coverage: {analysis['coverage_percent']:.1f}%")
        print(f"   Extracted operations: {len(analysis['extracted_operations'])}")
        print(f"   Untranslated fragments: {len(analysis['untranslated_fragments'])}")
        
        if analysis['untranslated_fragments']:
            print("   \n   MISSED TEXT:")
            for j, fragment in enumerate(analysis['untranslated_fragments'][:3], 1):
                print(f"   {j}. {fragment[:60]}...")
        
        print(f"   \n   EXTRACTED LOGIC:")
        logic_lines = analysis['logic_extracted'].split('\n')
        for line in logic_lines[:3]:
            print(f"      {line[:70]}")
        if len(logic_lines) > 3:
            print(f"      ... ({len(logic_lines) - 3} more lines)")
        print("-" * 80)
    
    # Summary of common untranslated patterns
    print("\n" + "=" * 80)
    print("SUMMARY: COMMON UNTRANSLATED FRAGMENTS")
    print("=" * 80)
    
    all_fragments = []
    for analysis in abilities_with_gaps:
        all_fragments.extend(analysis['untranslated_fragments'])
    
    # Group similar fragments
    fragment_counts = {}
    for frag in all_fragments:
        # Simplify for grouping
        key = frag[:20] if len(frag) > 20 else frag
        fragment_counts[key] = fragment_counts.get(key, 0) + 1
    
    # Show most common
    sorted_frags = sorted(fragment_counts.items(), key=lambda x: x[1], reverse=True)
    for frag, count in sorted_frags[:15]:
        print(f"  {count:3d}x: {frag[:50]}...")
    
    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    main()
