"""Modifier patterns.

Modifiers apply flags and adjustments to parsed abilities:
- is_optional: Whether the effect can be declined
- is_once_per_turn: Usage limit
- duration: How long effects last
- target: Who is affected
"""

from .base import Pattern, PatternPhase

MODIFIER_PATTERNS = [
    # ==========================================================================
    # Optionality (key fix for the bug in legacy parser)
    # ==========================================================================
    Pattern(
        name="optional_may",
        phase=PatternPhase.MODIFIER,
        regex=r"てもよい",
        priority=10,
        output_params={"is_optional": True},
    ),
    Pattern(
        name="optional_can",
        phase=PatternPhase.MODIFIER,
        regex=r"てよい",
        priority=10,
        output_params={"is_optional": True},
    ),
    Pattern(
        name="optional_cost",
        phase=PatternPhase.MODIFIER,
        regex=r"(?:支払うことで|支払えば)",
        priority=15,
        output_params={"cost_is_optional": True},
    ),
    # ==========================================================================
    # Usage limits
    # ==========================================================================
    Pattern(
        name="once_per_turn",
        phase=PatternPhase.MODIFIER,
        regex=r"1ターンに1回|ターン終了時まで1回|に限る|ターン1回|［ターン1回］|【ターン1回】",
        priority=10,
        output_params={"is_once_per_turn": True},
    ),
    # ==========================================================================
    # Duration modifiers
    # ==========================================================================
    Pattern(
        name="until_live_end",
        phase=PatternPhase.MODIFIER,
        keywords=["ライブ終了時まで"],
        priority=20,
        output_params={"duration": "live_end"},
    ),
    Pattern(
        name="until_turn_end",
        phase=PatternPhase.MODIFIER,
        regex=r"ターン終了まで|終了時まで",
        priority=20,
        excludes=["ライブ終了時まで"],  # More specific pattern takes precedence
        output_params={"duration": "turn_end"},
    ),
    # ==========================================================================
    # Target modifiers
    # ==========================================================================
    Pattern(
        name="target_all_players",
        phase=PatternPhase.MODIFIER,
        any_keywords=["自分と相手", "自分も相手も", "全員", "自分および相手"],
        priority=20,
        output_params={"target": "ALL_PLAYERS", "both_players": True},
    ),
    Pattern(
        name="target_opponent",
        phase=PatternPhase.MODIFIER,
        regex=r"相手は.*?(?:する|引く|置く)",
        priority=25,
        excludes=["自分は", "自分を"],
        output_params={"target": "OPPONENT"},
    ),
    Pattern(
        name="target_opponent_hand",
        phase=PatternPhase.MODIFIER,
        keywords=["相手の手札"],
        priority=20,
        output_params={"target": "OPPONENT_HAND"},
    ),
    # ==========================================================================
    # Scope modifiers
    # ==========================================================================
    Pattern(
        name="scope_all",
        phase=PatternPhase.MODIFIER,
        keywords=["すべての"],
        priority=30,
        output_params={"all": True},
    ),
    # ==========================================================================
    # Multiplier modifiers
    # ==========================================================================
    Pattern(
        name="multiplier_per_unit",
        phase=PatternPhase.MODIFIER,
        regex=r"(\d+)(枚|人)につき",
        priority=20,
        output_params={"has_multiplier": True},
    ),
    Pattern(
        name="multiplier_per_member",
        phase=PatternPhase.MODIFIER,
        keywords=["人につき"],
        priority=25,
        output_params={"per_member": True},
    ),
    Pattern(
        name="multiplier_per_live",
        phase=PatternPhase.MODIFIER,
        any_keywords=["成功ライブカード", "ライブカード"],
        requires=["につき", "枚数"],
        priority=25,
        output_params={"per_live": True},
    ),
    Pattern(
        name="multiplier_per_energy",
        phase=PatternPhase.MODIFIER,
        keywords=["エネルギー"],
        requires=["につき"],
        priority=25,
        output_params={"per_energy": True},
    ),
    # ==========================================================================
    # Filter modifiers (for effect targets)
    # ==========================================================================
    Pattern(
        name="filter_cost_max",
        phase=PatternPhase.MODIFIER,
        regex=r"コスト(\d+)以下",
        priority=25,
        output_params={"has_cost_filter": True},
    ),
    Pattern(
        name="filter_group",
        phase=PatternPhase.MODIFIER,
        regex=r"『(.*?)』",
        priority=30,
        consumes=True,
        extractor=lambda text, m: {"params": {"group": m.group(1)}},
    ),
    Pattern(
        name="filter_names",
        phase=PatternPhase.MODIFIER,
        regex=r"「(?!\{\{)(.*?)」",
        priority=30,
        consumes=True,
        extractor=lambda text, m: {"params": {"target_name": m.group(1)}},
    ),
    Pattern(
        name="filter_has_ability",
        phase=PatternPhase.MODIFIER,
        any_keywords=["アクティブにする」を持つ", "【起動】"],
        priority=25,
        output_params={"has_ability": "active"},
    ),
    # ==========================================================================
    # Meta modifiers
    # ==========================================================================
    Pattern(
        name="opponent_trigger_allowed",
        phase=PatternPhase.MODIFIER,
        keywords=["対戦相手のカードの効果でも発動する"],
        priority=10,
        output_params={"opponent_trigger_allowed": True},
    ),
]
