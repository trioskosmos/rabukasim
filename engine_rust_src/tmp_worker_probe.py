import json
from engine.compiler import main as m
with open('data/cards.json', encoding='utf-8') as f:
    data=json.load(f)
item=data['PL!N-pb1-017-R']
res=m._process_card_worker(('PL!N-pb1-017-R', item, 'runtime', 4442, 0, 0))
print('type', res[0])
print('pk', res[1])
print('err', bool(res[3]))
print(res[3] if res[3] else 'ok')
print('dumped_card_no', None if res[2] is None else res[2].get('card_no'))
print('dumped_abilities', None if res[2] is None else len(res[2].get('abilities', [])))
