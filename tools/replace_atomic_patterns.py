import json
import re

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

def load_atomic_mapping():
    """Load atomic variable pattern mapping"""
    with open('../data/atomic_variable_patterns.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['replacement_mapping']

def replace_broad_captures(patterns, atomic_mapping):
    """Replace broad ([^。]+) captures with atomic patterns"""
    replaced_patterns = []
    replacement_count = 0
    
    for pattern in patterns:
        regex = pattern['regex']
        template = pattern['template']
        name = pattern['name']
        structure = pattern['structure']
        
        # Extract variable names from template
        template_vars = re.findall(r'⟦([^⟧]+)⟧', template)
        
        # Find all capture groups in regex
        new_regex = regex
        var_index = 0
        
        # Replace each broad capture with atomic pattern if mapping exists
        for i, var_name in enumerate(template_vars):
            if var_name in atomic_mapping:
                # Find the i-th capture group (non-capturing groups complicate this)
                # For simplicity, replace ([^。]+) patterns
                atomic_pattern = atomic_mapping[var_name]
                
                # Replace the i-th occurrence of ([^。]+) with atomic pattern
                # This is a simplified approach - may need refinement
                if var_index < regex.count('([^。]+)'):
                    # Replace the var_index-th occurrence
                    parts = regex.split('([^。]+)', var_index + 1)
                    if len(parts) > var_index + 1:
                        new_regex = parts[0]
                        for j, part in enumerate(parts[1:]):
                            if j == var_index:
                                new_regex += f'({atomic_pattern})'
                            else:
                                new_regex += part
                        break
                var_index += 1
        
        # Check if any replacement was made
        if new_regex != regex:
            replacement_count += 1
            print(f"Replaced captures in pattern: {name}")
        
        replaced_patterns.append({
            'name': name,
            'regex': new_regex,
            'template': template,
            'structure': structure
        })
    
    return replaced_patterns, replacement_count

def write_replaced_patterns(patterns, output_file):
    """Write replaced patterns back to the file"""
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
    print("ATOMIC PATTERN REPLACEMENT")
    print("=" * 80)
    
    # Load patterns and atomic mapping
    patterns = load_patterns('../tools/extract_abilities_to_template.py')
    print(f"Loaded {len(patterns)} patterns")
    
    atomic_mapping = load_atomic_mapping()
    print(f"Loaded {len(atomic_mapping)} atomic pattern mappings")
    
    # Replace broad captures with atomic patterns
    print("\nReplacing broad captures with atomic patterns...")
    replaced_patterns, replacement_count = replace_broad_captures(patterns, atomic_mapping)
    
    print(f"\nReplaced captures in {replacement_count} patterns")
    print(f"Total patterns: {len(replaced_patterns)}")
    
    # Write back to file
    write_replaced_patterns(replaced_patterns, '../tools/extract_abilities_to_template.py')
    print("\nAtomic pattern replacement applied successfully")
    
    # Save analysis
    analysis = {
        'total_patterns': len(patterns),
        'patterns_replaced': replacement_count,
        'atomic_mappings_used': len(atomic_mapping),
        'replaced_patterns': replaced_patterns
    }
    
    with open('../data/atomic_pattern_replacement_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalysis saved to ../data/atomic_pattern_replacement_analysis.json")

if __name__ == "__main__":
    main()
