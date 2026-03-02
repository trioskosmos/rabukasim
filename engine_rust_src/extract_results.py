import sys
import os

def read_results():
    targets = [
        'debug_q203',
        'test_q160_q161_q162_play_count_trigger',
        'test_q203_niji_score_buff',
        'test_card_579_ability_1_heart_filter',
        'test_repro_card_103_full_board',
        'test_area_rotation_mei',
        'test_look_and_choose_color_filter_parity',
        'test_move_to_discard_deck_top_slot_1_repro'
    ]
    
    results = {t: 'NOT FOUND' for t in targets}
    
    try:
        with open('reports/rust_test_verification.txt', 'r', encoding='utf-16le') as f:
            content = f.read()
            for line in content.splitlines():
                for t in targets:
                    if t in line and (' ... ok' in line or ' ... FAILED' in line):
                        results[t] = line.strip()
    except Exception as e:
        return str(e)
        
    return '\n'.join(results.values())

if __name__ == "__main__":
    print(read_results())
