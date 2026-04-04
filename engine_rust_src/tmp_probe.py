import json
from engine.compiler import main as m
with open('data/cards.json', encoding='utf-8') as f:
    data=json.load(f)
card=data['PL!N-pb1-017-R']
m._load_translations_if_present(True)
m._sparse_manager.load()
entry=m._sparse_manager.get_ability('PL!N-pb1-017-R', 0)
print('entry_found', entry is not None)
print('entry_trigger', entry.get('trigger_id') if entry else None)
print('has_source', m._card_has_ability_source(card))
abilities=m._resolve_abilities('MEMBER','PL!N-pb1-017-R',card)
print('ability_count', len(abilities))
print('ability_trigger', int(abilities[0].trigger) if abilities else None)
print('raw_text', abilities[0].raw_text if abilities else None)
