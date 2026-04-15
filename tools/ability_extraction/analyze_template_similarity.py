#!/usr/bin/env python3
"""
Analyze template similarity and subsets to identify compression potential.
"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict

def load_templates():
    """Load templates from coverage log."""
    coverage_file = Path("data/ability_coverage_log.json")
    
    with open(coverage_file, 'r', encoding='utf-8') as f:
        coverage_data = json.load(f)
    
    return coverage_data['templates']

def calculate_similarity(template1, template2):
    """Calculate similarity between two templates using SequenceMatcher."""
    return SequenceMatcher(None, template1, template2).ratio()

def find_common_subpatterns(template1, template2, min_length=5):
    """Find common subpatterns between two templates."""
    matcher = SequenceMatcher(None, template1, template2)
    matches = matcher.get_matching_blocks()
    
    subpatterns = []
    for match in matches:
        start_a, start_b, length = match
        if length >= min_length:
            subpattern = template1[start_a:start_a + length]
            subpatterns.append({
                'pattern': subpattern,
                'length': length,
                'pos1': start_a,
                'pos2': start_b
            })
    
    return subpatterns

def analyze_template_similarity(templates):
    """Analyze similarity between all templates."""
    print(f"Analyzing {len(templates)} templates for similarity...")
    
    # Group templates by similarity
    similarity_groups = defaultdict(list)
    
    # Compare each template with others
    for i, t1 in enumerate(templates):
        template1 = t1['template']
        
        for j, t2 in enumerate(templates):
            if i >= j:  # Avoid duplicate comparisons and self-comparison
                continue
            
            template2 = t2['template']
            similarity = calculate_similarity(template1, template2)
            
            if similarity >= 0.5:  # 50% similarity threshold
                similarity_groups[f"{i}-{j}"] = {
                    'template1': template1,
                    'template2': template2,
                    'similarity': similarity,
                    'usage_count1': t1['usage_count'],
                    'usage_count2': t2['usage_count'],
                    'common_patterns': find_common_subpatterns(template1, template2)
                }
    
    return similarity_groups

def analyze_placeholder_patterns(templates):
    """Analyze common placeholder patterns across templates."""
    print("Analyzing placeholder patterns...")
    
    # Extract placeholder sequences from each template
    placeholder_patterns = defaultdict(list)
    
    for template_data in templates:
        template = template_data['template']
        
        # Find all placeholders
        placeholders = re.findall(r'\[[^\]]+\]', template)
        placeholder_seq = '+'.join(placeholders)
        
        placeholder_patterns[placeholder_seq].append({
            'template': template,
            'usage_count': template_data['usage_count']
        })
    
    # Find patterns that appear in multiple templates
    common_patterns = {k: v for k, v in placeholder_patterns.items() if len(v) > 1}
    
    return common_patterns

def analyze_clause_subsets(templates):
    """Analyze clause subsets (split by 。) for compression potential."""
    print("Analyzing clause subsets...")
    
    clause_patterns = defaultdict(list)
    
    for template_data in templates:
        template = template_data['template']
        
        # Split by clauses
        clauses = template.split('。')
        clauses = [c.strip() for c in clauses if c.strip()]
        
        for clause in clauses:
            clause_patterns[clause].append({
                'template': template,
                'usage_count': template_data['usage_count']
            })
    
    # Find clauses that appear in multiple templates
    common_clauses = {k: v for k, v in clause_patterns.items() if len(v) > 1}
    
    return common_clauses

def main():
    """Main analysis function."""
    print("Loading templates...")
    templates = load_templates()
    
    print(f"Loaded {len(templates)} templates")
    
    # Analyze template similarity
    print("\n" + "="*60)
    print("TEMPLATE SIMILARITY ANALYSIS")
    print("="*60)
    similarity_groups = analyze_template_similarity(templates)
    
    # Sort by similarity (highest first)
    sorted_similarity = sorted(similarity_groups.values(), key=lambda x: -x['similarity'])
    
    print(f"\nFound {len(sorted_similarity)} template pairs with >= 50% similarity")
    print("\nTop 20 most similar template pairs:")
    for i, pair in enumerate(sorted_similarity[:20]):
        print(f"\n{i+1}. Similarity: {pair['similarity']:.2f}")
        print(f"   Template 1 (usage {pair['usage_count1']}): {pair['template1']}")
        print(f"   Template 2 (usage {pair['usage_count2']}): {pair['template2']}")
        print(f"   Common patterns: {len(pair['common_patterns'])}")
    
    # Analyze placeholder patterns
    print("\n" + "="*60)
    print("PLACEHOLDER PATTERN ANALYSIS")
    print("="*60)
    common_patterns = analyze_placeholder_patterns(templates)
    
    print(f"\nFound {len(common_patterns)} placeholder patterns appearing in multiple templates")
    print("\nTop 20 most common placeholder patterns:")
    sorted_patterns = sorted(common_patterns.items(), key=lambda x: -len(x[1]))
    for i, (pattern, templates_list) in enumerate(sorted_patterns[:20]):
        print(f"\n{i+1}. Pattern: {pattern}")
        print(f"   Appears in {len(templates_list)} templates")
        total_usage = sum(t['usage_count'] for t in templates_list)
        print(f"   Total usage count: {total_usage}")
    
    # Analyze clause subsets
    print("\n" + "="*60)
    print("CLAUSE SUBSET ANALYSIS")
    print("="*60)
    common_clauses = analyze_clause_subsets(templates)
    
    print(f"\nFound {len(common_clauses)} clauses appearing in multiple templates")
    print("\nTop 20 most common clauses:")
    sorted_clauses = sorted(common_clauses.items(), key=lambda x: -len(x[1]))
    for i, (clause, templates_list) in enumerate(sorted_clauses[:20]):
        print(f"\n{i+1}. Clause: {clause}")
        print(f"   Appears in {len(templates_list)} templates")
        total_usage = sum(t['usage_count'] for t in templates_list)
        print(f"   Total usage count: {total_usage}")
    
    # Save results to file
    results = {
        'similarity_analysis': {
            'total_pairs': len(sorted_similarity),
            'top_pairs': sorted_similarity[:50]
        },
        'placeholder_patterns': {
            'total_patterns': len(sorted_patterns),
            'top_patterns': [(p, [{'template': t['template'], 'usage_count': t['usage_count']} for t in templates_list]) for p, templates_list in sorted_patterns[:50]]
        },
        'clause_subsets': {
            'total_clauses': len(sorted_clauses),
            'top_clauses': [(c, [{'template': t['template'], 'usage_count': t['usage_count']} for t in templates_list]) for c, templates_list in sorted_clauses[:50]]
        }
    }
    
    output_file = Path("data/template_similarity_analysis.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    main()
