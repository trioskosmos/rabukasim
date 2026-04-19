import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
count = 0
abilities_with_filters = []

for a in data['unique_abilities']:
    actions = a.get('effect', {}).get('actions', [])
    has_look = any(act.get('action') == 'look_at_cards' for act in actions)
    has_select = any(act.get('action') == 'select_from_looked_at_cards' for act in actions)
    
    if has_look and has_select:
        count += 1
        select_action = [act for act in actions if act.get('action') == 'select_from_looked_at_cards'][0]
        has_filters = any(k in select_action for k in ['value_threshold', 'min_cost', 'group', 'card_type'])
        abilities_with_filters.append({
            'full_text': a.get('full_text', '')[:100],
            'has_filters': has_filters,
            'filters': {k: v for k, v in select_action.items() if k in ['value_threshold', 'min_cost', 'group', 'card_type']}
        })

print(f'Found {count} abilities with look_at_cards + select_from_looked_at_cards')
print(f'Of these, {sum(1 for a in abilities_with_filters if a["has_filters"])} have filters')

for a in abilities_with_filters[:10]:
    print(f"\nText: {a['full_text']}")
    print(f"Has filters: {a['has_filters']}")
    print(f"Filters: {a['filters']}")
