#!/usr/bin/env python3
"""
Deep analysis of template structures to identify specific compression opportunities.
"""

import json
from pathlib import Path
from collections import defaultdict
import difflib

def load_templates(coverage_log_file: Path):
    """Load templates from coverage log."""
    with open(coverage_log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['templates']

def analyze_template_differences(templates):
    """Analyze specific differences between similar templates."""
    # Group templates by length to find similar ones
    by_length = defaultdict(list)
    for i, t in enumerate(templates):
        by_length[len(t['template'])].append((i, t))
    
    # For each length group, find similar templates
    similar_pairs = []
    for length, group in sorted(by_length.items()):
        if len(group) > 1:
            for i in range(len(group)):
                for j in range(i+1, len(group)):
                    t1 = group[i][1]['template']
                    t2 = group[j][1]['template']
                    
                    # Calculate similarity
                    similarity = difflib.SequenceMatcher(None, t1, t2).ratio()
                    if similarity > 0.7:  # 70% similar
                        similar_pairs.append({
                            'similarity': similarity,
                            'template1': t1,
                            'template2': t2,
                            'usage1': group[i][1]['usage_count'],
                            'usage2': group[j][1]['usage_count']
                        })
    
    # Sort by similarity
    similar_pairs.sort(key=lambda x: -x['similarity'])
    return similar_pairs[:20]

def analyze_placeholder_usage(templates):
    """Analyze how placeholders are used across templates."""
    placeholder_stats = defaultdict(lambda: {'count': 0, 'templates': []})
    
    for t in templates:
        placeholders = []
        for match in t['template'].split('[')[1:]:
            if ']' in match:
                ph = match.split(']')[0]
                placeholders.append(ph)
                placeholder_stats[ph]['count'] += 1
                placeholder_stats[ph]['templates'].append(t['template'][:100])
    
    return dict(placeholder_stats)

def identify_very_similar_templates(templates):
    """Identify templates that are almost identical."""
    # Normalize templates by replacing specific values
    normalized = {}
    for i, t in enumerate(templates):
        # Replace all placeholders with generic types
        norm = t['template']
        norm = norm.replace('[card_type]', '[CT]')
        norm = norm.replace('[zone]', '[Z]')
        norm = norm.replace('[player]', '[P]')
        norm = norm.replace('[number]', '[N]')
        norm = norm.replace('[position]', '[POS]')
        norm = norm.replace('[timing_modifier]', '[TM]')
        norm = norm.replace('[group_name]', '[G]')
        norm = norm.replace('[character_name]', '[C]')
        norm = norm.replace('[energy]', '[E]')
        norm = norm.replace('[score_modifier]', '[S]')
        norm = norm.replace('[icon]', '[I]')
        norm = norm.replace('[icon_text]', '[IT]')
        
        normalized[norm] = normalized.get(norm, []) + [i]
    
    # Find groups with multiple templates
    multi_groups = {k: v for k, v in normalized.items() if len(v) > 1}
    
    return multi_groups

def analyze_verb_particle_combinations(templates):
    """Analyze specific verb-particle combinations."""
    import re
    
    combinations = defaultdict(int)
    
    for t in templates:
        template = t['template']
        
        # Find verb-particle patterns
        # Pattern: [X]を[Y]に置く
        verb_particle = re.findall(r'\[([^\]]+)\]を.*?\[([^\]]+)\]に(置く|加える|引く|見る|する)', template)
        for match in verb_particle:
            combinations[f"{match[0]}を{match[1]}に{match[2]}"] += 1
        
        # Pattern: [X]から[Y]を[Z]
        from_pattern = re.findall(r'\[([^\]]+)\]から.*?\[([^\]]+)\]を', template)
        for match in from_pattern:
            combinations[f"{match[0]}から{match[1]}を"] += 1
    
    return dict(sorted(combinations.items(), key=lambda x: -x[1])[:15])

def analyze_conditional_structures(templates):
    """Analyze conditional structures in templates."""
    import re
    
    conditionals = defaultdict(int)
    
    for t in templates:
        template = t['template']
        
        # Find conditional patterns
        if '場合' in template:
            # Extract what comes before 場合
            before_case = template.split('場合')[0][-50:]
            conditionals[f"...場合: {before_case}"] += 1
        
        if '以上' in template:
            before_above = template.split('以上')[0][-50:]
            conditionals[f"...以上: {before_above}"] += 1
        
        if '以下' in template:
            before_below = template.split('以下')[0][-50:]
            conditionals[f"...以下: {before_below}"] += 1
    
    return dict(sorted(conditionals.items(), key=lambda x: -x[1])[:10])

def main():
    coverage_log_file = Path("data/ability_coverage_log.json")
    templates = load_templates(coverage_log_file)
    
    print(f"Deep analysis of {len(templates)} templates...\n")
    
    # Analyze similar templates
    print("=== Most Similar Template Pairs ===")
    similar = analyze_template_differences(templates)
    for i, pair in enumerate(similar[:10]):
        print(f"\nPair {i+1} (similarity: {pair['similarity']:.2f})")
        print(f"  Template 1: {pair['template1']}")
        print(f"  Template 2: {pair['template2']}")
        print(f"  Usage: {pair['usage1']} vs {pair['usage2']}")
    
    # Analyze placeholder usage
    print("\n=== Placeholder Usage Analysis ===")
    placeholder_stats = analyze_placeholder_usage(templates)
    for ph, stats in sorted(placeholder_stats.items(), key=lambda x: -x[1]['count'])[:15]:
        print(f"{ph}: {stats['count']} templates")
    
    # Identify very similar templates (normalized)
    print("\n=== Templates with Identical Structure ===")
    similar_structure = identify_very_similar_templates(templates)
    print(f"Found {len(similar_structure)} template groups with identical placeholder structure")
    for i, (structure, indices) in enumerate(list(similar_structure.items())[:5]):
        print(f"\nGroup {i+1} ({len(indices)} templates):")
        print(f"  Structure: {structure}")
        for idx in indices[:3]:
            print(f"    Original: {templates[idx]['template'][:80]}...")
    
    # Analyze verb-particle combinations
    print("\n=== Common Verb-Particle Combinations ===")
    verb_particle = analyze_verb_particle_combinations(templates)
    for combo, count in verb_particle.items():
        print(f"{combo}: {count}")
    
    # Analyze conditional structures
    print("\n=== Common Conditional Structures ===")
    conditional = analyze_conditional_structures(templates)
    for cond, count in conditional.items():
        print(f"{cond}: {count}")
    
    print("\n=== Specific Compression Recommendations ===")
    print("1. Merge templates with identical placeholder structure but different text between placeholders")
    print("2. Abstract common verb-particle combinations (e.g., 'XをYに置く' as [move_action])")
    print("3. Group templates with same conditional patterns (e.g., 'X以上' as [above_condition])")
    print("4. Abstract sequential actions (e.g., 'do X then do Y' as [sequential_action])")
    print("5. Create template inheritance hierarchy (base templates + modifiers)")

if __name__ == "__main__":
    main()
