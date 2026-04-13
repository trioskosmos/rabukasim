# Show example abilities and how they're represented in clause-level DSL
import json

data = json.load(open('../data/abilities_from_cards.json', encoding='utf-8'))
abilities = data['abilities']

print("="*80)
print("EXAMPLE CARDS AND THEIR ABILITY STRUCTURES")
print("="*80)
print()

examples = [
    # Simple single-clause
    abilities[0],  # 高坂 穂乃果 - ON_PLAY with condition
    abilities[1],  # 高坂 穂乃果 - CONSTANT
    
    # Multi-clause sequential
    abilities[5],  # 南 ことり - ON_PLAY with look/add/discard sequence
    abilities[7],  # 西木野 真姫 - ON_PLAY with conditional follow-up
]

# Also show Daydream Mermaid specifically
daydream_mermaid = {
    'trigger': 'LIVE_SUCCESS',
    'trigger_id': 3,
    'source_ability_texts': [{
        'jp': "{{live_success.png|ライブ成功時}}以下から1つを選ぶ。自分の成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ。\n・自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。\n・自分の控え室からメンバーカードを1枚手札に加える。",
        'cards': ['PL!N-bp4-030-L | Daydream Mermaid']
    }]
}

for ab in examples + [daydream_mermaid]:
    trigger = ab['trigger']
    trigger_id = ab['trigger_id']
    for source in ab['source_ability_texts']:
        jp_text = source['jp']
        cards = source['cards'][0] if source['cards'] else "Unknown"
        
        print(f"Card: {cards}")
        print(f"Trigger: {trigger} (ID: {trigger_id})")
        print(f"Original: {jp_text}")
        print()
        
        # Show how current DSL splits this
        clauses = jp_text.split('。')
        clauses = [c.strip() for c in clauses if c.strip()]
        
        print(f"Clause-level DSL splits into {len(clauses)} clause(s):")
        for i, clause in enumerate(clauses, 1):
            print(f"  {i}. {clause}")
        
        print()
        print(f"Simple ordered combination: {'。'.join(clauses)}")
        print()
        print("-"*80)
        print()
