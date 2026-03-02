#!/usr/bin/env python3
"""
Merge cards_old.json with new cards.json while preserving existing card_ids.

The problem: card_id generation uses sorted_keys = sorted(raw_data.keys())
which sorts alphabetically. New cards inserted alphabetically will shift IDs.

Solution: Modify the compiler to respect existing ID mappings from cards_compiled.json

Strategy:
1. Load existing ID mapping from data/cards_compiled.json
2. For existing cards: use their existing card_id
3. For new cards: assign new IDs starting from the next available logic_id

Usage:
    python tools/merge_cards_stable.py
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_existing_compiled_mapping() -> dict[str, int]:
    """Load card_no -> card_id mapping from existing cards_compiled.json"""
    compiled_path = "data/cards_compiled.json"
    if not os.path.exists(compiled_path):
        print(f"Warning: {compiled_path} not found, no existing mapping")
        return {}

    with open(compiled_path, "r", encoding="utf-8") as f:
        compiled = json.load(f)

    mapping = {}
    for db_name in ["member_db", "live_db", "energy_db"]:
        if db_name in compiled:
            for card_id_str, card_data in compiled[db_name].items():
                card_no = card_data.get("card_no")
                if card_no:
                    mapping[card_no] = int(card_id_str)

    return mapping


def compute_new_card_ids(
    old_cards: dict, new_cards: dict, existing_mapping: dict[str, int]
) -> tuple[dict, dict[str, int]]:
    """
    Merge cards and compute ID mapping that preserves existing IDs.

    Returns:
        - merged_cards: the merged cards dictionary
        - new_mapping: card_no -> card_id mapping for all cards
    """
    # Start with old cards
    merged = dict(old_cards)

    # Find new cards
    old_card_nos = set(old_cards.keys())
    new_card_nos = set(new_cards.keys())

    added = new_card_nos - old_card_nos
    updated = old_card_nos & new_card_nos

    print(f"Old cards: {len(old_card_nos)}")
    print(f"New cards: {len(new_card_nos)}")
    print(f"Cards to update: {len(updated)}")
    print(f"Cards to add: {len(added)}")

    # Update existing cards with new data
    for card_no in updated:
        merged[card_no] = new_cards[card_no]

    # Add new cards
    for card_no in added:
        merged[card_no] = new_cards[card_no]

    # Compute new mapping
    # For existing cards: use existing_mapping
    # For new cards: compute new IDs

    # First, find the max logic_id used in existing mapping
    max_logic_id = 0
    logic_id_usage = {}  # logic_id -> count of variants

    for card_no, card_id in existing_mapping.items():
        logic_id = card_id & 0xFFF  # Lower 12 bits
        variant_idx = (card_id >> 12) & 0xF  # Upper 4 bits

        if logic_id > max_logic_id:
            max_logic_id = logic_id

        if logic_id not in logic_id_usage:
            logic_id_usage[logic_id] = 0
        if variant_idx >= logic_id_usage[logic_id]:
            logic_id_usage[logic_id] = variant_idx + 1

    print(f"Max existing logic_id: {max_logic_id}")

    # Build the new mapping
    new_mapping = dict(existing_mapping)

    # For new cards, we need to compute their logic_key and assign IDs
    # Process in sorted order for consistency
    next_logic_id = max_logic_id + 1
    new_logic_key_map = {}  # (name, ability) -> logic_id for new cards

    # We need to process ALL cards (old and new) to handle variants correctly
    # But we only assign new IDs to new cards

    sorted_keys = sorted(merged.keys())
    processed_keys = set()

    for key in sorted_keys:
        if key in processed_keys:
            continue

        item = merged[key]

        # Collect variants
        variants = [{"card_no": key, "name": item.get("name", ""), "data": item}]
        processed_keys.add(key)

        if "rare_list" in item and isinstance(item["rare_list"], list):
            for r in item["rare_list"]:
                v_no = r.get("card_no")
                if v_no and v_no != key:
                    if v_no in sorted_keys:
                        processed_keys.add(v_no)

                    v_item = item.copy()
                    v_item.update(r)
                    variants.append({"card_no": v_no, "name": r.get("name", item.get("name", "")), "data": v_item})

        for v in variants:
            v_key = v["card_no"]
            v_data = v["data"]

            v_name = str(v_data.get("name", "Unknown"))
            v_ability = str(v_data.get("ability", ""))
            logic_key = (v_name, v_ability)

            # If this card already has an ID, keep it
            if v_key in new_mapping:
                continue

            # This is a new card - assign a new ID
            if logic_key not in new_logic_key_map:
                new_logic_key_map[logic_key] = next_logic_id
                logic_id_usage[next_logic_id] = 0
                next_logic_id += 1

            logic_id = new_logic_key_map[logic_key]
            variant_idx = logic_id_usage[logic_id]
            logic_id_usage[logic_id] += 1

            if variant_idx >= 16:
                variant_idx = 15

            packed_id = (variant_idx << 12) | logic_id
            new_mapping[v_key] = packed_id

    return merged, new_mapping


def main():
    """Main entry point."""
    old_path = "data/cards_old.json"
    new_path = "C:/Users/trios/Downloads/cards.json"
    output_path = "data/cards.json"
    mapping_output_path = "data/card_id_mapping.json"

    # Check files exist
    if not os.path.exists(old_path):
        print(f"Error: {old_path} not found")
        sys.exit(1)

    if not os.path.exists(new_path):
        print(f"Error: {new_path} not found")
        sys.exit(1)

    # Load existing mapping from compiled data
    print("Loading existing card_id mapping from cards_compiled.json...")
    existing_mapping = load_existing_compiled_mapping()
    print(f"Found {len(existing_mapping)} existing card_id mappings")

    # Load cards
    print(f"\nLoading {old_path}...")
    with open(old_path, "r", encoding="utf-8") as f:
        old_cards = json.load(f)

    print(f"Loading {new_path}...")
    with open(new_path, "r", encoding="utf-8") as f:
        new_cards = json.load(f)

    # Merge and compute new mapping
    print("\nMerging cards and computing ID mapping...")
    merged, new_mapping = compute_new_card_ids(old_cards, new_cards, existing_mapping)

    # Verify old IDs are preserved
    print("\nVerifying ID preservation...")
    preserved = 0
    changed = 0

    for card_no, old_id in existing_mapping.items():
        if card_no in new_mapping:
            new_id = new_mapping[card_no]
            if old_id == new_id:
                preserved += 1
            else:
                changed += 1
                print(f"  WARNING: {card_no} changed from {old_id} to {new_id}")

    print("\nID Preservation Results:")
    print(f"  Preserved: {preserved}")
    print(f"  Changed: {changed}")

    if changed > 0:
        print("\nWARNING: Some existing IDs changed! Not saving.")
        sys.exit(1)

    # Save merged cards
    print(f"\nSaving merged cards to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=4)

    # Save mapping for reference
    print(f"Saving ID mapping to {mapping_output_path}...")
    with open(mapping_output_path, "w", encoding="utf-8") as f:
        json.dump(new_mapping, f, ensure_ascii=False, indent=2)

    print("\nDone!")
    print("\nSummary:")
    print(f"  Old cards: {len(old_cards)}")
    print(f"  New cards added: {len(merged) - len(old_cards)}")
    print(f"  Total cards: {len(merged)}")
    print(f"  Total IDs mapped: {len(new_mapping)}")


if __name__ == "__main__":
    main()
