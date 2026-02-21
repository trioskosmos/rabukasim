import json
import os

def analyze_scenarios():
    path = 'engine_rust_src/data/scenarios.json'
    if not os.path.exists(path):
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scenarios = data.get('scenarios', [])
    sorted_s = sorted(scenarios, key=lambda x: len(x.get('original_text_jp', '')), reverse=True)
    
    results = []
    seen_ids = set()
    for s in sorted_s:
        card_id = s.get('id', 'N/A')
        if card_id in seen_ids: continue
        seen_ids.add(card_id)
        
        results.append({
            "id": card_id,
            "text": s.get('original_text_jp', ''),
            "name": s.get('scenario_name', '')
        })
        if len(results) >= 10: break

    with open('complex_cards.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    analyze_scenarios()
