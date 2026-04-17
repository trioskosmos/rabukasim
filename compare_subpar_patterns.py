"""Compare generated vs authored ability_frame_source to identify subpar frame patterns."""

import json
from collections import defaultdict

with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    generated = json.load(f)

with open('data/ability_frame_source_authored.json', 'r', encoding='utf-8') as f:
    authored = json.load(f)

print(f"Generated abilities: {len(generated['abilities'])}")
print(f"Authored abilities: {len(authored['abilities'])}")

# Create lookup by ability_id
generated_by_id = {ab['ability_id']: ab for ab in generated['abilities']}
authored_by_id = {ab['ability_id']: ab for ab in authored['abilities']}

# Find differences
differences = []
only_in_generated = set(generated_by_id.keys()) - set(authored_by_id.keys())
only_in_authored = set(authored_by_id.keys()) - set(generated_by_id.keys())
common_ids = set(generated_by_id.keys()) & set(authored_by_id.keys())

print(f"\nOnly in generated: {len(only_in_generated)}")
print(f"Only in authored: {len(only_in_authored)}")
print(f"Common abilities: {len(common_ids)}")

# Analyze common abilities for frame differences
frame_diff_stats = defaultdict(int)
frame_diff_details = []

for ability_id in sorted(common_ids):
    gen_ab = generated_by_id[ability_id]
    auth_ab = authored_by_id[ability_id]
    
    gen_frames = gen_ab.get('frames', [])
    auth_frames = auth_ab.get('frames', [])
    
    if gen_frames != auth_frames:
        frame_diff_stats[f"{len(gen_frames)} vs {len(auth_frames)} frames"] += 1
        
        # Detailed analysis
        if len(gen_frames) != len(auth_frames):
            frame_diff_details.append({
                'ability_id': ability_id,
                'issue': f'Frame count mismatch: {len(gen_frames)} generated vs {len(auth_frames)} authored',
                'generated_ops': [f.get('op') for f in gen_frames],
                'authored_ops': [f.get('op') for f in auth_frames],
            })
        else:
            # Check for op differences
            gen_ops = [f.get('op') for f in gen_frames]
            auth_ops = [f.get('op') for f in auth_frames]
            if gen_ops != auth_ops:
                frame_diff_details.append({
                    'ability_id': ability_id,
                    'issue': 'Opcode sequence mismatch',
                    'generated_ops': gen_ops,
                    'authored_ops': auth_ops,
                })
            else:
                # Check for attribute/slot differences
                for i, (gen_f, auth_f) in enumerate(zip(gen_frames, auth_frames)):
                    if gen_f != auth_f:
                        frame_diff_details.append({
                            'ability_id': ability_id,
                            'issue': f'Frame {i} details differ',
                            'generated_frame': gen_f,
                            'authored_frame': auth_f,
                        })
                        break

print(f"\nFrame differences: {len(frame_diff_details)}")
print("\nFrame difference statistics:")
for diff_type, count in sorted(frame_diff_stats.items()):
    print(f"  {diff_type}: {count}")

# Show first 10 differences
print("\nFirst 10 frame differences:")
for i, diff in enumerate(frame_diff_details[:10]):
    print(f"\n{i+1}. Ability ID: {diff['ability_id']}")
    print(f"   Issue: {diff['issue']}")
    if 'generated_ops' in diff:
        print(f"   Generated ops: {diff['generated_ops']}")
        print(f"   Authored ops: {diff['authored_ops']}")

# Analyze opcode usage patterns
gen_op_counts = defaultdict(int)
auth_op_counts = defaultdict(int)

for ab in generated['abilities']:
    for frame in ab.get('frames', []):
        gen_op_counts[frame.get('op')] += 1

for ab in authored['abilities']:
    for frame in ab.get('frames', []):
        auth_op_counts[frame.get('op')] += 1

print("\n\nOpcode usage comparison:")
all_ops = sorted(set(gen_op_counts.keys()) | set(auth_op_counts.keys()))
for op in all_ops:
    gen_count = gen_op_counts.get(op, 0)
    auth_count = auth_op_counts.get(op, 0)
    if gen_count != auth_count:
        print(f"  {op}: {gen_count} generated vs {auth_count} authored")
