from __future__ import annotations

from typing import Dict, Tuple

from engine.models.ability import TargetType

from .parser_patterns import EFFECT_GRAMMAR_CONVENIENCES, EFFECT_SEMANTIC_SPECIAL_CASES, EFFECT_TRUE_ALIASES


def resolve_effect_aliases(
    name_up: str, params: Dict[str, object], target: TargetType
) -> Tuple[str, Dict[str, object], TargetType]:
    """Normalize effect names through rename, grammar, and semantic alias buckets."""
    if name_up in EFFECT_TRUE_ALIASES:
        name_up = EFFECT_TRUE_ALIASES[name_up]

    if name_up in EFFECT_GRAMMAR_CONVENIENCES:
        name_up = EFFECT_GRAMMAR_CONVENIENCES[name_up]

    if name_up in EFFECT_SEMANTIC_SPECIAL_CASES:
        canonical_name, extra_params = EFFECT_SEMANTIC_SPECIAL_CASES[name_up]
        name_up = canonical_name
        for key, value in extra_params.items():
            if key not in params:
                params[key] = value
        if extra_params.get("target") == "MEMBER_SELF":
            target = TargetType.MEMBER_SELF

    return name_up, params, target

