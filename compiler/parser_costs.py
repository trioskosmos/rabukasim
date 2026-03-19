from __future__ import annotations

from typing import List

from engine.models.ability import Cost

from .parser_cost_aliases import normalize_cost_instruction
from .parser_lexer import StructuralLexer


def parse_pseudocode_costs(parser, text: str) -> List[Cost]:
    costs = []
    parts = StructuralLexer.split_respecting_nesting(text, delimiter=",", extra_delimiters=[" OR ", ";"])

    for part in parts:
        if not part:
            continue

        spec = normalize_cost_instruction(parser, part.strip(), text)
        if not spec:
            continue

        costs.append(
            Cost(
                spec["ctype"],
                spec["value"],
                is_optional=spec["is_optional"],
                params=spec["params"],
            )
        )

    return costs

