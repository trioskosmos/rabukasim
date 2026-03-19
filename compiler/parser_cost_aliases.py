from __future__ import annotations

import re
from typing import Any, Dict, Optional

from engine.models.ability import AbilityCostType

from .parser_lexer import StructuralLexer


def normalize_cost_instruction(parser: Any, part_stripped: str, full_text: str = "") -> Optional[Dict[str, Any]]:
    """Normalize one cost fragment into canonical name/value/params metadata."""
    if part_stripped.startswith("SELECT_SELF_OR_DISCARD"):
        match = re.match(
            r"^SELECT_SELF_OR_DISCARD(?:\((.*?)\))?\s*(?:\(Optional\)\s*)?(?:(\{.*?\})\s*)?(.*)$",
            part_stripped,
        )
        if not match:
            return None

        _, brace_params, rest = match.groups()
        rest = rest or ""
        params = parser._parse_pseudocode_params(brace_params or "")
        if rest:
            params["raw_cost"] = rest.strip()
        params["cost_type_name"] = "SELECT_SELF_OR_DISCARD"
        params.setdefault("choices", ["TAP_SELF", "DISCARD_HAND(1)"])
        return {
            "ctype": AbilityCostType.NONE,
            "value": 0,
            "params": params,
            "is_optional": False,
        }

    match = re.match(
        r"^([\w_]+)(?:\((.*?)\))?\s*(?:\(Optional\)\s*)?(?:(\{.*?\})\s*)?(?:\(Optional\)\s*)?(?:->\s*([\w, _]+))?(.*)$",
        part_stripped,
    )
    if not match:
        return None

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

    name_up = name.upper()
    source_hint = (brace_params or "").lower()

    if name_up == "MOVE_TO_DECK":
        if 'from="discard"' in source_hint or "from='discard'" in source_hint:
            name_up = "RETURN_DISCARD_TO_DECK"
        else:
            name_up = "RETURN_MEMBER_TO_DECK"
    elif name_up == "SELECT_RECOVER_MEMBER":
        name_up = "SELECT_CARDS"
    elif name_up == "PLACE_ENERGY_WAIT":
        name_up = "PLACE_ENERGY_FROM_DECK"
    elif name_up == "MOVE_TO_DISCARD":
        if 'from="deck_top"' in source_hint:
            name_up = "DISCARD_TOP_DECK"
        else:
            name_up = "SACRIFICE_SELF"
    elif name_up == "REMOVE_SELF":
        name_up = "SACRIFICE_SELF"
    elif name_up == "DISCARD_SELF":
        name_up = "DISCARD_HAND"
    elif name_up == "PAY_ENERGY":
        name_up = "ENERGY"
    elif name_up == "SELECT_HAND":
        name_up = "SELECT_CARDS"
    elif name_up == "PLACE_UNDER" and ('from="energy"' in source_hint or "from='energy'" in source_hint):
        name_up = "SELECT_ENERGY"
    elif "REVEAL_HAND" in name_up:
        name_up = "REVEAL_HAND"

    try:
        if val_str and val_str.upper() in ["VARIABLE", "ANY"]:
            val = -1
        else:
            val = int(val_str) if val_str else 0
    except ValueError:
        val = 0

    if name_up == "DISCARD_HAND" and val == 0:
        val = 1

    if val_str and val_str.upper() == "VARIABLE":
        val = -1

    params = parser._parse_pseudocode_params(brace_params or "")
    if name_up == "SELECT_HAND":
        params.setdefault("from", "hand")
    if destination:
        params["destination"] = destination.strip().lower()

    if name_up in ["ENERGY_CHARGE", "CALC_SUM_COST", "SELECT_CARDS", "SELECT_MEMBER", "SELECT_ENERGY"]:
        params["cost_type_name"] = name_up

    if name_up == "SELECT_ENERGY":
        params.setdefault("source", "energy")
    if name_up == "PLACE_ENERGY_FROM_DECK" and (
        "wait" in part_stripped.lower() or "wait" in (brace_params or "").lower() or "wait" in rest.lower()
    ):
        params.setdefault("wait", True)

    if name_up in ["ENERGY_CHARGE", "CALC_SUM_COST", "SELECT_CARDS", "SELECT_MEMBER", "SELECT_ENERGY"]:
        params["cost_type_name"] = name_up

    is_optional = "(Optional)" in part_stripped or "(Optional)" in rest or "(Optional)" in (brace_params or "") or " OR " in full_text
    if name_up in ["ENERGY_CHARGE", "CALC_SUM_COST", "SELECT_CARDS", "SELECT_MEMBER", "SELECT_ENERGY"]:
        ctype = AbilityCostType.NONE
    else:
        ctype = getattr(AbilityCostType, name_up, AbilityCostType.NONE)

    return {
        "ctype": ctype,
        "value": val,
        "params": params,
        "is_optional": is_optional,
    }
