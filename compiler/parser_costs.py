from __future__ import annotations

import re
from typing import List

from engine.models.ability import AbilityCostType, Cost

from .parser_lexer import StructuralLexer


def parse_pseudocode_costs(parser, text: str) -> List[Cost]:
    costs = []
    parts = StructuralLexer.split_respecting_nesting(text, delimiter=",", extra_delimiters=[" OR ", ";"])

    for part in parts:
        if not part:
            continue

        match = re.match(
            r"^([\w_]+)(?:\((.*?)\))?\s*(?:\(Optional\)\s*)?(?:(\{.*?\})\s*)?(?:\(Optional\)\s*)?(?:->\s*([\w, _]+))?(.*)$",
            part.strip(),
        )
        if not match:
            continue

        name, val_str, brace_params, destination, rest = match.groups()
        rest = rest or ""

        if not brace_params and "{" in rest:
            brace_start = rest.find("{")
            if brace_start != -1:
                recovered_params, _ = StructuralLexer.extract_balanced(rest, brace_start, "{", "}")
                if recovered_params:
                    brace_params = "{" + recovered_params + "}"

        if not destination and "->" in rest:
            destination = rest.split("->", 1)[1].split("->", 1)[0].strip()

        if name == "MOVE_TO_DECK":
            if 'from="discard"' in (brace_params or "").lower() or "from='discard'" in (brace_params or "").lower():
                name = "RETURN_DISCARD_TO_DECK"
            else:
                name = "RETURN_MEMBER_TO_DECK"
        elif name == "SELECT_RECOVER_MEMBER":
            name = "SELECT_CARDS"

        cost_name = name.upper()
        try:
            val = int(val_str) if val_str else 0
        except ValueError:
            val = 0

        if name == "MOVE_TO_DISCARD":
            if 'from="deck_top"' in (brace_params or "").lower():
                cost_name = "DISCARD_TOP_DECK"
            else:
                cost_name = "SACRIFICE_SELF"
        elif name == "REMOVE_SELF":
            cost_name = "SACRIFICE_SELF"
        else:
            cost_name = name.upper()

        if cost_name == "DISCARD_SELF":
            cost_name = "DISCARD_HAND"
            val = 1
        if cost_name == "PAY_ENERGY":
            cost_name = "ENERGY"
        if cost_name == "SELECT_HAND":
            cost_name = "SELECT_CARDS"
        if cost_name == "PLACE_UNDER":
            source_hint = (brace_params or "").lower()
            if 'from="energy"' in source_hint or "from='energy'" in source_hint:
                cost_name = "SELECT_ENERGY"
        if cost_name == "ENERGY":
            cost_name = "ENERGY"
        if "REVEAL_HAND" in cost_name:
            cost_name = "REVEAL_HAND"

        if val_str and val_str.upper() == "VARIABLE":
            val = 99

        if cost_name in ["ENERGY_CHARGE", "SELECT_ENERGY"]:
            ctype = AbilityCostType.NONE
        else:
            ctype = getattr(AbilityCostType, cost_name, AbilityCostType.NONE)

        is_optional = "(Optional)" in part or "(Optional)" in rest or "(Optional)" in (brace_params or "") or " OR " in text
        params = parser._parse_pseudocode_params(brace_params or "")
        if name.upper() == "SELECT_HAND":
            params.setdefault("from", "hand")
        if destination:
            params["destination"] = destination.strip().lower()

        if cost_name in ["ENERGY_CHARGE", "CALC_SUM_COST", "SELECT_CARDS", "SELECT_MEMBER", "SELECT_ENERGY"]:
            params["cost_type_name"] = cost_name

        if cost_name == "SELECT_ENERGY":
            params.setdefault("source", "energy")

        costs.append(Cost(ctype, val, is_optional=is_optional, params=params))

    return costs