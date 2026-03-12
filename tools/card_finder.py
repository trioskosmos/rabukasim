import argparse
import json
import os
import re
import sys

from verify.bytecode_decoder import decode_bytecode


# Standardized UTF-8 Handling (as per GEMINI.md)
def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_card_no(query):
    # Regex to find card numbers like PL!S-bp2-005-P or PL!-bp3-001-R
    # Matches strings that look like Love Live card IDs within URLs or paths
    pattern = r"([A-Z!]+-[a-zA-Z0-9]+-[0-9]+-[A-Z＋-]+)"
    match = re.search(pattern, query)
    if match:
        return match.group(1)

    # Try simpler match for filenames in URLs if complex pattern fails
    # e.g. .../PL!S-bp2-005-P.webp
    pattern_simple = r"/([^/]+)\.(?:webp|png|jpg)$"
    match_simple = re.search(pattern_simple, query)
    if match_simple:
        return match_simple.group(1)

    return query


def find_card_by_id(query_id, cards_compiled):
    # Try to find card by its Packed ID or Logic ID
    try:
        qid = int(query_id)
    except ValueError:
        return None, None

    # Search in all DBs (member, live, energy)
    for db_name in ["member_db", "live_db", "energy_db"]:
        db = cards_compiled.get(db_name, {})
        # 1. Search by exact key (Packed ID as string)
        if str(qid) in db:
            return db[str(qid)], str(qid)

        # 2. Search by Logic ID
        for cid, c in db.items():
            logic_id = int(cid) & 0x0FFF
            if logic_id == qid:
                return c, cid

    return None, None


def find_card_by_no(no, cards_raw, cards_compiled):
    # Standardize plus signs for searching
    nos_to_try = [no]
    if "＋" in no:
        nos_to_try.append(no.replace("＋", "+"))
    if "+" in no:
        nos_to_try.append(no.replace("+", "＋"))
    # Remove duplicates while preserving order for efficiency
    nos_to_try = list(dict.fromkeys(nos_to_try))

    raw_data = None
    for n in nos_to_try:
        raw_data = cards_raw.get(n)
        if raw_data:
            # If found, update 'no' to the variant that worked for raw_data
            # This ensures subsequent searches for compiled data use the same successful variant
            no = n
            break

    compiled_data = None
    compiled_id = None

    # Search for all variants in compiled data
    for n_compiled in nos_to_try:
        db_names = ["member_db", "live_db", "energy_db"]
        for db_name in db_names:
            db = cards_compiled.get(db_name, {})
            for cid, c in db.items():
                if c.get("card_no") == n_compiled:
                    compiled_data = c
                    compiled_id = cid
                    return raw_data, compiled_data, compiled_id

    return raw_data, compiled_data, compiled_id


def main():
    # Ensure stdout/stderr use UTF-8 regardless of locale
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    elif sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Unified card lookup and report generator.")
    parser.add_argument("queries", nargs="+", help="Card No, URL, Packed ID, or Logic ID (one or more)")
    parser.add_argument("-o", "--output", help="Write report(s) to folder or specific file (if single query)", type=str)
    parser.add_argument("--json", action="store_true", help="Output raw JSON for the first matched card and exit")
    parser.add_argument("--legacy", action="store_true", help="Output legacy verbose terminal format instead of AI-optimized markdown")

    args = parser.parse_args()

    CARDS_RAW_PATH = "data/cards.json"
    CARDS_COMPILED_PATH = "data/cards_compiled.json"

    # Efficiently load (standardized)
    print("--- Loading Sources ---")
    cards_raw = load_json(CARDS_RAW_PATH) or {}
    cards_compiled = load_json(CARDS_COMPILED_PATH) or {}
    manual_pseudo = load_json("data/manual_pseudocode.json") or {}
    qa_data = load_json("data/qa_data.json") or []
    consolidated_pseudo = load_json("data/consolidated_abilities.json") or {}

    for raw_query in args.queries:
        raw_query = raw_query.strip()
        query = extract_card_no(raw_query)

        print(f"\n--- Searching for '{query}' (from '{raw_query}') ---")

        # 1. Search by exact Card No
        raw, compiled, cid = find_card_by_no(query, cards_raw, cards_compiled)

        # 2. Search by ID if No not found and query looks like a number
        if (not raw and not compiled) and query.isdigit():
            compiled, cid = find_card_by_id(query, cards_compiled)
            if compiled:
                # If we found it by ID, try to get raw data by its card_no
                raw = cards_raw.get(compiled.get("card_no"))

        if not raw and not compiled:
            # 3. Search by text if no exact match
            found_nos = []
            for no, c in cards_raw.items():
                if query.lower() in str(c).lower():
                    found_nos.append(no)

            if found_nos:
                print(f"Found {len(found_nos)} matches by text for '{query}':")
                for no in found_nos[:10]:
                    print(f"  - {no}")
                if len(found_nos) > 10:
                    print(f"  ... and {len(found_nos) - 10} more.")
            else:
                print(f"No matches found for '{query}'.")
            continue

        if args.json:
            print(json.dumps(compiled, indent=2, ensure_ascii=False))
            sys.exit(0)

        # 4. Fetch Cross-References
        card_no = compiled.get("card_no") if compiled else raw.get("card_no") if raw else query

        # 4a. Find QA Data
        related_qas = []
        if card_no:
            for qa in qa_data:
                for rc in qa.get("related_cards", []):
                    if rc.get("card_no") == card_no:
                        related_qas.append(qa)
                        break

        # 4b. Find Shared Abilities
        shared_cards = []
        baseline_ability = raw.get("ability", "").strip() if raw else ""
        if baseline_ability:
            for no, c in cards_raw.items():
                if no != card_no and c.get("ability", "").strip() == baseline_ability:
                    shared_cards.append(no)

        # 4c. Find Rust Tests
        rust_tests = []
        if card_no:
            search_terms = set([card_no, card_no.replace("＋", "+")])
            for q in related_qas:
                search_terms.add(q.get("id"))
            for sc in shared_cards:
                search_terms.add(sc)
                search_terms.add(sc.replace("＋", "+"))

            rust_dir = "engine_rust_src/src"
            if os.path.exists(rust_dir):
                for root, dirs, files in os.walk(rust_dir):
                    for file in files:
                        if file.endswith(".rs"):
                            filepath = os.path.join(root, file)
                            try:
                                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                                    lines = f.readlines()

                                for i, line in enumerate(lines):
                                    if any(term in line for term in search_terms):
                                        func_name = "Unknown Test"
                                        for j in range(i, -1, -1):
                                            if "fn test_" in lines[j] or "fn repro_" in lines[j] or "fn " in lines[j]:
                                                m = re.search(r"fn\s+([a-zA-Z0-9_]+)\s*\(", lines[j])
                                                if m:
                                                    func_name = m.group(1)
                                                    break
                                        rust_tests.append(f"{file}::{func_name}")
                            except:
                                pass
            rust_tests = sorted(list(set(rust_tests)))

        # 5. Display or Save
        if args.output:
            out_file = args.output
            if len(args.queries) > 1 or os.path.isdir(args.output):
                if not os.path.exists(args.output):
                    os.makedirs(args.output, exist_ok=True)

                safe_no = card_no.replace("!", "_").replace("+", "plus").replace("＋", "plus")
                out_file = os.path.join(args.output, f"card_{safe_no}.md")

            generate_report(
                out_file,
                query,
                raw,
                compiled,
                cid,
                manual_pseudo,
                consolidated_pseudo,
                related_qas,
                shared_cards,
                rust_tests,
            )
        elif args.legacy:
            display_card_legacy(
                query, raw, compiled, cid, manual_pseudo, consolidated_pseudo, related_qas, shared_cards, rust_tests
            )
        else:
            display_card_ai(
                query, raw, compiled, cid, manual_pseudo, consolidated_pseudo, related_qas, shared_cards, rust_tests
            )


def display_card_legacy(
    query, raw, compiled, cid, manual_pseudo, consolidated_pseudo, related_qas, shared_cards, rust_tests
):
    print(f"\n[ CARD: {compiled.get('card_no') if compiled else query} ]")
    if cid is not None:
        packed_id = int(cid)
        logic_id = packed_id & 0x0FFF
        variant = packed_id >> 12
        print(f"Engine Packed ID: {packed_id}")
        print(f"Logic ID: {logic_id}, Variant: {variant}")

    print("\n--- CONTENT (Source: cards.json) ---")
    if raw:
        print(f"Name: {raw.get('name')}")
        print(f"Card No: {raw.get('card_no')}")
        print(f"Ability (JP): {raw.get('ability')}")
        print(f"Ability (JP): {raw.get('ability')}")
        print(f"Pseudocode (Raw): {raw.get('pseudocode')}")

        # Consolidate Check
        ab_norm = raw.get("ability", "").strip()
        if ab_norm in consolidated_pseudo:
            print(f"Pseudocode (Consolidated DB): {consolidated_pseudo[ab_norm]}")

        # Check Manual Override
        card_no = raw.get("card_no")
        if card_no and card_no in manual_pseudo:
            print(f"Pseudocode (Manual Override): {manual_pseudo[card_no].get('pseudocode')}")
    else:
        print("NOT FOUND IN RAW DATA")

    print("\n--- CROSS-REFERENCES ---")
    if shared_cards:
        print(
            f"Shared Ability Cards: {len(shared_cards)} ({', '.join(shared_cards[:5])}{'...' if len(shared_cards) > 5 else ''})"
        )
    else:
        print("Shared Ability Cards: None")

    print(f"QA Rulings: {len(related_qas)}")
    for qa in related_qas:
        print(f"\n  [{qa.get('id')}] Q: {qa.get('question')}")
        print(f"  A: {qa.get('answer')}")

    print(f"Rust Test Coverage: {len(rust_tests)} files")
    for t in rust_tests:
        print(f"  - {t}")

    print("\n--- LOGIC (Source: cards_compiled.json) ---")
    if compiled:
        print(f"Name (Compiled): {compiled.get('name')}")
        for i, ab in enumerate(compiled.get("abilities", [])):
            print(f"Ability {i}:")
            trigger_id = ab.get("trigger", 0)
            bytecode = ab.get("bytecode", [])
            print(f"  Trigger: {trigger_id}")
            print(f"  Bytecode: {bytecode}")
            print(f"  Decoded:\n{decode_bytecode(bytecode)}")

        print("\n--- RAW JSON DUMP ---")
        print(json.dumps(compiled, indent=2, ensure_ascii=False))
    else:
        print("NOT FOUND IN COMPILED DATA")


def display_card_ai(query, raw, compiled, cid, manual_pseudo, consolidated_pseudo, related_qas, shared_cards, rust_tests):
    """Output a dense, structured markdown summary optimized for AI consumption."""
    card_no = compiled.get("card_no") if compiled else raw.get("card_no") if raw else query
    print(f"\n### Card Analysis: {card_no}")

    if cid is not None:
        packed_id = int(cid)
        logic_id = packed_id & 0x0FFF
        variant = packed_id >> 12
        print(f"- **IDs**: Packed=`{packed_id}`, Logic=`{logic_id}`, Var=`{variant}`")

    if raw:
        print(f"- **Name**: {raw.get('name')}")
        print(f"- **JP Ability**: {raw.get('ability').replace('\n', ' ')}")

        # Pseudocode resolution
        ab_norm = raw.get("ability", "").strip()
        pseudo = ""
        if card_no in manual_pseudo:
            pseudo = manual_pseudo[card_no].get("pseudocode")
            print(f"- **Pseudocode (Manual)**: `{pseudo}`")
        elif ab_norm in consolidated_pseudo:
            pseudo = consolidated_pseudo[ab_norm]
            if isinstance(pseudo, dict):
                pseudo = pseudo.get("pseudocode", "")
            print(f"- **Pseudocode (Consolidated)**: `{pseudo}`")
        else:
            pseudo = raw.get("pseudocode", "")
            print(f"- **Pseudocode (Raw)**: `{pseudo}`")

    if compiled:
        for i, ab in enumerate(compiled.get("abilities", [])):
            trigger_id = ab.get("trigger", 0)
            bytecode = ab.get("bytecode", [])
            print(f"\n#### Ability {i} (Trigger: {trigger_id})")
            print(f"**Bytecode**: `{bytecode}`")
            print("**Decoded**:")
            print("```")
            print(decode_bytecode(bytecode))
            print("```")

    if related_qas:
        print(f"- **QA Rulings**: {len(related_qas)} items found.")

    if rust_tests:
        print(f"- **Rust Tests**: {', '.join(rust_tests[:3])}{'...' if len(rust_tests) > 3 else ''}")

    print("\n---\n")


def generate_report(
    output_path, query, raw, compiled, cid, manual_pseudo, consolidated_pseudo, related_qas, shared_cards, rust_tests
):
    card_no = compiled.get("card_no") if compiled else query
    lines = []
    lines.append(f"# Card Report: {card_no}")

    if cid is not None:
        packed_id = int(cid)
        logic_id = packed_id & 0x0FFF
        variant = packed_id >> 12
        lines.append("\n## IDs")
        lines.append(f"- **Engine Packed ID**: `{packed_id}`")
        lines.append(f"- **Logic ID**: `{logic_id}`")
        lines.append(f"- **Variant Index**: `{variant}`")

    lines.append("\n## Metadata (Source: cards.json)")
    if raw:
        lines.append(f"- **Name**: {raw.get('name')}")
        lines.append(f"- **Card No**: {raw.get('card_no')}")
        lines.append(f"- **Ability (JP)**:\n```\n{raw.get('ability')}\n```")
        lines.append(f"- **Pseudocode (Raw)**: `{raw.get('pseudocode')}`")

        ab_norm = raw.get("ability", "").strip()
        if ab_norm in consolidated_pseudo:
            lines.append(f"\n### Pseudocode (Consolidated DB)\n```\n{consolidated_pseudo[ab_norm]}\n```")

        # Check Manual Override
        card_no = raw.get("card_no")
        if card_no and card_no in manual_pseudo:
            mp = manual_pseudo[card_no].get("pseudocode")
            lines.append(f"\n### Manual Pseudocode (Override)\n```\n{mp}\n```")
    else:
        lines.append("\n> [!WARNING]\n> Not found in raw database.")

    lines.append("\n## Cross-References")

    if related_qas:
        lines.append(f"### QA Rulings ({len(related_qas)})")
        for qa in related_qas:
            lines.append(f"**{qa.get('id')}**: {qa.get('question')}")
            lines.append(f"> {qa.get('answer')}\n")
    else:
        lines.append("### QA Rulings: None")

    lines.append(f"### Shared Ability Cards ({len(shared_cards)})")
    if shared_cards:
        lines.append(", ".join([f"`{c}`" for c in shared_cards]))
    else:
        lines.append("*Unique ability.*")

    lines.append(f"### Rust Engine Tests ({len(rust_tests)})")
    if rust_tests:
        for t in rust_tests:
            lines.append(f"- `{t}`")
    else:
        lines.append("\n> [!CAUTION]\n> No known Rust tests cover this card, its ability peers, or its QA items.")

    lines.append("\n## Compiled Logic (Source: cards_compiled.json)")
    if compiled:
        lines.append(f"- **Name (Compiled)**: {compiled.get('name')}")
        for i, ab in enumerate(compiled.get("abilities", [])):
            trigger_id = ab.get("trigger", 0)
            bytecode = ab.get("bytecode", [])
            lines.append(f"\n### Ability {i}")
            lines.append(f"- **Trigger**: `{trigger_id}`")
            lines.append(f"- **Bytecode**: `{bytecode}`")
            lines.append("\n#### Decoded Bytecode")
            lines.append(f"```\n{decode_bytecode(bytecode)}\n```")

        lines.append("\n### Raw Compiled JSON Data")
        lines.append(f"```json\n{json.dumps(compiled, indent=2, ensure_ascii=False)}\n```")
    else:
        lines.append("\n> [!WARNING]\n> Not found in compiled database.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n--- Report generated: {output_path} ---")


if __name__ == "__main__":
    main()
