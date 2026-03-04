import os
import re

replacements = [
    (r'state\.core\.players', 'state.players'),
    (r'state\.core\.phase', 'state.phase'),
    (r'state\.core\.turn', 'state.turn'),
    (r'state\.core\.current_player', 'state.current_player'),
    (r'state\.core\.interaction_stack', 'state.interaction_stack'),
    (r'state\.core\.trigger_queue', 'state.trigger_queue'),
    (r'state\.core\.first_player', 'state.first_player'),
    (r'state\.core\.prev_phase', 'state.prev_phase'),
    (r'state\.core\.prev_card_id', 'state.prev_card_id'),
    (r'state\.core\.trigger_depth', 'state.trigger_depth'),
    (r'state\.core\.live_set_pending_draws', 'state.live_set_pending_draws'),
    (r'state\.core\.rng', 'state.rng'),
    (r'state\.core\.rps_choices', 'state.rps_choices'),
    (r'state\.core\.turn_history', 'state.turn_history'),
    (r'state\.core\.obtained_success_live', 'state.obtained_success_live'),
    (r'state\.core\.live_result_selection_pending', 'state.live_result_selection_pending'),
    (r'state\.core\.live_result_triggers_done', 'state.live_result_triggers_done'),
    (r'state\.core\.live_start_triggers_done', 'state.live_start_triggers_done'),
    (r'state\.core\.live_result_processed_mask', 'state.live_result_processed_mask'),
    (r'state\.core\.live_start_processed_mask', 'state.live_start_processed_mask'),
    (r'state\.core\.live_success_processed_mask', 'state.live_success_processed_mask'),
    (r'state\.core\.performance_reveals_done', 'state.performance_reveals_done'),
    (r'state\.core\.performance_yell_done', 'state.performance_yell_done'),
]

root_dir = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src'

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.rs'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(path, 'r', encoding='cp1252', errors='replace') as f:
                    content = f.read()
            
            new_content = content
            for pattern, replacement in replacements:
                new_content = re.sub(pattern, replacement, new_content)
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Patched: {path}")
