#!/usr/bin/env python3
"""
Extract the main card from each failed Rust test and show comparison data.
"""
import json
import re
from pathlib import Path

# Load data
cards_file = Path("data/cards.json")
cards_compiled_file = Path("data/cards_compiled.json")
authored_frames_file = Path("data/ability_frame_source_authored.json")
converted_frames_file = Path("data/ability_frame_source.json")
extracted_abilities_file = Path("data/abilities_extracted_from_cards.json")

with open(cards_file, encoding='utf-8') as f:
    cards = json.load(f)

with open(cards_compiled_file, encoding='utf-8') as f:
    cards_compiled = json.load(f)

with open(authored_frames_file, encoding='utf-8') as f:
    authored_frames = json.load(f)

with open(converted_frames_file, encoding='utf-8') as f:
    converted_frames = json.load(f)

with open(extracted_abilities_file, encoding='utf-8') as f:
    extracted_abilities = json.load(f)

# Build mapping from card_id numbers to card IDs using cards_compiled.json
# cards_compiled.json has structure: {member_db: {card_id: {card_id, card_no, ...}}, live_db: {...}, ...}
card_id_to_card_no = {}

# Check member_db
if 'member_db' in cards_compiled:
    for card_id_str, card_data in cards_compiled['member_db'].items():
        card_id = int(card_id_str)
        card_no = card_data.get('card_no')
        if card_no:
            card_id_to_card_no[card_id] = card_no

# Check live_db
if 'live_db' in cards_compiled:
    for card_id_str, card_data in cards_compiled['live_db'].items():
        card_id = int(card_id_str)
        card_no = card_data.get('card_no')
        if card_no:
            card_id_to_card_no[card_id] = card_no

print(f"Built mapping from {len(card_id_to_card_no)} card_id numbers to card IDs")

# Failed test names from cargo test output
failed_tests = [
    "test_card_697_live_start_discards_dollchestra_to_copy_cost_and_gain_heart",
    "test_card_755_on_leaves_cost_fifteen_baton_also_draws",
    "test_card_854_live_start_wait_branch_only_targets_cost_4_or_less",
    "test_card_8844_activate_recover_branch_uses_non_muse_discard",
    "test_card_8844_constant_grants_heart_only_with_three_distinct_names",
    "test_card_8844_activate_draw_branch_requires_discard_tracking",
    "test_card_755_on_leaves_cost_twelve_baton_untaps_two_without_draw",
    "test_card_761_on_play_requires_three_distinct_lives_before_any_recovery_mode_is_legal",
    "test_card_761_on_play_distinct_live_groups_only_enables_double_recovery_mode",
    "test_card_761_on_play_distinct_live_names_only_enables_single_recovery_mode",
    "test_card_761_on_play_when_both_modes_are_legal_single_recovery_mode_stays_isolated",
    "test_card_761_on_play_when_both_modes_are_legal_double_recovery_mode_stays_isolated",
    "test_multi_qa_ll_bp2_001",
    "test_q110_q127_vienna_constant_stacking",
    "test_q111_q117_vienna_yell_penalty",
    "test_pl_n_bp5_030_l_resolve_trigger",
    "test_card_801_on_play_only_high_cost_aqours_choice_is_legal_and_remainders_discard",
    "test_live_709_live_start_with_duplicate_cost_skips_score_bonus",
    "test_q168_q169_q170_q181_q188_nico_exhaustive",
    "test_q183_cost_selection_isolation",
    "test_q160_q161_q162_play_count_trigger",
    "test_q196_select_member_empty",
    "test_q206_baton_touch_cost_reduction",
    "test_q203_niji_score_buff",
    "test_q230_setsuna_zero_equality",
    "test_q229_response_skips_controller_discard_and_opens_opponent_owned_prompt",
    "test_q232_score_icon_does_not_change_live_self_score",
    "test_q237_revealing_nonmatching_variant_does_not_recover_base_name",
    "test_card_861_on_play_only_high_cost_liella_choice_is_legal_and_remainders_discard",
    "test_q132_live_success_bonus_applies_for_first_player",
    "test_q144_up_to_two_can_choose_only_one_target",
    "test_recursive_multi_card_discard_batch_context",
    "test_q171_until_live_end_effect_expires_even_without_a_live",
    "test_q204_same_name_condition_counts_multi_name_member",
    "test_live_260_live_start_paying_energy_without_nijigasaki_skips_score_bonus",
    "test_live_459_live_start_six_blade_aqours_target_grants_score_bonus",
    "test_cost_13_blade_aura_requires_structured_stage_gate",
    "test_id_717_baton_touch_untaps_energy",
    "test_hand_only_structured_cost_reducers_use_authored_conditions",
    "test_hs_pr_016_same_unit_discard_requires_matching_partner",
    "test_q96_q97_q103_catchu_exhaustive",
    "test_q4791_on_leaves_position_change_prompts_for_destination",
    "test_q4794_same_group_discard_requires_matching_partner",
    "test_rule_bp4_001_group_condition",
    "test_rule_bp4_001_triggers_on_both_sequential_plays",
    "test_split_frame_index_entries_follow_their_gameplay_text",
    "test_real_card_646_color_select_uses_color_mask",
    "test_verify_buff_logic",
    "test_baton_touch_restriction",
    "test_q203_niji_score_buff_requires_energy_activation_before_member_activation",
    "test_q203_niji_score_buff_reaches_two_with_energy_and_member_activation",
]

# Extract card_id numbers from test names and map to card_no using cards_compiled.json
def extract_card_id_from_test_name(test_name):
    """Extract numeric card_id from test name."""
    # Pattern 1: test_card_XXX -> XXX
    match = re.search(r'test_card_(\d+)', test_name)
    if match:
        return int(match.group(1))
    
    # Pattern 2: test_qXXX -> XXX
    match = re.search(r'test_q(\d+)', test_name)
    if match:
        return int(match.group(1))
    
    # Pattern 3: test_live_XXX -> XXX
    match = re.search(r'test_live_(\d+)', test_name)
    if match:
        return int(match.group(1))
    
    # Pattern 4: test_real_card_XXX -> XXX
    match = re.search(r'test_real_card_(\d+)', test_name)
    if match:
        return int(match.group(1))
    
    # Pattern 5: test_rule_bp4_001 -> extract from bp4-001
    match = re.search(r'test_rule_bp(\d+)_(\d+)', test_name)
    if match:
        # For bp4-001, we can't easily map this to a card_id
        # Need to search differently
        return None
    
    # Pattern 6: test_hs_pr_016 -> 16
    match = re.search(r'test_hs_pr_0?(\d+)', test_name)
    if match:
        return int(match.group(1))
    
    # Pattern 7: test_id_717 -> 717
    match = re.search(r'test_id_(\d+)', test_name)
    if match:
        return int(match.group(1))
    
    # Pattern 8: test_pl_n_bp5_030 -> extract from bp5-030
    match = re.search(r'test_pl_\w+_bp(\d+)_(\d+)', test_name)
    if match:
        # Can't easily map bp5-030 to card_id
        return None
    
    # Pattern 9: test_multi_qa_ll_bp2_001 -> extract from bp2-001
    match = re.search(r'test_multi_qa_ll_bp(\d+)_(\d+)', test_name)
    if match:
        # Can't easily map bp2-001 to card_id
        return None
    
    return None

# Extract card_id numbers and map to card_no
card_ids = set()
for test_name in failed_tests:
    card_id = extract_card_id_from_test_name(test_name)
    if card_id:
        card_ids.add(card_id)

print(f"Extracted {len(card_ids)} unique card_id numbers from {len(failed_tests)} failed tests")
print(f"Card ID numbers: {sorted(card_ids)}")

# Map card_id numbers to card_no using cards_compiled.json
mapped_card_nos = set()
for card_id in card_ids:
    if card_id in card_id_to_card_no:
        mapped_card_nos.add(card_id_to_card_no[card_id])
        print(f"card_id {card_id} -> card_no {card_id_to_card_no[card_id]}")
    else:
        print(f"card_id {card_id} not found in cards_compiled.json mapping")

print(f"\nMapped to {len(mapped_card_nos)} unique card_nos")
print(f"Card IDs: {sorted(mapped_card_nos)}")

# Create lookup by card
authored_by_card = {}
for ability in authored_frames['abilities']:
    for ref in ability.get('card_refs', []):
        card_no = ref.get('card_no')
        if card_no:
            if card_no not in authored_by_card:
                authored_by_card[card_no] = []
            authored_by_card[card_no].append(ability)

converted_by_card = {}
for ability in converted_frames['abilities']:
    for ref in ability.get('card_refs', []):
        card_no = ref.get('card_no')
        if card_no:
            if card_no not in converted_by_card:
                converted_by_card[card_no] = []
            converted_by_card[card_no].append(ability)

extracted_by_card = {}
for ability in extracted_abilities['unique_abilities']:
    for card_ref in ability.get('cards', []):
        if ' | ' in card_ref:
            card_no = card_ref.split(' | ')[0]
            if card_no not in extracted_by_card:
                extracted_by_card[card_no] = []
            extracted_by_card[card_no].append(ability)

# Find matching cards in cards.json using mapped card_nos
matched_cards = []
for card_no in sorted(mapped_card_nos):
    if card_no in cards:
        card = cards[card_no]
        matched_cards.append({
            'card_no': card_no,
            'name': card.get('name', ''),
            'ability': card.get('ability', ''),
            'has_authored': card_no in authored_by_card,
            'has_converted': card_no in converted_by_card,
            'has_extracted': card_no in extracted_by_card,
        })
    else:
        matched_cards.append({
            'card_no': card_no,
            'name': 'NOT FOUND',
            'ability': '',
            'has_authored': False,
            'has_converted': False,
            'has_extracted': False,
        })

print(f"\nMatched {len(matched_cards)} cards in cards.json")

# Output to JSON
output_file = Path("tools/ability_extraction/failed_test_cards.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'total_failed_tests': len(failed_tests),
        'unique_card_ids': len(card_ids),
        'matched_cards': len(matched_cards),
        'cards': matched_cards
    }, f, ensure_ascii=False, indent=2)

print(f"Output written to {output_file}")

# Create detailed markdown
md_file = Path("tools/ability_extraction/failed_test_cards.md")
with open(md_file, 'w', encoding='utf-8') as f:
    f.write("# Failed Test Cards\n\n")
    f.write(f"Total failed tests: {len(failed_tests)}\n")
    f.write(f"Unique card IDs extracted: {len(card_ids)}\n")
    f.write(f"Cards matched in cards.json: {len(matched_cards)}\n\n")
    
    for i, card_data in enumerate(matched_cards):
        f.write(f"## {i+1}. {card_data['card_no']} | {card_data['name']}\n\n")
        
        if card_data['name'] == 'NOT FOUND':
            f.write("⚠️ Card not found in cards.json\n\n")
            continue
        
        f.write(f"**Ability Text:**\n```\n{card_data['ability']}\n```\n\n")
        
        f.write(f"**Data Availability:**\n")
        f.write(f"- Authored frames: {'✓' if card_data['has_authored'] else '✗'}\n")
        f.write(f"- Converted frames: {'✓' if card_data['has_converted'] else '✗'}\n")
        f.write(f"- Extracted semantics: {'✓' if card_data['has_extracted'] else '✗'}\n\n")
        
        if card_data['has_authored']:
            authored = authored_by_card[card_data['card_no']]
            f.write(f"**Authored Abilities ({len(authored)}):**\n")
            for j, ability in enumerate(authored[:2]):  # Show first 2
                f.write(f"\nAbility {j}:\n")
                f.write(f"- Trigger: {ability.get('trigger', 'N/A')}\n")
                f.write(f"- Frames: {len(ability.get('frames', []))}\n")
                frames = ability.get('frames', [])
                for k, frame in enumerate(frames[:3]):  # Show first 3 frames
                    f.write(f"  Frame {k}: {frame.get('op')} | value={frame.get('value')} | attr={frame.get('attr')} | slot={frame.get('slot')}\n")
            f.write("\n")
        
        if card_data['has_converted']:
            converted = converted_by_card[card_data['card_no']]
            f.write(f"**Converted Abilities ({len(converted)}):**\n")
            for j, ability in enumerate(converted[:2]):  # Show first 2
                f.write(f"\nAbility {j}:\n")
                f.write(f"- Trigger: {ability.get('trigger', 'N/A')}\n")
                f.write(f"- Frames: {len(ability.get('frames', []))}\n")
                frames = ability.get('frames', [])
                for k, frame in enumerate(frames[:3]):  # Show first 3 frames
                    f.write(f"  Frame {k}: {frame.get('op')} | value={frame.get('value')} | attr={frame.get('attr')} | slot={frame.get('slot')}\n")
            f.write("\n")
        
        f.write("---\n\n")

print(f"Markdown version written to {md_file}")
