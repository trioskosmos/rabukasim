"""
Comprehensive Ability Pipeline Audit
Analyzes weakpoints across the entire cards.json -> pseudocode -> bytecode -> engine pipeline.
"""

import json
import os
import re
from collections import defaultdict


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_audit():
    cards = load_json("data/cards.json")
    pseudocode = load_json("data/manual_pseudocode.json")
    compiled = load_json("data/cards_compiled.json")
    qa_data = load_json("data/qa_data.json")

    # Build reverse lookups
    compiled_by_cardno = {}
    for db_key in ["member_db", "live_db", "energy_db"]:
        for cid, cdata in compiled.get(db_key, {}).items():
            card_no = cdata.get("card_no", "")
            if card_no:
                compiled_by_cardno[card_no] = cdata

    # QA cards
    qa_cards = set()
    for qa in qa_data:
        for rc in qa.get("related_cards", []):
            qa_cards.add(rc.get("card_no", ""))

    # Rust test file card references
    rust_test_dir = "engine_rust_src/src"
    tested_cards = set()
    for root, dirs, files in os.walk(rust_test_dir):
        for fn in files:
            if "test" in fn and fn.endswith(".rs"):
                filepath = os.path.join(root, fn)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Find card_no patterns like "PL!..."
                found = re.findall(r"PL![A-Za-z!-]+[-_][a-zA-Z0-9＋+]+[-_][a-zA-Z0-9＋+]+", content)
                tested_cards.update(found)

    # Python test card references
    py_test_dir = "tests"
    if os.path.exists(py_test_dir):
        for root, dirs, files in os.walk(py_test_dir):
            for fn in files:
                if fn.endswith(".py"):
                    filepath = os.path.join(root, fn)
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    found = re.findall(r"PL![A-Za-z!-]+[-_][a-zA-Z0-9＋+]+[-_][a-zA-Z0-9＋+]+", content)
                    tested_cards.update(found)

    # --- ANALYSIS ---
    report = []
    report.append("# Ability Pipeline Audit Report\n")

    # 1. Cards with abilities but NO pseudocode anywhere
    cards_with_ability = {k: v for k, v in cards.items() if v.get("ability", "").strip()}
    cards_no_pseudocode = []
    for card_no, card_data in cards_with_ability.items():
        has_manual = card_no in pseudocode and pseudocode[card_no].get("pseudocode", "").strip()
        if not has_manual:
            cards_no_pseudocode.append(card_no)

    report.append("## 1. Coverage Gap: Cards with Abilities but No Manual Pseudocode")
    report.append(f"**Count: {len(cards_no_pseudocode)} / {len(cards_with_ability)} cards with abilities**\n")
    if cards_no_pseudocode:
        for cn in sorted(cards_no_pseudocode)[:50]:
            name = cards.get(cn, {}).get("name", "?")
            ab_preview = cards.get(cn, {}).get("ability", "")[:80]
            report.append(f"- `{cn}` ({name}): {ab_preview}...")
        if len(cards_no_pseudocode) > 50:
            report.append(f"- ... and {len(cards_no_pseudocode) - 50} more")
    report.append("")

    # 2. Cards with QA data but no test coverage
    qa_no_test = qa_cards - tested_cards
    report.append("## 2. QA Data Without Test Coverage")
    report.append(f"**{len(qa_no_test)} cards referenced in QA but not found in any test file**\n")
    for cn in sorted(qa_no_test)[:30]:
        # Find which QA items reference this card
        qa_ids = []
        for qa in qa_data:
            for rc in qa.get("related_cards", []):
                if rc.get("card_no") == cn:
                    qa_ids.append(qa.get("id", "?"))
        report.append(f"- `{cn}`: QA refs: {', '.join(qa_ids[:5])}")
    if len(qa_no_test) > 30:
        report.append(f"- ... and {len(qa_no_test) - 30} more")
    report.append("")

    # 3. Bytecode quality: cards where bytecode is empty but pseudocode exists
    empty_bytecode = []
    for card_no in pseudocode:
        pcode = pseudocode[card_no].get("pseudocode", "").strip()
        if not pcode:
            continue
        compiled_card = compiled_by_cardno.get(card_no)
        if compiled_card:
            abilities = compiled_card.get("abilities", [])
            if abilities:
                all_empty = all(not ab.get("bytecode") for ab in abilities)
                if all_empty:
                    empty_bytecode.append(card_no)
            else:
                empty_bytecode.append(card_no)

    report.append("## 3. Pseudocode Exists but Bytecode is Empty")
    report.append(f"**{len(empty_bytecode)} cards have manual pseudocode but compiled to empty bytecode**\n")
    for cn in sorted(empty_bytecode)[:30]:
        pcode_preview = pseudocode.get(cn, {}).get("pseudocode", "")[:80]
        report.append(f"- `{cn}`: `{pcode_preview}...`")
    if len(empty_bytecode) > 30:
        report.append(f"- ... and {len(empty_bytecode) - 30} more")
    report.append("")

    # 4. Pseudocode inconsistencies within same-ability groups
    ability_groups = defaultdict(list)
    for card_no, card_data in cards.items():
        ab = card_data.get("ability", "").strip()
        if ab:
            ability_groups[ab].append(card_no)

    inconsistent_groups = []
    for ab_text, group_cards in ability_groups.items():
        pcodes = {}
        for cn in group_cards:
            if cn in pseudocode:
                p = pseudocode[cn].get("pseudocode", "").strip()
                if p:
                    pcodes[cn] = p
        unique = set(pcodes.values())
        if len(unique) > 1:
            inconsistent_groups.append((ab_text, pcodes))

    report.append("## 4. Pseudocode Inconsistencies Within Same-Ability Groups")
    report.append(f"**{len(inconsistent_groups)} ability groups have conflicting pseudocodes**\n")
    for ab_text, pcodes in inconsistent_groups[:15]:
        report.append(f"### Ability: `{ab_text[:100]}...`")
        unique_pcodes = set(pcodes.values())
        report.append(f"**{len(unique_pcodes)} different pseudocodes across {len(pcodes)} cards:**")
        for i, (cn, p) in enumerate(pcodes.items()):
            if i < 3:
                report.append(f"- `{cn}`: `{p[:100]}...`")
        report.append("")
    if len(inconsistent_groups) > 15:
        report.append(f"... and {len(inconsistent_groups) - 15} more groups\n")

    # 5. Variant cards (rarity variants) with different pseudocode from base
    variant_divergence = []
    for card_no, card_data in cards.items():
        rare_list = card_data.get("rare_list", [])
        if len(rare_list) > 1:
            base_ab = card_data.get("ability", "").strip()
            for r in rare_list:
                v_no = r.get("card_no", "")
                if v_no != card_no and v_no in cards:
                    v_ab = cards[v_no].get("ability", "").strip()
                    if v_ab and v_ab != base_ab:
                        variant_divergence.append((card_no, v_no))

    report.append("## 5. Variant Cards with Different Ability Text")
    report.append(f"**{len(variant_divergence)} variant pairs have divergent ability text**\n")
    for base, var in variant_divergence[:20]:
        report.append(f"- `{base}` vs `{var}`")
    report.append("")

    # 6. High-value untested: cards with complex abilities (multi-trigger) and no tests
    complex_untested = []
    for card_no, card_data in cards_with_ability.items():
        ab = card_data.get("ability", "")
        trigger_count = (
            ab.count("png|登場")
            + ab.count("png|起動")
            + ab.count("png|常時")
            + ab.count("png|ライブ")
            + ab.count("png|自動")
        )
        if trigger_count >= 2 and card_no not in tested_cards:
            complex_untested.append((card_no, trigger_count, card_data.get("name", "?")))

    complex_untested.sort(key=lambda x: -x[1])

    report.append("## 6. Complex (Multi-Trigger) Cards Without Test Coverage")
    report.append(f"**{len(complex_untested)} cards have 2+ triggers and no test references**\n")
    for cn, tcount, name in complex_untested[:30]:
        report.append(f"- `{cn}` ({name}): **{tcount} triggers**")
    if len(complex_untested) > 30:
        report.append(f"- ... and {len(complex_untested) - 30} more")
    report.append("")

    # 7. Summary Stats
    report.append("## 7. Pipeline Summary Statistics\n")
    report.append("| Metric | Count |")
    report.append("|---|---|")
    report.append(f"| Total cards in cards.json | {len(cards)} |")
    report.append(f"| Cards with abilities | {len(cards_with_ability)} |")
    report.append(f"| Cards with manual pseudocode | {len(pseudocode)} |")
    report.append(f"| Cards with NO pseudocode (have ability) | {len(cards_no_pseudocode)} |")
    report.append(f"| QA items | {len(qa_data)} |")
    report.append(f"| Unique cards in QA | {len(qa_cards)} |")
    report.append(f"| Cards referenced in tests | {len(tested_cards)} |")
    report.append(f"| QA cards without tests | {len(qa_no_test)} |")
    report.append(f"| Pseudocode -> empty bytecode | {len(empty_bytecode)} |")
    report.append(f"| Same-ability pseudocode conflicts | {len(inconsistent_groups)} |")
    report.append(f"| Complex untested cards (2+ triggers) | {len(complex_untested)} |")
    report.append(f"| Compiled cards total | {len(compiled_by_cardno)} |")

    # Pseudocode coverage rate
    coverage = (
        ((len(cards_with_ability) - len(cards_no_pseudocode)) / len(cards_with_ability) * 100)
        if cards_with_ability
        else 0
    )
    report.append(f"| **Pseudocode coverage rate** | **{coverage:.1f}%** |")
    report.append("")

    # 8. Risk Assessment
    report.append("## 8. Risk Assessment\n")
    report.append("### 🔴 Critical Risks")
    report.append(
        f"- **{len(empty_bytecode)} cards** have pseudocode that compiles to empty bytecode — these abilities are silently broken"
    )
    report.append(
        f"- **{len(inconsistent_groups)} ability groups** have multiple conflicting pseudocodes — the consolidated mapping picks one but may pick wrong"
    )
    report.append("")
    report.append("### 🟠 High Risks")
    report.append(
        f"- **{len(cards_no_pseudocode)} cards** have abilities but no pseudocode at all — these parse raw JP text, likely producing garbage bytecode"
    )
    report.append(
        f"- **{len(qa_no_test)} QA-referenced cards** have no test coverage — official FAQs document edge cases that aren't verified"
    )
    report.append("")
    report.append("### 🟡 Medium Risks")
    report.append(
        f"- **{len(complex_untested)} complex multi-trigger cards** have no tests — these are most likely to have subtle bugs"
    )
    report.append(
        "- The parser (`parser_v2.py`) at 2066 lines has many alias mappings that can silently map wrong opcode"
    )
    report.append("")
    report.append("### Architectural Weakpoints")
    report.append(
        "1. **Pseudocode is freeform text** → no schema validation, easy to write something the parser silently ignores"
    )
    report.append(
        "2. **Parser alias explosion** → 50+ aliases mean the same intent can be expressed many ways, causing silent divergence"
    )
    report.append(
        "3. **No round-trip verification** → bytecode is never decompiled back to pseudocode to verify semantic equivalence"
    )
    report.append(
        "4. **Consolidated mapping uses longest-wins** → a longer but wrong pseudocode beats a shorter correct one"
    )
    report.append(
        "5. **Variant cards share ability text but may need distinct pseudocode** due to group filters (e.g., Nijigasaki vs μ's)"
    )
    report.append("6. **No compile-time warning for unrecognized pseudocode tokens** → typos pass silently")

    output_path = os.path.join("reports", "ability_pipeline_audit.md")
    os.makedirs("reports", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print(f"Audit report written to: {output_path}")
    print("Key findings:")
    print(f"  - {len(cards_no_pseudocode)} cards with ability but no pseudocode")
    print(f"  - {len(empty_bytecode)} cards with pseudocode but empty bytecode")
    print(f"  - {len(inconsistent_groups)} conflicting pseudocode groups")
    print(f"  - {len(qa_no_test)} QA cards without test coverage")
    print(f"  - {len(complex_untested)} complex untested cards")


if __name__ == "__main__":
    run_audit()
