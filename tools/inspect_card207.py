import json
p = 'data/cards_compiled.json'
with open(p,'r',encoding='utf-8') as f:
    j = json.load(f)
card = j['live_db']['207']
print('units:', card.get('units'))
for ab in card.get('abilities',[]):
    sf = ab.get('semantic_form') or {}
    for eff in sf.get('effects',[]):
        if eff.get('type')=='META_RULE':
            print('semantic tag raw:', eff.get('params'))
    for eff in ab.get('effects',[]):
        if eff.get('effect_type')==29:
            print('effect params:', eff.get('params'))
print('done')
