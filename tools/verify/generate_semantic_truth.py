import json

from semantic_oracle_v2 import SemanticOracleV2


def generate_truth():
    print("🚀 Generating Semantic Truth Set...")
    oracle = SemanticOracleV2()

    truth_db = {}
    total = len(oracle.db)
    count = 0

    for cid in oracle.db:
        try:
            interp = oracle.interpret_card(cid)
            if interp["abilities"]:
                truth_db[cid] = interp
            count += 1
            if count % 100 == 0:
                print(f"   Progress: {count}/{total}")
        except Exception as e:
            print(f"Error processing {cid}: {e}")

    output_path = "reports/semantic_truth.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(truth_db, f, indent=2, ensure_ascii=False)

    print(f"✅ Truth set generated with {len(truth_db)} entries at {output_path}")


if __name__ == "__main__":
    generate_truth()
