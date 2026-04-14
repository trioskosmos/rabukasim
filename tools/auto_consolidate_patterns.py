import json
import re
from collections import defaultdict

def load_patterns(file_path):
    """Load DSL patterns from the extract_abilities_to_template.py file"""
    import sys
    import os
    
    # Read and execute the file to extract DSL_PATTERNS
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
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
        namespace = {}
        exec(patterns_code, namespace)
        patterns = namespace.get('DSL_PATTERNS', [])
        return patterns
    except Exception as e:
        print(f"Error executing patterns code: {e}")
        return []

def load_similarity_analysis(file_path):
    """Load pattern similarity analysis results"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_exact_duplicates(similarity_data):
    """Find patterns with 1.0 structure match and 1.0 regex similarity"""
    exact_duplicates = []
    
    for sim in similarity_data.get('top_similarities', []):
        if (sim['structure_match'] == 1.0 and 
            sim['regex_similarity'] == 1.0 and
            sim['template_similarity'] == 1.0):
            exact_duplicates.append(sim)
    
    return exact_duplicates

def find_resource_variants(similarity_data):
    """Find blade/heart resource variants for consolidation"""
    resource_variants = []
    
    blade_patterns = []
    heart_patterns = []
    
    # Collect patterns with blade/heart in names
    for sim in similarity_data.get('top_similarities', []):
        if 'blade' in sim['pattern1'].lower() and 'heart' in sim['pattern2'].lower():
            if sim['structure_match'] > 0.8 and sim['regex_similarity'] > 0.8:
                resource_variants.append(sim)
        elif 'heart' in sim['pattern1'].lower() and 'blade' in sim['pattern2'].lower():
            if sim['structure_match'] > 0.8 and sim['regex_similarity'] > 0.8:
                resource_variants.append(sim)
    
    return resource_variants

def find_action_condition_variants(similarity_data):
    """Find action/condition variants for consolidation"""
    action_condition_variants = []
    
    for sim in similarity_data.get('top_similarities', []):
        if (('action' in sim['pattern1'].lower() and 'condition' in sim['pattern2'].lower()) or
            ('condition' in sim['pattern1'].lower() and 'action' in sim['pattern2'].lower())):
            if sim['structure_match'] > 0.9 and sim['regex_similarity'] > 0.9:
                action_condition_variants.append(sim)
    
    return action_condition_variants

def consolidate_exact_duplicates(patterns, exact_duplicates):
    """Consolidate exact duplicate patterns"""
    consolidated_patterns = []
    processed_names = set()
    
    # Create a mapping of pattern names to their indices
    pattern_map = {p['name']: i for i, p in enumerate(patterns)}
    
    for sim in exact_duplicates:
        pattern1_name = sim['pattern1']
        pattern2_name = sim['pattern2']
        
        if pattern1_name in processed_names or pattern2_name in processed_names:
            continue
        
        # Keep the first pattern, skip the second
        if pattern1_name in pattern_map and pattern2_name in pattern_map:
            idx1 = pattern_map[pattern1_name]
            idx2 = pattern_map[pattern2_name]
            
            # Add pattern1 to consolidated list
            consolidated_patterns.append(patterns[idx1])
            processed_names.add(pattern1_name)
            processed_names.add(pattern2_name)
            
            print(f"Merging exact duplicates: {pattern2_name} -> {pattern1_name}")
    
    # Add patterns not involved in exact duplicates
    for i, pattern in enumerate(patterns):
        if pattern['name'] not in processed_names:
            consolidated_patterns.append(pattern)
    
    return consolidated_patterns

def consolidate_resource_variants(patterns, resource_variants):
    """Consolidate blade/heart resource variants using regex alternatives"""
    # This is more complex - need to modify regexes to include alternatives
    # For now, just identify them
    print("\nResource variant consolidations (manual implementation needed):")
    for sim in resource_variants[:10]:
        print(f"  {sim['pattern1']} <-> {sim['pattern2']}")
        print(f"    Structure match: {sim['structure_match']:.2f}, Regex similarity: {sim['regex_similarity']:.2f}")
    
    return patterns  # Return unchanged for now

def write_consolidated_patterns(patterns, output_file):
    """Write consolidated patterns back to the file"""
    # Read the original file
    with open('../tools/extract_abilities_to_template.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find DSL_PATTERNS start and end
    start_idx = content.find('DSL_PATTERNS = [')
    if start_idx == -1:
        print("Could not find DSL_PATTERNS in file")
        return False
    
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
    
    # Generate the new patterns code
    patterns_code = "DSL_PATTERNS = [\n"
    for pattern in patterns:
        patterns_code += f"        {{\n"
        patterns_code += f"            \"name\": \"{pattern['name']}\",\n"
        patterns_code += f"            \"regex\": r\"{pattern['regex']}\",\n"
        patterns_code += f"            \"template\": \"{pattern['template']}\",\n"
        patterns_code += f"            \"structure\": \"{pattern['structure']}\"\n"
        patterns_code += f"        }},\n"
    patterns_code += "]\n"
    
    # Replace the old patterns with the new ones
    new_content = content[:start_idx] + patterns_code + content[end_idx:]
    
    # Write back to file
    with open('../tools/extract_abilities_to_template.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Wrote {len(patterns)} patterns to file")
    return True

def main():
    print("=" * 80)
    print("AUTOMATED PATTERN CONSOLIDATION")
    print("=" * 80)
    
    # Load patterns and similarity data
    patterns = load_patterns('../tools/extract_abilities_to_template.py')
    print(f"Loaded {len(patterns)} patterns")
    
    similarity_data = load_similarity_analysis('../data/pattern_similarity_analysis.json')
    print(f"Loaded similarity analysis")
    
    # Find consolidation opportunities
    exact_duplicates = find_exact_duplicates(similarity_data)
    print(f"\nFound {len(exact_duplicates)} exact duplicate pairs")
    
    resource_variants = find_resource_variants(similarity_data)
    print(f"Found {len(resource_variants)} resource variant pairs")
    
    action_condition_variants = find_action_condition_variants(similarity_data)
    print(f"Found {len(action_condition_variants)} action/condition variant pairs")
    
    # Consolidate exact duplicates
    if exact_duplicates:
        print("\n" + "=" * 80)
        print("CONSOLIDATING EXACT DUPLICATES")
        print("=" * 80)
        
        consolidated = consolidate_exact_duplicates(patterns, exact_duplicates)
        print(f"Reduced from {len(patterns)} to {len(consolidated)} patterns")
        
        # Write back to file
        write_consolidated_patterns(consolidated, '../tools/extract_abilities_to_template.py')
        print("\nExact duplicate consolidation applied successfully")
    else:
        print("No exact duplicates found")
    
    # Show resource variants (for manual implementation)
    if resource_variants:
        consolidate_resource_variants(patterns, resource_variants)
    
    # Show action/condition variants
    if action_condition_variants:
        print("\nAction/condition variant consolidations (manual implementation needed):")
        for sim in action_condition_variants[:10]:
            print(f"  {sim['pattern1']} <-> {sim['pattern2']}")
            print(f"    Structure match: {sim['structure_match']:.2f}, Regex similarity: {sim['regex_similarity']:.2f}")

if __name__ == "__main__":
    main()
