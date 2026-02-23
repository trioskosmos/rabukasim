
import os
import re
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional

@dataclass
class FailureRecord:
    card_no: str
    ability_idx: str
    segment: str
    error_type: str
    effect_text: str
    expected: str
    actual: str
    raw_message: str

@dataclass
class ErrorPattern:
    pattern_id: str
    error_type: str
    effect: str
    count: int
    examples: List[str]
    value_mismatches: Dict[str, int]

def parse_audit_report(filepath: str) -> List[FailureRecord]:
    failures = []
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Regex for ability-level reporting rows
    # | Card No | Ability | Status | Details |
    # | PL!-PR-001-PR | Ab0 | ❌ FAIL | Stuck at segment 0: Mismatch OPPONENT_HAND_DELTA for 'EFFECT: ACTIVATE_MEMBER(1)': Exp 1, Got 0 |
    row_re = re.compile(r"\| (.*?) \| (.*?) \| ❌ FAIL \| (.*) \|")
    
    # Details parser: Stuck at segment (\d+): Mismatch (.*?) for '(.*?)': Exp (.*?), Got (.*)
    details_re = re.compile(r"Stuck at segment (\d+): Mismatch (.*?) for '(.*?)': Exp (.*?), Got (.*)")

    for line in lines:
        match = row_re.search(line)
        if match:
            card_no = match.group(1).strip()
            ability_idx = match.group(2).strip()
            details = match.group(3).strip()
            
            detail_match = details_re.search(details)
            if detail_match:
                segment = detail_match.group(1)
                error_type = detail_match.group(2)
                effect_text = detail_match.group(3)
                expected = detail_match.group(4)
                actual = detail_match.group(5)
                
                failures.append(FailureRecord(
                    card_no=card_no,
                    ability_idx=ability_idx,
                    segment=segment,
                    error_type=error_type,
                    effect_text=effect_text,
                    expected=expected,
                    actual=actual,
                    raw_message=details
                ))
            else:
                # Handle other failure formats (e.g., panics or different mismatch phrasing)
                failures.append(FailureRecord(
                    card_no=card_no,
                    ability_idx=ability_idx,
                    segment="?",
                    error_type="OTHER",
                    effect_text="?",
                    expected="?",
                    actual="?",
                    raw_message=details
                ))
    return failures

def get_effect_category(effect_text: str) -> str:
    # Normalize effect text for grouping
    # e.g., "EFFECT: ACTIVATE_MEMBER(1)" -> "ACTIVATE_MEMBER"
    if "EFFECT:" in effect_text:
        match = re.search(r"EFFECT: ([A-Z_]+)", effect_text)
        if match:
            return match.group(1)
    return effect_text

def analyze_failures(failures: List[FailureRecord]) -> Dict[str, ErrorPattern]:
    patterns = {}
    
    for f in failures:
        effect = get_effect_category(f.effect_text)
        pattern_id = f"{f.error_type}_{effect}"
        
        if pattern_id not in patterns:
            patterns[pattern_id] = ErrorPattern(
                pattern_id=pattern_id,
                error_type=f.error_type,
                effect=effect,
                count=0,
                examples=[],
                value_mismatches={}
            )
        
        p = patterns[pattern_id]
        p.count += 1
        if len(p.examples) < 5:
            p.examples.append(f"{f.card_no} ({f.ability_idx})")
        
        mismatch_key = f"Exp {f.expected}, Got {f.actual}"
        p.value_mismatches[mismatch_key] = p.value_mismatches.get(mismatch_key, 0) + 1
        
    return patterns

def generate_markdown(patterns: Dict[str, ErrorPattern], total_fails: int) -> str:
    sorted_patterns = sorted(patterns.values(), key=lambda x: x.count, reverse=True)
    
    md = "# Error Pattern Analysis Report\n\n"
    md += f"- Total Failures: {total_fails}\n"
    md += f"- Unique Patterns: {len(patterns)}\n\n"
    
    md += "## Summary Table\n\n"
    md += "| Pattern | Count | Error Type | Effect | Examples |\n"
    md += "| :--- | ---: | :--- | :--- | :--- |\n"
    
    for p in sorted_patterns:
        examples = ", ".join(p.examples[:3])
        md += f"| **{p.pattern_id}** | {p.count} | {p.error_type} | {p.effect} | {examples} |\n"
    
    md += "\n## Detailed Pattern Breakdown\n\n"
    
    for p in sorted_patterns:
        md += f"### {p.pattern_id}\n\n"
        md += f"- **Count**: {p.count}\n"
        md += f"- **Error Type**: {p.error_type}\n"
        md += f"- **Effect**: {p.effect}\n\n"
        
        md += "#### Value Mismatches\n"
        sorted_mismatches = sorted(p.value_mismatches.items(), key=lambda x: x[1], reverse=True)
        for val, count in sorted_mismatches:
            md += f"- `{val}`: {count} occurrences\n"
        
        md += "\n#### Examples\n"
        for ex in p.examples:
            md += f"- {ex}\n"
        md += "\n---\n"
        
    return md

def main():
    report_path = "reports/COMPREHENSIVE_SEMANTIC_AUDIT.md"
    output_path = "reports/ERROR_PATTERN_ANALYSIS.md"
    json_path = "reports/ERROR_PATTERN_ANALYSIS.json"
    
    print(f"Reading audit report from {report_path}...")
    failures = parse_audit_report(report_path)
    print(f"Found {len(failures)} failures.")
    
    patterns = analyze_failures(failures)
    print(f"Identified {len(patterns)} unique error patterns.")
    
    md_content = generate_markdown(patterns, len(failures))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Markdown report written to {output_path}")
    
    # Save JSON for programmatic access
    json_data = {pid: asdict(p) for pid, p in patterns.items()}
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print(f"JSON data written to {json_path}")

if __name__ == "__main__":
    main()
