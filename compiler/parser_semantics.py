from __future__ import annotations

import re
from typing import Any, Dict, List

from engine.models.ability import Condition, ConditionType

from .parser_lexer import StructuralLexer
from .parser_patterns import (
    CONDITION_SEMANTIC_SPECIAL_CASES,
    CONDITION_TRUE_ALIASES,
    IGNORED_CONDITIONS,
    KEYWORD_CONDITIONS,
)


def parse_pseudocode_conditions(parser: Any, text: str) -> List[Condition]:
    conditions: List[Condition] = []
    stripped_text = text.strip()

    if stripped_text.upper().startswith("OR(") and stripped_text.endswith(")"):
        inner = stripped_text[3:-1].strip()
        clauses = []
        for clause_text in StructuralLexer.split_respecting_nesting(inner, delimiter=","):
            clause_text = clause_text.strip()
            if not clause_text:
                continue
            parsed_clause = parse_pseudocode_conditions(parser, clause_text)
            if parsed_clause:
                clauses.append(parser._serialize_condition_clause(parsed_clause[0]))
        if clauses:
            return [Condition(ConditionType.NONE, {"raw_cond": "OR", "clauses": clauses})]

    top_level_or_parts = StructuralLexer.split_respecting_nesting(text, delimiter=" OR ")
    if len(top_level_or_parts) > 1:
        clauses = []
        for clause_text in top_level_or_parts:
            clause_text = clause_text.strip()
            if not clause_text:
                continue
            parsed_clause = parse_pseudocode_conditions(parser, clause_text)
            if parsed_clause:
                clauses.append(parser._serialize_condition_clause(parsed_clause[0]))
        if clauses:
            return [Condition(ConditionType.NONE, {"raw_cond": "OR", "clauses": clauses})]

    parts = StructuralLexer.split_respecting_nesting(text, delimiter=",", extra_delimiters=[";"])

    for part in parts:
        if not part:
            continue

        negated = part.startswith("NOT ") or part.startswith("NOT_")
        name_part = part[4:] if negated else part
        if not negated and name_part.startswith("!"):
            negated = True
            name_part = name_part[1:]

        params: Dict[str, Any] = {}
        for brace_block in re.findall(r"\{([^{}]*)\}", name_part):
            params.update(parser._parse_pseudocode_params("{" + brace_block + "}"))

        name_part_no_braces = re.sub(r"\s*\{[^{}]*\}", "", name_part).strip()

        match = re.match(r"(\w+)(?:\((.*?)\))?", name_part_no_braces)
        if not match:
            continue

        name = match.group(1).upper()
        val_in_parens = match.group(2)
        if val_in_parens:
            value_parts = [vp.strip() for vp in val_in_parens.split(",")]
            for value_part in value_parts:
                value_upper = value_part.upper()
                if value_upper.startswith("UNIT_"):
                    params["unit"] = value_part[5:]
                elif value_upper.startswith("GROUP_"):
                    params["group"] = value_part[6:]
                elif value_upper in [
                    "STAGE",
                    "HAND",
                    "DISCARD",
                    "ENERGY",
                    "SUCCESS_LIVE",
                    "LIVE_ZONE",
                    "SUCCESS_PILE",
                ]:
                    params["zone"] = value_upper
                elif "=" in value_part:
                    key, value = [s.strip().strip('"').strip("'") for s in value_part.split("=", 1)]
                    params[key.lower()] = value
                elif ":" in value_part:
                    key, value = [s.strip().strip('"').strip("'") for s in value_part.split(":", 1)]
                    params[key.lower()] = value
                else:
                    params["val"] = value_part

        if "->" in name_part_no_braces:
            arrow_pos = name_part_no_braces.find("->")
            target_part = name_part_no_braces[arrow_pos + 2 :].strip()
            target_word = target_part.split()[0].strip().upper()
            if target_word:
                params["target"] = target_word

        remaining_part = name_part_no_braces[len(match.group(0)) :].strip()
        if "->" in remaining_part:
            remaining_part = remaining_part[: remaining_part.find("->")].strip()

        if remaining_part:
            comparison_match = re.match(r"(>=|<=|>|<|=)\s*[\"']?(.*?)[\"']?$", remaining_part)
            if comparison_match:
                op_map = {">=": "GE", "<=": "LE", ">": "GT", "<": "LT", "=": "EQ"}
                params["comparison"] = op_map.get(comparison_match.group(1), "GE")
                params["val"] = comparison_match.group(2)
            else:
                equals_match = re.search(r"=\s*[\"']?(.*?)[\"']?$", remaining_part)
                if equals_match:
                    params["val"] = equals_match.group(1)

        params["raw_cond"] = name
        is_negated = negated

        if name == "PLAYER_CENTER_COST_GT_OPPONENT_CENTER_COST":
            name = "SYNC_COST"
            params["area"] = "CENTER"
            params["comparison"] = "GT"
            params["val"] = "0"
        elif name == "OPPONENT_CENTER_COST_GT_PLAYER_CENTER_COST":
            name = "SYNC_COST"
            params["area"] = "CENTER"
            params["comparison"] = "LT"
            params["val"] = "0"
        elif name == "HEARTS_COUNT" and "OPPONENT" in str(params.get("val", "")).upper():
            name = "HEART_LEAD"
            params["target"] = "opponent"
            params["val"] = "0"

        if name in IGNORED_CONDITIONS:
            conditions.append(Condition(ConditionType.NONE, params, is_negated=is_negated))
            continue

        if name in KEYWORD_CONDITIONS:
            params["keyword"] = KEYWORD_CONDITIONS[name]
            conditions.append(Condition(ConditionType.HAS_KEYWORD, params, is_negated=is_negated))
            continue

        if name.startswith("MATCH_") or name.startswith("DID_ACTIVATE_"):
            params["keyword"] = name
            conditions.append(Condition(ConditionType.HAS_KEYWORD, params, is_negated=is_negated))
            continue

        if name in ["COUNT_SUCCESS_LIVES", "COUNT_SUCCESS_LIVE", "COUNT_CARDS"]:
            zone_value = str(params.get("zone") or "").upper()
            if name == "COUNT_CARDS" and zone_value not in ["SUCCESS_PILE", "SUCCESS_LIVE"]:
                pass
            else:
                if "target" not in params:
                    target_value = str(params.get("PLAYER", params.get("val", "self"))).upper()
                    params["target"] = "opponent" if target_value in {"OPPONENT", "1"} else "self"
                    if "PLAYER" in params:
                        del params["PLAYER"]
                    if "val" in params and str(params["val"]).upper() in ["PLAYER", "OPPONENT"]:
                        del params["val"]
                if "COUNT" in params:
                    params["value"] = params["COUNT"]
                    params["comparison"] = "EQ"
                    del params["COUNT"]
                conditions.append(Condition(ConditionType.COUNT_SUCCESS_LIVE, params, is_negated=is_negated))
                continue

        if name in CONDITION_TRUE_ALIASES:
            canonical_name, extra_params = CONDITION_TRUE_ALIASES[name]
            try:
                condition_type = ConditionType[canonical_name]
            except KeyError:
                condition_type = ConditionType.NONE
            conditions.append(Condition(condition_type, {**params, **extra_params}, is_negated=is_negated))
            continue

        if name in CONDITION_SEMANTIC_SPECIAL_CASES:
            canonical_name, extra_params = CONDITION_SEMANTIC_SPECIAL_CASES[name]
            try:
                condition_type = ConditionType[canonical_name]
            except KeyError:
                condition_type = ConditionType.NONE
            for key, value in extra_params.items():
                if key not in params:
                    params[key] = value
            if name == "NOT_MOVED_THIS_TURN":
                is_negated = True
            conditions.append(Condition(condition_type, params, is_negated=is_negated))
            continue

        if name in {"AREA_IN", "AREA"}:
            value = str(params.get("val", "")).upper().strip('"')
            if value == "CENTER" or params.get("zone") == "CENTER" or params.get("area") == "CENTER":
                condition_type = ConditionType.IS_CENTER
            else:
                condition_type = ConditionType.AREA_CHECK
                params["keyword"] = "AREA_CHECK"
                area_map = {"LEFT_SIDE": 0, "LEFT": 0, "RIGHT_SIDE": 2, "RIGHT": 2}
                if value in area_map:
                    params["value"] = area_map[value]
            conditions.append(Condition(condition_type, params, is_negated=is_negated))
            continue

        if name == "COST_LEAD" and params.get("area") == "CENTER":
            params["zone"] = "CENTER_STAGE"
            del params["area"]

        if name == "REVEALED_CONTAINS":
            if "TYPE_LIVE" in params:
                params["value"] = "live"
            if "TYPE_MEMBER" in params:
                params["value"] = "member"

        if name == "SELECT_CARD" and str(params.get("val", "")).upper() == "REVEALED_CARD":
            filter_str = str(params.get("FILTER") or params.get("filter") or "").upper()
            if "TYPE_LIVE" in filter_str:
                params["card_type"] = "live"
                conditions.append(Condition(ConditionType.TYPE_CHECK, params, is_negated=is_negated))
                continue
            if "TYPE_MEMBER" in filter_str:
                params["card_type"] = "member"
                conditions.append(Condition(ConditionType.TYPE_CHECK, params, is_negated=is_negated))
                continue

        condition_type = getattr(ConditionType, name, ConditionType.NONE)
        conditions.append(Condition(condition_type, params, is_negated=is_negated))

    return conditions


def looks_like_condition_instruction(text: str) -> bool:
    """Return True if the instruction text should be routed through the condition parser."""
    stripped = text.strip()
    if not stripped:
        return False

    upper = stripped.upper()
    if upper.startswith("CONDITION:") or upper.startswith("OR("):
        return True

    name_match = re.match(r"^([\w_]+)", stripped)
    if not name_match:
        return False

    name = name_match.group(1).upper()
    if (
        name in CONDITION_TRUE_ALIASES
        or name in CONDITION_SEMANTIC_SPECIAL_CASES
        or name in KEYWORD_CONDITIONS
        or name in IGNORED_CONDITIONS
        or hasattr(ConditionType, name)
        or name.startswith("MATCH_")
        or name.startswith("DID_ACTIVATE_")
        or name in {
            "AREA",
            "AREA_IN",
            "REVEALED_CONTAINS",
            "SELECT_CARD",
            "PLAYER_CENTER_COST_GT_OPPONENT_CENTER_COST",
            "OPPONENT_CENTER_COST_GT_PLAYER_CENTER_COST",
            "HEARTS_COUNT",
            "COUNT_SUCCESS_LIVES",
            "COUNT_SUCCESS_LIVE",
            "COUNT_CARDS",
        }
    ):
        return True

    return False


__all__ = ["parse_pseudocode_conditions", "looks_like_condition_instruction"]
