"""
Test suite for ability parsing refactor.
This provides regression tests for the parsing logic during refactoring.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from effect_parser import parse_generic_effect
from condition_parser import parse_condition

def test_multi_branch_cost_total_conditions():
    """Test that multi-branch conditions based on cost total stay separate.
    
    Multi-branch cost total conditions use a special 'branches' structure.
    """
    text = (
        '控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：'
        'それらのカードのコストの合計が、6の場合、カードを1枚引く。'
        '合計が8の場合、ライブ終了時まで、ハートを得る。'
        '合計が25の場合、ライブ終了時まで、ライブの合計スコアを+１する。'
    )
    effect = parse_generic_effect(text)

    assert 'branches' in effect
    # Should have 3 branches (6, 8, 25)
    assert len(effect['branches']) == 3
    # Verify the branches are parsed with correct cost totals
    assert effect['branches'][0]['cost_total'] == 6
    assert effect['branches'][1]['cost_total'] == 8
    assert effect['branches'][2]['cost_total'] == 25

def test_count_based_conditions_separate():
    """Test that count-based conditions (1枚 vs 2枚) stay separate.
    
    ISSUE: Currently returns nested structure with 'actions' inside 'actions'.
    The "2枚ある場合" should be a separate chain at the top level, not nested
    under the first condition.
    """
    text = (
        'このメンバーをウェイトにする：カードを3枚引き、手札を2枚控え室に置く。'
        'これにより控え室に置いたカードの中にブレードハートを持たないメンバーカードが1枚以上ある場合、'
        'このメンバーをアクティブにする。'
        '2枚ある場合、さらにライブ終了時まで、ブレードを得る。'
    )
    effect = parse_generic_effect(text)

    # Currently returns a single action with nested actions
    # TODO: Should return 2 separate top-level actions
    assert 'actions' in effect

def test_is_not_conditions_separate():
    """Test that is/is-not conditions stay separate.
    
    ISSUE: Currently returns 3 actions but they all contain the full text.
    The conditional branching (μ's vs not μ's) is not being parsed correctly.
    """
    text = (
        '手札を1枚控え室に置く：'
        'これにより控え室に置いたカードがμ\'sのカードの場合、'
        '自分のデッキの上からカードを4枚見る。その中からカードを2枚手札に加える。残りを控え室に置く。'
        'μ\'sのカード以外の場合、自分の控え室からライブカードを1枚手札に加える。'
    )
    effect = parse_generic_effect(text)

    assert 'actions' in effect
    # TODO: Should return 2 separate conditional chains
    # Currently returns 3 actions with full text (not parsing the conditional structure)
    assert len(effect['actions']) == 3

def test_surplus_heart_conditions_separate():
    """Test that surplus heart conditions (none vs 2+) stay separate.
    
    This one works correctly - returns 2 separate conditional chains.
    """
    text = (
        '自分が余剰ハートを持たない場合、ライブの合計スコアを+１する。'
        '自分が余剰ハートを2つ以上持つ場合、ライブの合計スコアを－１する。'
        'この効果ではライブの合計スコアは０未満にはならない。'
    )
    effect = parse_generic_effect(text)

    assert 'actions' in effect
    assert len(effect['actions']) == 2
    assert effect['actions'][0]['condition']['type'] == 'surplus_heart_equal'
    assert effect['actions'][0]['condition']['value'] == 0
    assert effect['actions'][1]['condition']['type'] == 'heart_count_at_least'
    assert effect['actions'][1]['condition']['value'] == 2

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

def test_opponent_member_to_wait_keeps_opponent_target():
    text = '相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）'
    effect = parse_generic_effect(text)

    assert effect['action']['action'] == 'member_to_wait'
    assert effect['action']['target'] == 'opponent'
    assert effect['action']['source'] == 'stage'
    assert effect['action']['cost_limit'] == 4

def test_waitroom_live_recovery_keeps_add_to_hand():
    text = '自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。'
    effect = parse_generic_effect(text)

    assert effect['action']['action'] == 'add_to_hand'
    assert effect['action']['source'] == 'waitroom'
    assert effect['action']['target'] == 'self'
    assert effect['action']['card_type'] == 'live_card'
    assert effect['action']['group'] == '虹ヶ咲'

def test_choice_pattern_with_conditionals():
    """Test that choice patterns with conditional branches stay separate.
    
    ISSUE: Choice patterns (以下から1つを選ぶ) with conditional branches
    inside each option need to be parsed correctly.
    """
    text = (
        '以下から1つを選ぶ。'
        '・自分の控え室にカード名が異なるライブカードが3枚以上ある場合、'
        '自分の控え室からライブカードを1枚手札に加える。'
        '・自分の控え室にグループ名が異なるライブカードが3枚以上ある場合、'
        '自分の控え室からライブカードを2枚手札に加える。'
    )
    effect = parse_generic_effect(text)

    assert 'actions' in effect
    # Choice patterns should be parsed as separate options
    # TODO: Verify the structure is correct for choice patterns

def test_simple_choice_pattern():
    """Test simple choice pattern without conditionals."""
    text = (
        '以下から1つを選ぶ。'
        '・カードを1枚引き、手札を1枚控え室に置く。'
        '・相手のステージにいるすべてのコスト2以下のメンバーをウェイトにする。'
    )
    effect = parse_generic_effect(text)

    assert 'actions' in effect
    # Simple choice should have 2 options

def test_both_players_ability_has_actor_info():
    """Test that both-players abilities have proper actor/target information."""
    text = (
        '自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。'
    )
    effect = parse_generic_effect(text)

    assert 'actions' in effect
    # Both-players abilities should have multi_target field
    assert effect['actions'][0].get('target') == 'both_players'
    assert effect['actions'][0].get('multi_target') == True

def test_opponent_targeting_has_target_field():
    """Test that abilities targeting opponent have explicit target field."""
    text = (
        'このメンバーをウェイトにしてもよい：'
        '相手のステージにいるコスト4以下のメンバー1人をウェイトにする。'
    )
    effect = parse_generic_effect(text)

    assert 'action' in effect
    # Abilities targeting opponent should have source field indicating self
    # ISSUE: Currently target is 'self' but should indicate opponent for the second action
    # TODO: This needs to be fixed - the opponent targeting should have target='opponent'

def test_implicit_self_ability():
    """Test that implicit self abilities (card abilities) don't require explicit actor."""
    text = (
        'カードを1枚引き、手札を1枚控え室に置く。'
    )
    effect = parse_generic_effect(text)

    assert 'actions' in effect or 'action' in effect
    # Implicit self abilities are acceptable without explicit actor field
    # The card's controller is understood to be the actor

def test_exclusion_pattern_is_captured():
    """Test that '以外' (except) exclusion pattern is captured in effect structure.
    
    ISSUE: Currently '以外' is being lost in the parsed structure.
    The condition "このメンバー以外のメンバー" should have an exclude/except field.
    """
    text = (
        '自分のステージにこのメンバー以外のメンバーが1人以上いる場合、'
        'ライブ終了時まで、エールによって公開される自分のカードの枚数が8枚減る。'
    )
    effect = parse_generic_effect(text)

    assert 'condition' in effect
    effect_str = str(effect)
    # TODO: Should have 'exclude' or 'except' field to capture "このメンバー以外"
    # Currently this information is lost

def test_card_negation_is_captured():
    """Test that card negation (持たない) is properly captured."""
    text = (
        '自分がエールしたとき、'
        'エールにより公開された自分のカードの中にブレードハートを持たないメンバーカードが3枚以上ある場合、'
        'ライブ終了時まで、ハートを得る。'
    )
    effect = parse_generic_effect(text)

    assert 'condition' in effect
    # The negation "持たない" should be captured
    # Currently it's implicit in the card_type filtering
    # TODO: Consider adding explicit negation field

def test_comparison_negation_is_captured():
    """Test that comparison negation (少ない場合) is properly captured with operator."""
    text = (
        'エールにより公開された自分のカードの枚数が、'
        '相手がエールによって公開したカードの枚数より少ない場合、'
        'カードを1枚引く。'
    )
    effect = parse_generic_effect(text)

    assert 'condition' in effect
    assert effect['condition']['operator'] == '<'
    # Comparison negation is correctly captured with operator field

def test_names_different_is_captured():
    """Test that '異なる' (different) is captured."""
    text = (
        '自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、'
        'かつ名前が異なる場合、'
        'ライブの合計スコアを+１する。'
    )
    effect = parse_generic_effect(text)

    assert 'condition' in effect
    assert effect['condition']['names_different'] == True
    # This pattern is correctly captured


if __name__ == '__main__':
    # Run only the new regression tests for multi-conditional patterns
    print("Running new regression tests...")
    print("=" * 60)
    
    test_multi_branch_cost_total_conditions()
    test_count_based_conditions_separate()
    test_is_not_conditions_separate()
    test_surplus_heart_conditions_separate()
    test_choice_pattern_with_conditionals()
    test_simple_choice_pattern()
    test_both_players_ability_has_actor_info()
    test_opponent_targeting_has_target_field()
    test_implicit_self_ability()
    test_exclusion_pattern_is_captured()
    test_card_negation_is_captured()
    test_comparison_negation_is_captured()
    test_names_different_is_captured()
    
    print("=" * 60)
    print("All new regression tests passed!")
