import json
import sys

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
            for player_key, results in hist.items():
                print(f"  Player {player_key} yell_count: {results.get('yell_count')}, yell_cards_len: {len(results.get('yell_cards', []))}")

check_yell(r'c:\Users\trios\Downloads\lovecasim_report_2026-03-03T10-16-30-454Z.json')
