#!/usr/bin/env python3
"""
Test to compare card_id generation between two cards.json files.

This test compiles both the repository's cards.json and a downloaded cards.json,
then compares the generated card_id mappings to determine if IDs will remain stable.

Usage:
    pytest tests/test_card_id_parity.py -v
    python tests/test_card_id_parity.py
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def compute_card_id_mapping(cards_path: str) -> dict[str, int]:
    """
    Compute card_no -> card_id mapping from a cards.json file.

    This replicates the ID generation logic from compiler/main.py:
    - Cards are processed in sorted key order
    - logic_key = (name, ability_text) determines logical identity
    - packed_id = (variant_idx << 12) | logic_id

    Args:
        cards_path: Path to cards.json file

    Returns:
        Dictionary mapping card_no to card_id
    """
    with open(cards_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Replicate the exact logic from compiler/main.py
    sorted_keys = sorted(raw_data.keys())

    # Logic for bit-packed IDs
    # Bits 0-11: Logical ID (0-4095)
    # Bits 12-15: Variant Index (0-15)
    logical_id_map = {}  # (name, ability_text) -> logic_id
    logic_id_to_variant_count = {}  # logic_id -> next_variant_index
    next_logic_id = 0

    card_no_to_id = {}
    processed_keys = set()

    for key in sorted_keys:
        if key in processed_keys:
            continue

        item = raw_data[key]
        ctype = item.get("type", "")

        # Collect variants from rare_list
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

            # Determine Logical Identity
            v_name = str(v_data.get("name", "Unknown"))
            v_ability = str(v_data.get("ability", ""))
            logic_key = (v_name, v_ability)

            if logic_key not in logical_id_map:
                logical_id_map[logic_key] = next_logic_id
                logic_id_to_variant_count[next_logic_id] = 0
                next_logic_id += 1

            logic_id = logical_id_map[logic_key]
            variant_idx = logic_id_to_variant_count[logic_id]
            logic_id_to_variant_count[logic_id] += 1

            # Pack ID: (variant << 12) | logic
            if variant_idx >= 16:
                variant_idx = 15  # Cap at maximum

            packed_id = (variant_idx << 12) | logic_id
            card_no_to_id[v_key] = packed_id

    return card_no_to_id


def compare_mappings(
    old_mapping: dict[str, int], new_mapping: dict[str, int], old_cards: dict, new_cards: dict
) -> dict:
    """
    Compare two card_no -> card_id mappings.

    Returns a dict with:
        - matching: list of (card_no, card_id) that match
        - mismatched: list of (card_no, old_id, new_id, reason)
        - added: list of (card_no, new_id)
        - removed: list of (card_no, old_id)
    """
    old_keys = set(old_mapping.keys())
    new_keys = set(new_mapping.keys())

    common_keys = old_keys & new_keys
    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys

    matching = []
    mismatched = []

    for key in sorted(common_keys):
        old_id = old_mapping[key]
        new_id = new_mapping[key]

        if old_id == new_id:
            matching.append((key, old_id))
        else:
            # Determine reason for mismatch
            old_card = old_cards.get(key, {})
            new_card = new_cards.get(key, {})

            old_name = old_card.get("name", "")
            new_name = new_card.get("name", "")
            old_ability = old_card.get("ability", "")
            new_ability = new_card.get("ability", "")

            reasons = []
            if old_name != new_name:
                reasons.append(f"name changed: '{old_name}' -> '{new_name}'")
            if old_ability != new_ability:
                reasons.append("ability changed")

            if not reasons:
                reasons.append("order shifted (new cards inserted before this card)")

            mismatched.append((key, old_id, new_id, "; ".join(reasons)))

    added = [(key, new_mapping[key]) for key in sorted(added_keys)]
    removed = [(key, old_mapping[key]) for key in sorted(removed_keys)]

    return {"matching": matching, "mismatched": mismatched, "added": added, "removed": removed}


def print_report(comparison: dict, verbose: bool = False):
    """Print a detailed comparison report."""
    matching = comparison["matching"]
    mismatched = comparison["mismatched"]
    added = comparison["added"]
    removed = comparison["removed"]

    total_old = len(matching) + len(mismatched) + len(removed)
    total_new = len(matching) + len(mismatched) + len(added)

    print("\n" + "=" * 60)
    print("CARD ID PARITY TEST REPORT")
    print("=" * 60)

    print(f"\nRepository cards: {total_old}")
    print(f"Downloaded cards: {total_new}")

    # Matching IDs
    print(f"\n=== ID MATCH: {len(matching)} cards ===")
    if verbose and matching:
        for card_no, card_id in matching[:20]:
            print(f"  [OK] {card_no}: card_id={card_id}")
        if len(matching) > 20:
            print(f"  ... and {len(matching) - 20} more")

    # Mismatched IDs
    if mismatched:
        print(f"\n=== ID MISMATCH: {len(mismatched)} cards ===")
        print("WARNING: These cards will have DIFFERENT IDs after update!")
        for card_no, old_id, new_id, reason in mismatched[:30]:
            print(f"  [X] {card_no}: old_id={old_id}, new_id={new_id}")
            print(f"      Reason: {reason}")
        if len(mismatched) > 30:
            print(f"  ... and {len(mismatched) - 30} more")

    # Added cards
    if added:
        print(f"\n=== ADDED IN DOWNLOAD: {len(added)} cards ===")
        for card_no, new_id in added[:20]:
            print(f"  [+] {card_no}: new_id={new_id}")
        if len(added) > 20:
            print(f"  ... and {len(added) - 20} more")

    # Removed cards
    if removed:
        print(f"\n=== REMOVED FROM DOWNLOAD: {len(removed)} cards ===")
        for card_no, old_id in removed[:20]:
            print(f"  [-] {card_no}: old_id={old_id}")
        if len(removed) > 20:
            print(f"  ... and {len(removed) - 20} more")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total cards tested: {total_old}")
    print(f"Matching IDs: {len(matching)} ({100 * len(matching) / total_old:.1f}%)")
    print(f"Mismatched IDs: {len(mismatched)} ({100 * len(mismatched) / total_old:.1f}%)")
    print(f"Added: {len(added)}")
    print(f"Removed: {len(removed)}")

    if mismatched:
        print("\n[!] WARNING: Card IDs will NOT be stable after update!")
        print("    Tests with hardcoded card_ids may fail.")
        print("    Consider migrating test data or updating card_id references.")
    else:
        print("\n[OK] All card IDs are stable. Safe to update cards.json!")


def test_card_id_parity():
    """
    Test that card_ids remain stable between repository and downloaded cards.json.

    This test FAILS if:
    - Any existing card gets a different card_id

    This test WARNS if:
    - Cards are added or removed
    """
    repo_cards_path = "data/cards_old.json"
    download_cards_path = "data/cards.json"
    compiled_path = "data/cards_compiled.json"
    mapping_path = "data/card_id_mapping.json"

    # Check if downloaded file exists
    if not os.path.exists(download_cards_path):
        print(f"Skipping test: cards.json not found at {download_cards_path}")
        return

    if not os.path.exists(repo_cards_path):
        print(f"Skipping test: cards_old.json not found at {repo_cards_path}")
        return

    # Load raw card data for comparison
    with open(repo_cards_path, "r", encoding="utf-8") as f:
        repo_cards = json.load(f)

    with open(download_cards_path, "r", encoding="utf-8") as f:
        download_cards = json.load(f)

    # Load existing mapping from compiled data or mapping file
    print("\nLoading existing card_id mapping...")
    repo_mapping = {}

    # First try to load from cards_compiled.json
    if os.path.exists(compiled_path):
        with open(compiled_path, "r", encoding="utf-8") as f:
            compiled = json.load(f)
        for db_name in ["member_db", "live_db", "energy_db"]:
            if db_name in compiled:
                for card_id_str, card_data in compiled[db_name].items():
                    card_no = card_data.get("card_no")
                    if card_no:
                        repo_mapping[card_no] = int(card_id_str)
        print(f"Loaded {len(repo_mapping)} mappings from {compiled_path}")

    # If no compiled data, compute from cards_old.json
    if not repo_mapping:
        print("Computing card_id mapping for repository cards...")
        repo_mapping = compute_card_id_mapping(repo_cards_path)

    # Load new mapping from card_id_mapping.json (generated by merge tool)
    print("Loading new card_id mapping...")
    if os.path.exists(mapping_path):
        with open(mapping_path, "r", encoding="utf-8") as f:
            download_mapping = json.load(f)
        # Convert string keys to int values
        download_mapping = {k: int(v) for k, v in download_mapping.items()}
        print(f"Loaded {len(download_mapping)} mappings from {mapping_path}")
    else:
        print("Computing card_id mapping for downloaded cards...")
        download_mapping = compute_card_id_mapping(download_cards_path)

    # Compare
    comparison = compare_mappings(repo_mapping, download_mapping, repo_cards, download_cards)

    # Print report
    print_report(comparison, verbose=True)

    # Assert no mismatches
    mismatched = comparison["mismatched"]
    if mismatched:
        mismatch_details = "\n".join(
            [f"  {card_no}: old={old_id}, new={new_id}" for card_no, old_id, new_id, _ in mismatched[:10]]
        )
        raise AssertionError(
            f"Card ID mismatch detected for {len(mismatched)} cards!\n"
            f"This means updating cards.json will break existing card_id references.\n"
            f"First 10 mismatches:\n{mismatch_details}"
        )


def main():
    """Run the test as a standalone script."""
    try:
        test_card_id_parity()
        print("\n[OK] TEST PASSED: All card IDs are stable!")
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n[SKIP] SKIPPED: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()
