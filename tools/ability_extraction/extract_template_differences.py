#!/usr/bin/env python3
"""
Extract specific examples of template differences that could be abstracted as variables.
"""

import json
from pathlib import Path
import re

def load_templates(coverage_log_file: Path):
    """Load templates from coverage log."""
    with open(coverage_log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['templates']

def find_conditional_threshold_differences(templates):
    """Find templates that differ only in conditional thresholds (6 vs 7, etc.)."""
    examples = []
    
    for i, t1 in enumerate(templates):
        for t2 in templates[i+1:]:
            # Check if templates differ only in numbers in conditionals
            t1_text = t1['template']
            t2_text = t2['template']
            
            # Replace numbers with placeholder and compare
            t1_normalized = re.sub(r'[0-9]+以上', '[NUM]以上', t1_text)
            t2_normalized = re.sub(r'[0-9]+以上', '[NUM]以上', t2_text)
            
            if t1_normalized == t2_normalized and t1_text != t2_text:
                # Extract the specific numbers
                nums1 = re.findall(r'([0-9]+)以上', t1_text)
                nums2 = re.findall(r'([0-9]+)以上', t2_text)
                
                if nums1 and nums2 and nums1 != nums2:
                    examples.append({
                        'type': 'conditional_threshold',
                        'template1': t1_text,
                        'template2': t2_text,
                        'threshold1': nums1,
                        'threshold2': nums2,
                        'usage1': t1['usage_count'],
                        'usage2': t2['usage_count']
                    })
                    if len(examples) >= 5:
                        return examples
    
    return examples

def find_position_modifier_differences(templates):
    """Find templates that differ only in position modifiers (一番上 vs 一番下)."""
    examples = []
    
    for i, t1 in enumerate(templates):
        for t2 in templates[i+1:]:
            t1_text = t1['template']
            t2_text = t2['template']
            
            # Check for position modifier differences
            t1_normalized = re.sub(r'一番[上下]', '[POSITION]', t1_text)
            t2_normalized = re.sub(r'一番[上下]', '[POSITION]', t2_text)
            
            if t1_normalized == t2_normalized and t1_text != t2_text:
                pos1 = re.findall(r'一番([上下])', t1_text)
                pos2 = re.findall(r'一番([上下])', t2_text)
                
                if pos1 and pos2 and pos1 != pos2:
                    examples.append({
                        'type': 'position_modifier',
                        'template1': t1_text,
                        'template2': t2_text,
                        'position1': pos1,
                        'position2': pos2,
                        'usage1': t1['usage_count'],
                        'usage2': t2['usage_count']
                    })
                    if len(examples) >= 5:
                        return examples
    
    return examples

def find_quantifier_differences(templates):
    """Find templates that differ only in quantifiers (1人 vs すべて)."""
    examples = []
    
    for i, t1 in enumerate(templates):
        for t2 in templates[i+1:]:
            t1_text = t1['template']
            t2_text = t2['template']
            
            # Check for quantifier differences
            t1_normalized = re.sub(r'(すべて|1人|2人|3人)', '[QUANT]', t1_text)
            t2_normalized = re.sub(r'(すべて|1人|2人|3人)', '[QUANT]', t2_text)
            
            if t1_normalized == t2_normalized and t1_text != t2_text:
                quant1 = re.findall(r'(すべて|1人|2人|3人)', t1_text)
                quant2 = re.findall(r'(すべて|1人|2人|3人)', t2_text)
                
                if quant1 and quant2 and quant1 != quant2:
                    examples.append({
                        'type': 'quantifier',
                        'template1': t1_text,
                        'template2': t2_text,
                        'quantifier1': quant1,
                        'quantifier2': quant2,
                        'usage1': t1['usage_count'],
                        'usage2': t2['usage_count']
                    })
                    if len(examples) >= 5:
                        return examples
    
    return examples

def find_parentheses_differences(templates):
    """Find templates that differ only in parentheses types."""
    examples = []
    
    for i, t1 in enumerate(templates):
        for t2 in templates[i+1:]:
            t1_text = t1['template']
            t2_text = t2['template']
            
            # Check for parentheses differences
            t1_normalized = re.sub(r'[（）()]', '[PAREN]', t1_text)
            t2_normalized = re.sub(r'[（）()]', '[PAREN]', t2_text)
            
            if t1_normalized == t2_normalized and t1_text != t2_text:
                paren1 = re.findall(r'[（）()]', t1_text)
                paren2 = re.findall(r'[（）()]', t2_text)
                
                if paren1 and paren2 and paren1 != paren2:
                    examples.append({
                        'type': 'parentheses',
                        'template1': t1_text,
                        'template2': t2_text,
                        'parentheses1': paren1,
                        'parentheses2': paren2,
                        'usage1': t1['usage_count'],
                        'usage2': t2['usage_count']
                    })
                    if len(examples) >= 5:
                        return examples
    
    return examples

def find_color_sequence_differences(templates):
    """Find templates that differ only in color sequences."""
    examples = []
    
    for i, t1 in enumerate(templates):
        for t2 in templates[i+1:]:
            t1_text = t1['template']
            t2_text = t2['template']
            
            # Check for color sequence differences
            t1_normalized = re.sub(r'(桃|赤|黄|緑|紫|青)\[CT\]', '[COLOR_CT]', t1_text)
            t2_normalized = re.sub(r'(桃|赤|黄|緑|紫|青)\[CT\]', '[COLOR_CT]', t2_text)
            
            if t1_normalized == t2_normalized and t1_text != t2_text:
                colors1 = re.findall(r'(桃|赤|黄|緑|紫|青)\[CT\]', t1_text)
                colors2 = re.findall(r'(桃|赤|黄|緑|紫|青)\[CT\]', t2_text)
                
                if colors1 and colors2 and colors1 != colors2:
                    examples.append({
                        'type': 'color_sequence',
                        'template1': t1_text,
                        'template2': t2_text,
                        'colors1': colors1,
                        'colors2': colors2,
                        'usage1': t1['usage_count'],
                        'usage2': t2['usage_count']
                    })
                    if len(examples) >= 5:
                        return examples
    
    return examples

def main():
    coverage_log_file = Path("data/ability_coverage_log.json")
    templates = load_templates(coverage_log_file)
    
    print("=== Actual Examples of Template Differences ===\n")
    
    # Conditional threshold differences
    print("1. CONDITIONAL THRESHOLDS (6 vs 7, etc.)")
    cond_examples = find_conditional_threshold_differences(templates)
    for ex in cond_examples[:3]:
        print(f"\n  Threshold: {ex['threshold1']} vs {ex['threshold2']}")
        print(f"  Template 1: {ex['template1']}")
        print(f"  Template 2: {ex['template2']}")
        print(f"  Usage: {ex['usage1']} vs {ex['usage2']}")
    
    # Position modifier differences
    print("\n\n2. POSITION MODIFIERS (一番上 vs 一番下)")
    pos_examples = find_position_modifier_differences(templates)
    for ex in pos_examples[:3]:
        print(f"\n  Position: {ex['position1']} vs {ex['position2']}")
        print(f"  Template 1: {ex['template1']}")
        print(f"  Template 2: {ex['template2']}")
        print(f"  Usage: {ex['usage1']} vs {ex['usage2']}")
    
    # Quantifier differences
    print("\n\n3. QUANTIFIERS (1人 vs すべて)")
    quant_examples = find_quantifier_differences(templates)
    for ex in quant_examples[:3]:
        print(f"\n  Quantifier: {ex['quantifier1']} vs {ex['quantifier2']}")
        print(f"  Template 1: {ex['template1']}")
        print(f"  Template 2: {ex['template2']}")
        print(f"  Usage: {ex['usage1']} vs {ex['usage2']}")
    
    # Parentheses differences
    print("\n\n4. PARENTHESES TYPES")
    paren_examples = find_parentheses_differences(templates)
    for ex in paren_examples[:3]:
        print(f"\n  Parentheses: {ex['parentheses1']} vs {ex['parentheses2']}")
        print(f"  Template 1: {ex['template1']}")
        print(f"  Template 2: {ex['template2']}")
        print(f"  Usage: {ex['usage1']} vs {ex['usage2']}")
    
    # Color sequence differences
    print("\n\n5. COLOR SEQUENCES")
    color_examples = find_color_sequence_differences(templates)
    for ex in color_examples[:3]:
        print(f"\n  Colors: {ex['colors1']} vs {ex['colors2']}")
        print(f"  Template 1: {ex['template1']}")
        print(f"  Template 2: {ex['template2']}")
        print(f"  Usage: {ex['usage1']} vs {ex['usage2']}")
    
    print("\n\n=== CONCLUSION ===")
    print("These differences ARE essentially variables that could be abstracted:")
    print("- Threshold numbers → [threshold_value]")
    print("- Position modifiers → [position_modifier]")  
    print("- Quantifiers → [quantifier]")
    print("- Parentheses types → [parentheses_type]")
    print("- Color sequences → [color_sequence]")
    print("\nAbstracting these would further reduce template count.")

if __name__ == "__main__":
    main()
