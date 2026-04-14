import sys

sys.path.insert(0, 'tools')
from extract_abilities_to_template import DSL_PATTERNS

target_patterns = ['comma_separated_action', 'live_card_count_condition_resource_gain', 'score_modify', 
                   'trigger_hand_names_optional_discard_per_card', 'live_card_count_action_two_part', 
                   'trigger_energy_optional_per_resource_score']

for pattern_name in target_patterns:
    for i, pattern in enumerate(DSL_PATTERNS):
        if pattern['name'] == pattern_name:
            print(f"{pattern_name}: index {i}")
            break
