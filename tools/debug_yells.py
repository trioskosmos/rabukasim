import json

def check_yell(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for i, p in enumerate(data.get('players', [])):
        print(f"Player {i}:")
        print(f"  total_blades: {p.get('total_blades')}")
        yell_cards = p.get('yell_cards', [])
        print(f"  yell_cards length: {len(yell_cards)}")
        
        stage_energy = p.get('stage_energy', [[], [], []])
        sum_stage = sum(len(s) for s in stage_energy)
        print(f"  stage_energy total items: {sum_stage}")
        
    if 'performance_history' in data:
        for j, hist in enumerate(data['performance_history']):
            print(f"Performance History {j}:")
            if isinstance(hist, dict):
                for p_idx, res in hist.items():
                    print(f"  Player {p_idx} yell_count: {res.get('yell_count', 0)}, yell_cards len: {len(res.get('yell_cards', []))}")
                    if len(res.get('yell_cards', [])) > 10:
                        print(f"    WARNING: High yell count! {len(res.get('yell_cards', []))} cards")

check_yell(r'c:\Users\trios\Downloads\lovecasim_report_2026-03-03T10-16-30-454Z.json')
