"""Find cards with OnPlay and Activated abilities for verification testing."""

import json

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    d = json.load(f)

out = []

# Check card 4596 first
card_4596 = d["member_db"].get("4596")
if card_4596 and isinstance(card_4596, dict):
    out.append("=== Card 4596 ===")
    out.append(f"Name: {card_4596.get('name')}")
    out.append(f"Cost: {card_4596.get('cost')}")
    for i, ab in enumerate(card_4596.get("abilities", [])):
        out.append(f"  Ability {i}: trigger={ab.get('trigger')}, pseudocode={str(ab.get('pseudocode', ''))[:80]}")
        out.append(f"    conditions={ab.get('conditions', [])}")
        out.append(f"    costs={ab.get('costs', [])}")
else:
    out.append("Card 4596 NOT FOUND")

on_play_cards = []
activated_cards = []

for id_str, card in d["member_db"].items():
    if not isinstance(card, dict):
        continue
    for ab_idx, ab in enumerate(card.get("abilities", [])):
        t = ab.get("trigger", 0)
        if t == 1:  # OnPlay
            on_play_cards.append(
                (int(id_str), card.get("name", "?"), card.get("cost", 0), ab_idx, str(ab.get("pseudocode", ""))[:60])
            )
        if t == 7:  # Activated
            activated_cards.append(
                (
                    int(id_str),
                    card.get("name", "?"),
                    card.get("cost", 0),
                    ab_idx,
                    str(ab.get("pseudocode", ""))[:60],
                    ab.get("costs", []),
                )
            )

out.append("\n=== OnPlay cards (first 15): ===")
for cid, name, cost, ab_idx, pseudo in on_play_cards[:15]:
    out.append(f"  ID={cid}, cost={cost}, name={name}, ab_idx={ab_idx}, pseudo={pseudo}")

out.append("\n=== Activated cards (first 15, no-cost first): ===")
no_cost = [x for x in activated_cards if not x[5]]
with_cost = [x for x in activated_cards if x[5]]
for cid, name, cost, ab_idx, pseudo, costs in no_cost[:8] + with_cost[:7]:
    out.append(f"  ID={cid}, cost={cost}, name={name}, ab_idx={ab_idx}, pseudo={pseudo}, costs={costs}")

out.append(f"\nTotal OnPlay: {len(on_play_cards)}, Total Activated: {len(activated_cards)}")

result = "\n".join(out)
with open("reports/card_ability_survey.txt", "w", encoding="utf-8") as f:
    f.write(result)
print(result)
