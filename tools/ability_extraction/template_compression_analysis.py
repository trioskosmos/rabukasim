#!/usr/bin/env python3
"""
Analyze template structures to identify opportunities for further compression.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import re

def load_templates(coverage_log_file: Path):
    """Load templates from coverage log."""
    with open(coverage_log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['templates']

def analyze_structural_patterns(templates):
    """Analyze structural patterns in templates."""
    # Extract common Japanese grammatical patterns
    verbs = []
    particles = []
    connectors = []
    conditionals = []
    
    verb_pattern = re.compile(r'(置く|加える|引く|見る|公開する|選ぶ|得る|する|なる|増える|減る|出す|戻す|捨てる|持つ|使う|払う|支払う)')
    particle_pattern = re.compile(r'(を|に|から|の|が|は|で|まで|より)')
    conditional_pattern = re.compile(r'(場合|とき|まで|以下|以上|かぎり|すると|すれば)')
    connector_pattern = re.compile(r'(そして|または|あるいは|さらに|そのあと|その後|また)')
    
    for template_data in templates:
        template = template_data['template']
        
        verbs.extend(verb_pattern.findall(template))
        particles.extend(particle_pattern.findall(template))
        conditionals.extend(conditional_pattern.findall(template))
        connectors.extend(connector_pattern.findall(template))
    
    return {
        'verbs': Counter(verbs),
        'particles': Counter(particles),
        'conditionals': Counter(conditionals),
        'connectors': Counter(connectors)
    }

def analyze_action_sequences(templates):
    """Analyze common action sequences in templates."""
    sequences = defaultdict(int)
    
    for template_data in templates:
        template = template_data['template']
        # Extract placeholder sequences
        placeholders = re.findall(r'\[([^\]]+)\]', template)
        
        # Track sequences of 2-3 placeholders
        for i in range(len(placeholders) - 1):
            seq = f"{placeholders[i]}->{placeholders[i+1]}"
            sequences[seq] += 1
        
        for i in range(len(placeholders) - 2):
            seq = f"{placeholders[i]}->{placeholders[i+1]}->{placeholders[i+2]}"
            sequences[seq] += 1
    
    return dict(sorted(sequences.items(), key=lambda x: -x[1])[:20])

def analyze_template_lengths(templates):
    """Analyze template length distribution."""
    lengths = [len(t['template']) for t in templates]
    return {
        'min': min(lengths),
        'max': max(lengths),
        'avg': sum(lengths) / len(lengths),
        'median': sorted(lengths)[len(lengths) // 2]
    }

def identify_compression_opportunities(templates):
    """Identify specific opportunities for template compression."""
    opportunities = []
    
    # 1. Templates that differ only in numbers
    number_variants = defaultdict(list)
    for i, t1 in enumerate(templates):
        for j, t2 in enumerate(templates[i+1:], i+1):
            # Replace numbers with generic placeholder and compare
            t1_generic = re.sub(r'\[number\]', '[N]', t1['template'])
            t2_generic = re.sub(r'\[number\]', '[N]', t2['template'])
            if t1_generic == t2_generic:
                number_variants[t1_generic].append((i, j))
    
    if number_variants:
        opportunities.append({
            'type': 'number_variants',
            'count': len(number_variants),
            'description': 'Templates that differ only in number values'
        })
    
    # 2. Templates with similar structure (same placeholder types in different order)
    placeholder_sequences = defaultdict(list)
    for i, t in enumerate(templates):
        placeholders = tuple(re.findall(r'\[([^\]]+)\]', t['template']))
        placeholder_sequences[placeholders].append(i)
    
    similar_structure = {k: v for k, v in placeholder_sequences.items() if len(v) > 1}
    if similar_structure:
        opportunities.append({
            'type': 'similar_structure',
            'count': len(similar_structure),
            'description': 'Templates with same placeholder types but different order/arrangement'
        })
    
    # 3. Templates with common sub-patterns
    common_subpatterns = analyze_action_sequences(templates)
    if common_subpatterns:
        opportunities.append({
            'type': 'common_subpatterns',
            'count': len(common_subpatterns),
            'description': 'Common action sequences that could be abstracted',
            'examples': list(common_subpatterns.items())[:5]
        })
    
    return opportunities

def main():
    coverage_log_file = Path("data/ability_coverage_log.json")
    templates = load_templates(coverage_log_file)
    
    print(f"Analyzing {len(templates)} templates...\n")
    
    # Analyze structural patterns
    structural = analyze_structural_patterns(templates)
    print("=== Structural Patterns ===")
    print(f"Top verbs: {structural['verbs'].most_common(10)}")
    print(f"Top particles: {structural['particles'].most_common(10)}")
    print(f"Top conditionals: {structural['conditionals'].most_common(10)}")
    print(f"Top connectors: {structural['connectors'].most_common(10)}")
    print()
    
    # Analyze action sequences
    sequences = analyze_action_sequences(templates)
    print("=== Common Action Sequences ===")
    for seq, count in list(sequences.items())[:10]:
        print(f"{seq}: {count}")
    print()
    
    # Analyze template lengths
    lengths = analyze_template_lengths(templates)
    print("=== Template Length Statistics ===")
    print(f"Min: {lengths['min']}, Max: {lengths['max']}, Avg: {lengths['avg']:.1f}, Median: {lengths['median']}")
    print()
    
    # Identify compression opportunities
    opportunities = identify_compression_opportunities(templates)
    print("=== Compression Opportunities ===")
    for opp in opportunities:
        print(f"{opp['type']}: {opp['count']}")
        print(f"  {opp['description']}")
        if 'examples' in opp:
            print(f"  Examples: {opp['examples']}")
        print()
    
    print("\n=== Recommendations for Further Compression ===")
    print("1. Abstract Japanese verbs as [verb] variables")
    print("2. Abstract particles as [particle] variables") 
    print("3. Abstract conditionals as [conditional] variables")
    print("4. Abstract common action sequences as [action_seq] variables")
    print("5. Use graph-based pattern matching to find structural similarities")
    print("6. Implement optional part detection for conditional logic")

if __name__ == "__main__":
    main()
