#!/usr/bin/env python3
"""
Script to analyze ability_frame_source.json and generate:
1. Frame statistics (most to least common)
2. Documentation of all frame types with examples
"""

import json
from collections import defaultdict
from pathlib import Path


def load_json_file(filepath):
    """Load JSON file and return data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_frames_and_examples(data):
    """
    Extract all frames with their examples.
    Returns: dict with frame_op -> list of {frame_data, examples}
    """
    frame_data = defaultdict(list)
    
    for ability in data.get('abilities', []):
        # Get text examples
        examples = []
        for text_info in ability.get('source_ability_texts', []):
            examples.extend(text_info.get('card_examples', []))
        
        primary_text = ability.get('primary_text_jp', '')
        
        for frame in ability.get('frames', []):
            op = frame.get('op', 'UNKNOWN')
            frame_data[op].append({
                'frame': frame,
                'examples': examples[:3],  # First 3 examples
                'text': primary_text[:200] if primary_text else ''  # Truncated text
            })
    
    return frame_data


def generate_statistics(frame_data):
    """Generate frame statistics sorted by frequency."""
    stats = []
    for op, entries in frame_data.items():
        stats.append({
            'op': op,
            'count': len(entries),
            'percentage': 0  # Will calculate later
        })
    
    # Sort by count descending
    stats.sort(key=lambda x: x['count'], reverse=True)
    
    total = sum(s['count'] for s in stats)
    for s in stats:
        s['percentage'] = (s['count'] / total * 100) if total > 0 else 0
    
    return stats


def write_statistics(stats, output_path):
    """Write frame statistics to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_frames': sum(s['count'] for s in stats),
            'unique_frame_types': len(stats),
            'frames_by_frequency': stats
        }, f, indent=2, ensure_ascii=False)


def extract_param_keys(frame):
    """Extract all parameter keys from a frame."""
    keys = set()
    
    # Direct frame keys (excluding common ones)
    for key in ['value', 'frame_index', 'op']:
        if key in frame:
            keys.add(key)
    
    # attr keys
    if 'attr' in frame and isinstance(frame['attr'], dict):
        for k in frame['attr'].keys():
            keys.add(f'attr.{k}')
    
    # slot keys
    if 'slot' in frame and isinstance(frame['slot'], dict):
        for k in frame['slot'].keys():
            keys.add(f'slot.{k}')
    
    # params keys
    if 'params' in frame and isinstance(frame['params'], dict):
        for k in frame['params'].keys():
            keys.add(f'params.{k}')
    
    return sorted(keys)


def collect_frame_variations(frame_data):
    """
    For each frame type, collect all the different parameter combinations seen.
    """
    variations = {}
    
    for op, entries in frame_data.items():
        seen_params = set()
        examples = []
        
        for entry in entries:
            frame = entry['frame']
            params = extract_param_keys(frame)
            param_tuple = tuple(params)
            
            if param_tuple not in seen_params:
                seen_params.add(param_tuple)
                examples.append({
                    'params': params,
                    'frame': frame,
                    'text': entry['text'],
                    'examples': entry['examples']
                })
        
        variations[op] = examples
    
    return variations


def write_documentation(variations, stats, output_path):
    """Write comprehensive markdown documentation."""
    lines = []
    
    lines.append('# Ability Frame Documentation\n')
    lines.append('Generated from ability_frame_source.json\n')
    lines.append(f'Total frame types: {len(stats)}\n')
    lines.append(f'Total frames: {sum(s["count"] for s in stats)}\n')
    lines.append('---\n\n')
    
    # Sort by frequency for the main documentation
    sorted_ops = [s['op'] for s in stats]
    
    for op in sorted_ops:
        entries = variations.get(op, [])
        count = sum(s['count'] for s in stats if s['op'] == op)
        
        lines.append(f'## {op}\n')
        lines.append(f'**Frequency:** {count} occurrences\n\n')
        
        if not entries:
            lines.append('_No examples available_\n\n')
            continue
        
        lines.append('### Parameter Variations\n')
        lines.append(f'{len(entries)} distinct parameter patterns observed.\n\n')
        
        for i, ex in enumerate(entries[:5], 1):  # Show up to 5 variations
            lines.append(f'#### Variation {i}\n')
            
            # Show the frame JSON (formatted)
            frame_json = json.dumps(ex['frame'], indent=2, ensure_ascii=False)
            lines.append('**Frame structure:**\n')
            lines.append(f'```json\n{frame_json}\n```\n')
            
            # Show text example
            if ex['text']:
                lines.append(f'**Matching text:** `{ex["text"][:150]}...`\n')
            
            # Show card examples
            if ex['examples']:
                lines.append('**Card examples:** ' + ', '.join(ex['examples']) + '\n')
            
            lines.append('\n')
        
        if len(entries) > 5:
            lines.append(f'... and {len(entries) - 5} more variations\n\n')
        
        lines.append('---\n\n')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(lines))


def main():
    data_dir = Path('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data')
    input_file = data_dir / 'ability_frame_source.json'
    stats_output = data_dir / 'frame_statistics.json'
    doc_output = data_dir / 'frame_documentation.md'
    
    print(f'Loading {input_file}...')
    data = load_json_file(input_file)
    
    print('Extracting frames and examples...')
    frame_data = extract_frames_and_examples(data)
    
    print('Generating statistics...')
    stats = generate_statistics(frame_data)
    write_statistics(stats, stats_output)
    print(f'  Written to: {stats_output}')
    
    print('Collecting frame variations...')
    variations = collect_frame_variations(frame_data)
    
    print('Writing documentation...')
    write_documentation(variations, stats, doc_output)
    print(f'  Written to: {doc_output}')
    
    print('\nTop 10 most common frames:')
    for s in stats[:10]:
        print(f'  {s["op"]}: {s["count"]} ({s["percentage"]:.1f}%)')
    
    print('\nTop 10 least common frames:')
    for s in stats[-10:]:
        print(f'  {s["op"]}: {s["count"]} ({s["percentage"]:.1f}%)')


if __name__ == '__main__':
    main()
