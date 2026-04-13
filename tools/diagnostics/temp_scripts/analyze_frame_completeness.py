#!/usr/bin/env python3
"""
Analyze ability_frame_source.json to identify incomplete abilities and suggest completion strategies.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter

def analyze_frames(source_file):
    """Analyze frame completeness across all abilities."""
    
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data.get('abilities', [])
    
    # Categories
    meta_rule_abilities = []  # Using META_RULE placeholders
    verified_abilities = []  # verified: true
    unverified_abilities = []  # verified: false
    no_frames = []  # Empty frames array
    missing_verification = []  # No frame_verification section
    
    # Frame operation statistics
    op_counts = Counter()
    frame_count_distribution = Counter()
    
    for ability in abilities:
        frames = ability.get('frames', [])
        verification = ability.get('frame_verification', {})
        verified = verification.get('verified', False)
        
        frame_count_distribution[len(frames)] += 1
        
        # Count operations
        for frame in frames:
            op = frame.get('op', 'UNKNOWN')
            op_counts[op] += 1
        
        # Categorize
        if not frames:
            no_frames.append(ability)
            continue
            
        # Check for META_RULE placeholders
        has_meta_rule = any(frame.get('op') == 'META_RULE' for frame in frames)
        if has_meta_rule:
            meta_rule_abilities.append(ability)
        elif verified:
            verified_abilities.append(ability)
        elif not verification:
            missing_verification.append(ability)
        else:
            unverified_abilities.append(ability)
    
    # Print summary
    print("=" * 60)
    print("FRAME COMPLETENESS ANALYSIS")
    print("=" * 60)
    print(f"\nTotal abilities: {len(abilities)}")
    print(f"\n--- Categories ---")
    print(f"Verified (complete): {len(verified_abilities)}")
    print(f"Using META_RULE placeholders: {len(meta_rule_abilities)}")
    print(f"Unverified (need review): {len(unverified_abilities)}")
    print(f"No frames: {len(no_frames)}")
    print(f"Missing verification section: {len(missing_verification)}")
    
    print(f"\n--- Frame Count Distribution ---")
    for count in sorted(frame_count_distribution.keys()):
        print(f"{count} frames: {frame_count_distribution[count]} abilities")
    
    print(f"\n--- Operation Types ---")
    for op, count in op_counts.most_common():
        print(f"{op}: {count}")
    
    # Show examples of each category
    print(f"\n--- META_RULE Placeholder Examples (first 5) ---")
    for i, ability in enumerate(meta_rule_abilities[:5]):
        print(f"\n{i+1}. {ability.get('primary_text_jp', '')[:80]}...")
        frames = ability.get('frames', [])
        print(f"   Frames: {len(frames)}")
        for frame in frames:
            print(f"   - {frame.get('op')}: {frame.get('params', {})}")
    
    print(f"\n--- Unverified Examples (first 5) ---")
    for i, ability in enumerate(unverified_abilities[:5]):
        print(f"\n{i+1}. {ability.get('primary_text_jp', '')[:80]}...")
        frames = ability.get('frames', [])
        verification = ability.get('frame_verification', {})
        print(f"   Frames: {len(frames)}")
        print(f"   Issues: {verification.get('issues', [])}")
    
    # Suggest completion strategy
    print(f"\n" + "=" * 60)
    print("COMPLETION STRATEGY")
    print("=" * 60)
    print(f"\n1. META_RULE abilities ({len(meta_rule_abilities)}):")
    print(f"   - These need concrete operations implemented")
    print(f"   - Use similar verified abilities as templates")
    print(f"   - Map Japanese text to operations")
    
    print(f"\n2. Unverified abilities ({len(unverified_abilities)}):")
    print(f"   - Review frame_verification.issues for specific problems")
    print(f"   - Compare with similar verified abilities")
    print(f"   - Add missing frames or fix incorrect ones")
    
    print(f"\n3. No frames ({len(no_frames)}):")
    print(f"   - Need complete frame implementation from scratch")
    print(f"   - Analyze Japanese text to determine required operations")
    
    print(f"\n4. Missing verification ({len(missing_verification)}):")
    print(f"   - Add frame_verification section")
    print(f"   - Document what each frame does")
    print(f"   - Set verified: true if confident")
    
    return {
        'total': len(abilities),
        'verified': len(verified_abilities),
        'meta_rule': len(meta_rule_abilities),
        'unverified': len(unverified_abilities),
        'no_frames': len(no_frames),
        'missing_verification': len(missing_verification),
        'op_counts': dict(op_counts),
        'frame_count_distribution': dict(frame_count_distribution)
    }

if __name__ == "__main__":
    source_file = Path(__file__).parent.parent / "data" / "ability_frame_source.json"
    analyze_frames(source_file)
