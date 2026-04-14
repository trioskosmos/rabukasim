import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def remove_trigger_from_start(text: str) -> str:
    """Remove trigger from the start of text, preserving triggers in the middle/end."""
    # Match trigger pattern: {{icon.png|text}} or {{icon.png|text}}/{{icon2.png|text2}}
    trigger_pattern = r'^(\{\\{[^}]+\\.png\|[^}]+\}\}(?:/\{\\{[^}]+\\.png\|[^}]+\}\})?)'
    trigger_match = re.match(trigger_pattern, text)
    
    if trigger_match:
        return text[trigger_match.end():].strip()
    else:
        return text


def extract_trigger(ability_text: str) -> dict[str, str]:
    """Extract trigger from ability text and return trigger and remaining text."""
    # Match trigger pattern: {{icon.png|text}} or {{icon.png|text}}/{{icon2.png|text2}}
    trigger_pattern = r'^(\{\\{[^}]+\\.png\|[^}]+\}\}(?:/\{\\{[^}]+\\.png\|[^}]+\}\})?)'
    trigger_match = re.match(trigger_pattern, ability_text)
    
    if trigger_match:
        trigger = trigger_match.group(1)
        remaining_text = ability_text[trigger_match.end():].strip()
        return {
            "trigger": trigger,
            "remaining_text": remaining_text,
            "original": ability_text
        }
    else:
        return {
            "trigger": "",
            "remaining_text": ability_text,
            "original": ability_text
        }


def process_patterns_triggers():
    """Remove triggers from the start of all pattern literals/templates."""
    global DSL_PATTERNS, LITERAL_PATTERNS, FAMILY_PATTERNS
    
    # Process DSL_PATTERNS
    for pattern in DSL_PATTERNS:
        if "template" in pattern:
            pattern["template"] = remove_trigger_from_start(pattern["template"])
    
    # Process LITERAL_PATTERNS
    for pattern in LITERAL_PATTERNS:
        if "literal" in pattern:
            pattern["literal"] = remove_trigger_from_start(pattern["literal"])
        if "template" in pattern:
            pattern["template"] = remove_trigger_from_start(pattern["template"])
    
    # Process FAMILY_PATTERNS
    for pattern in FAMILY_PATTERNS:
        if "prefix" in pattern:
            pattern["prefix"] = remove_trigger_from_start(pattern["prefix"])
        if "template" in pattern:
            pattern["template"] = remove_trigger_from_start(pattern["template"])


DSL_PATTERNS = [
        {
                "name": "heart_total_condition_opponent_phase_cost_increase",
                "regex": "\\b([^。]+)の([^。]+)いる([^。]+)が持つ([^。]+)に([^。]+)が([^。]+)(\\d+)つ以上ある場合、([^。]+)の([^。]+)、([^。]+)の([^。]+)にある([^。]+)(\\d+)枚は、([^。]+)ための([^。]+)が([^。]+)多くなる",
                "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧が持つ⟦HEART_TYPE⟧に⟦RESOURCE⟧が⟦TOTAL⟧⟦NUMBER⟧つ以上ある場合、⟦OPPONENT⟧の⟦PHASE⟧、⟦OPPONENT⟧の⟦ZONE⟧にある⟦CARD_TYPE⟧⟦NUMBER2⟧枚は、⟦CONTEXT⟧ための⟦COST⟧が⟦MODIFIER⟧多くなる",
                "structure": "Heart total condition opponent phase cost increase"
        },
        {
                "name": "cost_calculation_summon",
                "regex": "\\bそうした場合、([^。]+)の([^。]+)から、その([^。]+)の([^。]+)に(\\d+)を([^。]+)した([^。]+)に([^。]+)コストの『([^』]+)』の([^。]+)を(\\d+)枚、その([^。]+)いた([^。]+)に([^。]+)させる",
                "template": "そうした場合、⟦SOURCE⟧の⟦ZONE⟧から、その⟦MEMBER⟧の⟦ATTRIBUTE⟧に⟦NUMBER1⟧を⟦OPERATION⟧した⟦CALCULATED⟧に⟦EQUAL⟧コストの『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER2⟧枚、その⟦MEMBER2⟧いた⟦ZONE2⟧に⟦ACTION⟧させる",
                "structure": "Cost calculation summon"
        },
        {
                "name": "both_players_summon",
                "regex": "\\b([^。]+)と([^。]+)は([^。]+)、([^。]+)の([^。]+)からコスト(\\d+)以下の([^。]+)を(\\d+)枚、([^。]+)の([^。]+)([^。]+)に([^。]+)で([^。]+)させる",
                "template": "⟦PLAYER1⟧と⟦PLAYER2⟧は⟦EACH⟧、⟦SELF⟧の⟦ZONE⟧からコスト⟦COST⟧以下の⟦CARD_TYPE⟧を⟦NUMBER⟧枚、⟦MEMBER⟧の⟦CONDITION⟧⟦AREA⟧に⟦STATE⟧で⟦ACTION⟧させる",
                "structure": "Both players summon"
        },
        {
                "name": "center_member_position_change",
                "regex": "\\(?\\s*([^。]+)いる([^。]+)を([^。]+)いる([^。]+)以外の([^。]+)に([^。]+)させる。その([^。]+)に([^。]+)いる場合、その([^。]+)は([^。]+)に([^。]+)させる",
                "template": "⟦ZONE⟧いる⟦TARGET⟧を⟦CURRENT⟧いる⟦AREA⟧以外の⟦ZONE2⟧に⟦ACTION⟧させる。その⟦ZONE3⟧に⟦TARGET2⟧いる場合、その⟦TARGET2⟧は⟦DESTINATION⟧に⟦ACTION2⟧させる",
                "structure": "Center member position change"
        },
        {
                "name": "heart_color_exception_per_member_cost_reduction",
                "regex": "\\b([^。]+)の([^。]+)いる([^。]+)と([^。]+)以外の([^。]+)の([^。]+)を持つ([^。]+)(\\d+)人につき、([^。]+)の([^。]+)を([^。]+)([^。]+)",
                "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦HEART1⟧と⟦HEART2⟧以外の⟦COLOR⟧の⟦HEART⟧を持つ⟦TARGET⟧⟦NUMBER⟧人につき、⟦CARD⟧の⟦COST⟧を⟦MODIFIER⟧⟦ACTION⟧",
                "structure": "Heart color exception per member cost reduction"
        },
        {
                "name": "member_gains_hearts_from_selected_card_colors",
                "regex": "\\b([^。]+)の([^。]+)いる「([^」]+)」(\\d+)人は、([^。]+)により([^。]+)([^。]+)が持つ([^。]+)の([^。]+)を(\\d+)つずつ([^。]+)",
                "template": "⟦SOURCE⟧の⟦ZONE⟧いる「⟦MEMBER⟧」⟦NUMBER⟧人は、⟦CONTEXT⟧により⟦SELECTED⟧⟦CARD⟧が持つ⟦ATTRIBUTE⟧の⟦RESOURCE⟧を⟦NUMBER2⟧つずつ⟦ACTION⟧",
                "structure": "Member gains hearts from selected card colors"
        },
        {
                "name": "zone_different_group_name_card_add",
                "regex": "\\b([^。]+)の([^。]+)にある、([^。]+)の([^。]+)いるすべての([^。]+)と([^。]+)([^。]+)を持つ([^。]+)(\\d+)枚を([^。]+)に加える",
                "template": "⟦SOURCE⟧の⟦ZONE⟧にある、⟦SOURCE2⟧の⟦ZONE2⟧いるすべての⟦TARGET⟧と⟦DIFFERENT⟧⟦ATTRIBUTE⟧を持つ⟦CARD_TYPE⟧⟦NUMBER⟧枚を⟦DESTINATION⟧に加える",
                "structure": "Zone different group name card add"
        },
        {
                "name": "per_group_cost_reduction",
                "regex": "\\b([^。]+)を([^。]+)するための([^。]+)は([^。]+)の([^。]+)いる([^。]+)の中の([^。]+)(\\d+)種類につき、([^。]+)([^。]+)",
                "template": "⟦ABILITY⟧を⟦ACTION⟧するための⟦COST⟧は⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧の中の⟦ATTRIBUTE⟧⟦NUMBER⟧種類につき、⟦RESOURCE⟧⟦REDUCTION⟧",
                "structure": "Per group cost reduction"
        },
        {
                "name": "per_member_wait_then_draw",
                "regex": "\\b([^。]+)を(\\d+)人まで([^。]+)してもよい：これにより([^。]+)にした([^。]+)(\\d+)人につき、([^。]+)を(\\d+)枚([^。]+)",
                "template": "⟦TARGET⟧を⟦NUMBER1⟧人まで⟦STATE⟧してもよい：これにより⟦STATE2⟧にした⟦TARGET2⟧⟦NUMBER2⟧人につき、⟦CARD_TYPE⟧を⟦NUMBER3⟧枚⟦ACTION⟧",
                "structure": "Per member wait then draw"
        },
        {
                "name": "zone_card_except_group_per_card_cost_reduce",
                "regex": "\\b([^。]+)の([^。]+)にある([^。]+)以外の『([^』]+)』の([^。]+)(\\d+)枚につき、([^。]+)の([^。]+)を([^。]+)減らす",
                "template": "⟦SOURCE⟧の⟦ZONE⟧にある⟦EXCEPT_CARD⟧以外の『⟦GROUP⟧』の⟦CARD_TYPE⟧⟦NUMBER⟧枚につき、⟦TARGET⟧の⟦COST⟧を⟦MODIFIER⟧減らす",
                "structure": "Zone card except group per card cost reduce"
        },
        {
                "name": "dual_zone_card_count_condition_resource_gain",
                "regex": "\\b([^。]+)の([^。]+)の([^。]+)が(\\d+)枚で、かつ([^。]+)の([^。]+)に([^。]+)が(\\d+)枚以上ある場合、([^。]+)を得る",
                "template": "⟦SOURCE1⟧の⟦ZONE1⟧の⟦CARD_TYPE⟧が⟦NUMBER1⟧枚で、かつ⟦SOURCE2⟧の⟦ZONE2⟧に⟦CARD_TYPE2⟧が⟦NUMBER2⟧枚以上ある場合、⟦RESOURCE⟧を得る",
                "structure": "Dual zone card count condition resource gain"
        },
        {
                "name": "wait_member_count_selection",
                "regex": "\\b([^。]+)の([^。]+)いる([^。]+)の([^。]+)の([^。]+)まで、([^。]+)の([^。]+)にある『([^』]+)』の([^。]+)を選ぶ",
                "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦STATE⟧の⟦TARGET⟧の⟦COUNT⟧まで、⟦SOURCE2⟧の⟦ZONE2⟧にある『⟦GROUP⟧』の⟦CARD_TYPE⟧を選ぶ",
                "structure": "Wait member count selection"
        },
        {
                "name": "score_based_card_reveal",
                "regex": "\\b([^。]+)の([^。]+)から、([^。]+)の([^。]+)の([^。]+)に(\\d+)を([^。]+)した([^。]+)に等しい([^。]+)見る",
                "template": "⟦SOURCE⟧の⟦ZONE⟧から、⟦SOURCE2⟧の⟦LIVE⟧の⟦ATTRIBUTE1⟧に⟦NUMBER⟧を⟦OPERATION⟧した⟦CALCULATED⟧に等しい⟦COUNT⟧見る",
                "structure": "Score based card reveal"
        },
        {
                "name": "per_member_reveal_from_deck",
                "regex": "\\b([^。]+)の([^。]+)から、([^。]+)と([^。]+)の([^。]+)いる([^。]+)(\\d+)人につき、(\\d+)枚([^。]+)する",
                "template": "⟦SOURCE⟧の⟦ZONE⟧から、⟦SOURCE1⟧と⟦SOURCE2⟧の⟦ZONE2⟧いる⟦TARGET⟧⟦NUMBER1⟧人につき、⟦NUMBER2⟧枚⟦ACTION⟧する",
                "structure": "Per member reveal from deck"
        },
        {
                "name": "state_change_optional_cost_condition_state_change",
                "regex": "\\b([^。]+)を([^。]+)にしてもよい：([^。]+)の([^。]+)いるコスト(\\d+)以下の([^。]+)(\\d+)人を([^。]+)にする",
                "template": "⟦TARGET⟧を⟦STATE1⟧にしてもよい：⟦SOURCE⟧の⟦ZONE⟧いるコスト⟦COST⟧以下の⟦NEW_TARGET⟧⟦NUMBER⟧人を⟦STATE2⟧にする",
                "structure": "State change optional cost condition state change"
        },
        {
                "name": "zone_card_count_condition_zone_to_zone_add",
                "regex": "([^。]+)の([^。]+)に(?:この|その)?カードが(\\d+)枚以上ある場合、([^。]+)の([^。]+)から(?:この|その)?([^。]+)を(\\d+)枚([^。]+)に加える",
                "template": "⟦ZONE⟧の⟦ZONE2⟧にカードが⟦NUMBER⟧枚以上ある場合、⟦PLAYER⟧の⟦SOURCE⟧から⟦CARD_TYPE⟧を⟦NUMBER2⟧枚⟦DESTINATION⟧に加える",
                "structure": "Zone card count condition zone to zone add"
        },
        {
                "name": "cost_total_condition_summon",
                "regex": "\\b([^。]+)から、([^。]+)の([^。]+)が(\\d+)以下になるように([^。]+)を(\\d+)枚まで([^。]+)に([^。]+)させる",
                "template": "⟦SOURCE⟧から、⟦ATTRIBUTE⟧の⟦TOTAL⟧が⟦NUMBER1⟧以下になるように⟦CARD_TYPE⟧を⟦NUMBER2⟧枚まで⟦DESTINATION⟧に⟦ACTION⟧させる",
                "structure": "Cost total condition summon"
        },
        {
                "name": "zone_card_reveal_optional_zone_card_count_add",
                "regex": "\\b([^。]+)の([^。]+)を(\\d+)枚公開してもよい：([^。]+)の([^。]+)にある([^。]+)を(\\d+)枚([^。]+)に加える",
                "template": "⟦SOURCE1⟧の⟦CARD_TYPE⟧を⟦NUMBER1⟧枚公開してもよい：⟦SOURCE2⟧の⟦ZONE⟧にある⟦RESOURCE⟧を⟦NUMBER2⟧枚⟦DESTINATION⟧に加える",
                "structure": "Zone card reveal optional zone card count add"
        },
        {
                "name": "player_selection_card_placement",
                "regex": "\\b([^。]+)は、その([^。]+)の([^。]+)にある([^。]+)を(\\d+)枚、その([^。]+)の([^。]+)の([^。]+)に置く",
                "template": "⟦PLAYER⟧は、その⟦TARGET_PLAYER⟧の⟦ZONE⟧にある⟦CARD_TYPE⟧を⟦NUMBER⟧枚、その⟦TARGET_PLAYER2⟧の⟦ZONE2⟧の⟦POSITION⟧に置く",
                "structure": "Player selection card placement"
        },
        {
                "name": "area_placement_turn_restriction",
                "regex": "\\(?\\s*([^。]+)で([^。]+)した([^。]+)の([^。]+)([^。]+)には、この([^。]+)に([^。]+)は([^。]+)できない",
                "template": "⟦EFFECT⟧で⟦SUMMONED⟧した⟦MEMBER⟧の⟦AREA⟧⟦LOCATION⟧には、この⟦TURN⟧に⟦MEMBER2⟧は⟦ACTION⟧できない",
                "structure": "Area placement turn restriction"
        },
        {
                "name": "conditional_card_add_and_discard_others",
                "regex": "\\bその([^。]+)を([^。]+)に加え、([^。]+)により([^。]+)された([^。]+)すべての([^。]+)を([^。]+)に置く",
                "template": "その⟦CARD⟧を⟦DESTINATION⟧に加え、⟦CONTEXT⟧により⟦REVEALED⟧された⟦OTHER⟧すべての⟦CARD_TYPE⟧を⟦DESTINATION2⟧に置く",
                "structure": "Conditional card add and discard others"
        },
        {
                "name": "activation_cost_zone_to_zone_add",
                "regex": "([^。]+)を([^。]+)から([^。]+)に置く：([^。]+)の([^。]+)から([^。]+)を(\\d+)枚([^。]+)に加える",
                "template": "⟦COST_TARGET⟧を⟦SOURCE_ZONE⟧から⟦DESTINATION_ZONE⟧に置く：⟦SOURCE⟧の⟦ZONE⟧から⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に加える",
                "structure": "Activation cost zone to zone add"
        },
        {
                "name": "highest_cost_member_condition",
                "regex": "\\b([^。]+)の([^。]+)いる([^。]+)のうち、([^。]+)にいる([^。]+)が([^。]+)大きい([^。]+)を持つ場合",
                "template": "⟦SOURCE⟧の⟦ZONE1⟧いる⟦TARGET⟧のうち、⟦ZONE2⟧にいる⟦TARGET2⟧が⟦SUPERLATIVE⟧大きい⟦ATTRIBUTE⟧を持つ場合",
                "structure": "Highest cost member condition"
        },
        {
                "name": "swap_members",
                "regex": "\\bその([^。]+)に([^。]+)いる場合、その([^。]+)は([^。]+)の([^。]+)いた([^。]+)に([^。]+)させる",
                "template": "その⟦ZONE1⟧に⟦TARGET1⟧いる場合、その⟦TARGET1⟧は⟦TARGET2⟧の⟦MEMBER⟧いた⟦ZONE2⟧に⟦ACTION⟧させる",
                "structure": "Swap members"
        },
        {
                "name": "ability_activation_condition",
                "regex": "\\b([^。]+)は、([^。]+)が([^。]+)の([^。]+)によって([^。]+)されている([^。]+)のみ([^。]+)する",
                "template": "⟦ABILITY⟧は、⟦CARD⟧が⟦SOURCE⟧の⟦CONTEXT⟧によって⟦STATE⟧されている⟦CONDITION⟧のみ⟦ACTION⟧する",
                "structure": "Ability activation condition"
        },
        {
                "name": "from_revealed_cards_to_deck_bottom",
                "regex": "\\b([^。]+)により([^。]+)された([^。]+)の中から、([^。]+)を(\\d+)枚まで([^。]+)の([^。]+)に置く",
                "template": "⟦CONTEXT⟧により⟦ACTION⟧された⟦SOURCE⟧の中から、⟦CARD_TYPE⟧を⟦NUMBER⟧枚まで⟦DESTINATION⟧の⟦POSITION⟧に置く",
                "structure": "From revealed cards to deck bottom"
        },
        {
                "name": "zone_member_cost_except_group_per_member_resource_gain",
                "regex": "\\b([^。]+)の([^。]+)いるコスト(\\d+)以上の([^。]+)以外の([^。]+)(\\d+)人につき、([^。]+)を得る",
                "template": "⟦SOURCE⟧の⟦ZONE⟧いるコスト⟦COST⟧以上の⟦EXCEPT_GROUP⟧以外の⟦TARGET⟧⟦NUMBER⟧人につき、⟦RESOURCE⟧を得る",
                "structure": "Zone member cost except group per member resource gain"
        },
        {
                "name": "hand_cost_group_card_summon_optional",
                "regex": "\\b([^。]+)からコスト(\\d+)以下の『([^』]+)』の([^。]+)を(\\d+)枚([^。]+)に([^。]+)させてもよい",
                "template": "⟦SOURCE⟧からコスト⟦COST⟧以下の『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に⟦ACTION⟧させてもよい",
                "structure": "Hand cost group card summon optional"
        },
        {
                "name": "member_leave_energy_return",
                "regex": "\\(?\\s*([^。]+)が([^。]+)から([^。]+)とき、([^。]+)に([^。]+)(?:されている|いる)([^。]+)は([^。]+)に置く",
                "template": "⟦MEMBER⟧が⟦ZONE⟧から⟦ACTION⟧とき、⟦LOCATION⟧に⟦STATE⟧されている⟦CARD_TYPE⟧は⟦DESTINATION⟧に置く",
                "structure": "Member leave energy return"
        },
        {
                "name": "zone_card_score_comparison_condition_resource_gain",
                "regex": "\\b([^。]+)の([^。]+)にある([^。]+)の([^。]+)が([^。]+)より([^。]+)かぎり、([^。]+)を得る",
                "template": "⟦SOURCE⟧の⟦ZONE⟧にある⟦CARD_TYPE⟧の⟦ATTRIBUTE⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧かぎり、⟦RESOURCE⟧を得る",
                "structure": "Zone card score comparison condition resource gain"
        },
        {
                "name": "hand_card_cost_reduce_per_hand_card",
                "regex": "\\b([^。]+)にある([^。]+)の([^。]+)は、([^。]+)以外の([^。]+)(\\d+)枚につき、(\\d+)少なくなる",
                "template": "⟦ZONE⟧にある⟦CARD⟧の⟦ATTRIBUTE⟧は、⟦EXCEPT_CARD⟧以外の⟦SOURCE⟧⟦NUMBER1⟧枚につき、⟦NUMBER2⟧少なくなる",
                "structure": "Hand card cost reduce per hand card"
        },
        {
                "name": "multi_resource_each_condition",
                "regex": "\\b([^。]+)の([^。]+)の([^。]+)の([^。]+)に([^。]+)が([^。]+)(\\d+)以上([^。]+)かぎり",
                "template": "⟦SOURCE⟧の⟦CONTEXT⟧の⟦CARD_TYPE⟧の⟦ATTRIBUTE⟧に⟦RESOURCE⟧が⟦CONDITION⟧⟦NUMBER⟧以上⟦STATE⟧かぎり",
                "structure": "Multi resource each condition"
        },
        {
                "name": "zone_to_zone_optional_deck_top_look",
                "regex": "\\b([^。]+)を(\\d+)枚([^。]+)に置いてもよい：([^。]+)の([^。]+)の上から([^。]+)を(\\d+)枚見る",
                "template": "⟦SOURCE⟧を⟦NUMBER1⟧枚⟦DESTINATION1⟧に置いてもよい：⟦SOURCE2⟧の⟦ZONE⟧の上から⟦RESOURCE⟧を⟦NUMBER2⟧枚見る",
                "structure": "Zone to zone optional deck top look"
        },
        {
                "name": "wait_and_discard_then_draw",
                "regex": "\\b([^。]+)を([^。]+)し、([^。]+)を(\\d+)枚([^。]+)に置く：([^。]+)を(\\d+)枚([^。]+)",
                "template": "⟦TARGET⟧を⟦STATE⟧し、⟦CARD1⟧を⟦NUMBER1⟧枚⟦ZONE⟧に置く：⟦CARD2⟧を⟦NUMBER2⟧枚⟦ACTION⟧",
                "structure": "Wait and discard then draw"
        },
        {
                "name": "zone_cost_group_card_add",
                "regex": "\\b([^。]+)の([^。]+)からコスト(\\d+)以下の『([^』]+)』の([^。]+)を(\\d+)枚([^。]+)に加える",
                "template": "⟦SOURCE⟧の⟦ZONE⟧からコスト⟦COST⟧以下の『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に加える",
                "structure": "Zone cost group card add"
        },
        {
                "name": "live_card_heart_total_condition",
                "regex": "\\b([^。]+)の([^。]+)に([^。]+)の([^。]+)が(\\d+)以上の『([^』]+)』の([^。]+)あるかぎり",
                "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦ATTRIBUTE⟧の⟦TOTAL⟧が⟦NUMBER⟧以上の『⟦GROUP⟧』の⟦CARD_TYPE⟧あるかぎり",
                "structure": "Live card heart total condition"
        },
        {
                "name": "hand_specific_card_summon",
                "regex": "\\b([^。]+)からコスト(\\d+)以下の(?:「([^」]+)」|『([^』]+)』)の([^。]+)を(\\d+)枚([^。]+)に([^。]+)させる",
                "template": "⟦SOURCE⟧からコスト⟦COST⟧以下の⟦IDENTIFIER⟧の⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に⟦ACTION⟧させる",
                "structure": "Hand specific card summon"
        },
        {
                "name": "member_leave_energy_return",
                "regex": "\\b([^。]+)が([^。]+)から([^。]+)とき、([^。]+)に([^。]+)いる([^。]+)は([^。]+)に置く",
                "template": "⟦MEMBER⟧が⟦ZONE⟧から⟦ACTION⟧とき、⟦LOCATION⟧に⟦PLACED⟧いる⟦CARD_TYPE⟧は⟦DESTINATION⟧に置く",
                "structure": "Member leave energy return"
        },
        {
                "name": "automatic_trigger_state_change_optional",
                "regex": "\\b([^。]+)が([^。]+)から([^。]+)に([^。]+)とき、([^。]+)(\\d+)人を([^。]+)にしてもよい",
                "template": "⟦TARGET⟧が⟦SOURCE⟧から⟦DESTINATION⟧に⟦TRIGGER⟧とき、⟦NEW_TARGET⟧⟦NUMBER⟧人を⟦STATE⟧にしてもよい",
                "structure": "Automatic trigger state change optional"
        },
        {
                "name": "blade_transformation",
                "regex": "\\b([^。]+)によって([^。]+)される([^。]+)の([^。]+)が持つ([^。]+)は、すべて([^。]+)になる",
                "template": "⟦CONTEXT⟧によって⟦ACTION⟧される⟦SOURCE⟧の⟦CARD_TYPE⟧が持つ⟦ATTRIBUTE⟧は、すべて⟦TRANSFORM⟧になる",
                "structure": "Blade transformation"
        },
        {
                "name": "per_group_reveal",
                "regex": "\\bその中から([^。]+)([^。]+)につき(\\d+)枚ずつ([^。]+)し、(\\d+)枚まで([^。]+)に加えてもよい",
                "template": "その中から⟦EACH⟧⟦ATTRIBUTE⟧につき⟦NUMBER1⟧枚ずつ⟦ACTION⟧し、⟦NUMBER2⟧枚まで⟦DESTINATION⟧に加えてもよい",
                "structure": "Per group reveal"
        },
        {
                "name": "then_opponent_wait_member_condition_draw",
                "regex": "\\bその後、([^。]+)の([^。]+)に([^。]+)の([^。]+)いる場合、([^。]+)を(\\d+)枚([^。]+)",
                "template": "その後、⟦SOURCE⟧の⟦ZONE⟧に⟦STATE⟧の⟦TARGET⟧いる場合、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
                "structure": "Then opponent wait member condition draw"
        },
        {
                "name": "zone_all_cards_cost_increase",
                "regex": "\\b([^。]+)の([^。]+)にあるすべての([^。]+)は、([^。]+)ための([^。]+)が([^。]+)多くなる",
                "template": "⟦SOURCE⟧の⟦ZONE⟧にあるすべての⟦CARD_TYPE⟧は、⟦CONTEXT⟧ための⟦COST⟧が⟦MODIFIER⟧多くなる",
                "structure": "Zone all cards cost increase"
        },
        {
                "name": "conditional_group_live_card_placement",
                "regex": "\\bそうした場合、([^。]+)の([^。]+)にある『([^』]+)』の([^。]+)を(\\d+)枚([^。]+)に置く",
                "template": "そうした場合、⟦SOURCE⟧の⟦ZONE⟧にある『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に置く",
                "structure": "Conditional group live card placement"
        },
        {
                "name": "card_location_condition_zone_member_resource_gain",
                "regex": "\\b([^。]+)が([^。]+)にあるかぎり、([^。]+)の([^。]+)にいる([^。]+)は([^。]+)を得る",
                "template": "⟦CARD⟧が⟦ZONE1⟧にあるかぎり、⟦SOURCE⟧の⟦ZONE2⟧にいる⟦TARGET⟧は⟦RESOURCE⟧を得る",
                "structure": "Card location condition zone member resource gain"
        },
        {
                "name": "surplus_heart_condition_draw",
                "regex": "\\b([^。]+)が([^。]+)に([^。]+)を(\\d+)つ以上持つ場合、([^。]+)を(\\d+)枚([^。]+)",
                "template": "⟦SOURCE⟧が⟦ZONE⟧に⟦RESOURCE⟧を⟦NUMBER1⟧つ以上持つ場合、⟦CARD_TYPE⟧を⟦NUMBER2⟧枚⟦ACTION⟧",
                "structure": "Surplus heart condition draw"
        },
        {
                "name": "summoned_member_condition_wait",
                "regex": "\\b([^。]+)により([^。]+)した([^。]+)が([^。]+)を持つ場合、([^。]+)を([^。]+)にする",
                "template": "⟦CONTEXT⟧により⟦SUMMONED⟧した⟦MEMBER⟧が⟦ATTRIBUTE⟧を持つ場合、⟦TARGET⟧を⟦STATE⟧にする",
                "structure": "Summoned member condition wait"
        },
        {
                "name": "reveal_count_reduction",
                "regex": "\\b([^。]+)によって([^。]+)される([^。]+)の([^。]+)の([^。]+)が(\\d+)枚([^。]+)",
                "template": "⟦CONTEXT⟧によって⟦REVEALED⟧される⟦SOURCE⟧の⟦CARD⟧の⟦COUNT⟧が⟦NUMBER⟧枚⟦REDUCTION⟧",
                "structure": "Reveal count reduction"
        },
        {
                "name": "live_score_comparison_card_add_optional",
                "regex": "\\b([^。]+)の([^。]+)が([^。]+)より([^。]+)場合、([^。]+)を([^。]+)に加えてもよい",
                "template": "⟦SOURCE⟧の⟦ATTRIBUTE⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧場合、⟦CARD⟧を⟦DESTINATION⟧に加えてもよい",
                "structure": "Live score comparison card add optional"
        },
        {
                "name": "condition_or_zone_cost_above_resource_gain",
                "regex": "\\b([^。]+)か([^。]+)の([^。]+)にコスト(\\d+)以上の([^。]+)いる場合、([^。]+)を得る",
                "template": "⟦SOURCE1⟧か⟦SOURCE2⟧の⟦ZONE⟧にコスト⟦COST⟧以上の⟦TARGET⟧いる場合、⟦RESOURCE⟧を得る",
                "structure": "Condition or zone cost above resource gain"
        },
        {
                "name": "live_score_comparison_draw",
                "regex": "\\b([^。]+)の([^。]+)が([^。]+)より([^。]+)場合、([^。]+)を(\\d+)枚([^。]+)",
                "template": "⟦SOURCE⟧の⟦ATTRIBUTE⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧場合、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
                "structure": "Live score comparison draw"
        },
        {
                "name": "exact_member_count_condition_resource_gain",
                "regex": "\\b([^。]+)の([^。]+)いる([^。]+)が([^。]+)(\\d+)人であるかぎり、([^。]+)を得る",
                "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧が⟦EXACT⟧⟦NUMBER⟧人であるかぎり、⟦RESOURCE⟧を得る",
                "structure": "Exact member count condition resource gain"
        },
        {
                "name": "energy_zone_to_member_under_optional",
                "regex": "\\b([^。]+)の([^。]+)にある([^。]+)(\\d+)枚を([^。]+)の([^。]+)に置いてもよい",
                "template": "⟦SOURCE⟧の⟦ZONE⟧にある⟦RESOURCE⟧⟦NUMBER⟧枚を⟦TARGET⟧の⟦LOCATION⟧に置いてもよい",
                "structure": "Energy zone to member under optional"
        },
        {
                "name": "select_cards_with_specific_resources_optional",
                "regex": "\\bその中から([^。]+)を持つ([^。]+)を(\\d+)枚まで([^。]+)して([^。]+)に加えてもよい",
                "template": "その中から⟦RESOURCE⟧を持つ⟦CARD_TYPE⟧を⟦NUMBER⟧枚まで⟦ACTION⟧して⟦DESTINATION⟧に加えてもよい",
                "structure": "Select cards with specific resources optional"
        },
        {
                "name": "per_live_card_score_increase",
                "regex": "\\b([^。]+)の中にある([^。]+)(\\d+)枚につき、([^。]+)の([^。]+)を([^。]+)する",
                "template": "⟦SOURCE⟧の中にある⟦CARD_TYPE⟧⟦NUMBER1⟧枚につき、⟦TARGET⟧の⟦ATTRIBUTE⟧を⟦MODIFICATION⟧する",
                "structure": "Per live card score increase"
        },
        {
                "name": "select_specific_group_live_card_optional",
                "regex": "\\bその中から『([^』]+)』の([^。]+)を(\\d+)枚まで([^。]+)して([^。]+)に加えてもよい",
                "template": "その中から『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚まで⟦ACTION⟧して⟦DESTINATION⟧に加えてもよい",
                "structure": "Select specific group live card optional"
        },
        {
                "name": "zone_member_resource_total_action",
                "regex": "\\b([^。]+)の([^。]+)いる([^。]+)が持つ([^。]+)の([^。]+)が(\\d+)以上の場合、([^。]+)。",
                "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧が持つ⟦RESOURCE⟧の⟦ATTRIBUTE⟧が⟦NUMBER⟧以上の場合、⟦ACTION⟧。",
                "structure": "Zone member resource total action"
        },
        {
                "name": "zone_group_card_deck_top_place",
                "regex": "\\b([^。]+)から『([^』]+)』の([^。]+)を(\\d+)枚まで([^。]+)の([^。]+)に置く",
                "template": "⟦SOURCE⟧から『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚まで⟦DESTINATION⟧の⟦POSITION⟧に置く",
                "structure": "Zone group card deck top place"
        },
        {
                "name": "zone_this_member_except_group_per_member_condition",
                "regex": "\\b([^。]+)の([^。]+)いる([^。]+)以外の『([^』]+)』の([^。]+)(\\d+)人につき",
                "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦EXCEPT_MEMBER⟧以外の『⟦GROUP⟧』の⟦TARGET⟧⟦NUMBER⟧人につき",
                "structure": "Zone this member except group per member condition"
        },
        {
                "name": "continuous_reveal_until_condition",
                "regex": "\\b([^。]+)が([^。]+)まで、([^。]+)の([^。]+)の([^。]+)を([^。]+)し続ける",
                "template": "⟦CARD_TYPE⟧が⟦CONDITION⟧まで、⟦SOURCE⟧の⟦ZONE⟧の⟦POSITION⟧を⟦ACTION⟧し続ける",
                "structure": "Continuous reveal until condition"
        },
        {
                "name": "opponent_wait_member_per_member_resource_gain",
                "regex": "\\b([^。]+)の([^。]+)いる([^。]+)の([^。]+)(\\d+)人につき、([^。]+)を得る",
                "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦STATE⟧の⟦TARGET⟧⟦NUMBER⟧人につき、⟦RESOURCE⟧を得る",
                "structure": "Opponent wait member per member resource gain"
        },
        {
                "name": "lose_resource_and_retry",
                "regex": "\\bその([^。]+)で([^。]+)を([^。]+)、もう一度([^。]+)を([^。]+)",
                "template": "その⟦CONTEXT⟧で⟦GAINED_RESOURCE⟧を⟦LOSE⟧、もう一度⟦ACTION⟧を⟦PERFORM⟧",
                "structure": "Lose resource and retry"
        },
        {
                "name": "no_other_members_condition_prevent_live",
                "regex": "\\b([^。]+)の([^。]+)にほかの([^。]+)いない場合、([^。]+)は([^。]+)できない",
                "template": "⟦SOURCE⟧の⟦ZONE⟧にほかの⟦TARGET⟧いない場合、⟦PLAYER⟧は⟦ACTION⟧できない",
                "structure": "No other members condition prevent live"
        },
        {
                "name": "zone_card_count_action",
                "regex": "\\b([^。]+)と([^。]+)の([^。]+)に([^。]+)が([^。]+)(\\d+)枚以上ある場合、([^。]+)。",
                "template": "⟦SOURCE1⟧と⟦SOURCE2⟧の⟦ZONE⟧に⟦CARD_TYPE⟧が⟦TOTAL⟧⟦NUMBER⟧枚以上ある場合、⟦ACTION⟧。",
                "structure": "Zone card count action"
        },
        {
                "name": "side_area_activation_restriction",
                "regex": "\\（([^。]+)は([^。]+)か([^。]+)に([^。]+)した([^。]+)のみ([^。]+)する",
                "template": "（⟦ABILITY⟧は⟦ZONE1⟧か⟦ZONE2⟧に⟦ACTION⟧した⟦CONDITION⟧のみ⟦ACTIVATE⟧する",
                "structure": "Side area activation restriction"
        },
        {
                "name": "area_specific_appearance_condition_draw",
                "regex": "\\b([^。]+)の([^。]+)に([^。]+)しているなら、([^。]+)を(\\d+)枚([^。]+)",
                "template": "⟦ZONE⟧の⟦AREA⟧に⟦STATE⟧しているなら、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
                "structure": "Area specific appearance condition draw"
        },
        {
                "name": "member_under_energy_cost_restriction",
                "regex": "\\b([^。]+)の([^。]+)に([^。]+)いる([^。]+)では([^。]+)を([^。]+)ない",
                "template": "⟦MEMBER⟧の⟦LOCATION⟧に⟦PLACED⟧いる⟦CARD_TYPE⟧では⟦COST⟧を⟦PAYMENT⟧ない",
                "structure": "Member under energy cost restriction"
        },
        {
                "name": "card_name_treatment",
                "regex": "\\b([^。]+)この([^。]+)は『([^』]+)』、『([^』]+)』、『([^』]+)』として扱う",
                "template": "⟦LOCATION⟧この⟦CARD⟧は『⟦GROUP1⟧』、『⟦GROUP2⟧』、『⟦GROUP3⟧』として扱う",
                "structure": "Card name treatment"
        },
        {
                "name": "zone_count_condition_card_draw",
                "regex": "\\b([^。]+)の([^。]+)が(\\d+)枚以上ある場合、([^。]+)を(\\d+)枚([^。]+)。",
                "template": "⟦SOURCE⟧の⟦RESOURCE⟧が⟦NUMBER1⟧枚以上ある場合、⟦CARD⟧を⟦NUMBER2⟧枚⟦ACTION⟧。",
                "structure": "Zone count condition card draw"
        },
        {
                "name": "zone_members_cost_below_wait",
                "regex": "([^。]+)の([^。]+)いるコスト(\\d+)以下の([^。]+)(\\d+)人を([^。]+)にする",
                "template": "⟦SOURCE⟧の⟦ZONE⟧いるコスト⟦COST⟧以下の⟦TARGET⟧⟦NUMBER⟧人を⟦STATE⟧にする",
                "structure": "Zone members cost below wait"
        },
        {
                "name": "look_at_deck_top",
                "regex": "\\b([^。]+)は、その([^。]+)の([^。]+)の([^。]+)の([^。]+)を([^。]+)",
                "template": "⟦PLAYER⟧は、その⟦TARGET_PLAYER⟧の⟦ZONE⟧の⟦POSITION⟧の⟦CARD_TYPE⟧を⟦ACTION⟧",
                "structure": "Look at deck top"
        },
        {
                "name": "zone_member_cost_distinct_action",
                "regex": "\\b([^。]+)の([^。]+)に([^。]+)が([^。]+)(?:この|その)?メンバーが(\\d+)人以上いるかぎり、([^。]+)。",
                "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦CARD_TYPE⟧が⟦ATTRIBUTE⟧メンバーが⟦NUMBER⟧人以上いるかぎり、⟦ACTION⟧。",
                "structure": "Zone member cost distinct action"
        },
        {
                "name": "member_movement_trigger_draw",
                "regex": "\\b([^。]+)が([^。]+)を([^。]+)するたび、([^。]+)を(\\d+)枚([^。]+)",
                "template": "⟦MEMBER⟧が⟦ZONE⟧を⟦ACTION⟧するたび、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DRAW⟧",
                "structure": "Member movement trigger draw"
        },
        {
                "name": "from_among_reveal_add_optional",
                "regex": "\\bその中から『([^』]+)』の([^。]+)を(\\d+)枚公開して([^。]+)に加えてもよい",
                "template": "その中から『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚公開して⟦ZONE⟧に加えてもよい",
                "structure": "From among reveal add optional"
        },
        {
                "name": "all_cards_type_condition_draw",
                "regex": "\\b([^。]+)が([^。ー]+)([^。]+)の場合、([^。]+)を(\\d+)枚([^。]+)",
                "template": "⟦THEY⟧が⟦ALL⟧⟦CARD_TYPE⟧の場合、⟦CARD_TYPE2⟧を⟦NUMBER⟧枚⟦ACTION⟧",
                "structure": "All cards type condition draw"
        },
        {
                "name": "zone_wait_state_member_condition",
                "regex": "\\b([^。]+)の([^。]+)に([^。]+)の『([^』]+)』の([^。]+)いるかぎり",
                "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦STATE⟧の『⟦GROUP⟧』の⟦TARGET⟧いるかぎり",
                "structure": "Zone wait state member condition"
        },
        {
                "name": "card_play_baton_touch_optional",
                "regex": "\\b([^。]+)の([^。]+)に際し、(\\d+)人の([^。]+)と([^。]+)してもよい",
                "template": "⟦CARD⟧の⟦CONTEXT⟧に際し、⟦NUMBER⟧人の⟦TARGET⟧と⟦ACTION⟧してもよい",
                "structure": "Card play baton touch optional"
        },
        {
                "name": "ability_activation_location_restriction",
                "regex": "\\b([^。]+)は、([^。]+)が([^。]+)にある([^。]+)のみ([^。]+)できる",
                "template": "⟦ABILITY⟧は、⟦CARD⟧が⟦ZONE⟧にある⟦CONDITION⟧のみ⟦ACTION⟧できる",
                "structure": "Ability activation location restriction"
        },
        {
                "name": "area_restriction_ability_activation",
                "regex": "\\（([^。]+)は([^。]+)に([^。]+)している([^。]+)のみ([^。]+)できる",
                "template": "（⟦ABILITY⟧は⟦ZONE⟧に⟦STATE⟧している⟦CONDITION⟧のみ⟦ACTION⟧できる",
                "structure": "Area restriction ability activation"
        },
        {
                "name": "energy_comparison_condition_resource_gain",
                "regex": "\\b([^。]+)の([^。]+)が([^。]+)より([^。]+)かぎり、([^。]+)を得る",
                "template": "⟦SOURCE⟧の⟦RESOURCE⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧かぎり、⟦RESOURCE2⟧を得る",
                "structure": "Energy comparison condition resource gain"
        },
        {
                "name": "alternative_condition_total_score_increase",
                "regex": "\\b([^。]+)が(\\d+)枚以上ある場合、([^。]+)に([^。]+)を([^。]+)する",
                "template": "⟦CARD⟧が⟦NUMBER1⟧枚以上ある場合、⟦ALTERNATIVE⟧に⟦SCORE⟧を⟦MODIFIER⟧する",
                "structure": "Alternative condition total score increase"
        },
        {
                "name": "optional_deck_top_discard",
                "regex": "\\b([^。]+)の([^。]+)の([^。]+)の([^。]+)を([^。]+)に置いてもよい",
                "template": "⟦SOURCE⟧の⟦ZONE⟧の⟦POSITION⟧の⟦CARD⟧を⟦DESTINATION⟧に置いてもよい",
                "structure": "Optional deck top discard"
        },
        {
                "name": "conditional_place",
                "regex": "そうした場合、これにより([^。]+)した([^。]+)を([^。]+)の([^。]+)に置く",
                "template": "そうした場合、これにより⟦ACTION⟧した⟦TARGET⟧を⟦SOURCE⟧の⟦ZONE⟧に置く",
                "structure": "Conditional place"
        },
        {
                "name": "energy_total_action",
                "regex": "\\b([^。]+)と([^。]+)の([^。]+)の([^。]+)が(\\d+)枚以上あるかぎり、([^。]+)。",
                "template": "⟦SOURCE1⟧と⟦SOURCE2⟧の⟦RESOURCE⟧の⟦ATTRIBUTE⟧が⟦NUMBER⟧枚以上あるかぎり、⟦ACTION⟧。",
                "structure": "Energy total action"
        },
        {
                "name": "move_to_different_area",
                "regex": "\\b([^。]+)を([^。]+)いる([^。]+)以外の([^。]+)に([^。]+)させる",
                "template": "⟦TARGET⟧を⟦CURRENT⟧いる⟦ZONE1⟧以外の⟦ZONE2⟧に⟦ACTION⟧させる",
                "structure": "Move to different area"
        },
        {
                "name": "select_specific_member_card",
                "regex": "\\b([^。]+)は([^。]+)の中から「([^」]+)」の([^。]+)を(\\d+)枚選ぶ",
                "template": "⟦PLAYER⟧は⟦SOURCE⟧の中から「⟦MEMBER⟧」の⟦CARD_TYPE⟧を⟦NUMBER⟧枚選ぶ",
                "structure": "Select specific member card"
        },
        {
                "name": "opponent_wait_member_count_condition",
                "regex": "\\b([^。]+)の([^。]+)に([^。]+)の([^。]+)が(\\d+)人以上いるかぎり",
                "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦STATE⟧の⟦TARGET⟧が⟦NUMBER⟧人以上いるかぎり",
                "structure": "Opponent wait member count condition"
        },
        {
                "name": "member_under_energy_per_energy_resource_gain",
                "regex": "\\b([^。]+)の([^。]+)にある([^。]+)(\\d+)枚につき、([^。]+)を得る",
                "template": "⟦MEMBER⟧の⟦LOCATION⟧にある⟦CARD_TYPE⟧⟦NUMBER⟧枚につき、⟦RESOURCE⟧を得る",
                "structure": "Member under energy per energy resource gain"
        },
        {
                "name": "score_based_energy_payment_optional",
                "regex": "\\b([^：]+)の([^：]+)に([^：]+)の([^：]+)を([^：]+)してもよい",
                "template": "⟦CARD⟧の⟦ATTRIBUTE⟧に⟦EQUAL⟧の⟦RESOURCE⟧を⟦ACTION⟧してもよい",
                "structure": "Score based energy payment optional"
        },
        {
                "name": "placed_cards_cost_reduction",
                "regex": "\\b([^：]+)に([^：]+)([^：]+)の([^：]+)が(\\d+)枚([^：]+)",
                "template": "⟦DESTINATION⟧に⟦PLACED⟧⟦SOURCE⟧の⟦COUNT⟧が⟦NUMBER⟧枚⟦REDUCTION⟧",
                "structure": "Placed cards cost reduction"
        },
        {
                "name": "score_floor_restriction",
                "regex": "\\b([^。]+)では([^。]+)の([^。]+)は(\\d+)未満には([^。]+)ない",
                "template": "⟦EFFECT⟧では⟦LIVE⟧の⟦SCORE⟧は⟦NUMBER⟧未満には⟦NEGATION⟧ない",
                "structure": "Score floor restriction"
        },
        {
                "name": "zone_card_count_add",
                "regex": "\\b([^。]+)の([^。]+)にある([^。]+)を(\\d+)枚([^。]+)に加える",
                "template": "⟦SOURCE⟧の⟦ZONE⟧にある⟦RESOURCE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に加える",
                "structure": "Zone card count add"
        },
        {
                "name": "conditional_consequence",
                "regex": "\\b([^。]+)により([^。]+)した([^。]+)、([^。]+)を([^。]+)。",
                "template": "⟦CONTEXT⟧により⟦ACTION⟧した⟦CONDITION⟧、⟦TARGET⟧を⟦RESULT⟧。",
                "structure": "Conditional consequence"
        },
        {
                "name": "energy_deck_place_wait_state",
                "regex": "\\b([^。]+)の([^。]+)から、([^。]+)を(\\d+)枚([^。]+)で置く",
                "template": "⟦SOURCE⟧の⟦ZONE⟧から、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦STATE⟧で置く",
                "structure": "Energy deck place wait state"
        },
        {
                "name": "original_heart_replacement",
                "regex": "([^。]+)、([^。]+)が([^。]+)持つ([^。]+)は([^。]+)([^。]+)になる",
                "template": "⟦PERIOD⟧、⟦MEMBER⟧が⟦ORIGINAL⟧持つ⟦HEART⟧は⟦SELECTED⟧⟦HEART2⟧になる",
                "structure": "Original heart replacement"
        },
        {
                "name": "deck_top_place",
                "regex": "\\b([^。]+)の([^。]+)(?:の上から|から)([^。]+)を(\\d+)枚([^。]+)に置く",
                "template": "⟦SOURCE⟧の⟦ZONE⟧から⟦RESOURCE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に置く",
                "structure": "Deck top place"
        },
        {
                "name": "phase_based_action_prevention",
                "regex": "\\b([^。]+)は([^。]+)の([^。]+)に([^。]+)に([^。]+)ない",
                "template": "⟦MEMBER⟧は⟦PLAYER⟧の⟦PHASE⟧に⟦ACTION⟧に⟦NEGATION⟧ない",
                "structure": "Phase based action prevention"
        },
        {
                "name": "per_discarded_card_draw",
                "regex": "\\b([^。]+)により([^。]+)した([^。ー]+)([^。]+)を([^。]+)",
                "template": "⟦CONTEXT⟧により⟦PLACED⟧した⟦COUNT⟧⟦ACTION⟧を⟦DRAW⟧",
                "structure": "Per discarded card draw"
        },
        {
                "name": "repeat_procedure",
                "regex": "\\b([^。]+)はこの([^。]+)をさらに(\\d+)回まで([^。]+)してもよい",
                "template": "⟦PLAYER⟧はこの⟦PROCEDURE⟧をさらに⟦NUMBER⟧回まで⟦REPEAT⟧してもよい",
                "structure": "Repeat procedure"
        },
        {
                "name": "draw_discard_combined",
                "regex": "\\b([^。]+)を(\\d+)枚引き、([^。]+)を(\\d+)枚([^。]+)に置く",
                "template": "⟦RESOURCE1⟧を⟦NUMBER1⟧枚引き、⟦RESOURCE2⟧を⟦NUMBER2⟧枚⟦DESTINATION⟧に置く",
                "structure": "Draw discard combined"
        },
        {
                "name": "zone_to_zone_add",
                "regex": "([^。]+)の([^。]+)から([^。]+)を(\\d+)枚([^。]+)に加える",
                "template": "⟦SOURCE⟧の⟦ZONE⟧から⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に加える",
                "structure": "Zone to zone add"
        },
        {
                "name": "condition_zone_member_presence_resource_gain",
                "regex": "\\b([^。]+)の([^。]+)に([^。]+)がいるかぎり、([^。]+)を得る",
                "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦CONDITION⟧がいるかぎり、⟦RESOURCE⟧を得る",
                "structure": "Condition zone member presence resource gain"
        },
        {
                "name": "condition_draw",
                "regex": "それらの中に([^。]+)がある場合、([^。]+)を(\\d+)枚([^。]+)",
                "template": "それらの中に⟦CARD_TYPE⟧がある場合、⟦RESOURCE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
                "structure": "Condition draw"
        },
        {
                "name": "icon_action_after_condition",
                "regex": "(\\{?\\{[^}]+\\.png\\|[^}]+\\}\\}?)+を得る。",
                "template": "⟦ICON⟧を得る。",
                "structure": "Icon action after condition"
        },
        {
                "name": "live_card_count_condition_resource_gain",
                "regex": "\\b([^。]+)の([^。]+)の([^。]+)が(\\d+)枚以上あるかぎり",
                "template": "⟦SOURCE⟧の⟦CONTEXT⟧の⟦CARD_TYPE⟧が⟦NUMBER⟧枚以上あるかぎり",
                "structure": "Live card count condition resource gain"
        },
        {
                "name": "from_among_member_card_reveal_add_optional",
                "regex": "\\bその中から([^。]+)を(\\d+)枚公開して([^。]+)に加えてもよい",
                "template": "その中から⟦CARD_TYPE⟧を⟦NUMBER⟧枚公開して⟦ZONE⟧に加えてもよい",
                "structure": "From among member card reveal add optional"
        },
        {
                "name": "ability_limitation",
                "regex": "\\b([^。]+)では([^。]+)は(\\d+)つまでしか([^。]+)ない",
                "template": "⟦ABILITY⟧では⟦RESOURCE⟧は⟦NUMBER⟧つまでしか⟦LIMITATION⟧ない",
                "structure": "Ability limitation"
        },
        {
                "name": "condition_opponent_draw",
                "regex": "\\bそうした場合、([^。]+)は([^。]+)を(\\d+)枚([^。]+)",
                "template": "そうした場合、⟦OPPONENT⟧は⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
                "structure": "Condition opponent draw"
        },
        {
                "name": "place_at_specific_deck_position",
                "regex": "\\b([^。]+)の([^。]+)から(\\d+)枚目に([^。]+)てもよい",
                "template": "⟦SOURCE⟧の⟦ZONE⟧から⟦POSITION⟧枚目に⟦ACTION⟧てもよい",
                "structure": "Place at specific deck position"
        },
        {
                "name": "side_area_activation",
                "regex": "\\（([^。]+)は([^。]+)に([^。]+)場合のみ([^。]+)する",
                "template": "（⟦ABILITY⟧は⟦ZONE⟧に⟦CONDITION⟧場合のみ⟦ACTION⟧する",
                "structure": "Side area activation"
        },
        {
                "name": "resource_selection",
                "regex": "\\b([^。]+)か([^。]+)か([^。]+)のうち、(\\d+)つを選ぶ",
                "template": "⟦RESOURCE1⟧か⟦RESOURCE2⟧か⟦RESOURCE3⟧のうち、⟦NUMBER⟧つを選ぶ",
                "structure": "Resource selection"
        },
        {
                "name": "deck_top_look",
                "regex": "\\b([^。]+)の([^。]+)の上から([^。]+)を(\\d+)枚見る",
                "template": "⟦SOURCE⟧の⟦ZONE⟧の上から⟦RESOURCE⟧を⟦NUMBER⟧枚見る",
                "structure": "Deck top look"
        },
        {
                "name": "summon_from_discard",
                "regex": "\\b([^。]+)を([^。]+)から([^。]+)に([^。]+)させる",
                "template": "⟦CARD⟧を⟦SOURCE⟧から⟦DESTINATION⟧に⟦ACTION⟧させる",
                "structure": "Summon from discard"
        },
        {
                "name": "draw_until_condition",
                "regex": "\\b([^。]+)が(\\d+)枚になるまで([^。]+)を([^。]+)",
                "template": "⟦ZONE⟧が⟦NUMBER⟧枚になるまで⟦CARD_TYPE⟧を⟦ACTION⟧",
                "structure": "Draw until condition"
        },
        {
                "name": "condition_action_period",
                "regex": "\\b([^。]+)が([^。]+)場合、([^。]+)を([^。]+)。",
                "template": "⟦SUBJECT⟧が⟦CONDITION⟧場合、⟦TARGET⟧を⟦ACTION⟧。",
                "structure": "Condition action period"
        },
        {
                "name": "hand_card_cost_reduce",
                "regex": "\\b([^。]+)にある([^。]+)の([^。]+)は(\\d+)減る",
                "template": "⟦ZONE⟧にある⟦CARD⟧の⟦ATTRIBUTE⟧は⟦NUMBER⟧減る",
                "structure": "Hand card cost reduce"
        },
        {
                "name": "parenthesized_clause_note",
                "regex": "[（(]([^）)]+)[）)]",
                "template": "（⟦CLAUSE⟧）",
                "structure": "Parenthesized clause note"
        },
        {
                "name": "bullet_draw",
                "regex": "・カードを1枚引く。",
                "template": "・カードを1枚引く。",
                "structure": "Bullet draw"
        },
        {
                "name": "bullet_cost_heart_reduce",
                "regex": "・このカードの必要ハートを([^。]+)減らす。",
                "template": "・このカードの必要ハートを⟦MODIFIER⟧減らす。",
                "structure": "Bullet cost heart reduce"
        },
        {
                "name": "energy_under_member_place",
                "regex": "\\b([^。]+)(\\d+)枚を([^。]+)の([^。]+)に置く",
                "template": "⟦RESOURCE⟧⟦NUMBER⟧枚を⟦TARGET⟧の⟦LOCATION⟧に置く",
                "structure": "Energy under member place"
        },
        {
                "name": "optional_card_discard",
                "regex": "\\b([^。]+)はその([^。]+)を([^。]+)に置いてもよい",
                "template": "⟦PLAYER⟧はその⟦CARD⟧を⟦DESTINATION⟧に置いてもよい",
                "structure": "Optional card discard"
        },
        {
                "name": "turn_member_not_moved_condition",
                "regex": "\\b([^。]+)に([^。]+)が([^。]+)していないかぎり",
                "template": "⟦TURN⟧に⟦TARGET⟧が⟦ACTION⟧していないかぎり",
                "structure": "Turn member not moved condition"
        },
        {
                "name": "card_placement_restriction",
                "regex": "\\b([^。]+)は([^。]+)に([^。]+)ことができない",
                "template": "⟦CARD⟧は⟦ZONE⟧に⟦ACTION⟧ことができない",
                "structure": "Card placement restriction"
        },
        {
                "name": "discard_all_revealed_cards",
                "regex": "\\b([^。]+)した([^。]+)をすべて([^。]+)に置く",
                "template": "⟦ACTION⟧した⟦CARD_TYPE⟧をすべて⟦DESTINATION⟧に置く",
                "structure": "Discard all revealed cards"
        },
        {
                "name": "from_among_place_deck_top_with_remainder",
                "regex": "\\bその中から好きな枚数を好きな順番で([^。]+)の上に置き、",
                "template": "その中から好きな枚数を好きな順番で⟦ZONE⟧の上に置き、",
                "structure": "From among place deck top with remainder"
        },
        {
                "name": "summon_to_empty_area",
                "regex": "\\b([^。]+)のいない([^。]+)に([^。]+)させる",
                "template": "⟦TARGET⟧のいない⟦ZONE⟧に⟦ACTION⟧させる",
                "structure": "Summon to empty area"
        },
        {
                "name": "effect_prevent_state_change",
                "regex": "\\b([^。]+)によっては([^。]+)に([^。]+)ない",
                "template": "⟦CONTEXT⟧によっては⟦STATE⟧に⟦NEGATION⟧ない",
                "structure": "Effect prevent state change"
        },
        {
                "name": "temporary_live_prevention",
                "regex": "\\b([^。]+)まで、([^。]+)は([^。]+)できない",
                "template": "⟦TIME⟧まで、⟦PLAYER⟧は⟦ACTION⟧できない",
                "structure": "Temporary live prevention"
        },
        {
                "name": "member_position_change_optional",
                "regex": "\\b([^。]+)(\\d+)人を([^。]+)させてもよい",
                "template": "⟦TARGET⟧⟦NUMBER⟧人を⟦ACTION⟧させてもよい",
                "structure": "Member position change optional"
        },
        {
                "name": "zone_to_zone_optional",
                "regex": "([^。]+)を(\\d+)枚([^。]+)に置いてもよい",
                "template": "⟦SOURCE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に置いてもよい",
                "structure": "Zone to zone optional"
        },
        {
                "name": "appearance_draw",
                "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}カードを1枚引く。",
                "template": "{{toujyou.png|登場}}カードを1枚引く。",
                "structure": "Appearance draw"
        },
        {
                "name": "appearance_member_move_optional",
                "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}自分のステージにいる(?:この|その)?メンバーを、それぞれ好きなエリアに移動させてもよい。",
                "template": "{{toujyou.png|登場}}自分のステージにいるメンバーを、それぞれ好きなエリアに移動させてもよい。",
                "structure": "Appearance member move optional"
        },
        {
                "name": "appearance_activate_discarded_member_ability",
                "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}自分の控え室にあるコスト4以下の『([^』]+)』の([^。]+)を1枚選ぶ。そのカードの\\{\\{toujyou\\.png\\|登場\\}\\}能力1つを発動させる。",
                "template": "{{toujyou.png|登場}}自分の控え室にあるコスト4以下の『⟦GROUP⟧』の⟦CARD_TYPE⟧を1枚選ぶ。そのカードの{{toujyou.png|登場}}能力1つを発動させる。",
                "structure": "Appearance activate discarded member ability"
        },
        {
                "name": "activation_cost_zone_to_zone",
                "regex": "([^。]+)を([^。]+)から([^。]+)に置く",
                "template": "⟦COST_TARGET⟧を⟦SOURCE_ZONE⟧から⟦DESTINATION_ZONE⟧に置く",
                "structure": "Activation cost zone to zone"
        },
        {
                "name": "ability_less_card",
                "regex": "\\b([^。]+)を([^。]+)ない([^。]+)",
                "template": "⟦ATTRIBUTE⟧を⟦NEGATION⟧ない⟦CARD_TYPE⟧",
                "structure": "Ability less card"
        },
        {
                "name": "energy_activation",
                "regex": "\\b([^。]+)を(\\d+)枚([^。]+)にする",
                "template": "⟦RESOURCE⟧を⟦NUMBER⟧枚⟦STATE⟧にする",
                "structure": "Energy activation"
        },
        {
                "name": "duration_gain_ability",
                "regex": "(?:ライブ(?:開始|終了)時|[^。]+)終了時まで、「([^」]+)」を得る。",
                "template": "⟦EVENT⟧終了時まで、「⟦ABILITY⟧」を得る。",
                "structure": "Duration gain ability"
        },
        {
                "name": "trigger_energy_colon_action",
                "regex": "(\\{?\\{[^}]+\\.png\\|[^}]+\\}\\}?)(\\{?\\{[^}]+\\.png\\|[^}]+\\}\\}?)+支払ってもよい：([^。]+)。",
                "template": "⟦TRIGGER⟧⟦ENERGY⟧支払ってもよい：⟦ACTION⟧。",
                "structure": "Trigger energy colon action"
        },
        {
                "name": "trigger_energy_optional_per_resource_score",
                "regex": "(\\{?\\{[^}]+\\.png\\|[^}]+\\}\\}?)(\\{?\\{[^}]+\\.png\\|[^}]+\\}\\}?)+を好きな数支払ってもよい：([^。]+)支払った([^。]+)(\\d+)つにつき、([^。]+)",
                "template": "⟦TRIGGER⟧⟦ENERGY⟧を好きな数支払ってもよい：⟦PREFIX⟧支払った⟦RESOURCE⟧⟦NUMBER⟧つにつき、⟦ACTION⟧。",
                "structure": "Trigger energy optional per resource score"
        },
        {
                "name": "comma_separated_action",
                "regex": "\\b([^：]+)、([^：]+)を([^：]+)。",
                "template": "⟦CONDITION⟧、⟦TARGET⟧を⟦ACTION⟧。",
                "structure": "Comma separated action"
        },
        {
                "name": "trigger_position_change_area",
                "regex": "(\\{?\\{[^}]+\\.png\\|[^}]+\\}\\}?)(\\{?\\{[^}]+\\.png\\|[^}]+\\}\\}?)*：([^。]+)を『([^』]+)』か『([^』]+)』の([^。]+)が([^。]+)エリアに([^。]+)。",
                "template": "⟦TRIGGER⟧⟦ENERGY⟧：⟦TARGET⟧を『⟦GROUP1⟧』か『⟦GROUP2⟧』の⟦MEMBER⟧が⟦CONDITION⟧エリアに⟦ACTION⟧。",
                "structure": "Trigger position change area"
        },
        {
                "name": "score_modify",
                "regex": "([^：]+)の([^：]+)を([^：]+)する",
                "template": "⟦TARGET⟧の⟦ATTRIBUTE⟧を⟦MODIFIER⟧する",
                "structure": "Score modify"
        },
        {
                "name": "selected_resource_gain",
                "regex": "\\b([^。]+)まで、([^。]+)を(\\d+)つ得る",
                "template": "⟦SELECTED⟧⟦RESOURCE⟧を⟦NUMBER⟧つ得る",
                "structure": "Selected resource gain"
        },
        {
                "name": "from_among_add_simple",
                "regex": "\\bその中から(\\d+)枚を([^。]+)に加え、",
                "template": "その中から⟦NUMBER⟧枚を⟦ZONE⟧に加え、",
                "structure": "From among add simple"
        },
        {
                "name": "member_state_condition",
                "regex": "\\b([^。]+)が([^。]+)であるかぎり",
                "template": "⟦MEMBER⟧が⟦STATE⟧であるかぎり",
                "structure": "Member state condition"
        },
        {
                "name": "position_change_optional",
                "regex": "\\b([^。]+)を([^。]+)してもよい",
                "template": "⟦TARGET⟧を⟦ACTION⟧してもよい",
                "structure": "Position change optional"
        },
        {
                "name": "ask_question",
                "regex": "\\b([^。]+)に([^。]+)と聞く。",
                "template": "⟦TARGET⟧に⟦QUESTION⟧と聞く。",
                "structure": "Ask question"
        },
        {
                "name": "player_selection",
                "regex": "\\b([^。]+)か([^。]+)を選ぶ",
                "template": "⟦PLAYER1⟧か⟦PLAYER2⟧を選ぶ",
                "structure": "Player selection"
        },
        {
                "name": "face_up_placement",
                "regex": "\\b([^。]+)で([^。]+)に置く",
                "template": "⟦STATE⟧で⟦ZONE⟧に置く",
                "structure": "Face up placement"
        },
        {
                "name": "auto_trigger_cost_group_baton_touch",
                "regex": "(\\{?\\{[^}]+\\.png\\|[^}]+\\}\\}?)このメンバーがコスト(\\d+)以上の『([^』]+)』のメンバーとバトンタッチして控え室に置かれた",
                "template": "⟦TRIGGER⟧このメンバーがコスト⟦COST⟧以上の『⟦GROUP⟧』のメンバーとバトンタッチして控え室に置かれた",
                "structure": "Auto trigger cost group baton touch"
        },
        {
                "name": "turn1_energy_card_draw",
                "regex": "\\{\\{kidou\\.png\\|起動\\}\\}\\{\\{turn1\\.png\\|ターン1回\\}\\}\\{\\{icon_energy\\.png\\|E\\}\\}\\{\\{icon_energy\\.png\\|E\\}\\}：カードを1枚引く。",
                "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。",
                "structure": "Turn 1 energy card draw"
        },
        {
                "name": "live_start_multi_member_blade_gain",
                "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}(?:ライブ(?:開始|終了)時)?まで、自分のステージにいる、「([^」]+)」「([^」]+)」「([^」]+)」のうちのメンバー1人と、これにより選んだメンバー以外の『([^』]+)』のメンバー1人は、\\{\\{icon_blade\\.png\\|ブレード\\}\\}を得る。",
                "template": "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、「⟦NAME1⟧」「⟦NAME2⟧」「⟦NAME3⟧」のうちのメンバー1人と、これにより選んだメンバー以外の『⟦GROUP⟧』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。",
                "structure": "Live start multi member blade gain"
        },
        {
                "name": "live_start_distinct_group_heart_gain",
                "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}自分のステージにグループ名がそれぞれ異なるメンバーが(\\d+)人以上いる場合、(?:ライブ(?:開始|終了)時)?まで、自分のセンターエリアにいるメンバーは\\{\\{icon_all\\.png\\|ハート\\}\\}を得る。",
                "template": "{{live_start.png|ライブ開始時}}自分のステージにグループ名がそれぞれ異なるメンバーが⟦NUMBER⟧人以上いる場合、ライブ終了時まで、自分のセンターエリアにいるメンバーは{{icon_all.png|ハート}}を得る。",
                "structure": "Live start distinct group heart gain"
        },
        {
                "name": "live_start_energy_payment_per_energy_gain",
                "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}\\{\\{icon_energy\\.png\\|E\\}\\}を(\\d+)つまで支払ってもよい：(?:ライブ(?:開始|終了)時)?まで、支払った\\{\\{icon_energy\\.png\\|E\\}\\}につき、\\{\\{icon_blade\\.png\\|ブレード\\}\\}を得る。",
                "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}を⟦NUMBER⟧つまで支払ってもよい：ライブ終了時まで、支払った{{icon_energy.png|E}}につき、{{icon_blade.png|ブレード}}を得る。",
                "structure": "Live start energy payment per energy gain"
        },
        {
                "name": "live_start_hand_names_optional_discard_per_card_gain",
                "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}手札の「([^」]+)」と「([^」]+)」と「([^」]+)」を、好きな枚数控え室に置いてもよい：(?:ライブ(?:開始|終了)時)?まで、これによって控え室に置いた枚数1枚につき、\\{\\{icon_blade\\.png\\|ブレード\\}\\}を得る。",
                "template": "{{live_start.png|ライブ開始時}}手札の「⟦NAME1⟧」と「⟦NAME2⟧」と「⟦NAME3⟧」を、好きな枚数控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いた枚数1枚につき、{{icon_blade.png|ブレード}}を得る。",
                "structure": "Live start hand names optional discard per card gain"
        },
        {
                "name": "live_start_same_card_name_heart_gain",
                "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}自分のライブ中の『([^』]+)』の([^。]+)を1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、(?:ライブ(?:開始|終了)時)?まで、\\{\\{heart_04\\.png\\|heart04\\}\\}を得る。",
                "template": "{{live_start.png|ライブ開始時}}自分のライブ中の『⟦GROUP⟧』の⟦CARD_TYPE⟧を1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。",
                "structure": "Live start same card name heart gain"
        },
        {
                "name": "live_start_other_group_member_blade_gain",
                "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}\\{\\{icon_energy\\.png\\|E\\}\\}支払ってもよい：(?:ライブ(?:開始|終了)時)?まで、自分のステージにいるほかの『([^』]+)』のメンバーは\\{\\{icon_blade\\.png\\|ブレード\\}\\}を得る。",
                "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のステージにいるほかの『⟦GROUP⟧』のメンバーは{{icon_blade.png|ブレード}}を得る。",
                "structure": "Live start other group member blade gain"
        },
        {
                "name": "live_start_energy_payment_single_blade_gain",
                "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}\\{\\{icon_energy\\.png\\|E\\}\\}支払ってもよい：(?:ライブ(?:開始|終了)時)?まで、\\{\\{icon_blade\\.png\\|ブレード\\}\\}を得る。",
                "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。",
                "structure": "Live start energy payment single blade gain"
        },
        {
                "name": "live_start_energy_payment_single_heart_gain",
                "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}\\{\\{icon_energy\\.png\\|E\\}\\}支払ってもよい：(?:ライブ(?:開始|終了)時)?まで、\\{\\{heart_02\\.png\\|heart02\\}\\}を得る。",
                "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_02.png|heart02}}を得る。",
                "structure": "Live start energy payment single heart gain"
        },
        {
                "name": "live_start_energy_payment_multi_blade_gain",
                "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}(\\{\\{icon_energy\\.png\\|E\\}\\}){6}支払ってもよい：(?:ライブ(?:開始|終了)時)?まで、(\\{\\{icon_blade\\.png\\|ブレード\\}\\}){3}を得る。",
                "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
                "structure": "Live start energy payment multi blade gain"
        },
        {
                "name": "live_start_no_blade_heart_condition_gain",
                "regex": "\\{\\{jidou\\.png\\|自動\\}\\}\\{\\{turn1\\.png\\|ターン1回\\}\\}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、(?:ライブ(?:開始|終了)時)?終了時まで、\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}を得る。",
                "template": "{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_XX.png|heartXX}}を得る。",
                "structure": "No blade heart condition gain"
        },
        {
                "name": "live_start_moved_member_blade_gain",
                "regex": "(?:\\{\\{live_start\\.png\\|ライブ開始時\\}\\}|\\{\\{live_success\\.png\\|ライブ成功時\\}\\})(?:ライブ(?:開始|終了)時)?まで、自分のステージにいる、このターン中にエリアを移動したメンバーは\\{\\{icon_blade\\.png\\|ブレード\\}\\}を得る。",
                "template": "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、このターン中にエリアを移動したメンバーは{{icon_blade.png|ブレード}}を得る。",
                "structure": "Live start moved member blade gain"
        },
        {
                "name": "live_start_energy_under_member_heart_gain",
                "regex": "(?:\\{\\{live_start\\.png\\|ライブ開始時\\}\\}|\\{\\{live_success\\.png\\|ライブ成功時\\}\\})自分のステージに([^。]+)が下にあるメンバーがいる場合、(?:ライブ(?:開始|終了)時)?まで、\\{\\{heart_01\\.png\\|heart01\\}\\}を得る。",
                "template": "{{live_start.png|ライブ開始時}}自分のステージに⟦CARD_TYPE⟧が下にあるメンバーがいる場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。",
                "structure": "Live start energy under member heart gain"
        },
        {
                "name": "turn1_discard_draw_live_card_add",
                "regex": "\\{\\{kidou\\.png\\|起動\\}\\}\\{\\{turn1\\.png\\|ターン1回\\}\\}手札を1枚控え室に置く：自分の控え室にある([^。]+)を1枚選び、そのカードのスコアに等しい数の\\{\\{icon_energy\\.png\\|E\\}\\}を支払ってもよい。そうした場合、その([^。]+)を手札に加える。",
                "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：自分の控え室にある⟦CARD_TYPE⟧を1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。そうした場合、その⟦CARD_TYPE⟧を手札に加える。",
                "structure": "Turn 1 discard draw live card add"
        },
        {
                "name": "turn1_cost4_member_discard_activate_ability",
                "regex": "\\{\\{kidou\\.png\\|起動\\}\\}\\{\\{turn1\\.png\\|ターン1回\\}\\}手札のコスト4以下の『([^』]+)』の([^。]+)を1枚控え室に置く：これにより控え室に置いた([^。]+)の\\{\\{toujyou\\.png\\|登場\\}\\}能力1つを発動させる。",
                "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『⟦GROUP⟧』の⟦CARD_TYPE⟧を1枚控え室に置く：これにより控え室に置いた⟦CARD_TYPE⟧の{{toujyou.png|登場}}能力1つを発動させる。",
                "structure": "Turn 1 cost 4 member discard activate ability"
        },
        {
                "name": "remainder_place",
                "regex": "\\b残りを([^。]+)に置く",
                "template": "残りを⟦ZONE⟧に置く",
                "structure": "Remainder place"
        }
]

LITERAL_PATTERNS = [
    {
        "name": "turn1_cost4_member_discard_activate_ability",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『⟦GROUP⟧』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる。",
        "structure": "Turn 1 cost 4 member discard activate ability",
    },
    {
        "name": "turn1_discard_draw_live_card_add",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：自分の控え室にあるライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。そうした場合、そのライブカードを手札に加える。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：自分の控え室にあるライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。そうした場合、そのライブカードを手札に加える。",
        "structure": "Turn 1 discard draw live card add",
    },
    {
        "name": "live_start_multi_member_blade_gain",
        "literal": "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、「澁谷かのん」「ウィーン・マルガレーテ」「鬼塚冬毬」のうちのメンバー1人と、これにより選んだメンバー以外の『Liella!』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、「⟦NAME1⟧」「⟦NAME2⟧」「⟦NAME3⟧」のうちのメンバー1人と、これにより選んだメンバー以外の『⟦GROUP⟧』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。",
        "structure": "Live start multi member blade gain",
    },
    {
        "name": "live_start_distinct_group_heart_gain",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにグループ名がそれぞれ異なるメンバーが3人以上いる場合、ライブ終了時まで、自分のセンターエリアにいるメンバーは{{icon_all.png|ハート}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにグループ名がそれぞれ異なるメンバーが⟦NUMBER⟧人以上いる場合、ライブ終了時まで、自分のセンターエリアにいるメンバーは{{icon_all.png|ハート}}を得る。",
        "structure": "Live start distinct group heart gain",
    },
    {
        "name": "live_start_energy_payment_per_energy_gain",
        "literal": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}を2つまで支払ってもよい：ライブ終了時まで、支払った{{icon_energy.png|E}}につき、{{icon_blade.png|ブレード}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}を⟦NUMBER⟧つまで支払ってもよい：ライブ終了時まで、支払った{{icon_energy.png|E}}につき、{{icon_blade.png|ブレード}}を得る。",
        "structure": "Live start energy payment per energy gain",
    },
    {
        "name": "live_start_two_energy_blade_gain_literal",
        "literal": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。",
        "structure": "Live start two energy blade gain literal",
    },
    {
        "name": "live_start_two_energy_heart_gain_literal",
        "literal": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_04.png|heart04}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_04.png|heart04}}を得る。",
        "structure": "Live start two energy heart gain literal",
    },
    {
        "name": "live_start_hand_names_optional_discard_per_card_gain",
        "literal": "{{live_start.png|ライブ開始時}}手札の「渡辺曜」と「鬼塚夏美」と「大沢瑠璃乃」を、好きな枚数控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いた枚数1枚につき、{{icon_blade.png|ブレード}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}手札の「⟦NAME1⟧」と「⟦NAME2⟧」と「⟦NAME3⟧」を、好きな枚数控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いた枚数1枚につき、{{icon_blade.png|ブレード}}を得る。",
        "structure": "Live start hand names optional discard per card gain",
    },
    {
        "name": "live_start_same_card_name_heart_gain",
        "literal": "{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}自分のライブ中の『⟦GROUP⟧』の⟦CARD_TYPE⟧を1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。",
        "structure": "Live start same card name heart gain",
    },
    {
        "name": "live_start_other_group_member_blade_gain",
        "literal": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のステージにいるほかの『虹ヶ咲』のメンバーは{{icon_blade.png|ブレード}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のステージにいるほかの『⟦GROUP⟧』のメンバーは{{icon_blade.png|ブレード}}を得る。",
        "structure": "Live start other group member blade gain",
    },
    {
        "name": "live_start_energy_payment_single_blade_gain",
        "literal": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。",
        "structure": "Live start energy payment single blade gain",
    },
    {
        "name": "live_start_energy_payment_single_heart_gain",
        "literal": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_02.png|heart02}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_02.png|heart02}}を得る。",
        "structure": "Live start energy payment single heart gain",
    },
    {
        "name": "live_start_energy_payment_multi_blade_gain",
        "literal": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Live start energy payment multi blade gain",
    },
    {
        "name": "live_start_no_blade_heart_condition_gain",
        "literal": "{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_06.png|heart06}}を得る。",
        "template": "{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_XX.png|heartXX}}を得る。",
        "structure": "No blade heart condition gain",
    },
    {
        "name": "live_start_moved_member_blade_gain",
        "literal": "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、このターン中にエリアを移動したメンバーは{{icon_blade.png|ブレード}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、このターン中にエリアを移動したメンバーは{{icon_blade.png|ブレード}}を得る。",
        "structure": "Live start moved member blade gain",
    },
    {
        "name": "live_start_hand_two_card_blade_gain",
        "literal": "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。",
        "structure": "Live start hand two card blade gain",
    },
    {
        "name": "live_start_draw_then_place_top",
        "literal": "{{live_start.png|ライブ開始時}}カードを1枚引いてもよい。そうした場合、手札2枚を好きな順番でデッキの上に置く。",
        "template": "{{live_start.png|ライブ開始時}}カードを1枚引いてもよい。そうした場合、手札2枚を好きな順番でデッキの上に置く。",
        "structure": "Live start draw then place top",
    },
    {
        "name": "bullet_wait_state_member_active_blade_gain",
        "literal": "・ウェイト状態のメンバー1人をアクティブにし、ライブ終了時まで、そのメンバーは{{icon_blade.png|ブレード}}を得る。",
        "template": "・ウェイト状態のメンバー1人をアクティブにし、ライブ終了時まで、そのメンバーは{{icon_blade.png|ブレード}}を得る。",
        "structure": "Bullet wait state member active blade gain",
    },
    {
        "name": "answer_otherwise_member_blade_gain",
        "literal": "回答がそれ以外の場合、ライブ終了時まで、自分と相手のステージにいるメンバーは{{icon_blade.png|ブレード}}を得る。",
        "template": "回答がそれ以外の場合、ライブ終了時まで、自分と相手のステージにいるメンバーは{{icon_blade.png|ブレード}}を得る。",
        "structure": "Answer otherwise member blade gain",
    },
    {
        "name": "jidou_zone_appearance_double_blade_gain",
        "literal": "{{jidou.png|自動}}このカードが表向きでライブカード置き場に置かれたとき、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{jidou.png|自動}}このカードが表向きでライブカード置き場に置かれたとき、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Jidou zone appearance double blade gain",
    },
    {
        "name": "jidou_energy_zone_bladeheart_gain",
        "literal": "{{jidou.png|自動}}カードの効果によって自分のエネルギー置き場にエネルギーカードが置かれるたび、ライブ終了時まで、{{heart_06.png|heart06}}を得る。(相手のカードの効果でも発動する。)",
        "template": "{{jidou.png|自動}}カードの効果によって自分のエネルギー置き場にエネルギーカードが置かれるたび、ライブ終了時まで、{{heart_06.png|heart06}}を得る。(相手のカードの効果でも発動する。)",
        "structure": "Jidou energy zone bladeheart gain",
    },
    {
        "name": "live_start_energy_under_member_heart_gain",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにエネルギーカードが下にあるメンバーがいる場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージに⟦CARD_TYPE⟧が下にあるメンバーがいる場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。",
        "structure": "Live start energy under member heart gain",
    },
    {
        "name": "toujyou_end_of_turn_blade_gain",
        "literal": "{{toujyou.png|登場}}ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。",
        "template": "{{toujyou.png|登場}}ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。",
        "structure": "Toujyou end of turn blade gain",
    },
    {
        "name": "live_start_energy_to_energy_deck_red_heart_gain",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにいるメンバー1人の下にあるエネルギーカードを、好きな枚数エネルギーデッキに置いてもよい。そうした場合、ライブ終了時まで、そのメンバーは、これによって置いたエネルギーカード1枚につき、［赤ハート］［赤ハート］［赤ハート］を得る。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにいるメンバー1人の下にあるエネルギーカードを、好きな枚数エネルギーデッキに置いてもよい。そうした場合、ライブ終了時まで、そのメンバーは、これによって置いたエネルギーカード1枚につき、［赤ハート］［赤ハート］［赤ハート］を得る。",
        "structure": "Live start energy to energy deck red heart gain",
    },
    {
        "name": "toujyou_center_blade_gain",
        "literal": "{{toujyou.png|登場}}{{center.png|センター}}ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{toujyou.png|登場}}{{center.png|センター}}ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Toujyou center blade gain",
    },
    {
        "name": "toujyou_right_side_energy_activate",
        "literal": "{{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。",
        "template": "{{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。",
        "structure": "Toujyou right side energy activate",
    },
    {
        "name": "toujyou_deck_top_three_discard_heart_gain",
        "literal": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。",
        "template": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_XX.png|heartXX}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_XX.png|heartXX}}を得る。",
        "structure": "Toujyou deck top three discard heart gain",
    },
    {
        "name": "toujyou_deck_top_three_discard_heart_gain_01",
        "literal": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_01.png|heart01}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。",
        "template": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_XX.png|heartXX}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_XX.png|heartXX}}を得る。",
        "structure": "Toujyou deck top three discard heart gain 01",
    },
    {
        "name": "toujyou_deck_top_three_discard_heart_gain_05",
        "literal": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_05.png|heart05}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_05.png|heart05}}を得る。",
        "template": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_XX.png|heartXX}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_XX.png|heartXX}}を得る。",
        "structure": "Toujyou deck top three discard heart gain 05",
    },
    {
        "name": "turn1_energy_move_area",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーがいるエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーがいるエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。",
        "structure": "Turn1 energy move area",
    },
    {
        "name": "toujyou_score_total_energy_deck_place",
        "literal": "{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、自分のエネルギーデッキから、エネルギーカードを1枚アクティブ状態で置く。",
        "template": "{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、自分のエネルギーデッキから、エネルギーカードを1枚アクティブ状態で置く。",
        "structure": "Toujyou score total energy deck place",
    },
    {
        "name": "jidou_main_phase_energy_payment_hand_add",
        "literal": "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のメインフェイズの間、自分のカードが1枚以上いずれかの領域から控え室に置かれるたび、{{icon_energy.png|E}}支払ってもよい。そうした場合、それらのカードの中から1枚手札に加える。",
        "template": "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のメインフェイズの間、自分のカードが1枚以上いずれかの領域から控え室に置かれるたび、{{icon_energy.png|E}}支払ってもよい。そうした場合、それらのカードの中から1枚手札に加える。",
        "structure": "Jidou main phase energy payment hand add",
    },
    {
        "name": "center_turn1_wait_select_public_until_top",
        "literal": "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。",
        "template": "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。",
        "structure": "Center turn1 wait select public until top",
    },
    {
        "name": "bullet_move_member_optional",
        "literal": "・自分のステージにいる『SaintSnow』のメンバー1人をポジションチェンジさせる。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)",
        "template": "・自分のステージにいる『SaintSnow』のメンバー1人をポジションチェンジさせる。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)",
        "structure": "Bullet move member optional",
    },
    {
        "name": "jyouji_energy_ten_bladeheart_gain",
        "literal": "{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。",
        "template": "{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。",
        "structure": "Jyouji energy ten bladeheart gain",
    },
    {
        "name": "jyouji_higher_cost_member_blade_gain",
        "literal": "{{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Jyouji higher cost member blade gain",
    },
    {
        "name": "jyouji_live_card_three_count_mixed_gain",
        "literal": "{{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Jyouji live card three count mixed gain",
    },
    {
        "name": "live_start_member_count_heart_reduce",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにいる、このターン中に登場、またはエリアを移動した『5yncri5e!』のメンバー1人につき、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにいる、このターン中に登場、またはエリアを移動した『5yncri5e!』のメンバー1人につき、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。",
        "structure": "Live start member count heart reduce",
    },
    {
        "name": "toujyou_draw_then_move",
        "literal": "{{toujyou.png|登場}}カードを1枚引く。その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。",
        "template": "{{toujyou.png|登場}}カードを1枚引く。その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。",
        "structure": "Toujyou draw then move",
    },
    {
        "name": "kidou_top_three_discard_liella_blade_gain",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：ライブ終了時まで、これにより控え室に置いた『Liella!』のメンバーカード1枚につき、{{icon_blade.png|ブレード}}を得る。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：ライブ終了時まで、これにより控え室に置いた『Liella!』のメンバーカード1枚につき、{{icon_blade.png|ブレード}}を得る。",
        "structure": "Kidou top three discard Liella blade gain",
    },
    {
        "name": "live_start_cost_total_less_draw_top",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを2枚引き、自分の手札を1枚デッキの一番上に置く。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを2枚引き、自分の手札を1枚デッキの一番上に置く。",
        "structure": "Live start cost total less draw top",
    },
    {
        "name": "jidou_main_phase_add_to_hand_dive",
        "literal": "{{jidou.png|自動}}自分のメインフェイズにこのカードが控え室から手札に加えられたとき、自分の手札からカード名が「DIVE!」のライブカード1枚を表向きでライブカード置き場に置いてもよい。そうした場合、次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。",
        "template": "{{jidou.png|自動}}自分のメインフェイズにこのカードが控え室から手札に加えられたとき、自分の手札からカード名が「DIVE!」のライブカード1枚を表向きでライブカード置き場に置いてもよい。そうした場合、次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。",
        "structure": "Jidou main phase add to hand dive",
    },
    {
        "name": "toujyou_wait_member_blade_note",
        "literal": "{{toujyou.png|登場}}このメンバーをウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）",
        "template": "{{toujyou.png|登場}}このメンバーをウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）",
        "structure": "Toujyou wait member blade note",
    },
    {
        "name": "live_start_deck_top_reveal_member_move",
        "literal": "{{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを公開する。公開したカードがコスト9以下のメンバーカードの場合、公開したカードを手札に加え、このメンバーはポジションチェンジする。それ以外の場合、公開したカードを控え室に置く。",
        "template": "{{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを公開する。公開したカードがコスト9以下のメンバーカードの場合、公開したカードを手札に加え、このメンバーはポジションチェンジする。それ以外の場合、公開したカードを控え室に置く。",
        "structure": "Live start deck top reveal member move",
    },
    {
        "name": "jyouji_wait_state_member_cost_reduce",
        "literal": "{{jyouji.png|常時}}自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり、手札にあるこのメンバーカードのコストは2減る。",
        "template": "{{jyouji.png|常時}}自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり、手札にあるこのメンバーカードのコストは2減る。",
        "structure": "Jyouji wait state member cost reduce",
    },
    {
        "name": "live_start_score_total_cond_heart_reduce_then_score_plus",
        "literal": "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。スコアの合計が９以上の場合、さらにこのカードのスコアを+１する。",
        "template": "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。スコアの合計が９以上の場合、さらにこのカードのスコアを+１する。",
        "structure": "Live start score total condition heart reduce then score plus",
    },
    {
        "name": "toujyou_or_live_start_wait_energy_cost_action",
        "literal": "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数がちょうど4つのメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）",
        "template": "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数がちょうど4つのメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）",
        "structure": "Toujyou or live start wait energy cost action",
    },
    {
        "name": "toujyou_hand_three_discard_draw",
        "literal": "{{toujyou.png|登場}}手札を3枚まで控え室に置いてもよい：これにより置いた枚数分カードを引く。",
        "template": "{{toujyou.png|登場}}手札を3枚まで控え室に置いてもよい：これにより置いた枚数分カードを引く。",
        "structure": "Toujyou hand three discard draw",
    },
    {
        "name": "jidou_three_appear_draw_to_five",
        "literal": "{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。",
        "template": "{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。",
        "structure": "Jidou three appear draw to five",
    },
    {
        "name": "jyouji_energy_ten_blade_gain_three",
        "literal": "{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Jyouji energy ten blade gain three",
    },
    {
        "name": "live_success_energy_deck_wait_state_place_opponent_draw",
        "literal": "{{live_success.png|ライブ成功時}}自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置いてもよい。そうした場合、相手はカードを1枚引く。",
        "template": "{{live_success.png|ライブ成功時}}自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置いてもよい。そうした場合、相手はカードを1枚引く。",
        "structure": "Live success energy deck wait state place opponent draw",
    },
    {
        "name": "jidou_three_appear_draw",
        "literal": "{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。",
        "template": "{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。",
        "structure": "Jidou three appear draw",
    },
    {
        "name": "live_start_aqours_member_heart_check_disable_success",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つ{{heart_02.png|heart02}}に、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{live_success.png|ライブ成功時}}能力を無効にする。{{live_success.png|ライブ成功時}}相手は、エネルギーデッキからエネルギーカードを1枚ウェイト状態で置く。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つ{{heart_02.png|heart02}}に、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{live_success.png|ライブ成功時}}能力を無効にする。{{live_success.png|ライブ成功時}}相手は、エネルギーデッキからエネルギーカードを1枚ウェイト状態で置く。",
        "structure": "Live start Aqours member heart check disable success",
    },
    {
        "name": "live_start_aqours_heart_disable_success",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{live_success.png|ライブ成功時}}能力を無効にする。{{live_success.png|ライブ成功時}}相手は、エネルギーデッキからエネルギーカードを1枚ウェイト状態で置く。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{live_success.png|ライブ成功時}}能力を無効にする。{{live_success.png|ライブ成功時}}相手は、エネルギーデッキからエネルギーカードを1枚ウェイト状態で置く。",
        "structure": "Live start Aqours heart disable success",
    },
    {
        "name": "toujyou_main_phase_energy_payment_livecard_place",
        "literal": "{{toujyou.png|登場}}自分のメインフェイズの場合、{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室からライブカードを1枚、表向きでライブカード置き場に置く。次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。",
        "template": "{{toujyou.png|登場}}自分のメインフェイズの場合、{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室からライブカードを1枚、表向きでライブカード置き場に置く。次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。",
        "structure": "Toujyou main phase energy payment livecard place",
    },
    {
        "name": "jyouji_opponent_energy_more_blade_gain",
        "literal": "{{jyouji.png|常時}}相手のエネルギーが自分より多い場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{jyouji.png|常時}}相手のエネルギーが自分より多い場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Jyouji opponent energy more blade gain",
    },
    {
        "name": "toujyou_other_group_member_energy_active",
        "literal": "{{toujyou.png|登場}}自分のステージにほかの『虹ヶ咲』のメンバーがいる場合、エネルギーを1枚アクティブにする。",
        "template": "{{toujyou.png|登場}}自分のステージにほかの『虹ヶ咲』のメンバーがいる場合、エネルギーを1枚アクティブにする。",
        "structure": "Toujyou other group member energy active",
    },
    {
        "name": "live_start_center_member_heart_reduce",
        "literal": "{{live_start.png|ライブ開始時}}自分のセンターエリアに『μ's』のメンバーがいる場合、そのメンバーが持つ{{heart_03.png|heart03}}2つにつき、このカードの必要ハートを{{heart_00.png|heart0}}減らす。この能力では{{heart_00.png|heart0}}は3つまでしか減らない。",
        "template": "{{live_start.png|ライブ開始時}}自分のセンターエリアに『μ's』のメンバーがいる場合、そのメンバーが持つ{{heart_03.png|heart03}}2つにつき、このカードの必要ハートを{{heart_00.png|heart0}}減らす。この能力では{{heart_00.png|heart0}}は3つまでしか減らない。",
        "structure": "Live start center member heart reduce",
    },
    {
        "name": "live_start_aqours_member_blade_score_plus",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバー1人を選ぶ。そのメンバーが持つ{{icon_blade.png|ブレード}}が6つ以上の場合、このカードのスコアを+１する。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバー1人を選ぶ。そのメンバーが持つ{{icon_blade.png|ブレード}}が6つ以上の場合、このカードのスコアを+１する。",
        "structure": "Live start Aqours member blade score plus",
    },
    {
        "name": "live_start_nijigasaki_member_deck_top_loop",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバー1人につき、自分のデッキの上からカードを1枚見る。その中から1枚までをデッキの上に置き、残りを控え室に置く。その後、自分のデッキの一番上のカードを1枚公開する。これによりライブカードを公開した場合、このカードのスコアを+１する。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバー1人につき、自分のデッキの上からカードを1枚見る。その中から1枚までをデッキの上に置き、残りを控え室に置く。その後、自分のデッキの一番上のカードを1枚公開する。これによりライブカードを公開した場合、このカードのスコアを+１する。",
        "structure": "Live start Nijigasaki member deck top loop",
    },
    {
        "name": "live_start_hand_discard_blade_then_draw",
        "literal": "{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。これによりライブカードを控え室に置いた場合、さらにカードを1枚引く。",
        "template": "{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。これによりライブカードを控え室に置いた場合、さらにカードを1枚引く。",
        "structure": "Live start hand discard blade then draw",
    },
    {
        "name": "toujyou_discard_two_livecards_opponent_choose",
        "literal": "{{toujyou.png|登場}}自分の控え室にある、カード名の異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。",
        "template": "{{toujyou.png|登場}}自分の控え室にある、カード名の異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。",
        "structure": "Toujyou discard two livecards opponent choose",
    },
    {
        "name": "toujyou_success_livecard_total_energy_active",
        "literal": "{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、エネルギーを2枚アクティブにする。",
        "template": "{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、エネルギーを2枚アクティブにする。",
        "structure": "Toujyou success livecard total energy active",
    },
    {
        "name": "live_start_aqours_heart_disable_success",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{live_success.png|ライブ成功時}}能力を無効にする。{{live_success.png|ライブ成功時}}相手は、エネルギーデッキからエネルギーカードを1枚ウェイト状態で置く。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{live_success.png|ライブ成功時}}能力を無効にする。{{live_success.png|ライブ成功時}}相手は、エネルギーデッキからエネルギーカードを1枚ウェイト状態で置く。",
        "structure": "Live start Aqours heart disable success",
    },
    {
        "name": "jyouji_cost_group_hand_cost_reduce",
        "regex": "\\{\\{jyouji\\.png\\|常時\\}\\}コスト(\\d+)の『([^』]+)』のメンバーカードを自分の手札から登場させるためのコストは(\\d+)減る。",
        "literal": "{{jyouji.png|常時}}コスト10の『Liella!』のメンバーカードを自分の手札から登場させるためのコストは2減る。",
        "template": "{{jyouji.png|常時}}コスト⟦COST1⟧の『⟦GROUP⟧』のメンバーカードを自分の手札から登場させるためのコストは⟦COST2⟧減る。",
        "structure": "Jyouji cost group hand cost reduce",
    },
    {
        "name": "trigger_position_group_wait_opponent_wait",
        "regex": "\\{\\{(?:toujyou|live_start)\\.png\\|(?:登場|ライブ開始時)\\}\\}/\\{\\{(?:toujyou|live_start)\\.png\\|(?:登場|ライブ開始時)\\}\\}(?:\\{\\{center\\.png\\|センター\\}\\})?『([^』]+)』のメンバー(\\d+)人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー(\\d+)人をウェイトにする。（この能力は(?:センターエリア|エリア)にいる場合のみ発動する。）",
        "literal": "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。）",
        "template": "⟦TRIGGER⟧⟦POSITION⟧『⟦GROUP⟧』のメンバー⟦NUMBER1⟧人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー⟦NUMBER2⟧人をウェイトにする。（この能力は⟦AREA⟧にいる場合のみ発動する。）",
        "structure": "Trigger position group wait opponent wait",
    },
    {
        "name": "kidou_turn1_discard_group_condition_livecard_add",
        "regex": "\\{\\{kidou\\.png\\|起動\\}\\}\\{\\{turn1\\.png\\|ターン1回\\}\\}手札を(\\d+)枚控え室に置く：自分のステージにほかの『([^』]+)』のメンバーがいる場合、自分の控え室から『([^』]+)』のライブカードを(\\d+)枚手札に加える。この能力を起動するためのコストは、自分の成功ライブカード置き場にあるカード(\\d+)枚につき、控え室に置く手札の数が(\\d+)枚減る。",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を3枚控え室に置く：自分のステージにほかの『lilywhite』のメンバーがいる場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力を起動するためのコストは、自分の成功ライブカード置き場にあるカード1枚につき、控え室に置く手札の数が1枚減る。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を⟦NUMBER1⟧枚控え室に置く：自分のステージにほかの『⟦GROUP1⟧』のメンバーがいる場合、自分の控え室から『⟦GROUP2⟧』のライブカードを⟦NUMBER2⟧枚手札に加える。この能力を起動するためのコストは、自分の成功ライブカード置き場にあるカード⟦NUMBER3⟧枚につき、控え室に置く手札の数が⟦NUMBER4⟧枚減る。",
        "structure": "Kidou turn1 discard group condition livecard add",
    },
    {
        "name": "toujyou_hand_discard_opponent_wait",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}手札を(\\d+)枚控え室に置いてもよい：相手のステージにいるコスト(\\d+)以下のメンバーを(\\d+)人までウェイトにする。（ウェイト状態のメンバーが持つ\\{\\{icon_blade\\.png\\|ブレード\\}\\}は、エールで公開する枚数を増やさない。）",
        "literal": "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）",
        "template": "{{toujyou.png|登場}}手札を⟦NUMBER1⟧枚控え室に置いてもよい：相手のステージにいるコスト⟦COST⟧以下のメンバーを⟦NUMBER2⟧人までウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）",
        "structure": "Toujyou hand discard opponent wait",
    },
    {
        "name": "live_success_wait_member_score_plus",
        "literal": "{{live_success.png|ライブ成功時}}自分のステージにいるウェイト状態のメンバー1人につき、このカードのスコアを+１する。",
        "template": "{{live_success.png|ライブ成功時}}自分のステージにいるウェイト状態のメンバー1人につき、このカードのスコアを+１する。",
        "structure": "Live success wait member score plus",
    },
    {
        "name": "kidou_energy_hand_blade_gain",
        "regex": "\\{\\{kidou\\.png\\|起動\\}\\}\\{\\{icon_energy\\.png\\|E\\}\\}\\{\\{icon_energy\\.png\\|E\\}\\}このカードを手札から控え室に置く：カードを(\\d+)枚引き、ライブ終了時まで、自分のステージにいる『([^』]+)』のメンバー(\\d+)人は\\{\\{icon_blade\\.png\\|ブレード\\}\\}を得る。この能力は、このカードが手札にある場合のみ起動できる。",
        "literal": "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを1枚引き、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は{{icon_blade.png|ブレード}}を得る。この能力は、このカードが手札にある場合のみ起動できる。",
        "template": "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを⟦NUMBER1⟧枚引き、ライブ終了時まで、自分のステージにいる『⟦GROUP⟧』のメンバー⟦NUMBER2⟧人は{{icon_blade.png|ブレード}}を得る。この能力は、このカードが手札にある場合のみ起動できる。",
        "structure": "Kidou energy hand blade gain",
    },
    {
        "name": "live_start_name_different_score_plus",
        "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}自分のステージにいる名前の異なる『([^』]+)』のメンバー(\\d+)人につき、このカードのスコアを\\+(\\d+)する。",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにいる名前の異なる『μ's』のメンバー1人につき、このカードのスコアを+1する。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにいる名前の異なる『⟦GROUP⟧』のメンバー⟦NUMBER1⟧人につき、このカードのスコアを+⟦SCORE⟧する。",
        "structure": "Live start name different score plus",
    },
    {
        "name": "kidou_turn1_energy_zone_move_energy_active",
        "regex": "\\{\\{kidou\\.png\\|起動\\}\\}\\{\\{turn1\\.png\\|ターン1回\\}\\}エネルギー置き場にあるエネルギー(\\d+)枚をこのメンバーの下に置く：エネルギーを(\\d+)枚アクティブにする。",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：エネルギーを2枚アクティブにする。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー⟦NUMBER1⟧枚をこのメンバーの下に置く：エネルギーを⟦NUMBER2⟧枚アクティブにする。",
        "structure": "Kidou turn1 energy zone move energy active",
    },
    {
        "name": "toujyou_wait_group_energy_active",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}このメンバーをウェイトにしてもよい：自分のステージにいる『([^』]+)』のメンバー(\\d+)人につき、エネルギーを(\\d+)枚アクティブにする。",
        "literal": "{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のステージにいる『μ's』のメンバー1人につき、エネルギーを1枚アクティブにする。",
        "template": "{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のステージにいる『⟦GROUP⟧』のメンバー⟦NUMBER1⟧人につき、エネルギーを⟦NUMBER2⟧枚アクティブにする。",
        "structure": "Toujyou wait group energy active",
    },
    {
        "name": "jyouji_side_heart_gain",
        "regex": "\\{\\{jyouji\\.png\\|常時\\}\\}【(?:左サイド|右サイド)】\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}(?:\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}){2,}を得る。",
        "literal": "{{jyouji.png|常時}}【左サイド】{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。",
        "template": "{{jyouji.png|常時}}【⟦SIDE⟧】{{heart_XX.png|heartXX}}を得る。",
        "structure": "Jyouji side heart gain",
    },
    {
        "name": "jyouji_right_side_heart_gain",
        "regex": "\\{\\{jyouji\\.png\\|常時\\}\\}【(?:左サイド|右サイド)】\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}(?:\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}){2,}を得る。",
        "literal": "{{jyouji.png|常時}}【右サイド】{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_05.png|heart05}}を得る。",
        "template": "{{jyouji.png|常時}}【⟦SIDE⟧】{{heart_XX.png|heartXX}}を得る。",
        "structure": "Jyouji side heart gain",
    },
    {
        "name": "toujyou_or_live_start_energy_payment_select_one",
        "literal": "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：以下から1つを選ぶ。",
        "template": "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：以下から1つを選ぶ。",
        "structure": "Toujyou or live start energy payment select one",
    },
    {
        "name": "jyouji_position_blade_gain",
        "regex": "\\{\\{jyouji\\.png\\|常時\\}\\}ステージの(?:センターエリア|エリア)にいる場合、\\{\\{icon_blade\\.png\\|ブレード\\}\\}(?:\\{\\{icon_blade\\.png\\|ブレード\\}\\})+を得る。",
        "literal": "{{jyouji.png|常時}}ステージのセンターエリアにいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{jyouji.png|常時}}ステージの⟦POSITION⟧にいる場合、{{icon_blade.png|ブレード}}を得る。",
        "structure": "Jyouji position blade gain",
    },
    {
        "name": "jidou_no_live_cards_reveal_redo_ally_blades",
        "literal": "{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。",
        "template": "{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。",
        "structure": "Jidou no live cards reveal redo ally blades",
    },
    {
        "name": "toujyou_deck_look_add",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}このメンバーをウェイトにし、手札を(\\d+)枚控え室に置いてもよい：自分のデッキの上からカードを(\\d+)枚見る。その中から(\\d+)枚を手札に加える。残りを控え室に置く。",
        "literal": "{{toujyou.png|登場}}このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加える。残りを控え室に置く。",
        "template": "{{toujyou.png|登場}}このメンバーをウェイトにし、手札を⟦NUMBER1⟧枚控え室に置いてもよい：自分のデッキの上からカードを⟦NUMBER2⟧枚見る。その中から⟦NUMBER3⟧枚を手札に加える。残りを控え室に置く。",
        "structure": "Toujyou deck look add",
    },
    {
        "name": "toujyou_score_total_deck_look_group_add",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}自分の成功ライブカード置き場にあるカードのスコアの合計が(\\d+)以上の場合、自分のデッキの上からカードを(\\d+)枚見る。その中から『([^』]+)』のメンバーカードを(\\d+)枚公開して手札に加えてもよい。残りを控え室に置く。",
        "literal": "{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が10以上の場合、自分のデッキの上からカードを3枚見る。その中から『μ's』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。",
        "template": "{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が⟦NUMBER1⟧以上の場合、自分のデッキの上からカードを⟦NUMBER2⟧枚見る。その中から『⟦GROUP⟧』のメンバーカードを⟦NUMBER3⟧枚公開して手札に加えてもよい。残りを控え室に置く。",
        "structure": "Toujyou score total deck look group add",
    },
    {
        "name": "live_start_success_card_total_heart_reduce",
        "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}自分の成功ライブカード置き場にあるカード(\\d+)枚につき、このカードを成功させるための必要ハートは\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}(?:\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\})+少なくなる。",
        "literal": "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード1枚につき、このカードを成功させるための必要ハートは{{heart_01.png|heart01}}少なくなる。",
        "template": "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード⟦NUMBER⟧枚につき、このカードを成功させるための必要ハートは{{heart_XX.png|heartXX}}少なくなる。",
        "structure": "Live start success card total heart reduce",
    },
    {
        "name": "kidou_turn1_shuffle_members_active_energy",
        "regex": "\\{\\{kidou\\.png\\|起動\\}\\}\\{\\{turn1\\.png\\|ターン1回\\}\\}自分の控え室にある(?:「([^」]+)」(?:と「([^」]+)」){2,})を、合計(\\d+)枚をシャッフルしてデッキの一番下に置く：エネルギーを(\\d+)枚までアクティブにする。",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}自分の控え室にある「園田海未」と「津島善子」と「天王寺璃奈」を、合計6枚をシャッフルしてデッキの一番下に置く：エネルギーを6枚までアクティブにする。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}自分の控え室にある⟦MEMBERS⟧を、合計⟦NUMBER1⟧枚をシャッフルしてデッキの一番下に置く：エネルギーを⟦NUMBER2⟧枚までアクティブにする。",
        "structure": "Kidou turn1 shuffle members active energy",
    },
    {
        "name": "jyouji_live_cards_no_abilities_heart_gain",
        "regex": "\\{\\{jyouji\\.png\\|常時\\}\\}自分のライブ中のライブカードに、\\{\\{live_start\\.png\\|ライブ開始時\\}\\}能力も\\{\\{live_success\\.png\\|ライブ成功時\\}\\}能力も持たないカードがあるかぎり、\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}(?:\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\})+を得る。",
        "literal": "{{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。",
        "template": "{{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあるかぎり、{{heart_XX.png|heartXX}}を得る。",
        "structure": "Jyouji live cards no abilities heart gain",
    },
    {
        "name": "toujyou_other_group_member_draw",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}自分のステージにほかの『([^』]+)』のメンバーがいる場合、カードを(\\d+)枚引く。",
        "literal": "{{toujyou.png|登場}}自分のステージにほかの『虹ヶ咲』のメンバーがいる場合、カードを1枚引く。",
        "template": "{{toujyou.png|登場}}自分のステージにほかの『⟦GROUP⟧』のメンバーがいる場合、カードを⟦NUMBER⟧枚引く。",
        "structure": "Toujyou other group member draw",
    },
    {
        "name": "toujyou_hand_card_discard_draw",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}手札の([^。]+)を(\\d+)枚控え室に置いてもよい：カードを(\\d+)枚引く。",
        "literal": "{{toujyou.png|登場}}手札のライブカードを1枚控え室に置いてもよい：カードを3枚引く。",
        "template": "{{toujyou.png|登場}}手札の⟦CARD_TYPE⟧を⟦NUMBER1⟧枚控え室に置いてもよい：カードを⟦NUMBER2⟧枚引く。",
        "structure": "Toujyou hand card discard draw",
    },
    {
        "name": "toujyou_success_total_score_draw",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}自分の成功ライブカード置き場にあるカードのスコアの合計が(\\d+)以上の場合、カードを(\\d+)枚引く。",
        "literal": "{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が10以上の場合、カードを1枚引く。",
        "template": "{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が⟦SCORE⟧以上の場合、カードを⟦NUMBER⟧枚引く。",
        "structure": "Toujyou success total score draw",
    },
    {
        "name": "kidou_turn1_energy_to_under_member_draw_heart",
        "regex": "\\{\\{kidou\\.png\\|起動\\}\\}\\{\\{turn1\\.png\\|ターン1回\\}\\}エネルギー置き場にあるエネルギー(\\d+)枚をこのメンバーの下に置く：カードを(\\d+)枚引き、ライブ終了時まで、\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}を得る。",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：カードを1枚引き、ライブ終了時まで、{{heart_01.png|heart01}}を得る。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー⟦NUMBER1⟧枚をこのメンバーの下に置く：カードを⟦NUMBER2⟧枚引き、ライブ終了時まで、{{heart_XX.png|heartXX}}を得る。",
        "structure": "Kidou turn1 energy to under member draw heart",
    },
    {
        "name": "toujyou_this_turn_other_member_moved_draw",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}このターン、自分のステージにいるほかのメンバーがエリアを移動している場合、カードを(\\d+)枚引く。",
        "literal": "{{toujyou.png|登場}}このターン、自分のステージにいるほかのメンバーがエリアを移動している場合、カードを1枚引く。",
        "template": "{{toujyou.png|登場}}このターン、自分のステージにいるほかのメンバーがエリアを移動している場合、カードを⟦NUMBER⟧枚引く。",
        "structure": "Toujyou this turn other member moved draw",
    },
    {
        "name": "live_success_member_heart_total_more_score_plus",
        "regex": "\\{\\{live_success\\.png\\|ライブ成功時\\}\\}自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを\\+(\\d+)する。",
        "literal": "{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを+1する。",
        "template": "{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを+⟦SCORE⟧する。",
        "structure": "Live success member heart total more score plus",
    },
    {
        "name": "live_start_center_member_cost_higher_score_plus",
        "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}自分のセンターエリアにいる『([^』]+)』のメンバーのコストが、相手のセンターエリアにいるメンバーより高い場合、このカードのスコアを\\+(\\d+)する。",
        "literal": "{{live_start.png|ライブ開始時}}自分のセンターエリアにいる『μ's』のメンバーのコストが、相手のセンターエリアにいるメンバーより高い場合、このカードのスコアを+1する。",
        "template": "{{live_start.png|ライブ開始時}}自分のセンターエリアにいる『⟦GROUP⟧』のメンバーのコストが、相手のセンターエリアにいるメンバーより高い場合、このカードのスコアを+⟦SCORE⟧する。",
        "structure": "Live start center member cost higher score plus",
    },
    {
        "name": "live_start_cost_total_less_draw",
        "regex": "\\{\\{live_start\\.png\\|ライブ開始時\\}\\}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを(\\d+)枚引く。",
        "literal": "{{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを1枚引く。",
        "template": "{{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを⟦NUMBER⟧枚引く。",
        "structure": "Live start cost total less draw",
    },
    {
        "name": "kidou_turn1_discard_position_change",
        "regex": "\\{\\{kidou\\.png\\|起動\\}\\}\\{\\{turn1\\.png\\|ターン1回\\}\\}デッキの上からカードを(\\d+)枚控え室に置く：このメンバーはポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：このメンバーはポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを⟦NUMBER⟧枚控え室に置く：このメンバーはポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)",
        "structure": "Kidou turn1 discard position change",
    },
    {
        "name": "jidou_cost_member_draw",
        "regex": "\\{\\{jidou\\.png\\|自動\\}\\}\\{\\{turn1\\.png\\|ターン1回\\}\\}自分のステージにコスト(\\d+)のメンバーが登場したとき、カードを(\\d+)枚引く。",
        "literal": "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにコスト10のメンバーが登場したとき、カードを1枚引く。",
        "template": "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにコスト⟦COST⟧のメンバーが登場したとき、カードを⟦NUMBER⟧枚引く。",
        "structure": "Jidou cost member draw",
    },
    {
        "name": "toujyou_mia_taylor_blade_match",
        "literal": "{{toujyou.png|登場}}相手のステージにいる「ミア・テイラー」以外のメンバーを1人選ぶ。そのメンバーが持つハートと、このメンバーが持つハートの中に同じ色のハートがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。それぞれのメンバーのコストが同じ場合、元々の{{icon_blade.png|ブレード}}の数が同じ場合についても同じことを行う。",
        "template": "{{toujyou.png|登場}}相手のステージにいる「ミア・テイラー」以外のメンバーを1人選ぶ。そのメンバーが持つハートと、このメンバーが持つハートの中に同じ色のハートがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。それぞれのメンバーのコストが同じ場合、元々の{{icon_blade.png|ブレード}}の数が同じ場合についても同じことを行う。",
        "structure": "Toujyou Mia Taylor blade match",
    },
    {
        "name": "kidou_turn1_show_all_hand_search_live",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札をすべて公開する：自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札をすべて公開する：自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。",
        "structure": "Kidou turn1 show all hand search live",
    },
    {
        "name": "live_success_greater_heart_member_draw",
        "literal": "{{live_success.png|ライブ成功時}}自分のステージに、元々持つハートの数より多い数のハートを持つメンバーがいる場合、カードを1枚引く。",
        "template": "{{live_success.png|ライブ成功時}}自分のステージに、元々持つハートの数より多い数のハートを持つメンバーがいる場合、カードを1枚引く。",
        "structure": "Live success greater heart member draw",
    },
    {
        "name": "toujyou_energy_under_member_draw",
        "literal": "{{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを2枚引く。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）",
        "template": "{{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを2枚引く。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）",
        "structure": "Toujyou energy under member draw",
    },
    {
        "name": "opponent_card_effect_activation_note",
        "literal": "(対戦相手のカードの効果でも発動する。)",
        "template": "(対戦相手のカードの効果でも発動する。)",
        "structure": "Opponent card effect activation note",
    },
    {
        "name": "live_success_aqours_member_draw_discard",
        "literal": "{{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバー1人につき、カードを1枚引く。その後、これにより引いた枚数と同じ枚数を手札から控え室に置く。",
        "template": "{{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバー1人につき、カードを1枚引く。その後、これにより引いた枚数と同じ枚数を手札から控え室に置く。",
        "structure": "Live success Aqours member draw discard",
    },
    {
        "name": "kidou_nijigasaki_member_wait_draw",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。",
        "structure": "Kidou nijigasaki member wait draw",
    },
    {
        "name": "toujyou_wait_printemps_draw_discard",
        "literal": "{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：カードを1枚引く。その後、このメンバーが『Printemps』のメンバーからバトンタッチして登場していないかぎり、手札を1枚控え室に置く。",
        "template": "{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：カードを1枚引く。その後、このメンバーが『⟦GROUP⟧』のメンバーからバトンタッチして登場していないかぎり、手札を1枚控え室に置く。",
        "structure": "Toujyou wait Printemps draw discard",
    },
    {
        "name": "jidou_opponent_stage_active_cost4_wait_draw",
        "literal": "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト4以下のメンバーがウェイト状態になったとき、カードを1枚引く。",
        "template": "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト4以下のメンバーがウェイト状態になったとき、カードを1枚引く。",
        "structure": "Jidou opponent stage active cost 4 wait draw",
    },
    {
        "name": "toujyou_saintsnow_energy_payment_blade_gain",
        "literal": "{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から『SaintSnow』のカードを1枚手札に加える。そうした場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から『⟦GROUP⟧』のカードを1枚手札に加える。そうした場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Toujyou SaintSnow energy payment blade gain",
    },
    {
        "name": "live_start_bottom_two_cards_draw_heart_score",
        "literal": "{{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "template": "{{live_start.png|ライブ開始時}}控え室にあるメンバーカード⟦NUMBER⟧枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、⟦NUMBER⟧の場合、カードを1枚引く。合計が⟦NUMBER⟧の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が⟦NUMBER⟧の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "structure": "Live start bottom two cards draw heart score",
    },
    {
        "name": "bullet_energy_activate",
        "literal": "・エネルギーを1枚アクティブにする。",
        "template": "・エネルギーを1枚アクティブにする。",
        "structure": "Bullet energy activate",
    },
    {
        "name": "kidou_show_livecard_opponent_discard_four_blades",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Kidou show livecard opponent discard four blades",
    },
    {
        "name": "toujyou_select_one_from_below",
        "literal": "{{toujyou.png|登場}}以下から1つを選ぶ。",
        "template": "{{toujyou.png|登場}}以下から1つを選ぶ。",
        "structure": "Toujyou select one from below",
    },
    {
        "name": "toujyou_lower_cost_dollchestra_batonpass_blade_gain",
        "literal": "{{toujyou.png|登場}}このメンバーよりコストが低い『DOLLCHESTRA』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{toujyou.png|登場}}このメンバーよりコストが低い『⟦GROUP⟧』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Toujyou lower cost DOLLCHESTRA batonpass blade gain",
    },
    {
        "name": "toujyou_top_four_discard_livecard_blade_gain",
        "literal": "{{toujyou.png|登場}}自分のデッキの上からカードを4枚控え室に置く。それらの中にライブカードがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "template": "{{toujyou.png|登場}}自分のデッキの上からカードを⟦NUMBER⟧枚控え室に置く。それらの中にライブカードがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。",
        "structure": "Toujyou top four discard livecard blade gain",
    },
    {
        "name": "toujyou_draw_discard_one",
        "literal": "{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。",
        "template": "{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。",
        "structure": "Toujyou draw discard one",
    },
    {
        "name": "toujyou_energy_active",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}エネルギーを(\\d+)枚アクティブにする。",
        "literal": "{{toujyou.png|登場}}エネルギーを2枚アクティブにする。",
        "template": "{{toujyou.png|登場}}エネルギーを⟦NUMBER⟧枚アクティブにする。",
        "structure": "Toujyou energy active",
    },
    {
        "name": "toujyou_top_discard",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}デッキの上からカードを(\\d+)枚控え室に置く。",
        "literal": "{{toujyou.png|登場}}デッキの上からカードを5枚控え室に置く。",
        "template": "{{toujyou.png|登場}}デッキの上からカードを⟦NUMBER⟧枚控え室に置く。",
        "structure": "Toujyou top discard",
    },
    {
        "name": "toujyou_lower_cost_batonpass_heart_gain",
        "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}\\{\\{icon_energy\\.png\\|E\\}\\}支払ってもよい：このメンバーよりコストが低い『([^』]+)』のメンバーからバトンタッチして登場した場合、(?:ライブ終了時まで)?、\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}(?:\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\})+を得る。",
        "literal": "{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：このメンバーよりコストが低い『みらくらぱーく！』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{heart_01.png|heart01}}{{heart_01.png|heart01}}を得る。",
        "template": "{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：このメンバーよりコストが低い『⟦GROUP⟧』のメンバーからバトンタッチして登場した場合、⟦DURATION⟧、{{heart_XX.png|heartXX}}を得る。",
        "structure": "Toujyou lower cost batonpass heart gain",
    },
    {
        "name": "jyouji_batonpass_cannot_discard",
        "literal": "{{jyouji.png|常時}}このメンバーはバトンタッチで控え室に置けない。",
        "template": "{{jyouji.png|常時}}このメンバーはバトンタッチで控え室に置けない。",
        "structure": "Jyouji batonpass cannot discard",
    },
    {
        "name": "toujyou_member_cost_13_draw",
        "literal": "{{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。",
        "template": "{{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。",
        "structure": "Toujyou member cost 13 draw",
    },
    {
        "name": "toujyou_energy_six_draw",
        "literal": "{{toujyou.png|登場}}自分のエネルギー6枚につき、カードを1枚引く。",
        "template": "{{toujyou.png|登場}}自分のエネルギー6枚につき、カードを1枚引く。",
        "structure": "Toujyou energy six draw",
    },
    {
        "name": "kidou_discard_two_add_mu_livecard_score6",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合のみ起動できる。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が⟦NUMBER⟧以上の場合のみ起動できる。",
        "structure": "Kidou discard two add mu livecard score 6",
    },
    {
        "name": "kidou_discard_two_add_mu_livecard_score7",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が７以上の場合のみ起動できる。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が⟦NUMBER⟧以上の場合のみ起動できる。",
        "structure": "Kidou discard two add mu livecard score 7",
    },
    {
        "name": "jidou_stage_member_live_start_havent_heart_gain",
        "literal": "{{jidou.png|自動}}自分のステージにいるメンバーの{{live_start.png|ライブ開始時}}能力が解決するたび、そのメンバーが{{icon_all.png|ハート}}を持たない場合、ライブ終了時まで、そのメンバーは{{icon_all.png|ハート}}を得る。",
        "template": "{{jidou.png|自動}}自分のステージにいるメンバーの{{live_start.png|ライブ開始時}}能力が解決するたび、そのメンバーが{{icon_all.png|ハート}}を持たない場合、ライブ終了時まで、そのメンバーは{{icon_all.png|ハート}}を得る。",
        "structure": "Jidou stage member live start havent heart gain",
    },
    {
        "name": "live_start_double_score_gain_quote",
        "literal": "{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "template": "{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "structure": "Live start double score gain quote",
    },
    {
        "name": "jyouji_landonno_stage_all_names_score_plus_quote",
        "literal": "{{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "template": "{{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "structure": "Jyouji landonno stage all names score plus quote",
    },
    {
        "name": "live_start_stage_double_score_gain_quote",
        "literal": "{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "template": "{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "structure": "Live start stage double score gain quote",
    },
    {
        "name": "toujyou_success_score_one_or_less_quote",
        "literal": "{{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "template": "{{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "structure": "Toujyou success score one or less quote",
    },
    {
        "name": "live_start_cost_public_gain_quote",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、⟦NUMBER⟧、⟦NUMBER⟧、⟦NUMBER⟧、⟦NUMBER⟧、⟦NUMBER⟧のいずれかの場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "structure": "Live start cost public gain quote",
    },
    {
        "name": "kidou_center_turn1_wait_score_plus_quote",
        "literal": "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。（この能力はセンターエリアに登場している場合のみ起動できる。）",
        "template": "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。（この能力はセンターエリアに登場している場合のみ起動できる。）",
        "structure": "Kidou center turn1 wait score plus quote",
    },
    {
        "name": "live_success_aqours_all_stage_score_plus_quote",
        "literal": "{{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを+１する。ライブカードが3枚以上ある場合、代わりに合計スコアを+２する。」を得る。",
        "template": "{{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを+１する。ライブカードが3枚以上ある場合、代わりに合計スコアを+２する。」を得る。",
        "structure": "Live success Aqours all stage score plus quote",
    },
    {
        "name": "kidou_turn1_energy_hand_public_live_quote",
        "literal": "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "template": "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。",
        "structure": "Kidou turn1 energy hand public live quote",
    },
    {
        "name": "live_success_member_heart_more_energy_wait_quote",
        "literal": "{{live_success.png|ライブ成功時}}このターン、自分が余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。",
        "template": "{{live_success.png|ライブ成功時}}このターン、自分が余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。",
        "structure": "Live success member heart more energy wait quote",
    },
]

FAMILY_PATTERNS = [
    {
        "name": "live_start_any_blade_gain",
        "prefix": "{{live_start.png|ライブ開始時}}",
        "contains": ["{{icon_blade.png|ブレード}}を得る。"],
        "suffix": "{{icon_blade.png|ブレード}}を得る。",
        "template": "{{live_start.png|ライブ開始時}}…{{icon_blade.png|ブレード}}を得る。",
        "structure": "Live start any blade gain",
    },
    {
        "name": "live_start_any_heart_gain",
        "prefix": "{{live_start.png|ライブ開始時}}",
        "contains": ["{{heart_"],
        "suffix": "を得る。",
        "template": "{{live_start.png|ライブ開始時}}…{{heart_XX.png|heartXX}}を得る。",
        "structure": "Live start any heart gain",
    },
    {
        "name": "jidou_any_blade_gain",
        "prefix": "{{jidou.png|自動}}",
        "contains": ["{{icon_blade.png|ブレード}}を得る。"],
        "suffix": "{{icon_blade.png|ブレード}}を得る。",
        "template": "{{jidou.png|自動}}…{{icon_blade.png|ブレード}}を得る。",
        "structure": "Jidou any blade gain",
    },
    {
        "name": "jidou_any_heart_gain",
        "prefix": "{{jidou.png|自動}}",
        "contains": ["{{heart_"],
        "suffix": "を得る。",
        "template": "{{jidou.png|自動}}…{{heart_XX.png|heartXX}}を得る。",
        "structure": "Jidou any heart gain",
    },
    {
        "name": "toujyou_draw_then_followup",
        "prefix": "{{toujyou.png|登場}}カードを1枚引く。",
        "contains": ["その後、"],
        "suffix": "移動する。",
        "template": "{{toujyou.png|登場}}カードを1枚引く。その後、…移動する。",
        "structure": "Toujyou draw then followup",
    },
    {
        "name": "bullet_blade_gain",
        "prefix": "・",
        "contains": ["{{icon_blade.png|ブレード}}を得る。"],
        "suffix": "{{icon_blade.png|ブレード}}を得る。",
        "template": "・…{{icon_blade.png|ブレード}}を得る。",
        "structure": "Bullet blade gain",
    },
    {
        "name": "bullet_heart_gain",
        "prefix": "・",
        "contains": ["{{heart_"],
        "suffix": "を得る。",
        "template": "・…{{heart_XX.png|heartXX}}を得る。",
        "structure": "Bullet heart gain",
    },
    {
        "name": "live_start_energy_payment_gain",
        "prefix": "{{live_start.png|ライブ開始時}}",
        "contains": ["支払ってもよい：", "ライブ終了時まで、"],
        "suffix": "を得る。",
        "template": "{{live_start.png|ライブ開始時}}…支払ってもよい：…ライブ終了時まで、…を得る。",
        "structure": "Live start energy payment gain",
    },
]

# Process patterns to remove triggers from the start of literals/templates
# process_patterns_triggers()  # DISABLED - will do this more slowly

def check_pattern_overlap(patterns: list[dict[str, Any]], cards_file: Path) -> list[dict[str, Any]]:
    """
    Check for overlap between patterns using actual ability texts.
    Returns a list of overlapping pattern pairs.
    """
    overlaps = []
    
    # Load cards to get actual ability texts
    with open(cards_file, 'r', encoding='utf-8') as f:
        cards = json.load(f)
    
    # Get ability texts from cards
    ability_texts = []
    for card_id, card in cards.items():
        ability = card.get("ability", "")
        if ability:
            ability_texts.append(ability)
    
    # Compile all patterns
    compiled_patterns = []
    for pattern in patterns:
        try:
            compiled = re.compile(pattern["regex"])
            compiled_patterns.append({
                "name": pattern["name"],
                "regex": pattern["regex"],
                "compiled": compiled,
            })
        except re.error as e:
            print(f"ERROR: Invalid regex in pattern '{pattern['name']}': {e}")
    
    # Check for overlaps using actual ability texts (scan all texts)
    for text in ability_texts:
        matches_in_text = []
        for pattern in compiled_patterns:
            matches = list(pattern["compiled"].finditer(text))
            if matches:
                for match in matches:
                    matches_in_text.append({
                        "pattern_name": pattern["name"],
                        "start": match.start(),
                        "end": match.end(),
                        "matched_text": match.group(0),
                    })
        
        # Optimize: Sort matches by start position for linear scan O(n) instead of O(n^2)
        matches_in_text.sort(key=lambda x: x["start"])
        
        # Check for overlapping matches using linear scan
        for i in range(len(matches_in_text)):
            match1 = matches_in_text[i]
            # Only check subsequent matches (they're sorted by start position)
            for j in range(i + 1, len(matches_in_text)):
                match2 = matches_in_text[j]
                # Early termination: if match2 starts after match1 ends, no more overlaps possible
                if match2["start"] >= match1["end"]:
                    break
                # Check if ranges overlap
                if not (match1["end"] <= match2["start"] or match2["end"] <= match1["start"]):
                    overlaps.append({
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "pattern1": match1["pattern_name"],
                        "pattern2": match2["pattern_name"],
                        "match1_text": match1["matched_text"],
                        "match2_text": match2["matched_text"],
                        "overlap_range": (max(match1["start"], match2["start"]), min(match1["end"], match2["end"])),
                    })
    
    return overlaps


def load_cards(cards_file: Path) -> dict[str, dict[str, Any]]:
    with open(cards_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def all_ability_texts(cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    abilities = []
    for card_id, card in cards.items():
        ability = card.get("ability", "")
        if ability:
            # Split ability by newlines to handle multiple abilities per card
            ability_parts = ability.split("\n")
            for part in ability_parts:
                if part.strip():  # Skip empty lines
                    abilities.append({"ability": part.strip(), "card_id": card_id})
    return abilities


def group_unique_abilities(abilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group unique abilities and track which cards have them."""
    unique_abilities = {}
    for ability_data in abilities:
        ability_text = ability_data["ability"]
        card_id = ability_data["card_id"]
        
        if ability_text not in unique_abilities:
            unique_abilities[ability_text] = {
                "ability": ability_text,
                "card_ids": [],
            }
        unique_abilities[ability_text]["card_ids"].append(card_id)
    
    # Convert to list
    return list(unique_abilities.values())


def match_dsl_patterns(texts: list[dict[str, Any]]) -> dict[str, Any]:
    dsl_patterns = DSL_PATTERNS
    
    # Pre-compile regex patterns for performance (compile once, use many times)
    compiled_dsl_patterns = []
    for pattern in dsl_patterns:
        try:
            compiled = re.compile(pattern["regex"])
            compiled_dsl_patterns.append({
                "name": pattern["name"],
                "regex": pattern["regex"],
                "compiled": compiled,
                "structure": pattern.get("structure", ""),
                "template": pattern.get("template", ""),
            })
        except re.error as e:
            print(f"ERROR: Invalid regex in pattern '{pattern['name']}': {e}")

    text_matches = []
    pattern_counts = Counter()
    pattern_variables = {}
    
    total_characters = 0
    total_covered_characters = 0

    for text_data in texts:
        text = text_data.get("ability") or text_data.get("clause", "")
        card_ids = text_data.get("card_ids", [])
        if not text:
            continue
            
        total_characters += len(text)
        matches = []
        
        # Track which positions are already covered by longer patterns
        covered_positions = [False] * len(text)

        def expand_match_span(start, end):
            """Include obvious wrapper characters around a matched clause."""
            while start >= 2 and text[start - 2:start] == "{{":
                start -= 2
            while start > 0 and text[start - 1] in {'・', '"', '「', '（', '('}:
                start -= 1
            while end < len(text) and text[end] in {'、', '：', '。', '）', ')', '』', '"', '」'}:
                end += 1
            for tail in ("を得る。", "を失う。", "を得る", "を失う"):
                if text.startswith(tail, end):
                    end += len(tail)
                    break
            return start, end

        for pattern in LITERAL_PATTERNS:
            literal = pattern["literal"]
            match_start = text.find(literal)
            if match_start == -1:
                continue

            match_end = match_start + len(literal)
            match_start, match_end = expand_match_span(match_start, match_end)
            already_covered = False
            for i in range(match_start, match_end):
                if i < len(covered_positions) and covered_positions[i]:
                    already_covered = True
                    break
            if already_covered:
                continue

            matches.append({
                "pattern_name": pattern["name"],
                "structure": pattern["structure"],
                "template": pattern["template"],
                "matched_text": text[match_start:match_end],
                "start": match_start,
                "end": match_end,
                "variables": [],
            })
            pattern_counts[pattern["name"]] += 1
            if pattern["name"] not in pattern_variables:
                pattern_variables[pattern["name"]] = []
            pattern_variables[pattern["name"]].append([])
            for i in range(match_start, match_end):
                if i < len(covered_positions):
                    covered_positions[i] = True

        for pattern in FAMILY_PATTERNS:
            prefix = pattern["prefix"]
            start = text.find(prefix)
            if start == -1:
                continue

            end_search_start = start + len(prefix)
            suffix = pattern["suffix"]
            end = text.find(suffix, end_search_start)
            if end == -1:
                continue
            end += len(suffix)

            contains_ok = True
            for needle in pattern.get("contains", []):
                if needle not in text[start:end]:
                    contains_ok = False
                    break
            if not contains_ok:
                continue

            start, end = expand_match_span(start, end)

            already_covered = False
            for i in range(start, end):
                if i < len(covered_positions) and covered_positions[i]:
                    already_covered = True
                    break
            if already_covered:
                continue

            matches.append({
                "pattern_name": pattern["name"],
                "structure": pattern["structure"],
                "template": pattern["template"],
                "matched_text": text[start:end],
                "start": start,
                "end": end,
                "variables": [],
            })
            pattern_counts[pattern["name"]] += 1
            if pattern["name"] not in pattern_variables:
                pattern_variables[pattern["name"]] = []
            pattern_variables[pattern["name"]].append([])
            for i in range(start, end):
                if i < len(covered_positions):
                    covered_positions[i] = True

        for pattern in compiled_dsl_patterns:
            for match in pattern["compiled"].finditer(text):
                # Check if this match overlaps with already-covered positions
                match_start = match.start()
                match_end = match.end()
                match_start, match_end = expand_match_span(match_start, match_end)
                
                # Check if any position in this match is already covered
                already_covered = False
                for i in range(match_start, match_end):
                    if i < len(covered_positions) and covered_positions[i]:
                        already_covered = True
                        break
                
                # Skip if already covered by a longer pattern
                if already_covered:
                    continue
                
                # This match is not covered, so add it and mark positions as covered
                variables = list(match.groups())
                
                matches.append({
                    "pattern_name": pattern["name"],
                    "structure": pattern["structure"],
                    "template": pattern["template"],
                    "matched_text": text[match_start:match_end],
                    "start": match_start,
                    "end": match_end,
                    "variables": variables,
                })
                pattern_counts[pattern["name"]] += 1

                if pattern["name"] not in pattern_variables:
                    pattern_variables[pattern["name"]] = []
                pattern_variables[pattern["name"]].append(variables)
                
                # Mark positions as covered
                for i in range(match_start, match_end):
                    if i < len(covered_positions):
                        covered_positions[i] = True

        if matches:
            covered = [False] * len(text)
            for m in matches:
                for i in range(m["start"], m["end"]):
                    if i < len(covered):
                        covered[i] = True
            
            coverage = sum(covered) / len(covered) if covered else 0
            total_covered_characters += sum(covered)
            
            text_matches.append({
                "original": text,
                "matches": matches,
                "coverage": coverage,
                "match_count": len(matches),
                "card_ids": card_ids,
            })
        else:
            text_matches.append({
                "original": text,
                "matches": [],
                "coverage": 0.0,
                "match_count": 0,
                "card_ids": card_ids,
            })

    total_coverage = total_covered_characters / total_characters if total_characters > 0 else 0

    return {
        "total_texts": len(texts),
        "total_characters": total_characters,
        "total_covered_characters": total_covered_characters,
        "total_coverage_percentage": total_coverage * 100,
        "unique_patterns": len(pattern_counts),
        "pattern_counts": dict(pattern_counts),
        "pattern_variables": pattern_variables,
        "text_matches": text_matches,
    }


def extract_abilities(cards_file: Path, rules_file: Path, output_file: Path, metadata_file: Path, show_summary: bool = True) -> dict[str, Any]:
    cards = load_cards(cards_file)
    abilities = all_ability_texts(cards)
    unique_abilities = group_unique_abilities(abilities)

    dsl_pattern_analysis = match_dsl_patterns(unique_abilities)

    result = {
        "schema": "ability_skeletons.v6",
        "source": str(cards_file),
        "rules_source": str(rules_file),
        "metadata_source": str(metadata_file),
        "dsl_pattern_analysis": dsl_pattern_analysis,
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Generate simple output with pattern matching info
    simple_output = generate_simple_output(cards, unique_abilities, dsl_pattern_analysis)
    simple_output_file = output_file.parent / "abilities_extracted_simple.json"
    with open(simple_output_file, 'w', encoding='utf-8') as f:
        json.dump(simple_output, f, ensure_ascii=False, indent=2)

    if show_summary:
        print_summary(dsl_pattern_analysis)

    return result


def generate_simple_output(cards: dict[str, dict[str, Any]], unique_abilities: list[dict[str, Any]], pattern_analysis: dict[str, Any]) -> dict[str, Any]:
    """Generate simple output with pattern matching information."""
    # Create a mapping from ability text to pattern matches
    text_matches_map = {}
    for match in pattern_analysis.get('text_matches', []):
        original = match.get('original', '')
        text_matches_map[original] = match

    simple_abilities = []
    for i, ability_data in enumerate(unique_abilities):
        ability_text = ability_data['ability']
        card_ids = ability_data['card_ids']
        
        # Get card examples (first 5)
        card_examples = []
        for card_id in card_ids[:5]:
            if card_id in cards:
                card = cards[card_id]
                card_name = card.get('name', card_id)
                card_no = card.get('card_no', card_id)
                card_examples.append(f"{card_no} | {card_name}")
        
        # Get pattern matches for this ability
        pattern_match = text_matches_map.get(ability_text, {})
        matches = pattern_match.get('matches', [])
        coverage = pattern_match.get('coverage', 0)
        
        # Format pattern matches
        pattern_matches_output = []
        for match in matches:
            pattern_matches_output.append({
                'pattern_name': match['pattern_name'],
                'structure': match['structure'],
                'template': match['template'],
                'matched_text': match['matched_text'],
                'extracted_variables': match['variables']
            })
        
        simple_abilities.append({
            'jp': ability_text,
            'ability_index': i,
            'card_examples': card_examples,
            'count': len(card_ids),
            'coverage': coverage,
            'pattern_matches': pattern_matches_output
        })
    
    return {
        'total_unique_abilities': len(simple_abilities),
        'abilities': simple_abilities
    }


def print_summary(analysis: dict[str, Any]) -> None:
    print("=" * 80)
    print("PATTERN MATCHING SUMMARY")
    print("=" * 80)
    
    print(f"\nTotal abilities: {analysis.get('total_texts', 0)}")
    print(f"Total characters: {analysis.get('total_characters', 0)}")
    print(f"Total covered characters: {analysis.get('total_covered_characters', 0)}")
    print(f"Total text coverage: {analysis.get('total_coverage_percentage', 0):.1f}%")
    print(f"Unique patterns: {analysis.get('unique_patterns', 0)}")
    
    print("\n" + "=" * 80)
    print("TOP PATTERNS BY MATCH COUNT")
    print("=" * 80)
    
    pattern_counts = analysis.get('pattern_counts', {})
    sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
    
    for pattern, count in sorted_patterns[:20]:
        print(f"{pattern:40s}: {count:4d} matches")
    
    print("\n" + "=" * 80)
    print("EXAMPLE MATCHES (first 5 abilities)")
    print("=" * 80)
    
    text_matches = analysis.get('text_matches', [])
    for i, match in enumerate(text_matches[:5]):
        print(f"\n--- Ability {i+1} ---")
        print(f"Coverage: {match.get('coverage', 0) * 100:.1f}%")
        print(f"Patterns matched: {match.get('match_count', 0)}")
        print(f"Original: {match.get('original', '')[:100]}...")
        
        if match.get('matches'):
            print("Matched patterns:")
            for m in match['matches'][:3]:
                print(f"  - {m['pattern_name']}: {m['matched_text'][:50]}...")
    
    print("\n" + "=" * 80)
    print("NO COVERAGE EXAMPLES (first 5)")
    print("=" * 80)
    
    no_coverage_count = 0
    for match in text_matches:
        if match.get('coverage', 0) == 0:
            print(f"\n--- No Coverage {no_coverage_count + 1} ---")
            print(f"Original: {match.get('original', '')[:100]}...")
            no_coverage_count += 1
            if no_coverage_count >= 5:
                break

    print("\n" + "=" * 80)
    print("UNCOVERED/PARTIALLY COVERED ABILITIES (lowest coverage)")
    print("=" * 80)

    # Debug: Show coverage distribution for ALL abilities
    coverage_values = [m.get('coverage', 0) for m in text_matches]
    print(f"\nCoverage distribution (ALL abilities):")
    print(f"  Total abilities: {len(coverage_values)}")
    print(f"  Min: {min(coverage_values) * 100:.1f}%")
    print(f"  Max: {max(coverage_values) * 100:.1f}%")
    print(f"  Mean: {sum(coverage_values) / len(coverage_values) * 100:.1f}%")
    below_100 = sum(1 for c in coverage_values if c < 1.0)
    print(f"  Abilities below 100%: {below_100}/{len(coverage_values)}")

    # Sort by coverage (ascending) to show least covered first
    sorted_by_coverage = sorted(text_matches, key=lambda x: x.get('coverage', 0))

    # Only show abilities below 100% coverage
    below_100_matches = [m for m in sorted_by_coverage if m.get('coverage', 0) < 1.0]
    print(f"\nShowing {len(below_100_matches)} abilities with <100% coverage:")

    for i, match in enumerate(below_100_matches[:50]):
        print(f"\n--- Ability {i+1} (Coverage: {match.get('coverage', 0) * 100:.1f}%) ---")
        original = match.get('original', '')

        # Build coverage breakdown
        covered = [False] * len(original)
        for m in match.get('matches', []):
            for j in range(m['start'], m['end']):
                if j < len(covered):
                    covered[j] = True

        # Mark covered parts with [COVERED] and uncovered with [UNCOVERED]
        coverage_breakdown = ""
        idx = 0
        while idx < len(original):
            if covered[idx]:
                # Start of covered section
                start = idx
                while idx < len(original) and covered[idx]:
                    idx += 1
                coverage_breakdown += f"[COVERED: {original[start:idx]}]"
            else:
                # Start of uncovered section
                start = idx
                while idx < len(original) and not covered[idx]:
                    idx += 1
                coverage_breakdown += f"[UNCOVERED: {original[start:idx]}]"

        print(f"Coverage breakdown:")
        print(f"  {coverage_breakdown}")
        print(f"Original: {original}")


if __name__ == "__main__":
    # Set up logging to both terminal and file
    import sys
    from datetime import datetime
    
    log_file = Path("../data/extract_abilities_log.txt")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a custom print function that writes to both stdout and file
    class Logger:
        def __init__(self, log_file):
            self.log_file = log_file
            self.terminal = sys.stdout
            self.log = open(log_file, 'w', encoding='utf-8')
            self.log.write(f"=== Pattern Extraction Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
        
        def flush(self):
            self.terminal.flush()
            self.log.flush()
    
    sys.stdout = Logger(log_file)
    
    cards_file = Path("../data/cards.json")
    rules_file = Path("../data/rules.txt")
    output_file = Path("../data/abilities_extracted.json")
    metadata_file = Path("../data/metadata.json")

    # First, check for pattern overlap
    print("=" * 80)
    print("CHECKING FOR PATTERN OVERLAP")
    print("=" * 80)
    overlaps = check_pattern_overlap(DSL_PATTERNS, cards_file)
    
    if overlaps:
        print(f"\nWARNING: Found {len(overlaps)} pattern overlaps!")
        print("\nOverlapping patterns:")
        for i, overlap in enumerate(overlaps[:20]):
            print(f"\n--- Overlap {i+1} ---")
            print(f"Text: {overlap['text']}")
            print(f"Pattern 1: {overlap['pattern1']} matched '{overlap['match1_text']}'")
            print(f"Pattern 2: {overlap['pattern2']} matched '{overlap['match2_text']}'")
            print(f"Overlap range: {overlap['overlap_range']}")
        
        print("\n" + "=" * 80)
        print("OVERLAP DETECTION COMPLETE - PROCEEDING WITH CAUTION")
        print("=" * 80)
    else:
        print("\nNo pattern overlaps detected.")
        print("=" * 80)

    extract_abilities(cards_file, rules_file, output_file, metadata_file)

