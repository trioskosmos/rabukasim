"""Condition patterns.

Conditions are gating requirements that must be met for an ability to activate.
Examples: COUNT_GROUP, SCORE_COMPARE, HAS_MEMBER, etc.
"""

from .base import Pattern, PatternPhase


# Helper function for extracting Japanese numbers
def _extract_number(text: str, match) -> int:
    """Extract a number from match, handling full-width and kanji numerals."""
    val_map = {
        "１": 1,
        "２": 2,
        "３": 3,
        "４": 4,
        "５": 5,
        "６": 6,
        "７": 7,
        "８": 8,
        "９": 9,
        "０": 0,
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "〇": 0,
    }
    if match.lastindex and match.lastindex >= 1:
        val = match.group(1)
        return int(val_map.get(val, val)) if not str(val).isdigit() else int(val)
    return 1


CONDITION_PATTERNS = [
    # ==========================================================================
    # Count conditions
    # ==========================================================================
    Pattern(
        name="count_group",
        phase=PatternPhase.CONDITION,
        regex=r"『(.*?)』.*?(\d+)(枚|人)以上",
        priority=20,
        output_type="ConditionType.COUNT_GROUP",
        extractor=lambda text, match: {
            "type": "ConditionType.COUNT_GROUP",
            "value": int(match.group(2)),
            "params": {"group": match.group(1), "min": int(match.group(2))},
        },
    ),
    Pattern(
        name="count_stage",
        phase=PatternPhase.CONDITION,
        regex=r"(\d+)(枚|人)以上",
        priority=50,
        requires=["ステージ"],
        output_type="ConditionType.COUNT_STAGE",
    ),
    Pattern(
        name="count_energy",
        phase=PatternPhase.CONDITION,
        regex=r"エネルギーが(\d+)枚以上",
        priority=30,
        output_type="ConditionType.COUNT_ENERGY",
    ),
    Pattern(
        name="count_active_energy",
        phase=PatternPhase.CONDITION,
        regex=r"アクティブ状態の(?:自分の)?エネルギーが(\d+)枚以上",
        priority=20,
        output_type="ConditionType.COUNT_ENERGY",
        extractor=lambda text, m: {
            "type": "ConditionType.COUNT_ENERGY",
            "value": int(m.group(1)),
            "attr": 1,  # Attribute 1 in CountEnergy means ACTIVE ONLY
        },
    ),
    Pattern(
        name="count_success_live",
        phase=PatternPhase.CONDITION,
        regex=r"成功ライブカード置き場.*?(\d+)枚以上",
        priority=20,
        output_type="ConditionType.COUNT_SUCCESS_LIVE",
    ),
    Pattern(
        name="count_live_zone",
        phase=PatternPhase.CONDITION,
        regex=r"ライブ中のカード.*?(\d+)枚以上",
        priority=20,
        output_type="ConditionType.COUNT_LIVE_ZONE",
    ),
    Pattern(
        name="count_hearts",
        phase=PatternPhase.CONDITION,
        regex=r"(?:ハート|heart).*?(\d+)(つ|個)以上",
        priority=30,
        output_type="ConditionType.COUNT_HEARTS",
    ),
    Pattern(
        name="count_blades",
        phase=PatternPhase.CONDITION,
        regex=r"ブレード.*?(\d+)(つ|個)以上",
        priority=30,
        output_type="ConditionType.COUNT_BLADES",
    ),
    # ==========================================================================
    # Comparison conditions
    # ==========================================================================
    Pattern(
        name="score_compare_gt",
        phase=PatternPhase.CONDITION,
        regex=r"(?:スコア|コスト).*?相手.*?より(?:高い|多い)",
        priority=25,
        output_type="ConditionType.SCORE_COMPARE",
        output_params={"comparison": "GT", "target": "opponent"},
    ),
    Pattern(
        name="score_compare_ge",
        phase=PatternPhase.CONDITION,
        regex=r"(?:スコア|コスト).*?同じか(?:高い|多い)",
        priority=25,
        output_type="ConditionType.SCORE_COMPARE",
        output_params={"comparison": "GE", "target": "opponent"},
    ),
    Pattern(
        name="score_compare_lt",
        phase=PatternPhase.CONDITION,
        regex=r"(?:スコア|コスト).*?相手.*?より(?:低い|少ない)",
        priority=25,
        output_type="ConditionType.SCORE_COMPARE",
        output_params={"comparison": "LT", "target": "opponent"},
    ),
    Pattern(
        name="score_compare_eq",
        phase=PatternPhase.CONDITION,
        regex=r"(?:スコア|コスト).*?同じ(?:場合|なら|とき)",
        priority=25,
        output_type="ConditionType.SCORE_COMPARE",
        output_params={"comparison": "EQ", "target": "opponent"},
    ),
    Pattern(
        name="opponent_hand_diff",
        phase=PatternPhase.CONDITION,
        regex=r"相手の手札(?:の枚数)?が自分より(\d+)?枚?以上?多い",
        priority=25,
        output_type="ConditionType.OPPONENT_HAND_DIFF",
    ),
    Pattern(
        name="opponent_energy_diff",
        phase=PatternPhase.CONDITION,
        regex=r"相手のエネルギーが自分より(?:(\d+)枚以上)?多い",
        priority=25,
        output_type="ConditionType.OPPONENT_ENERGY_DIFF",
    ),
    Pattern(
        name="life_lead_gt",
        phase=PatternPhase.CONDITION,
        regex=r"ライフが相手より多い",
        priority=25,
        output_type="ConditionType.LIFE_LEAD",
        output_params={"comparison": "GT", "target": "opponent"},
    ),
    Pattern(
        name="life_lead_lt",
        phase=PatternPhase.CONDITION,
        regex=r"ライフが相手より少ない",
        priority=25,
        output_type="ConditionType.LIFE_LEAD",
        output_params={"comparison": "LT", "target": "opponent"},
    ),
    Pattern(
        name="opponent_choice_select",
        phase=PatternPhase.CONDITION,
        keywords=["相手", "選ぶ"],
        excludes=["自分か相手"],
        priority=30,
        output_type="ConditionType.OPPONENT_CHOICE",
        output_params={"type": "select"},
    ),
    Pattern(
        name="opponent_choice_discard",
        phase=PatternPhase.CONDITION,
        keywords=["相手", "手札", "捨て"],
        priority=30,
        output_type="ConditionType.OPPONENT_CHOICE",
        output_params={"type": "discard"},
    ),
    # ==========================================================================
    # State conditions
    # ==========================================================================
    Pattern(
        name="is_center",
        phase=PatternPhase.CONDITION,
        keywords=["センターエリア", "場合"],
        priority=40,
        output_type="ConditionType.IS_CENTER",
    ),
    Pattern(
        name="has_moved",
        phase=PatternPhase.CONDITION,
        keywords=["移動している場合"],
        priority=30,
        output_type="ConditionType.HAS_MOVED",  # [UNUSED]
    ),
    Pattern(
        name="has_live_card",
        phase=PatternPhase.CONDITION,
        keywords=["ライブカードがある場合"],
        priority=30,
        output_type="ConditionType.HAS_LIVE_CARD",
    ),
    Pattern(
        name="has_choice",
        phase=PatternPhase.CONDITION,
        regex=r"(?:1つを選ぶ|どちらか.*?選ぶ|選んでもよい|のうち.*?選ぶ)",
        priority=40,
        output_type="ConditionType.HAS_CHOICE",  # [UNUSED]
    ),
    Pattern(
        name="group_filter",
        phase=PatternPhase.CONDITION,
        regex=r"『(.*?)』",
        priority=60,
        requires=["場合", "なら", "がいる"],
        output_type="ConditionType.GROUP_FILTER",
    ),
    Pattern(
        name="has_member",
        phase=PatternPhase.CONDITION,
        regex=r"「(.*?)」.*?(?:がある|がいる|登場している)場合",
        priority=30,
        output_type="ConditionType.HAS_MEMBER",
    ),
    # ==========================================================================
    # Once per turn / Turn restrictions
    # ==========================================================================
    Pattern(
        name="turn_1",
        phase=PatternPhase.CONDITION,
        regex=r"\[Turn 1\]|1ターン目|ターン1(?!回)",
        priority=20,
        output_type="ConditionType.TURN_1",
        output_params={"turn": 1},
    ),
    # ==========================================================================
    # Revealed/Milled card conditions
    # ==========================================================================
    Pattern(
        name="all_revealed_are_members",
        phase=PatternPhase.CONDITION,
        regex=r"それらがすべてメンバーカード.*?場合",
        priority=15,
        output_type="ConditionType.GROUP_FILTER",
        output_params={"filter_type": "all_revealed", "card_type": "member"},
    ),
    Pattern(
        name="is_in_discard",
        phase=PatternPhase.CONDITION,
        regex=r"この(カード|メンバー)が控え室にある場合のみ起動できる",
        priority=10,
        output_type="ConditionType.IS_IN_DISCARD",  # [UNUSED]
    ),
    # ==========================================================================
    # New conditions for BP05 and new card abilities
    # ==========================================================================
    Pattern(
        name="count_energy_exact",
        phase=PatternPhase.CONDITION,
        regex=r"エネルギーがちょうど(\d+)枚(ある|かぎり)",
        priority=25,
        output_type="ConditionType.COUNT_ENERGY_EXACT",
        extractor=lambda text, m: {
            "type": "ConditionType.COUNT_ENERGY_EXACT",
            "value": int(m.group(1)),
            "params": {"exact_count": int(m.group(1))},
        },
    ),
    Pattern(
        name="count_blade_heart_types",
        phase=PatternPhase.CONDITION,
        regex=r"ブレードハートの中に.*?(\d+)種類以上ある場合",
        priority=20,
        output_type="ConditionType.COUNT_BLADE_HEART_TYPES",
        extractor=lambda text, m: {
            "type": "ConditionType.COUNT_BLADE_HEART_TYPES",
            "value": int(m.group(1)),
            "params": {"min_types": int(m.group(1))},
        },
    ),
    Pattern(
        name="opponent_has_excess_heart",
        phase=PatternPhase.CONDITION,
        regex=r"相手の余剰ハートが(\d+)つ以上ある(かぎり|場合)",
        priority=20,
        output_type="ConditionType.OPPONENT_HAS_EXCESS_HEART",
        extractor=lambda text, m: {
            "type": "ConditionType.OPPONENT_HAS_EXCESS_HEART",
            "value": int(m.group(1)),
            "params": {"min_count": int(m.group(1))},
        },
    ),
    Pattern(
        name="score_total_check",
        phase=PatternPhase.CONDITION,
        regex=r"成功ライブカード置き場にあるカードのスコアの合計が(\d+)以上(の場合|であるかぎり)",
        priority=20,
        output_type="ConditionType.SCORE_TOTAL_CHECK",
        extractor=lambda text, m: {
            "type": "ConditionType.SCORE_TOTAL_CHECK",
            "value": int(m.group(1)),
            "params": {"min_score": int(m.group(1))},
        },
    ),
]
