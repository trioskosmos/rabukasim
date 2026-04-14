import re
import json
from difflib import SequenceMatcher
from collections import defaultdict

def load_patterns(file_path):
    """Load DSL patterns from the extract_abilities_to_template.py file"""
    import sys
    import os
    
    # Add the tools directory to path
    sys.path.insert(0, os.path.dirname(file_path))
    
    # Read and execute the file to extract DSL_PATTERNS
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a namespace to execute in
    namespace = {}
    
    # Execute only the DSL_PATTERNS definition
    # Find where DSL_PATTERNS starts and ends
    start_idx = content.find('DSL_PATTERNS = [')
    if start_idx == -1:
        return []
    
    # Find the matching closing bracket
    bracket_count = 0
    in_list = False
    end_idx = start_idx
    
    for i in range(start_idx, len(content)):
        char = content[i]
        if char == '[':
            bracket_count += 1
            in_list = True
        elif char == ']':
            bracket_count -= 1
            if bracket_count == 0 and in_list:
                end_idx = i + 1
                break
    
    # Extract just the DSL_PATTERNS definition
    patterns_code = content[start_idx:end_idx]
    
    # Execute to get the patterns
    try:
        exec(patterns_code, namespace)
        patterns = namespace.get('DSL_PATTERNS', [])
        return patterns
    except Exception as e:
        print(f"Error executing patterns code: {e}")
        return []

def calculate_similarity(str1, str2):
    """Calculate similarity between two strings using SequenceMatcher"""
    return SequenceMatcher(None, str1, str2).ratio()

def extract_regex_structure(regex):
    """Extract the structure of a regex pattern (capturing groups, literals)"""
    # Remove escape sequences for comparison
    cleaned = re.sub(r'\\.', '', regex)
    # Replace capturing groups with placeholders
    structure = re.sub(r'\([^)]+\)', 'X', cleaned)
    # Replace character classes with placeholders
    structure = re.sub(r'\[[^\]]+\]', 'C', structure)
    return structure

def analyze_pattern_similarity(patterns):
    """Analyze similarity between patterns"""
    similarities = []
    
    for i, pattern1 in enumerate(patterns):
        for j, pattern2 in enumerate(patterns[i+1:], i+1):
            # Calculate various similarity metrics
            name_similarity = calculate_similarity(pattern1['name'], pattern2['name'])
            regex_similarity = calculate_similarity(pattern1['regex'], pattern2['regex'])
            template_similarity = calculate_similarity(pattern1['template'], pattern2['template'])
            structure_similarity = calculate_similarity(pattern1['structure'], pattern2['structure'])
            
            # Extract regex structures
            regex_structure1 = extract_regex_structure(pattern1['regex'])
            regex_structure2 = extract_regex_structure(pattern2['regex'])
            structure_match = calculate_similarity(regex_structure1, regex_structure2)
            
            # Count capturing groups
            groups1 = len(re.findall(r'\([^?]', pattern1['regex']))
            groups2 = len(re.findall(r'\([^?]', pattern2['regex']))
            
            # Calculate overall similarity score
            overall_similarity = (
                name_similarity * 0.1 +
                regex_similarity * 0.3 +
                template_similarity * 0.3 +
                structure_similarity * 0.2 +
                structure_match * 0.1
            )
            
            if overall_similarity > 0.5:  # Only include reasonably similar patterns
                similarities.append({
                    'pattern1': pattern1['name'],
                    'pattern2': pattern2['name'],
                    'overall_similarity': overall_similarity,
                    'name_similarity': name_similarity,
                    'regex_similarity': regex_similarity,
                    'template_similarity': template_similarity,
                    'structure_similarity': structure_similarity,
                    'structure_match': structure_match,
                    'groups1': groups1,
                    'groups2': groups2,
                    'regex_structure1': regex_structure1,
                    'regex_structure2': regex_structure2
                })
    
    # Sort by overall similarity
    similarities.sort(key=lambda x: x['overall_similarity'], reverse=True)
    return similarities

def group_by_structure(patterns):
    """Group patterns by their structure names"""
    structure_groups = defaultdict(list)
    for pattern in patterns:
        # Extract key structural elements from structure name
        structure_key = pattern['structure'].lower()
        structure_groups[structure_key].append(pattern)
    return structure_groups

def find_consolidation_opportunities(similarities, patterns):
    """Identify specific consolidation opportunities"""
    opportunities = []
    
    # Group by structure similarity
    for sim in similarities[:50]:  # Top 50 most similar
        if sim['structure_match'] > 0.8 and sim['regex_similarity'] > 0.7:
            opportunities.append({
                'type': 'HIGH_SIMILARITY',
                'pattern1': sim['pattern1'],
                'pattern2': sim['pattern2'],
                'reason': f"Structure match: {sim['structure_match']:.2f}, Regex similarity: {sim['regex_similarity']:.2f}",
                'confidence': sim['overall_similarity']
            })
    
    # Group by structure names
    structure_groups = group_by_structure(patterns)
    for structure, group_patterns in structure_groups.items():
        if len(group_patterns) > 1:
            # Find patterns with similar names in the same structure group
            for i, p1 in enumerate(group_patterns):
                for p2 in group_patterns[i+1:]:
                    name_sim = calculate_similarity(p1['name'], p2['name'])
                    if name_sim > 0.6:
                        opportunities.append({
                            'type': 'STRUCTURE_GROUP',
                            'pattern1': p1['name'],
                            'pattern2': p2['name'],
                            'reason': f"Same structure group: {structure}",
                            'confidence': name_sim
                        })
    
    return opportunities

def main():
    patterns_file = "../tools/extract_abilities_to_template.py"
    
    print("=" * 80)
    print("PATTERN SIMILARITY ANALYSIS")
    print("=" * 80)
    
    patterns = load_patterns(patterns_file)
    print(f"\nLoaded {len(patterns)} patterns")
    
    if not patterns:
        print("No patterns found or could not parse patterns file")
        return
    
    # Analyze similarities
    print("\nAnalyzing pattern similarities...")
    similarities = analyze_pattern_similarity(patterns)
    print(f"Found {len(similarities)} similar pattern pairs")
    
    # Show top similarities
    print("\n" + "=" * 80)
    print("TOP 20 MOST SIMILAR PATTERNS")
    print("=" * 80)
    for i, sim in enumerate(similarities[:20]):
        print(f"\n{i+1}. {sim['pattern1']} <-> {sim['pattern2']}")
        print(f"   Overall similarity: {sim['overall_similarity']:.3f}")
        print(f"   Regex similarity: {sim['regex_similarity']:.3f}")
        print(f"   Template similarity: {sim['template_similarity']:.3f}")
        print(f"   Structure similarity: {sim['structure_similarity']:.3f}")
        print(f"   Structure match: {sim['structure_match']:.3f}")
        print(f"   Groups: {sim['groups1']} vs {sim['groups2']}")
    
    # Find consolidation opportunities
    print("\n" + "=" * 80)
    print("CONSOLIDATION OPPORTUNITIES")
    print("=" * 80)
    opportunities = find_consolidation_opportunities(similarities, patterns)
    
    for i, opp in enumerate(opportunities[:30]):
        print(f"\n{i+1}. {opp['pattern1']} <-> {opp['pattern2']}")
        print(f"   Type: {opp['type']}")
        print(f"   Reason: {opp['reason']}")
        print(f"   Confidence: {opp['confidence']:.3f}")
    
    # Structure group analysis
    print("\n" + "=" * 80)
    print("STRUCTURE GROUPS (potential for consolidation)")
    print("=" * 80)
    structure_groups = group_by_structure(patterns)
    multi_item_groups = {k: v for k, v in structure_groups.items() if len(v) > 1}
    
    for structure, group_patterns in sorted(multi_item_groups.items(), key=lambda x: len(x[1]), reverse=True)[:20]:
        print(f"\n{structure} ({len(group_patterns)} patterns):")
        for p in group_patterns:
            print(f"  - {p['name']}")
    
    # Save results
    results = {
        'total_patterns': len(patterns),
        'similar_pairs': len(similarities),
        'top_similarities': similarities[:50],
        'consolidation_opportunities': opportunities,
        'structure_groups': {k: [p['name'] for p in v] for k, v in multi_item_groups.items()}
    }
    
    output_file = "../data/pattern_similarity_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    main()
