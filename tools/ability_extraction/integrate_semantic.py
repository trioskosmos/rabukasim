#!/usr/bin/env python3
"""
Integrate semantic extraction results into abilities_extracted_from_cards.json
"""

import json
from pathlib import Path


def resolve_placeholder_chain(placeholder: str, variable_mappings: dict, visited: set = None) -> str:
    """Resolve placeholder chain to get actual value (handles nested placeholders like [card] -> [card_type] -> "カード")"""
    if visited is None:
        visited = set()
    
    if placeholder in visited:
        return placeholder  # Prevent infinite loops
    
    visited.add(placeholder)
    
    if placeholder in variable_mappings:
        mapped_value = variable_mappings[placeholder]
        # If mapped value is also a placeholder, resolve it recursively
        if isinstance(mapped_value, str) and mapped_value.startswith('[') and mapped_value.endswith(']'):
            return resolve_placeholder_chain(mapped_value, variable_mappings, visited)
        # Handle lists (for multiple occurrences) - use first value
        elif isinstance(mapped_value, list):
            if mapped_value:
                # If list contains placeholders, resolve the first one
                first_value = mapped_value[0]
                if isinstance(first_value, str) and first_value.startswith('[') and first_value.endswith(']'):
                    return resolve_placeholder_chain(first_value, variable_mappings, visited)
                return first_value
            return placeholder
        else:
            return mapped_value
    else:
        return placeholder


def resolve_variables(variables: dict, variable_mappings: dict) -> dict:
    """Resolve placeholder variables to actual values using variable_mappings"""
    resolved = {}
    for key, value in variables.items():
        placeholder = f"[{key}]"
        resolved_value = resolve_placeholder_chain(placeholder, variable_mappings)
        resolved[key] = resolved_value if resolved_value != placeholder else value
    return resolved


def resolve_sequential_operations(operations: list, variable_mappings: dict) -> list:
    """Resolve variables in sequential operations"""
    resolved_operations = []
    for operation in operations:
        resolved_op = operation.copy()
        if 'variables' in operation:
            resolved_op['variables'] = resolve_variables(operation['variables'], variable_mappings)
        resolved_operations.append(resolved_op)
    return resolved_operations


def main():
    abilities_file = Path("data/abilities_extracted_from_cards.json")
    semantic_file = Path("data/pattern_based_semantic_abilities.json")
    
    with open(abilities_file, 'r', encoding='utf-8') as f:
        abilities_data = json.load(f)
    
    with open(semantic_file, 'r', encoding='utf-8') as f:
        semantic_data = json.load(f)
    
    abilities = abilities_data['unique_abilities']
    semantic_abilities = semantic_data['semantic_abilities']
    
    print(f"Integrating semantic data for {len(abilities)} abilities...")
    
    # Match by index since both have 518 abilities in the same order
    for i, (ability, semantic) in enumerate(zip(abilities, semantic_abilities)):
        variable_mappings = ability.get('variable_mappings', {})
        
        # Resolve variables in semantic data
        resolved_semantic = {
            'timing': semantic['timing'],
            'cost': semantic['cost'],
            'conditions': semantic['conditions'],
            'selector': {
                'variables': resolve_variables(semantic['selector'].get('variables', {}), variable_mappings),
                'source': semantic['selector'].get('source', 'pattern_match')
            } if semantic.get('selector') else None,
            'action': {
                'operation': semantic['action']['operation'],
                'variables': resolve_variables(semantic['action'].get('variables', {}), variable_mappings),
                'source': semantic['action'].get('source', 'pattern_match')
            },
            'postcondition': semantic['postcondition'],
            'duration': semantic['duration'],
            'choice': semantic['choice'],
            'sequential_operations': resolve_sequential_operations(semantic['sequential_operations'], variable_mappings),
            'matched_patterns': semantic['matched_patterns']
        }
        
        ability['semantic'] = resolved_semantic
    
    # Update schema and add metadata
    abilities_data['schema'] = 'extracted_abilities_with_semantics.v1'
    abilities_data['semantic_source_file'] = 'data/pattern_based_semantic_abilities.json'
    
    # Save updated file
    with open(abilities_file, 'w', encoding='utf-8') as f:
        json.dump(abilities_data, f, indent=2, ensure_ascii=False)
    
    print(f"OK Integrated semantic data into {abilities_file}")
    print(f"  - {len(abilities)} abilities with semantic information")
    print(f"  - Variables resolved to actual values")
    print(f"  - Schema updated to: {abilities_data['schema']}")


if __name__ == "__main__":
    main()
