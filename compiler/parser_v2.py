# -*- coding: utf-8 -*-
"""New multi-pass ability parser using the pattern registry system.

This parser replaces the legacy 3500-line spaghetti parser with a clean,
modular architecture based on:
1. Declarative patterns organized by phase
2. Multi-pass parsing: Trigger → Conditions → Effects → Modifiers
3. Proper optionality handling (fixes the is_optional bug)
4. Structural Lexing: Balanced-brace scanning instead of greedy regex
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from engine.models.ability import (
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

from .aliases import (
    CONDITION_ALIASES,
    EFFECT_ALIASES,
    EFFECT_ALIASES_WITH_PARAMS,
    IGNORED_CONDITIONS,
    KEYWORD_CONDITIONS,
    MAX_SELECT_ALL,
    TRIGGER_ALIASES,
)

# =============================================================================
# Precompiled Regex Patterns
# =============================================================================

# Condition parsing patterns
_RE_CONDITION_NAME = re.compile(r"(\w+)(?:\s*\{(.*)\})?")
_RE_CONDITION_PARENS = re.compile(r"\((.*?)\)")
_RE_CONDITION_EQUALS = re.compile(r"=\s*[\"']?(.*?)[\"']?$")

# Effect parsing patterns
_RE_EFFECT_FULL = re.compile(r"^([\w_]+)(?:\((.*?)\))?\s*(?:(\{.*?\})\s*)?(?:->\s*([\w, _]+))?(.*)$")
_RE_EFFECT_COMPACT = re.compile(r"(\w+)\((.*?)\)\s*->\s*(\w+)(.*)")
_RE_GRANT_ABILITY = re.compile(r"GRANT_ABILITY\((.*?),\s*\"(.*?)\"\)")

# Cost parsing patterns
_RE_COST_FORMAT = re.compile(r"(\w+)(?:\((.*?)\))?(.*)")

# Trigger parsing patterns
_RE_TRIGGER_KEYWORD = re.compile(r"TRIGGER:", re.I)
_RE_TRIGGER_PARENS = re.compile(r"\(.*?\)")

# Value parsing patterns
_RE_COST_GE = re.compile(r"COST_GE=(\d+)")
_RE_COST_COMPARISON = re.compile(r"COST_(GE|LE|GT|LT|EQ)=(\d+)")


# =============================================================================
# Structural Lexing: Balanced-Brace Scanner
# =============================================================================


@dataclass
class StructuredEffect:
    """Represents a structurally parsed effect before type resolution."""

    name: str = ""
    value: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    target: str = ""
    raw: str = ""

    def __repr__(self):
        return (
            f"StructuredEffect(name={self.name!r}, value={self.value!r}, params={self.params}, target={self.target!r})"
        )


class StructuralLexer:
    """
    Balanced-brace scanner for pseudocode parsing.

    Instead of using greedy regex, this lexer treats pseudocode as a structured
    format with specific delimiters:
    - Value/Args are always inside (...)
    - Attributes/Filters are always inside {...}
    - Target is always preceded by ->

    This prevents the "Name" group from accidentally swallowing the { of the
    parameter block, which was causing keys like "recover_live(1) {filter".
    """

    # Opening and closing delimiters
    PAREN_OPEN = "("
    PAREN_CLOSE = ")"
    BRACE_OPEN = "{"
    BRACE_CLOSE = "}"

    @staticmethod
    def extract_balanced(text: str, start_pos: int, open_char: str, close_char: str) -> Tuple[str, int]:
        """
        Extract content between balanced delimiters starting at start_pos.

        Args:
            text: The full text string
            start_pos: Position of the opening delimiter
            open_char: The opening delimiter character
            close_char: The closing delimiter character

        Returns:
            Tuple of (extracted content without delimiters, position after closing delimiter)
        """
        if start_pos >= len(text) or text[start_pos] != open_char:
            return "", start_pos

        depth = 1
        pos = start_pos + 1
        content_start = pos

        while pos < len(text) and depth > 0:
            char = text[pos]
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
            elif char == '"':
                # Skip over quoted strings to avoid counting delimiters inside them
                pos += 1
                while pos < len(text) and text[pos] != '"':
                    if text[pos] == "\\" and pos + 1 < len(text):
                        pos += 1  # Skip escaped character
                    pos += 1
            elif char == "'":
                # Handle single quotes too
                pos += 1
                while pos < len(text) and text[pos] != "'":
                    if text[pos] == "\\" and pos + 1 < len(text):
                        pos += 1
                    pos += 1
            pos += 1

        if depth == 0:
            return text[content_start : pos - 1], pos
        else:
            # Unbalanced - return what we have
            return text[content_start:], pos

    @classmethod
    def parse_effect(cls, text: str) -> StructuredEffect:
        """
        Parse a single effect string structurally.

        Example: RECOVER_LIVE(1) {FILTER="GROUP=0"} -> CARD_HAND

        Steps:
        1. Find and extract (...) value block
        2. Find and extract {...} params block
        3. Find -> target
        4. What remains is the NAME
        """
        result = StructuredEffect(raw=text)
        text = text.strip()

        # Step 1: Extract value block (...)
        paren_pos = cls._find_delimiter(text, cls.PAREN_OPEN)
        if paren_pos != -1:
            # Everything before ( is potentially the name
            result.name = text[:paren_pos].strip()
            value_content, end_pos = cls.extract_balanced(text, paren_pos, cls.PAREN_OPEN, cls.PAREN_CLOSE)
            result.value = value_content.strip()
            remaining = text[end_pos:].strip()
        else:
            # No value block - need to find other delimiters
            remaining = text
            result.name = ""

        # Step 2: Extract params block {...}
        brace_pos = cls._find_delimiter(remaining, cls.BRACE_OPEN)
        if brace_pos != -1:
            # If name wasn't set from parens, take everything before {
            if not result.name:
                result.name = remaining[:brace_pos].strip()
            params_content, end_pos = cls.extract_balanced(remaining, brace_pos, cls.BRACE_OPEN, cls.BRACE_CLOSE)
            result.params = cls._parse_params_content(params_content)
            remaining = remaining[end_pos:].strip()
        elif not result.name:
            # Still no name - check for target arrow
            arrow_pos = remaining.find("->")
            if arrow_pos != -1:
                result.name = remaining[:arrow_pos].strip()
                remaining = remaining[arrow_pos:].strip()
            else:
                result.name = remaining.strip()
                remaining = ""

        # Step 3: Extract target (-> TARGET)
        arrow_pos = remaining.find("->")
        if arrow_pos != -1:
            target_part = remaining[arrow_pos + 2 :].strip()
            # Target might have trailing content, just take first word
            target_parts = target_part.split()
            if target_parts:
                result.target = target_parts[0].strip(",")
            # Check if there's anything before the arrow that should be part of name
            if arrow_pos > 0 and not result.name:
                result.name = remaining[:arrow_pos].strip()

        # Clean up name - remove any trailing punctuation
        result.name = result.name.strip(" ,;")

        return result

    @classmethod
    def _find_delimiter(cls, text: str, delimiter: str) -> int:
        """Find the first occurrence of delimiter not inside quotes."""
        in_double_quote = False
        in_single_quote = False

        for i, char in enumerate(text):
            if char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == delimiter and not in_double_quote and not in_single_quote:
                return i

        return -1

    @classmethod
    def _parse_params_content(cls, content: str) -> Dict[str, Any]:
        """
        Parse parameter content like: FILTER="GROUP=0", COUNT=2
        Respects quotes and nested structures.
        """
        params = {}
        if not content.strip():
            return params

        # Split by comma but respect quotes and nested braces
        parts = []
        current = ""
        depth = 0
        in_double_quote = False
        in_single_quote = False

        for char in content:
            if char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == "{" and not in_double_quote and not in_single_quote:
                depth += 1
            elif char == "}" and not in_double_quote and not in_single_quote:
                depth -= 1
            elif char == "," and not in_double_quote and not in_single_quote and depth == 0:
                parts.append(current.strip())
                current = ""
                continue
            current += char

        if current.strip():
            parts.append(current.strip())

        # Parse each KEY=VAL part
        for part in parts:
            if "=" in part:
                eq_pos = part.index("=")
                key = part[:eq_pos].strip().upper()
                val = part[eq_pos + 1 :].strip()

                # Strip quotes
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]

                # Type conversion
                if val.isdigit():
                    val = int(val)
                elif val.upper() == "TRUE":
                    val = True
                elif val.upper() == "FALSE":
                    val = False

                params[key] = val

        return params

    @classmethod
    def split_effects(cls, text: str) -> List[str]:
        """
        Split multiple effects by semicolon, respecting nested structures.

        Example: "DRAW(1); MOVE_TO_DECK(2) {zone=discard}"
        -> ["DRAW(1)", "MOVE_TO_DECK(2) {zone=discard}"]
        """
        return cls.split_respecting_nesting(text, delimiter=";")

    @staticmethod
    def split_respecting_nesting(
        text: str, delimiter: str = ";", extra_delimiters: Optional[List[str]] = None
    ) -> List[str]:
        """
        Split text by delimiter(s), respecting nested braces, parentheses, and quotes.

        Args:
            text: The text to split
            delimiter: Primary delimiter (default: semicolon)
            extra_delimiters: Additional delimiters to split on (e.g., [',', ' OR '])

        Returns:
            List of split parts with whitespace stripped
        """
        parts = []
        current = ""
        depth = 0
        in_double_quote = False
        in_single_quote = False
        all_delimiters = [delimiter] + (extra_delimiters or [])
        i = 0

        while i < len(text):
            char = text[i]

            if char == '"':
                in_double_quote = not in_double_quote
            elif char == "'":
                in_single_quote = not in_single_quote
            elif char == "{" and not in_double_quote and not in_single_quote:
                depth += 1
            elif char == "}" and not in_double_quote and not in_single_quote:
                depth -= 1
            elif char == "(" and not in_double_quote and not in_single_quote:
                depth += 1
            elif char == ")" and not in_double_quote and not in_single_quote:
                depth -= 1

            # Check for delimiters only at depth 0 and not in quotes
            if depth == 0 and not in_double_quote and not in_single_quote:
                matched = False
                for delim in all_delimiters:
                    if text[i : i + len(delim)] == delim:
                        if current.strip():
                            parts.append(current.strip())
                        current = ""
                        i += len(delim)
                        matched = True
                        break
                if matched:
                    continue

            current += char
            i += 1

        if current.strip():
            parts.append(current.strip())

        return parts


class AbilityParserV2:
    """Multi-pass ability parser using pattern registry."""

    def __init__(self):
        pass

    def parse(self, text: str) -> List[Ability]:
        """Parse ability text into structured Ability objects."""
        # Preprocess
        text = text.replace("<br>", "\n")

        # Detect format
        triggers = ["TRIGGER:", "CONDITION:", "EFFECT:", "COST:"]

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
                        current_triggers.append(t_text)
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
                    # Mandatory initial costs go to 'costs' for transactional shell payment.
                    # Optional or Mid-Ability costs go to 'instructions' for interpreter handling.
                    # Complex costs (SELECT_MEMBER, etc.) MUST be in bytecode
                    is_complex = c.type == AbilityCostType.NONE

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
                new_effects = self._parse_pseudocode_effects(eff_str, last_target=last_target)
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
                                except:
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
                        except:
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
        costs = []
        # Use the shared split method with multiple delimiters
        parts = StructuralLexer.split_respecting_nesting(text, delimiter=",", extra_delimiters=[" OR ", ";"])

        for p in parts:
            if not p:
                continue
            # Format: NAME(VAL) {PARAMS} -> DEST (Optional)
            m = re.match(r"^([\w_]+)(?:\((.*?)\))?\s*(?:(\{.*?\})\s*)?(?:->\s*([\w, _]+))?(.*)$", p.strip())
            if m:
                name, val_str, brace_params, destination, rest = m.groups()
                rest = rest or ""

                # Manual Mapping for specific cost names
                if name == "MOVE_TO_DECK":
                    if (
                        'from="discard"' in (brace_params or "").lower()
                        or "from='discard'" in (brace_params or "").lower()
                    ):
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
                if cost_name == "ENERGY":
                    cost_name = "ENERGY"
                if "REVEAL_HAND" in cost_name:
                    cost_name = "REVEAL_HAND"

                # Special mapping for ENERGY_CHARGE as a cost (optional/conditional)
                if cost_name == "ENERGY_CHARGE":
                    ctype = AbilityCostType.NONE
                else:
                    ctype = getattr(AbilityCostType, cost_name, AbilityCostType.NONE)

                is_opt = "(Optional)" in rest or "(Optional)" in (brace_params or "") or " OR " in text
                params = self._parse_pseudocode_params(brace_params or "")
                if destination:
                    params["destination"] = destination.strip().lower()

                # If it was ENERGY_CHARGE or CALC_SUM_COST or SELECT_CARDS or SELECT_MEMBER, ensure we have enough info
                if cost_name in ["ENERGY_CHARGE", "CALC_SUM_COST", "SELECT_CARDS", "SELECT_MEMBER"]:
                    params["cost_type_name"] = cost_name

                costs.append(Cost(ctype, val, is_optional=is_opt, params=params))
        return costs

    def _parse_pseudocode_conditions(self, text: str) -> List[Condition]:
        conditions = []
        # Use the shared split method with multiple delimiters
        parts = StructuralLexer.split_respecting_nesting(text, delimiter=",", extra_delimiters=[" OR ", ";"])

        for p in parts:
            if not p:
                continue
            negated = p.startswith("NOT ")
            name_part = p[4:] if negated else p

            # Support ! as prefix for negation
            if not negated and name_part.startswith("!"):
                negated = True
                name_part = name_part[1:]

            # Conditions can legitimately carry multiple brace blocks, e.g.
            # COUNT_SUCCESS_LIVE(PLAYER) {FILTER="GROUP_ID=0"} {MIN=2}
            # Parse and merge all of them before matching the condition name.
            params = {}
            for brace_block in re.findall(r"\{([^{}]*)\}", name_part):
                params.update(self._parse_pseudocode_params("{" + brace_block + "}"))

            name_part_no_braces = re.sub(r"\s*\{[^{}]*\}", "", name_part).strip()

            # Match "NAME(VAL) {PARAMS}" or "NAME {PARAMS}" or "NAME"
            m = re.match(r"(\w+)(?:\((.*?)\))?", name_part_no_braces)
            if m:
                name = m.group(1).upper()
                val_in_parens = m.group(2)

                if val_in_parens:
                    # Handle positional arguments in parentheses like COUNT_MEMBER(UNIT_CATCHU, STAGE)
                    v_parts = [vp.strip() for vp in val_in_parens.split(",")]
                    for vp in v_parts:
                        vp_up = vp.upper()
                        if vp_up.startswith("UNIT_"):
                            params["unit"] = vp[5:]
                        elif vp_up.startswith("GROUP_"):
                            params["group"] = vp[6:]
                        elif vp_up in [
                            "STAGE",
                            "HAND",
                            "DISCARD",
                            "ENERGY",
                            "SUCCESS_LIVE",
                            "LIVE_ZONE",
                            "SUCCESS_PILE",
                        ]:
                            params["zone"] = vp_up
                        elif "=" in vp:
                            sk, sv = [s.strip().strip('"').strip("'") for s in vp.split("=", 1)]
                            params[sk.lower()] = sv
                        elif ":" in vp:
                            sk, sv = [s.strip().strip('"').strip("'") for s in vp.split(":", 1)]
                            params[sk.lower()] = sv
                        else:
                            params["val"] = vp

                # Check for target arrow -> TARGET
                if "->" in name_part_no_braces:
                    arrow_pos = name_part_no_braces.find("->")
                    target_part = name_part_no_braces[arrow_pos + 2 :].strip()
                    # Target might have trailing content (like another condition), take first word
                    target_word = target_part.split()[0].strip().upper()
                    if target_word:
                        params["target"] = target_word
                    # The name match regex will naturally ignore the -> part if we split it early
                    # but since the regex already matched m, we just need to make sure we don't
                    # double-process it in remaining_part if it was handled here.

                # Check for comparison operators outside of {PARAMS}
                remaining_part = name_part_no_braces[len(m.group(0)) :].strip()
                if "->" in remaining_part:
                    # Strip the arrow and target from remaining_part to avoid confusing the comparison regex
                    arrow_pos = remaining_part.find("->")
                    remaining_part = remaining_part[:arrow_pos].strip()

                if remaining_part:
                    # Check for >=, <=, >, <, =
                    comp_match = re.match(r"(>=|<=|>|<|=)\s*[\"']?(.*?)[\"']?$", remaining_part)
                    if comp_match:
                        op_map = {">=": "GE", "<=": "LE", ">": "GT", "<": "LT", "=": "EQ"}
                        params["comparison"] = op_map.get(comp_match.group(1), "GE")
                        params["val"] = comp_match.group(2)
                    else:
                        # Fallback for old =VAL logic
                        e_m = re.search(r"=\s*[\"']?(.*?)[\"']?$", remaining_part)
                        if e_m:
                            params["val"] = e_m.group(1)

                params["raw_cond"] = name

                # Determine negation for NOT_MOVED_THIS_TURN
                is_negated = negated

                # === Apply condition aliases using module-level constants ===
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

                # Check if this is an ignored condition
                if name in IGNORED_CONDITIONS:
                    ctype = ConditionType.NONE
                    conditions.append(Condition(ctype, params, is_negated=is_negated))
                    continue

                # Check for HAS_KEYWORD fallback conditions
                if name in KEYWORD_CONDITIONS:
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = KEYWORD_CONDITIONS[name]
                    conditions.append(Condition(ctype, params, is_negated=is_negated))
                    continue

                # Check for prefix-based HAS_KEYWORD conditions (MATCH_*, DID_ACTIVATE_*)
                if name.startswith("MATCH_") or name.startswith("DID_ACTIVATE_"):
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = name
                    conditions.append(Condition(ctype, params, is_negated=is_negated))
                    continue

                # Special handling for COUNT_SUCCESS_LIVES or COUNT_CARDS(ZONE="SUCCESS_PILE" / "SUCCESS_LIVE")
                if name in ["COUNT_SUCCESS_LIVES", "COUNT_SUCCESS_LIVE", "COUNT_CARDS"]:
                    z_val = (params.get("zone") or "").upper()
                    print(f"DEBUG: Processing {name}, zone={z_val}, params={params}")
                    if name == "COUNT_CARDS" and z_val not in ["SUCCESS_PILE", "SUCCESS_LIVE"]:
                        # Not a success pile check, fall through to default (GROUP_FILTER) or handle elsewhere
                        pass
                    else:
                        ctype = ConditionType.COUNT_SUCCESS_LIVE
                        if "target" not in params:
                            target_val = str(params.get("PLAYER", params.get("val", "self"))).upper()
                            if target_val == "OPPONENT" or target_val == "1":
                                params["target"] = "opponent"
                            else:
                                params["target"] = "self"

                            if "PLAYER" in params:
                                del params["PLAYER"]
                            if "val" in params and params["val"].upper() in ["PLAYER", "OPPONENT"]:
                                del params["val"]
                        if "COUNT" in params:
                            params["value"] = params["COUNT"]
                            params["comparison"] = "EQ"
                            del params["COUNT"]
                        conditions.append(Condition(ctype, params, is_negated=is_negated))
                        continue

                # Check for condition aliases
                if name in CONDITION_ALIASES:
                    canonical_name, extra_params = CONDITION_ALIASES[name]
                    try:
                        ctype = ConditionType[canonical_name]
                    except KeyError:
                        ctype = ConditionType.NONE
                    # Merge extra params (don't overwrite existing)
                    for pk, pv in extra_params.items():
                        if pk not in params:
                            params[pk] = pv
                    # Handle NOT_MOVED_THIS_TURN negation
                    if name == "NOT_MOVED_THIS_TURN":
                        is_negated = True
                    conditions.append(Condition(ctype, params, is_negated=is_negated))
                    continue

                # Special handling for AREA_IN
                if name == "AREA_IN" or name == "AREA":
                    val = params.get("val", "").upper().strip('"')
                    if val == "CENTER" or params.get("zone") == "CENTER" or params.get("area") == "CENTER":
                        ctype = ConditionType.IS_CENTER
                    else:
                        ctype = ConditionType.AREA_CHECK
                        params["keyword"] = "AREA_CHECK"
                        area_map = {"LEFT_SIDE": 0, "LEFT": 0, "RIGHT_SIDE": 2, "RIGHT": 2}
                        if val in area_map:
                            params["value"] = area_map[val]
                    conditions.append(Condition(ctype, params, is_negated=is_negated))
                    continue

                # Special handling for COST_LEAD with area param
                if name == "COST_LEAD" and params.get("area") == "CENTER":
                    params["zone"] = "CENTER_STAGE"
                    del params["area"]

                # Special handling for REVEALED_CONTAINS with type params
                if name == "REVEALED_CONTAINS":
                    if "TYPE_LIVE" in params:
                        params["value"] = "live"
                    if "TYPE_MEMBER" in params:
                        params["value"] = "member"

                # Default: try to resolve from ConditionType enum
                ctype = getattr(ConditionType, name, ConditionType.NONE)

                conditions.append(Condition(ctype, params, is_negated=is_negated))
        return conditions

    def _parse_pseudocode_effects(self, text: str, last_target: TargetType = TargetType.PLAYER) -> List[Effect]:
        effects = []
        # Use the shared split method
        parts = StructuralLexer.split_respecting_nesting(text, delimiter=";")

        for p in parts:
            if not p:
                continue

            # Special handling for GRANT_ABILITY(TARGET, "ABILITY")
            if "GRANT_ABILITY" in p:
                grant_match = re.search(r"GRANT_ABILITY\((.*?),\s*\"(.*?)\"\)", p)
                if grant_match:
                    target_str, ability_str = grant_match.groups()
                    params = {"target_str": target_str, "ability_text": ability_str}
                    target = TargetType.PLAYER
                    if "MEMBER" in target_str:
                        target = TargetType.MEMBER_SELECT
                    effects.append(Effect(EffectType.GRANT_ABILITY, 0, ConditionType.NONE, target, params))
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

                # If we matched (Optional) via the explicit group, we should ensure is_optional is set later.
                # The current logic checks for "(Optional)" in rest or p, which is sufficient.

                # Extract params only from the isolated {...} block if found
                params = self._parse_pseudocode_params(param_block) if param_block else {}

                # Target Resolution
                target = last_target
                is_chained = False
                if target_name:
                    target_name = target_name.strip().upper()
                    if hasattr(EffectType, target_name):
                        is_chained = True
                    elif target_name == "SELF" or target_name == "MEMBER_SELF":
                        target = TargetType.MEMBER_SELF
                    elif target_name == "PLAYER":
                        target = TargetType.PLAYER
                    elif target_name == "OPPONENT":
                        target = TargetType.OPPONENT
                    elif target_name == "ALL_PLAYERS":
                        target = TargetType.ALL_PLAYERS
                    elif target_name == "CARD_HAND":
                        target = TargetType.CARD_HAND
                    elif "MEMBER_" in target_name:
                        target = TargetType.MEMBER_SELECT  # Fallback for complex targets
                    else:
                        try:
                            target = TargetType[target_name]
                        except:
                            # If not a valid target type, it might be a destination (e.g. DECK_BOTTOM)
                            params["destination"] = target_name.lower()
                            target = last_target

                # Legacy SELF mapping (If -> SELF exists in text)
                if "-> SELF" in p or "-> self" in p:
                    target = TargetType.MEMBER_SELF

                # Apply effect aliases using module-level constants
                name_up = name.upper()

                # First check simple aliases (name-only transformations)
                if name_up in EFFECT_ALIASES:
                    name_up = EFFECT_ALIASES[name_up]

                # Then check aliases with params
                if name_up in EFFECT_ALIASES_WITH_PARAMS:
                    canonical_name, extra_params = EFFECT_ALIASES_WITH_PARAMS[name_up]
                    name_up = canonical_name
                    # Merge extra params (don't overwrite existing)
                    for pk, pv in extra_params.items():
                        if pk not in params:
                            params[pk] = pv
                    # Handle target modifications
                    if extra_params.get("target") == "MEMBER_SELF":
                        target = TargetType.MEMBER_SELF

                # Special cases that need dynamic handling
                if name_up == "ADD_TAG":
                    name_up = "META_RULE"
                    params["tag"] = val

                if name_up.startswith("PLAY_MEMBER"):
                    if params.get("zone") == "DISCARD" or "DISCARD" in p.upper() or "DISCARD" in text.upper():
                        name_up = "PLAY_MEMBER_FROM_DISCARD"
                    else:
                        name_up = "PLAY_MEMBER_FROM_HAND"

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
                    etype = EffectType.META_RULE
                    params["raw_effect"] = name.upper()

                if target_name and target_name.upper() == "SLOT" and params.get("self"):
                    target = TargetType.MEMBER_SELF
                is_opt = "(Optional)" in rest or "(Optional)" in p

                val_int = 0
                val_cond = ConditionType.NONE

                # Check for comma-separated positional params in val (e.g. META_RULE(SCORE_RULE, ALL_ENERGY_ACTIVE))
                if val and "," in val:
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
                                except:
                                    pass
                # Check if val is a condition type (e.g. COUNT_STAGE)
                elif val and hasattr(ConditionType, val):
                    val_cond = getattr(ConditionType, val)
                elif etype == EffectType.REVEAL_UNTIL and val:
                    # Special parsing for REVEAL_UNTIL(CONDITION)
                    if "TYPE_LIVE" in val:
                        val_cond = ConditionType.TYPE_CHECK
                        params["card_type"] = "live"
                    elif "TYPE_MEMBER" in val:
                        val_cond = ConditionType.TYPE_CHECK
                        params["card_type"] = "member"

                    # Handle COST_GE/LE in REVEAL_UNTIL
                    if "COST_" in val:
                        # Extract COST_GE=10 or COST_LE=X
                        cost_match = re.search(r"COST_(GE|LE|GT|LT|EQ)=(\d+)", val)
                        if cost_match:
                            comp, cval = cost_match.groups()
                            # If we also have TYPE check, we need to combine them?
                            # Bytecode only supports one condition on REVEAL_UNTIL.
                            # We'll prioritize COST check if present, or maybe the engine supports compound?
                            # For now, map to COST_CHECK condition.
                            val_cond = ConditionType.COST_CHECK
                            params["comparison"] = comp
                            params["value"] = int(cval)

                    if "COST_GE" in val:
                        val_cond = ConditionType.COST_CHECK
                        m_cost = re.search(r"COST_GE=(\d+)", val)
                        if m_cost:
                            params["min"] = int(m_cost.group(1))

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
                        except:
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
