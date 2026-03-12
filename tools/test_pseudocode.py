# -*- coding: utf-8 -*-
import os

os.environ["PYTHONUTF8"] = "1"  # Force UTF-8 on Windows before any I/O
"""Quick pseudocode → bytecode tester.

Usage:
    # Test a single pseudocode string:
    uv run python tools/test_pseudocode.py "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"

    # Test by card number (looks up consolidated_abilities.json):
    uv run python tools/test_pseudocode.py --card "PL!N-bp3-005-P"

    # Test by JP ability text key (looks up consolidated_abilities.json):
    uv run python tools/test_pseudocode.py --jp "{{jidou.png|自動}}..."

    # Bulk test ALL consolidated abilities:
    uv run python tools/test_pseudocode.py --all

    # Output to file:
    uv run python tools/test_pseudocode.py --all --output reports/pseudocode_audit.md
"""

import argparse
import io
import json
import os
import sys
import traceback

# UTF-8 safety
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compiler.parser_v2 import AbilityParserV2
from tools.verify.bytecode_decoder import decode_bytecode


def test_one_pseudocode(pseudocode: str, label: str = "", metadata: str = "", parser: AbilityParserV2 = None) -> dict:
    """Parse + compile one pseudocode string, return structured result."""
    if parser is None:
        parser = AbilityParserV2()

    result = {
        "label": label,
        "metadata": metadata,
        "pseudocode": pseudocode,
        "abilities": [],
        "errors": [],
        "ok": True,
    }

    try:
        abilities = parser.parse(pseudocode)
    except Exception as e:
        result["errors"].append(f"PARSE ERROR: {e}\n{traceback.format_exc()}")
        result["ok"] = False
        return result

    if not abilities:
        result["errors"].append("WARNING: Parser returned 0 abilities")
        result["ok"] = False
        return result

    # GRANT_ABILITY flattening (same as compiler/main.py)
    from engine.models.ability import EffectType

    extra_abilities = []
    for ab in abilities:
        for eff in ab.effects:
            if eff.effect_type == EffectType.GRANT_ABILITY:
                if "granted_ability_text" in eff.params:
                    inner_text = str(eff.params.pop("granted_ability_text"))
                    granted_abs = parser.parse(inner_text)
                    if granted_abs:
                        start_idx = len(abilities) + len(extra_abilities)
                        eff.value = start_idx
                        if "target_str" in eff.params:
                            del eff.params["target_str"]
                        extra_abilities.extend(granted_abs)
    abilities.extend(extra_abilities)

    for idx, ab in enumerate(abilities):
        ab_info = {
            "index": idx,
            "trigger": ab.trigger.name if hasattr(ab.trigger, "name") else str(ab.trigger),
            "is_once_per_turn": ab.is_once_per_turn,
            "conditions": [],
            "costs": [],
            "effects": [],
            "filters": [],
            "bytecode_raw": [],
            "bytecode_decoded": "",
            "compile_error": None,
        }

        for c in ab.conditions:
            ab_info["conditions"].append(
                f"{c.type.name}(val={c.value}, attr={c.attr})"
                + (f" params={c.params}" if c.params else "")
                + (" [NEGATED]" if c.is_negated else "")
            )

        for cost in ab.costs:
            ab_info["costs"].append(
                f"{cost.type.name}(val={cost.value})"
                + (f" params={cost.params}" if cost.params else "")
                + (" [Optional]" if cost.is_optional else "")
            )

        for eff in ab.effects:
            ab_info["effects"].append(
                f"{eff.effect_type.name}(val={eff.value}, target={eff.target.name})"
                + (f" params={eff.params}" if eff.params else "")
                + (" [Optional]" if eff.is_optional else "")
            )

        # Compile
        ab.card_no = label or "TEST"
        try:
            bytecode = ab.compile()
            ab_info["filters"] = ab.filters
            ab_info["semantic_form"] = ab.semantic_form
            ab_info["bytecode_raw"] = bytecode
            ab_info["bytecode_decoded"] = decode_bytecode(bytecode)
        except Exception as e:
            ab_info["compile_error"] = f"COMPILE ERROR: {e}\n{traceback.format_exc()}"
            result["ok"] = False
            result["errors"].append(f"Ability #{idx}: {e}")

        result["abilities"].append(ab_info)

    return result


def format_result(result: dict, verbose: bool = True) -> str:
    """Format a test result as human-readable text."""
    lines = []
    status = "✅" if result["ok"] else "❌"
    label = result["label"] or "Direct Input"
    lines.append(f"\n{'=' * 60}")
    lines.append(f"{status} {label}")
    lines.append(f"{'=' * 60}")

    if result["errors"]:
        for err in result["errors"]:
            lines.append(f"  ⚠️  {err}")

    if verbose:
        if result.get("metadata"):
            lines.append(f"\n{result['metadata']}")
        lines.append(f"\n  Pseudocode: {result['pseudocode']}")

    for ab in result["abilities"]:
        lines.append(f"\n  --- Ability #{ab['index']} ---")
        lines.append(f"  Trigger:    {ab['trigger']}" + (" (Once per turn)" if ab["is_once_per_turn"] else ""))

        if ab["conditions"]:
            lines.append(f"  Conditions: {len(ab['conditions'])}")
            for c in ab["conditions"]:
                lines.append(f"    • {c}")

        if ab["costs"]:
            lines.append(f"  Costs:      {len(ab['costs'])}")
            for cost in ab["costs"]:
                lines.append(f"    • {cost}")

        lines.append(f"  Effects:    {len(ab['effects'])}")
        for eff in ab["effects"]:
            lines.append(f"    • {eff}")

        if ab["filters"]:
            lines.append(f"  Filters:    {len(ab['filters'])}")
            for filt in ab["filters"]:
                summary = filt.get("summary", "none")
                packed_attr_hex = filt.get("packed_attr_hex", "0x0000000000000000")
                lines.append(f"    • {summary} [{packed_attr_hex}]")

        if ab.get("semantic_form"):
            lines.append(f"  📖 Semantic Form:")
            sem = ab["semantic_form"]
            if sem.get("effects"):
                lines.append(f"     Effects: {len(sem['effects'])}")
                for eff in sem["effects"]:
                    eff_desc = f"{eff.get('type', '?')} value={eff.get('value', 0)} target={eff.get('target', '?')}"
                    if eff.get("optional"):
                        eff_desc += " [optional]"
                    lines.append(f"       • {eff_desc}")
            if sem.get("conditions"):
                lines.append(f"     Conditions: {len(sem['conditions'])}")
                for cond in sem["conditions"]:
                    cond_desc = f"{cond.get('type', '?')} {cond.get('comparison', 'GE')} {cond.get('value', 0)}"
                    if cond.get("filter"):
                        cond_desc += f" filter:{cond.get('filter')}"
                    if cond.get("negated"):
                        cond_desc = "NOT " + cond_desc
                    lines.append(f"       • {cond_desc}")
            if sem.get("instructions_summary"):
                lines.append(f"     Order: {sem['instructions_summary']}")

        if ab["compile_error"]:
            lines.append(f"  ❌ {ab['compile_error']}")
        elif ab["bytecode_raw"]:
            lines.append(f"  Bytecode ({len(ab['bytecode_raw'])} ints):")
            lines.append(f"    Raw: {ab['bytecode_raw']}")
            # Show decoded without the legend
            decoded = ab["bytecode_decoded"]
            legend_idx = decoded.find("\n--- BYTECODE LEGEND ---")
            if legend_idx >= 0:
                decoded = decoded[:legend_idx].rstrip()
            lines.append("    Decoded:")
            for dl in decoded.split("\n"):
                lines.append(f"      {dl}")

    return "\n".join(lines)


def load_consolidated():
    """Load consolidated_abilities.json."""
    path = os.path.join(os.getcwd(), "data", "consolidated_abilities.json")
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run from project root.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_by_card_no(card_no: str, consolidated: dict) -> tuple:
    """Find pseudocode by card number."""
    for jp_text, entry in consolidated.items():
        if isinstance(entry, dict):
            cards = entry.get("cards", [])
            if card_no in cards:
                return jp_text, entry.get("pseudocode", jp_text)
    return None, None


def dump_reference():
    """Dump a cheat sheet of all available keywords and aliases."""
    import compiler.parser_v2 as p2
    from engine.models.ability import AbilityCostType, ConditionType, EffectType, TriggerType

    lines = []
    lines.append("=" * 60)
    lines.append(" PSEUDOCODE CHEAT SHEET ")
    lines.append("=" * 60)

    lines.append("\n--- BASE TRIGGERS ---")
    vals = [t.name for t in TriggerType if t.name != "NONE"]
    lines.append(", ".join(vals))

    lines.append("\n--- TRIGGER ALIASES ---")
    for alias, target in sorted(p2.TRIGGER_ALIASES.items()):
        lines.append(f"  {alias:<25} -> {target}")

    lines.append("\n--- BASE EFFECTS ---")
    vals = [e.name for e in EffectType]
    lines.append(", ".join(vals))

    lines.append("\n--- EFFECT ALIASES ---")
    for alias, target in sorted(p2.EFFECT_ALIASES.items()):
        lines.append(f"  {alias:<25} -> {target}")

    lines.append("\n--- EFFECT ALIASES WITH PARAMS ---")
    for alias, (target, params) in sorted(p2.EFFECT_ALIASES_WITH_PARAMS.items()):
        lines.append(f"  {alias:<25} -> {target} {params}")

    lines.append("\n--- BASE CONDITIONS ---")
    vals = [c.name for c in ConditionType if c.name != "NONE"]
    lines.append(", ".join(vals))

    lines.append("\n--- CONDITION ALIASES ---")
    for alias, (target, params) in sorted(p2.CONDITION_ALIASES.items()):
        lines.append(f"  {alias:<25} -> {target} {params}")

    lines.append("\n--- KEYWORD CONDITIONS ---")
    for alias, kw in sorted(p2.KEYWORD_CONDITIONS.items()):
        lines.append(f"  {alias:<25} -> HAS_KEYWORD (key={kw})")

    lines.append("\n--- BASE COSTS ---")
    vals = [c.name for c in AbilityCostType if c.name != "NONE"]
    lines.append(", ".join(vals))

    return "\n".join(lines)


def fetch_card_metadata(card_no: str) -> str:
    """Dynamically pull metadata, QA, and tests similar to card_finder."""
    try:
        import tools.card_finder as cf

        cards_raw = cf.load_json("data/cards.json") or {}
        cards_compiled = cf.load_json("data/cards_compiled.json") or {}
        qa_data = cf.load_json("data/qa_data.json") or []

        query = cf.extract_card_no(card_no)
        raw, compiled, cid = cf.find_card_by_no(query, cards_raw, cards_compiled)
        if not raw and not compiled and query.isdigit():
            compiled, cid = cf.find_card_by_id(query, cards_compiled)
            if compiled:
                raw = cards_raw.get(compiled.get("card_no"))

        lines = []
        if raw:
            lines.append(f"  Name:    {raw.get('name')}")
            lines.append(f"  JP Text: {raw.get('ability').strip()}")
        else:
            lines.append("  Name:    Unknown (Not found in data/cards.json)")

        real_card_no = compiled.get("card_no") if compiled else raw.get("card_no") if raw else query

        if real_card_no:
            # QA Data
            related_qas = [
                qa for qa in qa_data for rc in qa.get("related_cards", []) if rc.get("card_no") == real_card_no
            ]
            # Shared Cards
            shared_cards = []
            baseline_ability = raw.get("ability", "").strip() if raw else ""
            if baseline_ability:
                shared_cards = [
                    no
                    for no, c in cards_raw.items()
                    if no != real_card_no and c.get("ability", "").strip() == baseline_ability
                ]
            # Rust Tests
            rust_tests = []
            search_terms = set(
                [real_card_no, real_card_no.replace("＋", "+")]
                + [q.get("id") for q in related_qas]
                + [sc for sc in shared_cards]
                + [sc.replace("＋", "+") for sc in shared_cards]
            )
            rust_dir = "engine_rust_src/src"
            if os.path.exists(rust_dir):
                for root, dirs, files in os.walk(rust_dir):
                    for file in files:
                        if not file.endswith(".rs"):
                            continue
                        with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                            file_lines = f.readlines()
                        for i, line in enumerate(file_lines):
                            if any(term in line for term in search_terms):
                                func_name = "Unknown Test"
                                for j in range(i, -1, -1):
                                    m = re.search(r"fn\s+([a-zA-Z0-9_]+)\s*\(", file_lines[j])
                                    if m:
                                        func_name = m.group(1)
                                        break
                                rust_tests.append(f"{file}::{func_name}")
            rust_tests = sorted(list(set(rust_tests)))

            if related_qas:
                lines.append(f"  QA:      {len(related_qas)} rulings found")
            if shared_cards:
                lines.append(f"  Shared:  {len(shared_cards)} other cards have this ability")
            if rust_tests:
                lines.append(f"  Tests:   {len(rust_tests)} covered in Rust")
            else:
                lines.append("  Tests:   0 covered (WARNING)")

        return "\n".join(lines) if lines else ""
    except Exception as e:
        return f"  Metadata Error: {e}"


def main():
    ap = argparse.ArgumentParser(description="Quick pseudocode → bytecode tester")
    ap.add_argument("pseudocode", nargs="?", help="Pseudocode string to test (use \\n for newlines)")
    ap.add_argument("--card", help="Look up by card number in consolidated_abilities.json")
    ap.add_argument("--jp", help="Look up by JP text key in consolidated_abilities.json")
    ap.add_argument("--all", action="store_true", help="Test ALL consolidated abilities")
    ap.add_argument(
        "--reference", action="store_true", help="Dump a cheat sheet of all available keywords and parameters"
    )
    ap.add_argument("--output", "-o", help="Write output to file instead of stdout")
    ap.add_argument("--errors-only", action="store_true", help="Only show entries with errors")
    args = ap.parse_args()

    if args.reference:
        output = dump_reference()
        if args.output:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Output written to {args.output}")
        else:
            print(output)
        sys.exit(0)

    parser = AbilityParserV2()
    results = []

    if args.all:
        consolidated = load_consolidated()
        for jp_text, entry in consolidated.items():
            if isinstance(entry, dict):
                pseudocode = entry.get("pseudocode", "")
                cards = entry.get("cards", [])
                label = cards[0] if cards else jp_text[:50]
            else:
                pseudocode = entry
                label = jp_text[:50]
            if pseudocode:
                results.append(test_one_pseudocode(pseudocode, label=label, parser=parser))

    elif args.card:
        consolidated = load_consolidated()
        jp_text, pseudocode = find_by_card_no(args.card, consolidated)
        if pseudocode is None:
            print(f"ERROR: Card '{args.card}' not found in consolidated_abilities.json")
            sys.exit(1)
        meta = fetch_card_metadata(args.card)
        results.append(test_one_pseudocode(pseudocode, label=args.card, metadata=meta, parser=parser))

    elif args.jp:
        consolidated = load_consolidated()
        entry = consolidated.get(args.jp)
        if entry is None:
            print("ERROR: JP text key not found in consolidated_abilities.json")
            sys.exit(1)
        pseudocode = entry.get("pseudocode", args.jp) if isinstance(entry, dict) else entry
        results.append(test_one_pseudocode(pseudocode, label="JP lookup", parser=parser))

    elif args.pseudocode:
        # Replace literal \n with actual newlines
        pseudocode = args.pseudocode.replace("\\n", "\n")
        results.append(test_one_pseudocode(pseudocode, label="Direct input", parser=parser))

    else:
        ap.print_help()
        sys.exit(1)

    # Format output
    output_lines = []
    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    failed = total - passed

    for r in results:
        if args.errors_only and r["ok"]:
            continue
        output_lines.append(format_result(r, verbose=not args.all))

    # Summary for --all
    if args.all:
        output_lines.insert(0, f"\n{'=' * 60}")
        output_lines.insert(1, "  PSEUDOCODE COMPILATION AUDIT")
        output_lines.insert(2, f"  Total: {total} | ✅ Passed: {passed} | ❌ Failed: {failed}")
        output_lines.insert(3, f"{'=' * 60}")

    output = "\n".join(output_lines)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Output written to {args.output}")
        print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    else:
        print(output)


if __name__ == "__main__":
    main()
