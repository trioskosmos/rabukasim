import collections
import json
import sys

# Load verified pool
try:
    with open("data/verified_card_pool.json", "r", encoding="utf-8") as f:
        pool_data = json.load(f)
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        full_db = json.load(f)
except FileNotFoundError as e:
    print(f"Error: {e}")
    sys.exit(1)

verified_codes = set(pool_data.get("verified_abilities", []) + pool_data.get("vanilla_lives", []))
# Merge member and live dbs
all_cards = list(full_db.get("member_db", {}).values()) + list(
    full_db.get("live_db", {1: {}}).values()
)  # Handle possible structure variations

cost_counts = collections.Counter()
unhandled_costs = []

# Known handled costs in Ability.compile
HANDLED_COSTS = [3]  # DISCARD_HAND

print(f"Verified Codes unique: {len(verified_codes)}")

found_count = 0
for card in all_cards:
    code = card.get("card_no")
    if code not in verified_codes:
        continue
    found_count += 1

    if "abilities" in card:
        for dh in card["abilities"]:
            if "costs" in dh:
                for cost in dh["costs"]:
                    ctype = cost.get("type")
                    val = cost.get("value")

                    cost_counts[ctype] += 1

                    if ctype not in HANDLED_COSTS:
                        unhandled_costs.append(
                            {
                                "card_code": code,
                                "card_name": card.get("name", "Unknown"),
                                "cost_type": ctype,
                                "value": val,
                                "raw": cost,
                            }
                        )

print(f"Cards successfully matched from DB: {found_count}")

print("\n--- Cost Type Usage ---")
for ctype, count in cost_counts.most_common():
    status = "[HANDLED]" if ctype in HANDLED_COSTS else "[MISSING]"
    print(f"Type {ctype}: {count} occurrences {status}")

if unhandled_costs:
    print("\n--- Examples of Unhandled Costs ---")
    # Show top 5 unique types
    seen_types = set()
    for item in unhandled_costs:
        if item["cost_type"] not in seen_types:
            print(
                f"Type {item['cost_type']} | Card: {item['card_name']} (ID {item['card_id']}) | Value: {item['value']}"
            )
            seen_types.add(item["cost_type"])
            if len(seen_types) >= 10:
                break
else:
    print("\nAll costs used in the verified pool are handled!")
