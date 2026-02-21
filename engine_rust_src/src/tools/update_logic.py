import os

file_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\core\logic.rs"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Ranges to delete (1-based inclusive, so need to adjust to 0-based exclusive/inclusive)
# 1299-2578 (resolve_bytecode body)
# 1163-1294 (pay_cost body)
# 1109-1159 (check_cost body)
# 982-1105 (check_condition_opcode body)
# 709-978 (check_condition body)
# 696-705 (get_context_card_id body)

ranges = [(1299, 2578), (1163, 1294), (1109, 1159), (982, 1105), (709, 978), (696, 705)]

# Sort ranges by start DESCENDING
ranges.sort(key=lambda x: x[0], reverse=True)

for start, end in ranges:
    # Convert 1-based inclusive to 0-based
    # Start: 1299 -> index 1298
    # End: 2578 -> index 2577 (but slice is exclusive, so +1? No, we want to delete line 2578 too)
    idx_start = start - 1
    idx_end = end  # slice [start:end] excludes end, so valid

    # Check bounds
    if idx_start < 0 or idx_end > len(lines):
        print(f"Error: Range {start}-{end} out of bounds")
        continue

    # Delete
    del lines[idx_start:idx_end]

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Updates applied.")
