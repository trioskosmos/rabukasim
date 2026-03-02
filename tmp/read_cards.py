import json
with open('data/cards.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

targets = ['PL!S-bp2-004-P', 'PL!SP-pb1-003-P＋', 'PL!-sd1-007-SD']
results = {}
for cno in targets:
    if cno in d:
        results[cno] = d[cno].get('ability')

with open('tmp/target_abilities.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
