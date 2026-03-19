# -*- coding: utf-8 -*-
"""Centralized aliases for the ability parser.

This module separates the parser helpers into three buckets:
1. True aliases: simple renames with no extra behavior.
2. Grammar conveniences: parser-only spellings and keyword shorthands.
3. Semantic special-cases: aliases that also inject or rewrite params.
"""

# Trigger type aliases: true renames only.
TRIGGER_ALIASES = {
    "ON_YELL_REVEAL": "ON_REVEAL",
    "ON_STAGE_ENTRY": "ON_PLAY",
    "ON_SELF_TAPPED": "ON_MEMBER_TAP",
    "ACTIVATED_FROM_DISCARD": "ACTIVATED",
    "ON_PLACE_ENERGY_BY_EFFECT": "ON_POSITION_CHANGE",
    "ON_RECOVERED_FROM_DISCARD": "ON_POSITION_CHANGE",
    "ON_SET_TO_LIVE_PLAY": "ON_POSITION_CHANGE",
}

# Effect aliases: true renames only.
EFFECT_TRUE_ALIASES = {
    "MOVE_TO_HAND": "ADD_TO_HAND",
    "SELECT_LIVE_CARD": "SELECT_LIVE",
    "POSITION_CHANGE": "MOVE_MEMBER",
    "TRANSFORM_YELL_BLADES": "TRANSFORM_COLOR",
    "LOOK_AND_CHOOSE_ORDER": "ORDER_DECK",
}

# Grammar conveniences for effect parsing.
EFFECT_GRAMMAR_CONVENIENCES = {
    "SELECT_OPTION": "SELECT_MODE",
    "CHOICE_MODE": "SELECT_MODE",
    "HEART_SELECT": "COLOR_SELECT",
}

# Effect aliases that require extra params or semantic rewriting.
EFFECT_SEMANTIC_SPECIAL_CASES = {
    "PLACE_ENERGY_WAIT": ("ENERGY_CHARGE", {"wait": True}),
    "LOOK_AND_CHOOSE_REVEAL": ("LOOK_AND_CHOOSE", {"reveal": True}),
    "REMOVE_SELF": ("MOVE_TO_DISCARD", {"target": "MEMBER_SELF"}),
    "DISCARD_HAND": ("MOVE_TO_DISCARD", {"source": "HAND", "destination": "discard"}),
    "RECOVER_LIVE": ("RECOVER_LIVE", {"source": "discard"}),
    "RECOVER_MEMBER": ("RECOVER_MEMBER", {"source": "discard"}),
    "SELECT_RECOVER_LIVE": ("RECOVER_LIVE", {"source": "discard"}),
    "SELECT_RECOVER_MEMBER": ("RECOVER_MEMBER", {"source": "discard"}),
    "DISCARD_UNTIL": ("MOVE_TO_DISCARD", {"operation": "UNTIL_SIZE"}),
    "YELL_MULLIGAN": ("META_RULE", {"meta_type": "ACTION_YELL_MULLIGAN"}),
}

# Condition aliases: true renames only.
CONDITION_TRUE_ALIASES = {
    "HAS_SUCCESS_LIVE": ("COUNT_SUCCESS_LIVE", {}),
    "SUM_ENERGY": ("COUNT_ENERGY", {}),
    "BATON_FROM_NAME": ("BATON", {}),
    "MOVED_THIS_TURN": ("HAS_MOVED", {}),
    "DECK_REFRESHED_THIS_TURN": ("DECK_REFRESHED", {}),
    "BATON_TOUCH": ("BATON", {}),
    "HAND_SIZE": ("COUNT_HAND", {}),
    "BLADES": ("COUNT_BLADES", {}),
    "ENERGY_COUNT": ("COUNT_ENERGY", {}),
    "SCORE_TOTAL": ("SCORE_TOTAL_CHECK", {}),
    "COUNT_MEMBER": ("COUNT_STAGE", {}),
    "TOTAL_HEARTS": ("COUNT_HEARTS", {}),
    "HEARTS_COUNT": ("COUNT_HEARTS", {}),
    "MEMBER_AT_SLOT": ("GROUP_FILTER", {}),
    "COUNT_DISCARDED_THIS_TURN": ("COUNT_DISCARD", {}),
    "FILTER": ("GROUP_FILTER", {}),
    "SUCCESS": ("MODAL_ANSWER", {}),
    "SUCCESS_LIVE_COUNT": ("COUNT_SUCCESS_LIVE", {}),
    "SCORE_GE": ("SCORE_TOTAL_CHECK", {"comparison": "GE"}),
    "SCORE_LE": ("SCORE_TOTAL_CHECK", {"comparison": "LE"}),
    "COUNT_CHARGED_ENERGY": ("COUNT_ENERGY", {}),
    "SUM_HEARTS": ("COUNT_HEARTS", {}),
    "ENERGY": ("COUNT_ENERGY", {}),
    "SUCCESS_LIVE_SCORE_TOTAL": ("SCORE_TOTAL_CHECK", {}),
    "NOT_DISCARDED_CARDS": ("DISCARDED_CARDS", {}),
}

# Condition aliases that need extra params or parser-specific rewrites.
CONDITION_SEMANTIC_SPECIAL_CASES = {
    "ALL_MEMBERS": ("GROUP_FILTER", {"all": True}),
    "COUNT_CARDS": ("GROUP_FILTER", {}),
    "SELECT_YELL": ("GROUP_FILTER", {"zone": "yell"}),
    "NAME_MATCH": ("GROUP_FILTER", {"filter": "NAME_MATCH"}),
    "EXTRA_HEARTS": ("COUNT_HEARTS", {"min": 1}),
    "HAS_ACTIVE_ENERGY": ("COUNT_ENERGY", {"filter": "active", "min": 1}),
    "ALL_ENERGY_ACTIVE": ("COUNT_ENERGY", {"filter": "active", "comparison": "ALL"}),
    "COST_LEAD": ("SCORE_COMPARE", {"type": "cost", "target": "opponent", "comparison": "GT"}),
    "SCORE_LEAD": ("SCORE_COMPARE", {"type": "score", "comparison": "GT", "target": "opponent"}),
    "TYPE_MEMBER": ("TYPE_CHECK", {"card_type": "member"}),
    "TYPE_LIVE": ("TYPE_CHECK", {"card_type": "live"}),
    "ENERGY_LAGGING": ("OPPONENT_ENERGY_DIFF", {"comparison": "GE", "diff": 1}),
    "ENERGY_LEAD": ("OPPONENT_ENERGY_DIFF", {"comparison": "LE", "diff": 0}),
    "SUM_SCORE": ("SCORE_COMPARE", {"type": "score", "comparison": "GE"}),
    "SUM_COST": ("SCORE_COMPARE", {"type": "cost", "comparison": "GE"}),
    "COST_LE_9": ("COST_CHECK", {"comparison": "LE", "value": 9}),
    "SCORE_EQUAL_OPPONENT": ("SCORE_COMPARE", {"comparison": "EQ", "target": "opponent"}),
    "SUCCESS_LIVE_COUNT_EQUAL_OPPONENT": ("SCORE_COMPARE", {"type": "score", "comparison": "EQ", "target": "opponent"}),
    "YELL_CARDS": ("COUNT_CARDS", {"zone": "YELL"}),
    "YELL_REVEALED": ("GROUP_FILTER", {"zone": "yell"}),
    "ALL_CARDS_MATCH": ("DISCARDED_CARDS", {"all": True}),
    "VALUE_GE": ("SUM_VALUE", {"comparison": "GE"}),
    "VALUE_GT": ("SUM_VALUE", {"comparison": "GT"}),
    "VALUE_EQ": ("SUM_VALUE", {"comparison": "EQ"}),
}

# Grammar conveniences: map to HAS_KEYWORD with a keyword param.
KEYWORD_CONDITIONS = {
    "COUNT_PLAYED_THIS_TURN": "PLAYED_THIS_TURN",
    "REVEALED_CONTAINS": "REVEALED_CONTAINS",
    "ZONE": "ZONE_CHECK",
    "AREA": "AREA_CHECK",
    "EFFECT_NEGATED_THIS_TURN": "EFFECT_NEGATED",
    "HIGHEST_COST_ON_STAGE": "HIGHEST_COST",
    "COUNT_UNIQUE_NAMES": "UNIQUE_NAMES",
    "OPPONENT_EXTRA_HEARTS": "OPPONENT_EXTRA_HEARTS",
    "HAS_LIVE_SET": "HAS_LIVE_SET",
    "SUCCESS_LIVES_CONTAINS": "SUCCESS_LIVES_CONTAINS",
    "YELL_COUNT": "YELL_COUNT",
    "COUNT_YELL_REVEALED": "YELL_COUNT",
}

# Grammar conveniences that should be ignored entirely.
IGNORED_CONDITIONS = {
    "TARGET",
    "ON_YELL",
    "ON_YELL_SUCCESS",
}

# Maximum value for "ALL" selector.
MAX_SELECT_ALL = 99
