"""
Test suite for ability parsing refactor.
This provides regression tests for the parsing logic during refactoring.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.ability_extraction.extract_costs import parse_cost, parse_generic_effect
from tools.ability_extraction.condition_parser import parse_condition

# Load fixtures
with open('tools/ability_extraction/fixtures/extract_fixtures.json', 'r', encoding='utf-8') as f:
    FIXTURES = json.load(f)


def assert_cost_matches(category):
    """Assert parse_cost output for all fixtures in a category."""
    for fixture in FIXTURES[category]:
        triggerless = fixture['triggerless_text']
        expected_cost = fixture['cost']
        actual_cost = parse_cost(triggerless)
        assert actual_cost == expected_cost, (
            f"Cost mismatch for {category}: {triggerless}\n"
            f"Expected: {expected_cost}\n"
            f"Actual:   {actual_cost}"
        )
        print(f"[OK] {category} fixture: {triggerless[:50]}...")


def extract_effect_text(triggerless):
    """Extract the effect text by removing the leading cost prefix."""
    if '：' in triggerless:
        return triggerless.split('：', 1)[1].strip()
    if ':' in triggerless:
        return triggerless.split(':', 1)[1].strip()
    return triggerless


def assert_effect_matches(category):
    """Assert parse_generic_effect output for all fixtures in a category."""
    for fixture in FIXTURES[category]:
        triggerless = fixture['triggerless_text']
        expected_effect = fixture['effect']
        actual_effect = parse_generic_effect(extract_effect_text(triggerless))
        assert actual_effect == expected_effect, (
            f"Effect mismatch for {category}: {triggerless}\n"
            f"Expected: {expected_effect}\n"
            f"Actual:   {actual_effect}"
        )
        print(f"[OK] {category} fixture: {triggerless[:50]}...")

def test_no_cost():
    """Test parsing abilities with no cost."""
    assert_cost_matches('no_cost')

def test_simple_energy_cost():
    """Test parsing abilities with simple energy cost."""
    assert_cost_matches('simple_energy_cost')

def test_member_to_wait_cost():
    """Test parsing abilities with member-to-wait cost."""
    assert_cost_matches('member_to_wait_cost')

def test_reveal_cost():
    """Test parsing abilities with reveal cost."""
    assert_cost_matches('reveal_cost')

def test_simple_single_action():
    """Test parsing abilities with simple single action."""
    assert_effect_matches('simple_single_action')

def test_compound_action_punctuation():
    """Test parsing abilities with compound action split by punctuation."""
    assert_effect_matches('compound_action_punctuation')

def test_conditional_effect():
    """Test parsing abilities with conditional effect."""
    assert_effect_matches('conditional_effect')

def test_position_condition():
    """Test parsing abilities with position-based condition."""
    assert_effect_matches('position_condition')

def test_score_cost_limit_condition():
    """Test parsing abilities with score/cost-limit condition."""
    assert_effect_matches('score_cost_limit_condition')

def test_hand_card_count_comparison():
    """Test parsing hand-count comparison with an explicit 2-card difference."""
    condition = parse_condition('相手の手札の枚数が自分より2枚以上多い')
    assert condition['type'] == 'hand_card_count_at_least_2_more'
    assert condition['value'] == 2
    assert condition['location'] == 'hand'
    assert condition['target'] == 'opponent'

def test_per_unit_condition_with_source_card():
    """Test parsing a per-unit condition that starts with これにより."""
    condition = parse_condition('これにより控え室に置いた『Liella!』のメンバーカード1枚につき')
    assert condition['type'] == 'per_unit'
    assert condition['value'] == 1
    assert condition['operator'] == '*'
    assert condition['group'] == 'Liella!'
    assert condition['card_type'] == 'member_card'
    assert condition['location'] == 'waitroom'

def test_fallback_raw_text():
    """Test parsing abilities that fall back to raw text."""
    assert_effect_matches('fallback_raw_text')

def test_nested_conditional_chain_is_not_mixed():
    """Test that two sentence-level condition/action chains stay separated."""
    text = (
        'このメンバーがステージから控え室に置かれたとき、'
        'このメンバーがコスト10以上のブレードハートを持たない『虹ヶ咲』のメンバーとバトンタッチしていた場合、'
        'エネルギーを2枚アクティブにする。'
        'コスト15以上のブレードハートを持たない『虹ヶ咲』のメンバーの場合、'
        'さらにカードを1枚引く。'
    )
    effect = parse_generic_effect(text)

    assert 'actions' in effect
    assert len(effect['actions']) == 2

    first = effect['actions'][0]
    second = effect['actions'][1]

    assert first['action']['condition']['value'] == '虹ヶ咲'
    assert first['action']['action']['action'] == 'activate_energy'
    assert first['action']['action']['count'] == 2
    assert 'コスト15以上' not in first['text']
    assert second['action']['action'] == 'draw_cards'
    assert second['action']['count'] == 1
    assert second['condition']['value'] == '虹ヶ咲'

def run_all_tests():
    """Run all test functions."""
    print("Running parser tests...")
    print("=" * 60)
    
    test_no_cost()
    test_simple_energy_cost()
    test_member_to_wait_cost()
    test_reveal_cost()
    test_simple_single_action()
    test_compound_action_punctuation()
    test_conditional_effect()
    test_position_condition()
    test_score_cost_limit_condition()
    test_hand_card_count_comparison()
    test_per_unit_condition_with_source_card()
    test_fallback_raw_text()
    test_nested_conditional_chain_is_not_mixed()
    
    print("=" * 60)
    print("All tests passed (fixtures loaded successfully)")

if __name__ == '__main__':
    run_all_tests()
