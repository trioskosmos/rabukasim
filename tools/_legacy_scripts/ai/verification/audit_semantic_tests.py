import json
import os

VERIFIED_POOL_PATH = "data/verified_card_pool.json"
TEST_DIR = "engine/tests/cards/batches"


def audit_semantic_tests():
    if not os.path.exists(VERIFIED_POOL_PATH):
        print(f"Verified pool not found at {VERIFIED_POOL_PATH}")
        return

    with open(VERIFIED_POOL_PATH, "r", encoding="utf-8") as f:
        verified_ids = json.load(f)

    # Map: Card ID -> List of Test Files
    coverage = {cid: [] for cid in verified_ids}

    # regex to match card IDs or parts of them (e.g. LL-bp1-001)
    # Most tests use the full ID in a string or the card_no

    found_any = set()

    for root, dirs, files in os.walk(TEST_DIR):
        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = os.path.join(root, file)

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

                for cid in verified_ids:
                    # Search for the ID itself or the card number representation
                    # Some IDs have special chars like ＋, handle with care or match substrings
                    # Normalize: strip ＋ for search if needed, but the IDs in JSON should match.

                    # Exact string match
                    if cid in content:
                        coverage[cid].append(file)
                        found_any.add(cid)
                    else:
                        # Try searching without suffix if it contains + or SEC
                        clean_id = cid.split("-SEC")[0].split("+")[0].split("＋")[0]
                        if len(clean_id) > 5 and clean_id in content:
                            coverage[cid].append(file + " (Partial/Num Match)")
                            found_any.add(cid)

    # Reporting
    print(f"Total Verified Cards: {len(verified_ids)}")
    print(f"Cards with Semantic Tests: {len(found_any)}")
    print(f"Missing Coverage: {len(verified_ids) - len(found_any)}")

    print("\n--- DETAILED REPORT ---")
    missing = []
    for cid, files in coverage.items():
        if files:
            print(f"[OK] {cid:20} -> {', '.join(set(files))}")
        else:
            missing.append(cid)

    if missing:
        print("\n--- MISSING SEMANTIC TESTS ---")
        for m in missing:
            print(f"[MISSING] {m}")


if __name__ == "__main__":
    audit_semantic_tests()
