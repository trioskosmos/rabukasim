import re
import os
import json

def parse_enums(enum_file):
    with open(enum_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    effects = {}
    conditions = {}
    
    # Simple regex to find enum members
    effect_match = re.search(r'pub enum EffectType \{(.*?)\}', content, re.DOTALL)
    if effect_match:
        for line in effect_match.group(1).split('\n'):
            line = line.strip()
            if '=' in line:
                name, val = line.split('=')
                name = name.strip()
                val = int(re.search(r'\d+', val).group())
                effects[val] = name
    
    cond_match = re.search(r'pub enum ConditionType \{(.*?)\}', content, re.DOTALL)
    if cond_match:
        for line in cond_match.group(1).split('\n'):
            line = line.strip()
            if '=' in line:
                name, val = line.split('=')
                name = name.strip()
                val = int(re.search(r'\d+', val).group())
                conditions[val] = name
                
    return effects, conditions

def analyze_trace(trace_file):
    if not os.path.exists(trace_file):
        return {}
        
    # Detect encoding or try UTF-16LE which PowerShell often uses
    try:
        with open(trace_file, 'rb') as f:
            raw = f.read(2)
            if raw == b'\xff\xfe':
                encoding = 'utf-16'
            else:
                encoding = 'utf-8' # Fallback
        
        with open(trace_file, 'r', encoding=encoding, errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading trace: {e}")
        return {}
        
    test_to_opcodes = {}
    current_test = "Unknown/Setup"
    
    # Regex patterns
    test_pattern = re.compile(r'test ([\w:]+) \.\.\.')
    op_pattern = re.compile(r'\[TEST_OPCODE\] (\d+)')
    
    for line in lines:
        test_match = test_pattern.search(line)
        if test_match:
            current_test = test_match.group(1)
            if current_test not in test_to_opcodes:
                test_to_opcodes[current_test] = set()
            continue
            
        op_match = op_pattern.search(line)
        if op_match:
            op = int(op_match.group(1))
            if current_test not in test_to_opcodes:
                test_to_opcodes[current_test] = set()
            test_to_opcodes[current_test].add(op)
            
    return test_to_opcodes

def main():
    enum_file = 'engine_rust_src/src/core/enums.rs'
    trace_file = 'engine_rust_src/reports/telemetry_raw.log'
    
    if not os.path.exists(enum_file) or not os.path.exists(trace_file):
        print(f"Missing files: {enum_file} or {trace_file}")
        return
        
    effects, conditions = parse_enums(enum_file)
    
    # Trackers
    all_seen_opcodes = set()
    opcode_frequencies = {} # global freq
    test_to_opcodes = {}    # unique per test
    
    with open(trace_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if '[OPCODE]' not in line or ' | Test: ' not in line:
                continue
                
            try:
                # Split specifically on the markers
                parts = line.split(' | Test: ')
                if len(parts) < 2:
                    continue
                    
                op_part = parts[0].replace('[OPCODE]', '').strip()
                if not op_part.isdigit():
                    continue
                    
                op = int(op_part) % 1000 # Normalize negated opcodes
                test_name = parts[1].strip()
                
                # Basic junk filtering for test names
                if not test_name or '[OPCODE]' in test_name:
                    continue
                
                all_seen_opcodes.add(op)
                opcode_frequencies[op] = opcode_frequencies.get(op, 0) + 1
                
                if test_name not in test_to_opcodes:
                    test_to_opcodes[test_name] = set()
                test_to_opcodes[test_name].add(op)
            except Exception:
                continue
        
    # Generate Report
    report = []
    report.append("# Opcode Coverage Report (Enhanced)\n")
    
    report.append("## Summary")
    report.append(f"- Total unique opcodes defined: {len(effects) + len(conditions)}")
    report.append(f"- Unique opcodes triggered: {len(all_seen_opcodes)}")
    report.append(f"- Opcodes missing coverage: {(len(effects) + len(conditions)) - len(all_seen_opcodes)}")
    report.append(f"- Total opcode executions captured: {sum(opcode_frequencies.values())}\n")
    
    report.append("## Untested Opcodes")
    report.append("| Opcode | Name | Type |")
    report.append("|---|---|---|")
    for op, name in sorted(effects.items()):
        if op not in all_seen_opcodes:
            report.append(f"| {op} | {name} | Effect |")
    for op, name in sorted(conditions.items()):
        if op not in all_seen_opcodes:
            report.append(f"| {op} | {name} | Condition |")
    
    report.append("\n## Triggered Opcodes (Frequency)")
    report.append("| Opcode | Name | Type | Frequency |")
    report.append("|---|---|---|---|")
    all_enum_opcodes = sorted(list(effects.items()) + list(conditions.items()))
    for op, name in all_enum_opcodes:
        if op in all_seen_opcodes:
            freq = opcode_frequencies.get(op, 0)
            report.append(f"| {op} | {name} | {'Effect' if op in effects else 'Condition'} | {freq} |")

    report.append("\n## Per-Test Opcode Usage")
    report.append("| Test Name | Unique Opcodes Used |")
    report.append("| :--- | :--- |")
    for test_name, ops in sorted(test_to_opcodes.items(), key=lambda x: len(x[1]), reverse=True):
        report.append(f"| {test_name} | {len(ops)} |")
            
    with open('engine_rust_src/reports/opcode_coverage_report.md', 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    
    print("Report generated: engine_rust_src/reports/opcode_coverage_report.md")

if __name__ == "__main__":
    main()
