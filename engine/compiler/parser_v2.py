# -*- coding: utf-8 -*-
"""New multi-pass ability parser using the pattern registry system.

This parser replaces the legacy 3500-line spaghetti parser with a clean,
modular architecture based on:
1. Declarative patterns organized by phase
2. Multi-pass parsing: Trigger → Conditions → Effects → Modifiers
3. Proper optionality handling (fixes the is_optional bug)
4. Structural Lexing: Balanced-brace scanning instead of greedy regex
"""

import functools
import re
from typing import Any, Dict, List

from ..models.ability import (
    Ability,
    AbilityCostType,
    Condition,
    ConditionType,
    Cost,
    Effect,
    EffectType,
    TargetType,
    TriggerType,
)

from .parser_costs import parse_pseudocode_costs
from .parser_effect_aliases import resolve_effect_aliases
from .parser_effect_normalization import normalize_select_hand_effect
from .parser_grant_ability import parse_grant_ability_effect
from .parser_lexer import StructuralLexer
from .parser_patterns import MAX_SELECT_ALL, TRIGGER_ALIASES
from .parser_play_member_resolution import resolve_play_member_source
from .parser_semantics import looks_like_condition_instruction, parse_pseudocode_conditions
from .parser_target_resolution import resolve_target_type


class AbilityParserV2:
    """Multi-pass ability parser using pattern registry."""

    def __init__(self):
        pass

    @functools.lru_cache(maxsize=2048)
    def parse(self, text: str) -> List[Ability]:
        """Parse ability text into structured Ability objects."""
        # Preprocess
        text = text.replace("<br>", "\n")

        # Detect format

        # Behavior blocks are handled if present, else fallback to pseudocode
        if text.strip().upper().startswith("BEHAVIOR:"):
            # Check if behavior parser exists (it was legacy/retired in some versions)
            if hasattr(self, "_parse_behavior_block"):
                return self._parse_behavior_block(text)
            return self._parse_pseudocode_block(text)

        return self._parse_pseudocode_block(text)

    # =========================================================================
    # Pseudocode Parsing (Inverse of tools/simplify_cards.py)
    # =========================================================================

    def _parse_pseudocode_block(self, text: str) -> List[Ability]:
        """Parse one or more abilities from pseudocode format."""
        # Normalized splitting: ensure each keyword starts a new line
        for kw in ["TRIGGER:", "CONDITION:", "EFFECT:", "COST:"]:
            text = text.replace(f"; {kw}", f"\n{kw}").replace(f";{kw}", f"\n{kw}")

        # Split by keywords but respect quotes
        # We want to identify blocks that belong together.
        # A block starts with one or more TRIGGER: lines followed by a body.

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Filter out reminder-only lines at the top level
        # (e.g. (エールで出たスコア...))
        filtered_lines = []
        for line in lines:
            cleaned = line.strip()
            if (
                cleaned.startswith("(")
                and cleaned.endswith(")")
                and not any(kw in cleaned.upper() for kw in ["TRIGGER:", "EFFECT:", "COST:", "CONDITION:"])
            ):
                continue
            filtered_lines.append(line)
        lines = filtered_lines

        if not lines:
            return []

        # Group lines into logical abilities
        # Each ability has a set of triggers and a set of instructions.
        current_triggers = []
        current_body = []
        ability_specs = []

        for line in lines:
            # Check if it's a trigger line (can be multiple on one line if separated by semicolon)
            if line.upper().startswith("TRIGGER:"):
                # If we have a body from a previous trigger group, finalize it
                if current_body:
                    ability_specs.append((current_triggers, current_body))
                    current_triggers = []
                    current_body = []

                # Split and add all triggers from this line
                # Use regex to find all TRIGGER: instances
                matches = re.finditer(r"TRIGGER:\s*([^;]+)(?:;|$)", line, re.I)
                for m in matches:
                    t_text = m.group(1).strip()
                    if t_text:
                        split_triggers = StructuralLexer.split_respecting_nesting(t_text, delimiter=",")
                        for split_trigger in split_triggers:
                            split_trigger = split_trigger.strip()
                            if split_trigger:
                                current_triggers.append(split_trigger)
            else:
                current_body.append(line)

        # Finalize last block
        if current_triggers or current_body:
            ability_specs.append((current_triggers, current_body))

        abilities = []
        for triggers, body in ability_specs:
            if not triggers:
                # Default to ACTIVATED if body exists but no trigger
                # BUT ONLY IF THERE IS SUBSTANCE (not just keywords or reminders)
                has_substance = False
                for line in body:
                    cleaned = line.upper()
                    if any(kw in cleaned for kw in ["EFFECT:", "COST:", "CONDITION:"]):
                        has_substance = True
                        break
                    # Also check for non-parenthesized text
                    if line.strip() and not (line.strip().startswith("(") and line.strip().endswith(")")):
                        has_substance = True
                        break

                if not has_substance:
                    continue

                triggers = ["ACTIVATED"]

            # For each trigger, create a separate ability but sharing the same body content
            body_text = "\n".join(body)
            for t_val in triggers:
                full_text = f"TRIGGER: {t_val}\n{body_text}"
                ability = self._parse_single_pseudocode(full_text)
                if ability:
                    abilities.append(ability)

        return abilities

    def _parse_single_pseudocode(self, text: str) -> Ability:
        """Parse a single ability from pseudocode format."""
        # Clean up lines but preserve structure for Options: parsing
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        trigger = TriggerType.NONE
        costs = []
        conditions = []
        effects = []
        instructions = []
        is_once_per_turn = False

        # New: Track nested options for SELECT_MODE
        # If we see "Options:", the next lines until the next keyword belong to it
        i = 0
        last_target = TargetType.PLAYER

        # Pre-pass: Remove parenthesized reminder text at the very start of the ability
        # unless it starts with a keyword.
        if lines and lines[0].startswith("(") and lines[0].endswith(")"):
            # If it's just reminder text like (エールで出たスコア...), skip it if no keywords inside
            inner = lines[0][1:-1].lower()
            keywords = ["trigger:", "effect:", "cost:", "condition:"]
            if not any(kw in inner for kw in keywords):
                lines = lines[1:]

        while i < len(lines):
            line = lines[i]
            upper_line = line.upper()

            # Check for Once per turn/Game flags globally for any instruction line
            low_line = line.lower()
            if "once per turn" in low_line or "once per game" in low_line or "(once per turn)" in low_line:
                is_once_per_turn = True

            if upper_line.startswith("TRIGGER:"):
                t_name = line[len("TRIGGER:") :].strip().upper()
                # Strip all content in parentheses (...) or braces {...}
                t_name = re.sub(r"\(.*?\)", "", t_name)
                t_name = re.sub(r"\{.*?\}", "", t_name).strip()

                # Use module-level constant for trigger aliases
                t_name = TRIGGER_ALIASES.get(t_name, t_name)
                try:
                    trigger = TriggerType[t_name]
                except (KeyError, ValueError):
                    trigger = getattr(TriggerType, t_name, TriggerType.NONE)

            elif upper_line.startswith("COST:"):
                cost_str = line[len("COST:") :].strip()
                new_costs = self._parse_pseudocode_costs(cost_str)
                for c in new_costs:
                    # SYSTEMIC FIX: Sort costs between Activation Phase (Shell) and Execution Phase (Bytecode)
                    # Mandatory initial costs stay in 'costs' for shell pre-checks.
                    # Optional or mid-ability costs move to 'instructions' so the bytecode
                    # interpreter can suspend for pay/skip interactions.
                    # Complex costs (SELECT_MEMBER, etc.) MUST be in bytecode
                    is_complex = c.type == AbilityCostType.NONE and c.params.get("cost_type_name") != "SELECT_SELF_OR_DISCARD"

                    if not c.is_optional and not instructions and not is_complex:
                        costs.append(c)
                    else:
                        instructions.append(c)

            elif upper_line.startswith("CONDITION:"):
                cond_str = line[len("CONDITION:") :].strip()
                new_conditions = self._parse_pseudocode_conditions(cond_str)
                # Only add to pre-activation pre-check conditions if NO effects or costs have been encountered yet
                if not effects and not costs:
                    conditions.extend(new_conditions)
                instructions.extend(new_conditions)

            elif upper_line.startswith("EFFECT:"):
                eff_str = line[len("EFFECT:") :].strip()
                new_effects = self._parse_pseudocode_effects(eff_str, last_target=last_target, full_text=text)
                if new_effects:
                    last_target = new_effects[-1].target if isinstance(new_effects[-1], Effect) else last_target

                # Filter out Conditions from the 'effects' list to avoid AttributeErrors in compiler
                effects.extend([e for e in new_effects if isinstance(e, Effect)])
                instructions.extend(new_effects)

            elif upper_line.startswith("OPTIONS:"):
                # The most recently added effect should be SELECT_MODE
                if effects and effects[-1].effect_type == EffectType.SELECT_MODE:
                    # Parse subsequent lines until next major keyword
                    modal_options = []
                    i += 1
                    while i < len(lines) and not any(
                        lines[i].upper().startswith(kw) for kw in ["TRIGGER:", "COST:", "CONDITION:", "EFFECT:"]
                    ):
                        # Format: N: EFFECT1, EFFECT2
                        option_match = re.match(r"\d+:\s*(.*)", lines[i])
                        if option_match:
                            option_text = option_match.group(1)
                            sub_effects = self._parse_pseudocode_effects_compact(option_text)
                            modal_options.append(sub_effects)
                        i += 1
                    effects[-1].modal_options = modal_options
                    continue  # Already incremented i

            elif upper_line.startswith("OPTION:"):
                # Format: OPTION: Description | EFFECT: Effect1; Effect2 | COST: Cost1
                if effects and effects[-1].effect_type == EffectType.SELECT_MODE:
                    # Parse the option line
                    parts = line.replace("OPTION:", "").split("|")
                    opt_desc = parts[0].strip()

                    # Store description in select_mode effect params
                    if "options" not in effects[-1].params:
                        effects[-1].params["options"] = []
                    effects[-1].params["options"].append(opt_desc)

                    sub_instructions = []

                    # Parse Costs
                    cost_part = next((p.strip() for p in parts if p.strip().startswith("COST:")), None)
                    if cost_part:
                        cost_str = cost_part.replace("COST:", "").strip()
                        sub_costs = self._parse_pseudocode_costs(cost_str)
                        sub_instructions.extend(sub_costs)

                    # Parse Effects
                    eff_part = next((p.strip() for p in parts if p.strip().startswith("EFFECT:")), None)
                    if eff_part:
                        eff_str = eff_part.replace("EFFECT:", "").strip()
                        # Use standard effect parser as these can be complex
                        sub_effects = self._parse_pseudocode_effects(eff_str)
                        # Filter for modal_options which expects List[Effect] usually, or Union
                        sub_instructions.extend(sub_effects)

                    # Initialize modal_options if needed
                    if not hasattr(effects[-1], "modal_options") or effects[-1].modal_options is None:
                        effects[-1].modal_options = []

                    effects[-1].modal_options.append(sub_instructions)

            i += 1

        return Ability(
            raw_text=text,
            trigger=trigger,
            costs=costs,
            conditions=conditions,
            effects=effects,
            is_once_per_turn=is_once_per_turn,
            instructions=instructions,
            pseudocode=text,
        )

    def _parse_pseudocode_effects_compact(self, text: str) -> List[Effect]:
        """Special parser for compact effects in Options list (comma separated)."""
        # Format example: DRAW(1)->SELF {PARAMS}, MOVE_TO_DECK(1)->SELF {PARAMS}
        # Split by comma but not inside {}
        parts = []
        current = ""
        depth = 0
        for char in text:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(current.strip())
                current = ""
                continue
            current += char
        if current:
            parts.append(current.strip())

        effects = []
        for p in parts:
            # Format: NAME(VAL)->TARGET {PARAMS} or NAME(VAL)->EFFECT(VAL2)
            # Try to match name and val first
            m = re.match(r"(\w+)\((.*?)\)(.*)", p)
            if m:
                name, val_part, rest = m.groups()
                name_up = name.upper()
                etype = getattr(EffectType, name_up, EffectType.DRAW)

                # Check for target or chained effect in rest
                target = last_target
                chained_effect_str = ""

                arrow_match = re.search(r"->\s*([\w!]+)(\(.*\))?(.*)", rest)
                if arrow_match:
                    target_or_eff_name = arrow_match.group(1).upper()
                    inner_val = arrow_match.group(2)
                    extra_rest = arrow_match.group(3)

                    if hasattr(EffectType, target_or_eff_name):
                        # Chained effect!
                        chained_effect_str = f"{target_or_eff_name}{inner_val if inner_val else '()'} {extra_rest}"
                        target = last_target  # Keep last target for the first effect
                    else:
                        target = getattr(TargetType, target_or_eff_name, TargetType.PLAYER)
                        rest = extra_rest  # Parameters belong to the first effect

                params = self._parse_pseudocode_params(rest)

                val_int = 0
                val_cond = ConditionType.NONE

                # Check if val_part is a condition type or contains multiple params
                val_up = str(val_part).upper()
                if "," in val_up:
                    # Positional params in parentheses: META_RULE(SCORE_RULE, ALL_ENERGY_ACTIVE)
                    v_parts = [vp.strip() for vp in val_part.split(",")]
                    for vp in v_parts:
                        vp_up = vp.upper()
                        if vp_up == "SCORE_RULE":
                            params["type"] = "SCORE_RULE"
                        elif vp_up == "ALL_ENERGY_ACTIVE":
                            params["rule"] = "ALL_ENERGY_ACTIVE"
                            val_int = 1  # v=1 for SCORE_RULE: ALL_ENERGY_ACTIVE
                        else:
                            if "=" in vp:
                                k, v = vp.split("=", 1)
                                params[k.strip().lower()] = v.strip().strip("\"'")
                            else:
                                try:
                                    if val_int == 0:
                                        val_int = int(vp)
                                except (TypeError, ValueError):
                                    pass
                elif hasattr(ConditionType, val_up):
                    val_cond = getattr(ConditionType, val_up)
                else:
                    try:
                        val_int = int(val_part)
                    except ValueError:
                        val_int = 1
                        params["raw_val"] = val_part

                effects.append(Effect(etype, val_int, val_cond, target, params))

                if chained_effect_str:
                    # Recursively parse the chained effect
                    effects.extend(self._parse_pseudocode_effects(chained_effect_str, last_target=target))

        return effects

    def _parse_pseudocode_params(self, param_str: str) -> Dict[str, Any]:
        """Parse parameters in {KEY=VAL, ...} format."""
        if not param_str or "{" not in param_str:
            return {}

        params = {}
        if not param_str or param_str == "{}":
            return params

        # Remove outer braces
        content = param_str.strip()
        if content.startswith("{") and content.endswith("}"):
            content = content[1:-1]

        # Split by comma but respect quotes and brackets
        parts = []
        current = ""
        in_quotes = False
        depth = 0
        for char in content:
            if char == '"':
                in_quotes = not in_quotes
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1

            if char == "," and not in_quotes and depth == 0:
                parts.append(current.strip())
                current = ""
                continue
            current += char
        if current:
            parts.append(current.strip())

        for p in parts:
            # Handle special formats like COUNT_EQ_2 (without = sign)
            # Pattern: KEY_EQ_N or KEY_LE_N or KEY_GE_N etc.
            special_match = re.match(r"(COUNT_EQ|COUNT_LE|COUNT_GE|COUNT_LT|COUNT_GT)_(\d+)$", p.strip(), re.I)
            if special_match:
                key_part = special_match.group(1).upper()
                num_val = int(special_match.group(2))
                params[key_part] = num_val
                continue

            if "=" in p:
                k, v = p.split("=", 1)
                k = k.strip().upper()
                v = v.strip().strip('"').strip("'")

                # Handle list values like [1, 2, 3]
                if v.startswith("[") and v.endswith("]"):
                    items = [i.strip().strip('"').strip("'") for i in v[1:-1].split(",") if i.strip()]
                    # Convert to ints if numeric
                    v = [int(i) if i.isdigit() else i for i in items]
                # Handle numeric values
                elif v.isdigit():
                    v = int(v)
                elif v.upper() == "TRUE":
                    v = True
                elif v.upper() == "FALSE":
                    v = False

                # HEART_TYPE / HEART_0x mapping
                if k == "HEART_TYPE" or k == "HEART":
                    if isinstance(v, str) and v.startswith("HEART_0"):
                        # Map HEART_00..05 to 0..5
                        try:
                            v = int(v[7:])
                        except ValueError:
                            pass

                # Special color mapping for FILTER strings
                if k == "FILTER" and isinstance(v, str):
                    h_map = {
                        "HEART_00": "COLOR_PINK",
                        "HEART_01": "COLOR_RED",
                        "HEART_02": "COLOR_YELLOW",
                        "HEART_03": "COLOR_GREEN",
                        "HEART_04": "COLOR_BLUE",
                        "HEART_05": "COLOR_PURPLE",
                    }
                    for old, new in h_map.items():
                        v = v.replace(old, new)

                params[k] = v
            else:
                # Single word like "UNIQUE_NAMES" or "ALL_AREAS"
                k = p.strip().upper()
                if k:
                    params[k] = True
        return params

    def _parse_pseudocode_costs(self, text: str) -> List[Cost]:
        return parse_pseudocode_costs(self, text)

    def _serialize_condition_clause(self, cond: Condition) -> Dict[str, Any]:
        return {
            "type": int(cond.type),
            "value": int(cond.value),
            "attr": int(cond.attr),
            "is_negated": bool(cond.is_negated),
            "params": dict(cond.params),
        }

    def _parse_pseudocode_conditions(self, text: str) -> List[Condition]:
        return parse_pseudocode_conditions(self, text)

    def _parse_pseudocode_effects(self, text: str, last_target: TargetType = TargetType.PLAYER, full_text: str = "") -> List[Effect]:
        effects = []
        # Use the shared split method
        parts = StructuralLexer.split_respecting_nesting(text, delimiter=";")

        for p in parts:
            if not p:
                continue

            # Special handling for GRANT_ABILITY(TARGET, "ABILITY")
            if "GRANT_ABILITY" in p:
                grant_effects = parse_grant_ability_effect(p)
                if grant_effects:
                    effects.extend(grant_effects)
                    continue

            # Special handling for CONDITION: inner instruction
            if p.upper().startswith("CONDITION:"):
                # Recursive call to condition parser
                cond_str = p[10:].strip()
                # These will be filtered out by the caller (parse method)
                effects.extend(self._parse_pseudocode_conditions(cond_str))
                continue

            p = p.strip()
            # More robust regex that handles underscores, varies spacing, and mid-string (Optional)
            # Format: NAME(VAL) (Optional)? {PARAMS}? -> TARGET? REST
            m = re.match(r"^([\w_]+)(?:\((.*?)\))?\s*(?:\(Optional\)\s*)?(?:(\{.*?\})\s*)?(?:->\s*([\w, _]+))?(.*)$", p)
            if m:
                name, val, param_block, target_name, rest = m.groups()
                rest = rest or ""

                # If we matched (Optional) via the explicit group, we should ensure is_optional is set later.
                # The current logic checks for "(Optional)" in rest or p, which is sufficient.

                # Extract params only from the isolated {...} block if found
                params = self._parse_pseudocode_params(param_block) if param_block else {}
                
                # FALLBACK: If params block was at the end (after target), it will be in 'rest'
                if not params and rest and "{" in rest:
                    import re as re_mod
                    m_param = re_mod.search(r"(\{.*?\})", rest)
                    if m_param:
                        params = self._parse_pseudocode_params(m_param.group(1))

                # Preserve chained destinations like:
                # SELECT_HAND(...) -> PLAY_STAGE_EMPTY -> TARGET_PLAYED
                chain_destinations = []
                if target_name:
                    chain_destinations.append(target_name.strip().upper())
                if rest:
                    chain_destinations.extend(m.group(1).strip().upper() for m in re.finditer(r"->\s*([\w_]+)", rest))
                if chain_destinations:
                    params["chain_destinations"] = chain_destinations
                    params.setdefault("destination", chain_destinations[0].lower())
                    if len(chain_destinations) > 1:
                        params["capture"] = chain_destinations[-1].lower()

                # Target Resolution
                target, is_chained = resolve_target_type(target_name, last_target, params)

                # Legacy SELF mapping (If -> SELF exists in text)
                if "-> SELF" in p or "-> self" in p:
                    target = TargetType.MEMBER_SELF

                # Apply effect aliases using module-level constants
                name_up = name.upper()

                # Normalize aliases in one helper so the parser only owns structure.
                name_up, params, target = resolve_effect_aliases(name_up, params, target)

                # Special cases that need dynamic handling
                if name_up == "ADD_TAG":
                    name_up = "META_RULE"
                    params["tag"] = val

                if name_up == "SELECT_HAND":
                    name_up, target = normalize_select_hand_effect(name_up, params, target)

                if name_up.startswith("PLAY_MEMBER"):
                    name_up = resolve_play_member_source(name_up, params, p, full_text)

                if name_up == "DRAW_MEMBER_FROM_DECK":
                    choose_count = 1
                    if val and str(val).strip().isdigit():
                        choose_count = int(str(val).strip())
                    look_count = params.get("LOOK") or params.get("look") or choose_count
                    try:
                        look_count = int(str(look_count).strip())
                    except (TypeError, ValueError):
                        look_count = choose_count

                    name_up = "LOOK_AND_CHOOSE"
                    val = str(look_count)
                    params["choose_count"] = choose_count
                    params.setdefault("destination", "card_hand")
                    params.setdefault("remainder", "discard")
                    params.setdefault("chain_destinations", ["CARD_HAND"])

                etype = getattr(EffectType, name_up, None)

                # Special handling for SELECT_MODE labels in inline params
                if etype == EffectType.SELECT_MODE:
                    option_names = []
                    for j in range(1, 11):
                        key = f"OPTION_{j}"
                        if val_from_params := (params.get(key) or params.get(key.lower())):
                            option_names.append(str(val_from_params))
                    if option_names:
                        params["options"] = option_names

                if target_name and not is_chained:
                    target_name_up = target_name.upper()
                    if "CARD_HAND" in target_name_up:
                        target = TargetType.CARD_HAND
                    elif "CARD_DISCARD" in target_name_up:
                        target = TargetType.CARD_DISCARD
                    elif target_name_up in {"ALL_PLAYERS", "PLAYER_AND_OPPONENT"}:
                        target = TargetType.ALL_PLAYERS
                    else:
                        t_part = target_name.split(",")[0].strip()
                        target = getattr(TargetType, t_part.upper(), last_target)

                    if "DISCARD_REMAINDER" in target_name_up:
                        params["destination"] = "discard"

                    # Variable targeting support: if target is "TARGET" or "TARGET_MEMBER" or "SLOT", use last_target
                    if target_name_up in ["TARGET", "TARGET_MEMBER", "SLOT"]:
                        target = last_target
                    elif target_name_up == "ACTIVATE_AND_SELF":
                        # Special case for "activate and self" -> targets player but implied multi-target
                        # For now default to player or member self
                        target = TargetType.PLAYER
                elif not is_chained:
                    target = TargetType.PLAYER

                if name.upper() == "LOOK_AND_CHOOSE_REVEAL" and "DISCARD_REMAINDER" in p.upper():
                    params["destination"] = "discard"

                if etype is None:
                    # Fallback to condition parser if name is a known condition alias
                    if looks_like_condition_instruction(p):
                        # Recursive call to condition parser for this single instruction
                        effects.extend(self._parse_pseudocode_conditions(p))
                        continue
                    
                    # Safe fallback: unknown instructions become NOP (NONE) instead of broken META_RULE
                    etype = EffectType.NONE
                    params["raw_effect"] = name.upper()

                if target_name and target_name.upper() == "SLOT" and params.get("self"):
                    target = TargetType.MEMBER_SELF
                is_opt = "(Optional)" in rest or "(Optional)" in p

                val_int = 0
                val_cond = ConditionType.NONE

                # SPECIAL HANDLING FOR REVEAL_UNTIL WITH COMMA-SEPARATED FILTERS
                # Must happen BEFORE comma parsing to properly extract TYPE and COST conditions
                if etype == EffectType.REVEAL_UNTIL and val and "," in val:
                    # Process: REVEAL_UNTIL(TYPE_LIVE, COST_GE_10) or REVEAL_UNTIL(TYPE_MEMBER, COST_GE_10)
                    parts = [p.strip() for p in val.split(",")]
                    for part in parts:
                        if "TYPE_LIVE" in part:
                            val_cond = ConditionType.TYPE_CHECK
                            params["card_type"] = "live"
                        elif "TYPE_MEMBER" in part:
                            val_cond = ConditionType.TYPE_CHECK
                            params["card_type"] = "member"
                        elif part.startswith("COST_"):
                            # Extract COST_GE=10 or COST_GE_10, COST_LE=X, etc.
                            cost_match = re.search(r"COST_(GE|LE|GT|LT|EQ)([=_])(\d+)", part)
                            if cost_match:
                                comp, sep, cval = cost_match.groups()
                                val_cond = ConditionType.COST_CHECK
                                params["comparison"] = comp
                                params["value"] = int(cval)
                        else:
                            # Unknown part, store as raw
                            if part and not part.startswith("COST_"):
                                params[part.lower()] = True
                # Check for comma-separated positional params in val (e.g. META_RULE(SCORE_RULE, ALL_ENERGY_ACTIVE))
                elif val and "," in val:
                    v_parts = [vp.strip() for vp in val.split(",")]
                    for vp in v_parts:
                        vp_up = vp.upper()
                        if vp_up == "SCORE_RULE":
                            params["type"] = "SCORE_RULE"
                        elif vp_up == "ALL_ENERGY_ACTIVE":
                            params["rule"] = "ALL_ENERGY_ACTIVE"
                            val_int = 1  # v=1 for SCORE_RULE: ALL_ENERGY_ACTIVE
                        else:
                            if "=" in vp:
                                k, v = vp.split("=", 1)
                                params[k.strip().lower()] = v.strip().strip("\"'")
                            else:
                                try:
                                    if val_int == 0:
                                        val_int = int(vp)
                                except (TypeError, ValueError):
                                    pass
                # Check if val is a condition type (e.g. COUNT_STAGE)
                elif val and hasattr(ConditionType, val):
                    val_cond = getattr(ConditionType, val)
                elif etype == EffectType.REVEAL_UNTIL and val:
                    # Special parsing for REVEAL_UNTIL(CONDITION) - single condition
                    if "TYPE_LIVE" in val:
                        val_cond = ConditionType.TYPE_CHECK
                        params["card_type"] = "live"
                    elif "TYPE_MEMBER" in val:
                        val_cond = ConditionType.TYPE_CHECK
                        params["card_type"] = "member"

                    # Handle COST_GE/LE in REVEAL_UNTIL (supports both = and _ separators)
                    if "COST_" in val:
                        # Extract COST_GE=10 or COST_GE_10, COST_LE=X, etc.
                        cost_match = re.search(r"COST_(GE|LE|GT|LT|EQ)([=_])(\d+)", val)
                        if cost_match:
                            comp, sep, cval = cost_match.groups()
                            # If we also have TYPE check, we need to combine them?
                            # Bytecode only supports one condition on REVEAL_UNTIL.
                            # We'll prioritize COST check if present, or maybe the engine supports compound?
                            # For now, map to COST_CHECK condition.
                            val_cond = ConditionType.COST_CHECK
                            params["comparison"] = comp
                            params["value"] = int(cval)

                    if "COST_GE" in val and val_cond == ConditionType.NONE:
                        val_cond = ConditionType.COST_CHECK
                        m_cost = re.search(r"COST_GE([=_])(\d+)", val)
                        if m_cost:
                            params["min"] = int(m_cost.group(2))

                    if val_cond == ConditionType.NONE:
                        try:
                            val_int = int(val)
                        except ValueError:
                            val_int = 1
                            if val:
                                params["raw_val"] = val
                else:
                    # Handle comma-separated values inside parentheses, e.g., NAME(VAL, OPT="X")
                    if val and "," in val:
                        inner_parts = val.split(",")
                        val = inner_parts[0].strip()
                        for inner_p in inner_parts[1:]:
                            inner_p = inner_p.strip()
                            if "=" in inner_p:
                                ik, iv = inner_p.split("=", 1)
                                ik = ik.strip().lower()
                                iv = iv.strip().strip('"').strip("'")
                                params[ik] = iv
                            else:
                                params[inner_p.lower()] = True

                    try:
                        val_int = int(val) if val else 1
                    except ValueError:
                        val_int = 1  # Fallback for non-numeric val (e.g. "ALL")
                        if val:
                            params["raw_val"] = val
                        if val == "ALL":
                            val_int = MAX_SELECT_ALL
                        elif val == "OPPONENT":
                            target = TargetType.OPPONENT
                            target_name = "OPPONENT"
                        elif val == "PLAYER":
                            target = TargetType.PLAYER
                            target_name = "PLAYER"
                if etype == EffectType.ENERGY_CHARGE:
                    if params.get("wait") or params.get("mode") == "WAIT":
                        params["wait"] = True

                # Special parsing for TRANSFORM_COLOR(ALL) -> X
                if etype == EffectType.TRANSFORM_COLOR:
                    # If val was "ALL", int(val) would have yielded 1 or 99.
                    # We want 'a' (source) to be 0 (all) and 'v' (destination) to be the target number.
                    if val == "ALL":
                        # Determine destination from target_name (e.g. -> 5)
                        try:
                            # The pseudocode usually uses 1-indexed colors (1=Pink, 5=Blue).
                            # The engine uses 0-indexed (0=Pink, 4=Blue).
                            val_int = int(target_name) - 1
                        except (ValueError, TypeError):
                            val_int = 0  # Default to pink if unknown
                        # Source (a) is encoded in attr in ability.py, so we just set it here
                        params["source_color"] = 0
                        target = TargetType.PLAYER  # Reset target so it doesn't try to target member '5'
                    elif val and val.isdigit():
                        # Standard TRANSFORM_COLOR(src) -> dst
                        try:
                            source_color = int(val)
                            dest_color = int(target_name) - 1 if target_name and target_name.isdigit() else 0
                            val_int = max(0, dest_color)
                            params["source_color"] = source_color
                            target = TargetType.PLAYER
                        except (TypeError, ValueError):
                            pass

                # Special parsing for TRANSFORM_BLADES(ALL) -> X
                if etype == EffectType.TRANSFORM_BLADES:
                    # If val was "ALL", we want to extract the destination from target_name
                    if val == "ALL" and target_name:
                        try:
                            val_int = int(target_name)
                            # Clear destination since we've extracted the value
                            if "destination" in params and params["destination"] == target_name:
                                del params["destination"]
                            target = TargetType.MEMBER_SELF  # targeting the selected member
                        except (ValueError, TypeError):
                            val_int = 99  # Fallback to ALL if not a number
                    elif val and val.isdigit():
                        # Direct value: TRANSFORM_BLADES(3) -> TARGET
                        val_int = int(val)

                if etype == EffectType.LOOK_AND_CHOOSE and "choose_count" not in params:
                    params["choose_count"] = 1

                # Special handling for SET_HEART_COST - parse array format [2,2,3,3,6,6]
                if etype == EffectType.SET_HEART_COST and val:
                    # Check if val is an array format like [2,2,3,3,6,6]
                    if val.startswith("[") and val.endswith("]"):
                        # Parse the array and convert to raw_val format
                        params["raw_val"] = val
                        val_int = 0
                    else:
                        # Try to parse as heart cost string like "2xYELLOW,2xGREEN,2xPURPLE"
                        # Strip quotes from the value
                        clean_val = val.strip('"').strip("'")
                        params["raw_val"] = clean_val

                effects.append(Effect(etype, val_int, val_cond, target, params, is_optional=is_opt))
                last_target = target

                # --- SELECT_MODE: Convert inline OPTION_N params to modal_options ---
                if etype == EffectType.SELECT_MODE:
                    option_keys = sorted(
                        [k for k in params if re.match(r"OPTION_\d+", str(k), re.I)],
                        key=lambda k: int(re.search(r"\d+", k).group()),
                    )
                    if option_keys:
                        modal_opts = []
                        for ok in option_keys:
                            opt_text = str(params[ok])
                            # Parse each option value as an effect string
                            sub_effects = self._parse_pseudocode_effects(opt_text)
                            modal_opts.append(sub_effects)
                        effects[-1].modal_options = modal_opts
                        # Clean up OPTION_N keys from params
                        for ok in option_keys:
                            del params[ok]

                if is_chained:
                    chained_str = f"{target_name}{rest}"
                    effects.extend(self._parse_pseudocode_effects(chained_str, last_target=target))
        return effects


# Convenience function
def parse_ability_text(text: str) -> List[Ability]:
    """Parse ability text using the V2 parser."""
    parser = AbilityParserV2()
    return parser.parse(text)
