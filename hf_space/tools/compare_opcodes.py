import os
import re


def parse_rust_enums(content):
    opcodes = {}
    in_enum = False
    for line in content.splitlines():
        line = line.strip()
        if "pub enum EffectType" in line:
            in_enum = True
            continue
        if in_enum and "}" in line:
            in_enum = False
            continue
        if in_enum:
            match = re.match(r"(\w+)\s*=\s*(\d+),?", line)
            if match:
                opcodes[match.group(1)] = int(match.group(2))
    return opcodes


def parse_python_opcodes(content):
    opcodes = {}
    for line in content.splitlines():
        line = line.strip()
        match = re.match(r"(\w+)\s*=\s*(\d+)", line)
        if match and match.group(1) != "NOP":  # Skip NOP if not in others
            # Python uses SCREAMING_SNAKE_CASE, Rust uses PascalCase.
            # We should normalize to integer ID comparison.
            opcodes[match.group(1)] = int(match.group(2))
    return opcodes


def parse_js_opcodes(content):
    opcodes = {}
    in_obj = False
    for line in content.splitlines():
        line = line.strip()
        if "const EffectType = {" in line:
            in_obj = True
            continue
        if in_obj and "};" in line:
            in_obj = False
            break  # JS Defines it in one block
        if in_obj:
            # JS format: NAME: ID, or multiple on one line
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                match = re.search(r"(\w+):\s*(\d+)", part)
                if match:
                    opcodes[match.group(1)] = int(match.group(2))
    return opcodes


BASE_DIR = os.getcwd()

# 1. Rust
with open(os.path.join(BASE_DIR, "engine_rust_src/src/core/enums.rs"), "r", encoding="utf-8") as f:
    rust_ops = parse_rust_enums(f.read())

# 2. Python
with open(os.path.join(BASE_DIR, "engine/models/opcodes.py"), "r", encoding="utf-8") as f:
    py_ops = parse_python_opcodes(f.read())

# 3. JS
with open(os.path.join(BASE_DIR, "frontend/web_ui/js/ability_translator.js"), "r", encoding="utf-8") as f:
    js_ops = parse_js_opcodes(f.read())

# Compare

all_ids = set(rust_ops.values()) | set(py_ops.values()) | set(js_ops.values())

print(f"{'ID':<5} | {'Rust':<25} | {'Python':<25} | {'JS':<25}")
print("-" * 85)

discrepancies = False

for oid in sorted(all_ids):
    r_name = next((k for k, v in rust_ops.items() if v == oid), "MISSING")
    p_name = next((k for k, v in py_ops.items() if v == oid), "MISSING")
    j_name = next((k for k, v in js_ops.items() if v == oid), "MISSING")

    # Check for mismatches (ignoring name case differences, just presence)
    if "MISSING" in [r_name, p_name, j_name]:
        discrepancies = True
        print(f"{oid:<5} | {r_name:<25} | {p_name:<25} | {j_name:<25} <--- DISCREPANCY")
    else:
        # Optional: Print all to see alignment
        pass
        # print(f"{oid:<5} | {r_name:<25} | {p_name:<25} | {j_name:<25}")

if not discrepancies:
    print("No opcode ID mismatches found!")
else:
    print("\nDiscrepancies found. See above.")
