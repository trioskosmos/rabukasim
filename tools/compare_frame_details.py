"""Compare frame details between backup and converted for common abilities."""

import json

with open("launcher/static_content/data/ability_frame_source.json.backup", "r", encoding="utf-8") as f:
    backup_data = json.load(f)
backup_abilities = {ab["primary_text_jp"]: ab for ab in backup_data["abilities"]}

with open("data/ability_frame_source.json", "r", encoding="utf-8") as f:
    converted_data = json.load(f)
converted_abilities = {ab["primary_text_jp"]: ab for ab in converted_data["abilities"]}

common_texts = set(backup_abilities.keys()) & set(converted_abilities.keys())

print(f"=== FRAME OPCODE COMPARISON FOR COMMON ABILITIES ===\n")

backup_op_counts = {}
converted_op_counts = {}

for text in common_texts:
    for frame in backup_abilities[text].get("frames", []):
        op = frame.get("op", "UNKNOWN")
        backup_op_counts[op] = backup_op_counts.get(op, 0) + 1
    
    for frame in converted_abilities[text].get("frames", []):
        op = frame.get("op", "UNKNOWN")
        converted_op_counts[op] = converted_op_counts.get(op, 0) + 1

all_ops = set(backup_op_counts.keys()) | set(converted_op_counts.keys())

print("OPCODE USAGE DIFFERENCES:\n")
for op in sorted(all_ops):
    backup_count = backup_op_counts.get(op, 0)
    converted_count = converted_op_counts.get(op, 0)
    diff = converted_count - backup_count
    if diff != 0:
        print(f"{op}: Backup={backup_count}, Converted={converted_count} (diff={diff})")

print("\n=== OPCODES ONLY IN BACKUP ===\n")
backup_only_ops = set(backup_op_counts.keys()) - set(converted_op_counts.keys())
for op in sorted(backup_only_ops):
    print(f"{op}: {backup_op_counts[op]} occurrences")

print("\n=== OPCODES ONLY IN CONVERTED ===\n")
converted_only_ops = set(converted_op_counts.keys()) - set(backup_op_counts.keys())
for op in sorted(converted_only_ops):
    print(f"{op}: {converted_op_counts[op]} occurrences")
