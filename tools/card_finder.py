import argparse
import json
import os
import sys
import re
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
    results = []

    # 1. Check raw source (data/cards.json)
    raw_data = cards_raw.get(no)

    # 2. Check compiled source (data/cards_compiled.json)
    compiled_data = None
    compiled_id = None
    # Search member_db
    for cid, c in cards_compiled.get("member_db", {}).items():
        if c.get("card_no") == no:
            compiled_data = c
            compiled_id = cid
            break

    # Search live_db if not found in member_db
    if not compiled_data:
        for cid, c in cards_compiled.get("live_db", {}).items():
            if c.get("card_no") == no:
                compiled_data = c
                compiled_id = cid
                break

    # Search energy_db if not found yet
    if not compiled_data:
        for cid, c in cards_compiled.get("energy_db", {}).items():
            if c.get("card_no") == no:
                compiled_data = c
                compiled_id = cid
                break

    return raw_data, compiled_data, compiled_id


def main():
    # Ensure stdout/stderr use UTF-8 regardless of locale
    if sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="Unified card lookup and report generator.")
    parser.add_argument("query", help="Card No, URL, Packed ID, or Logic ID")
    parser.add_argument("-o", "--output", help="Write report to this Markdown file", type=str)
    
    args = parser.parse_args()
    raw_query = args.query.strip()
    query = extract_card_no(raw_query)

    CARDS_RAW_PATH = "data/cards.json"
    CARDS_COMPILED_PATH = "data/cards_compiled.json"

    # Efficiently load (standardized)
    print(f"--- Loading Sources ---")
    cards_raw = load_json(CARDS_RAW_PATH) or {}
    cards_compiled = load_json(CARDS_COMPILED_PATH) or {}
    manual_pseudo = load_json("data/manual_pseudocode.json") or {}

    print(f"--- Searching for '{query}' (from '{raw_query}') ---")

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
            print(f"Found {len(found_nos)} matches by text:")
            for no in found_nos[:10]:
                print(f"  - {no}")
            if len(found_nos) > 10:
                print(f"  ... and {len(found_nos) - 10} more.")
            return
        else:
            print("No matches found.")
            return

    # 4. Display or Save
    if args.output:
        generate_report(args.output, query, raw, compiled, cid, manual_pseudo)
    else:
        display_card(query, raw, compiled, cid, manual_pseudo)


def display_card(query, raw, compiled, cid, manual_pseudo):
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
        
        # Check Manual Override
        card_no = raw.get('card_no')
        if card_no and card_no in manual_pseudo:
            print(f"Pseudocode (Manual): {manual_pseudo[card_no].get('pseudocode')}")
    else:
        print("NOT FOUND IN RAW DATA")

    print("\n--- LOGIC (Source: cards_compiled.json) ---")
    if compiled:
        print(f"Name (Compiled): {compiled.get('name')}")
        for i, ab in enumerate(compiled.get("abilities", [])):
            print(f"Ability {i}:")
            trigger_id = ab.get('trigger', 0)
            bytecode = ab.get('bytecode', [])
            print(f"  Trigger: {trigger_id}")
            print(f"  Bytecode: {bytecode}")
            print(f"  Decoded:\n{decode_bytecode(bytecode)}")
    else:
        print("NOT FOUND IN COMPILED DATA")


def generate_report(output_path, query, raw, compiled, cid, manual_pseudo):
    card_no = compiled.get('card_no') if compiled else query
    lines = []
    lines.append(f"# Card Report: {card_no}")
    
    if cid is not None:
        packed_id = int(cid)
        logic_id = packed_id & 0x0FFF
        variant = packed_id >> 12
        lines.append(f"\n## IDs")
        lines.append(f"- **Engine Packed ID**: `{packed_id}`")
        lines.append(f"- **Logic ID**: `{logic_id}`")
        lines.append(f"- **Variant Index**: `{variant}`")

    lines.append(f"\n## Metadata (Source: cards.json)")
    if raw:
        lines.append(f"- **Name**: {raw.get('name')}")
        lines.append(f"- **Card No**: {raw.get('card_no')}")
        lines.append(f"- **Ability (JP)**:\n```\n{raw.get('ability')}\n```")
        lines.append(f"- **Pseudocode (Raw)**: `{raw.get('pseudocode')}`")
        
        # Check Manual Override
        card_no = raw.get('card_no')
        if card_no and card_no in manual_pseudo:
            mp = manual_pseudo[card_no].get('pseudocode')
            lines.append(f"\n### Manual Pseudocode (Override)\n```\n{mp}\n```")
    else:
        lines.append("\n> [!WARNING]\n> Not found in raw database.")

    lines.append(f"\n## Compiled Logic (Source: cards_compiled.json)")
    if compiled:
        lines.append(f"- **Name (Compiled)**: {compiled.get('name')}")
        for i, ab in enumerate(compiled.get("abilities", [])):
            trigger_id = ab.get('trigger', 0)
            bytecode = ab.get('bytecode', [])
            lines.append(f"\n### Ability {i}")
            lines.append(f"- **Trigger**: `{trigger_id}`")
            lines.append(f"- **Bytecode**: `{bytecode}`")
            lines.append(f"\n#### Decoded Bytecode")
            lines.append(f"```\n{decode_bytecode(bytecode)}\n```")
    else:
        lines.append("\n> [!WARNING]\n> Not found in compiled database.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"\n--- Report generated: {output_path} ---")


if __name__ == "__main__":
    main()
