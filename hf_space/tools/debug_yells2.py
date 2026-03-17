import json

with open(r"c:\Users\trios\Downloads\lovecasim_report_2026-03-03T10-16-30-454Z.json", encoding="utf-8") as f:
    d = json.load(f)

print("Explanation:", d.get("explanation"))

p0 = d["players"][0]
print("P0 total_blades:", p0.get("total_blades"))
print("P0 yell_cards count:", len(p0.get("yell_cards", [])))

ph = d.get("performance_history", [])
print("performance_history length:", len(ph))
if ph:
    last_ph = ph[-1]
    p0_res = last_ph.get("0", {})
    if isinstance(p0_res, dict):
        print("P0 yell_count from performance_history:", p0_res.get("yell_count"))
        if "yell_cards" in p0_res:
            print("P0 performance_history yell_cards count:", len(p0_res["yell_cards"]))

    # Look at players in the history dict instead of string keys if it is a list of dicts.
print("---------")
print("Let's look at all p_idx in the last performance history:")
if ph:
    last_ph = ph[-1]
    for k, v in last_ph.items():
        if isinstance(v, dict):
            print(f"Player {k} yell_count: {v.get('yell_count')} actual yell_cards: {len(v.get('yell_cards', []))}")
