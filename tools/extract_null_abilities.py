import json


def extract_nulls():
    with open("reports/bp5_deep_audit_raw.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    result = {k: v for k, v in data.items() if not v.get("ability")}

    with open("reports/bp5_null_abilities.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(result)} cards with null/empty abilities.")


if __name__ == "__main__":
    extract_nulls()
