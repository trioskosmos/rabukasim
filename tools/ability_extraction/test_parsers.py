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

def test_fallback_raw_text():
    """Test parsing abilities that fall back to raw text."""
    assert_effect_matches('fallback_raw_text')

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
    test_fallback_raw_text()
    
    print("=" * 60)
    print("All tests passed (fixtures loaded successfully)")

if __name__ == '__main__':
    run_all_tests()
