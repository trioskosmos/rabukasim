import json
p='c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/cards_compiled.json'
with open(p,encoding='utf-8') as f:
    data=json.load(f)
found=False
for db in ('live_db','member_db'):
    for cid,card in data.get(db,{}).items():
        ot=card.get('original_text','')
        if 'ADD_TAG' in ot or 'UNIT_CERISE' in ot or 'UNIT_MIRAKURA' in ot:
            print('MATCH_ORIG',db,cid,card.get('card_no'),card.get('units'))
            found=True
        units=card.get('units',[])
        if isinstance(units,list) and any(u in (13,14,15) for u in units):
            print('UNITMATCH',db,cid,card.get('card_no'),units)
            found=True
if not found:
    print('NO_MATCHES')
