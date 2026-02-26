# -*- coding: utf-8 -*-
"""New multi-pass ability parser using the pattern registry system.

This parser replaces the legacy 3500-line spaghetti parser with a clean,
modular architecture based on:
1. Declarative patterns organized by phase
2. Multi-pass parsing: Trigger → Conditions → Effects → Modifiers
3. Proper optionality handling (fixes the is_optional bug)
4. Structural Lexing: Balanced-brace scanning instead of greedy regex
"""

import copy
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Match, Optional, Tuple

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

from .patterns.base import PatternPhase
from .patterns.registry import PatternRegistry, get_registry


# =============================================================================
# Constants: Alias Mappings
# =============================================================================

# Trigger type aliases (pseudocode -> canonical name)
TRIGGER_ALIASES = {
    "ON_YELL": "ON_REVEAL",
    "ON_YELL_SUCCESS": "ON_REVEAL",
    "ON_ACTIVATE": "ACTIVATED",
    "JIDOU": "ON_LEAVES",
    "ON_REVEAL": "ON_REVEAL",
    "ON_MEMBER_DISCARD": "ON_LEAVES",
    "ON_DISCARDED": "ON_LEAVES",
    "ON_REMOVE": "ON_LEAVES",
    "ON_SET": "ON_PLAY",
    "ON_STAGE_ENTRY": "ON_PLAY",
    "ON_PLAY_OTHER": "ON_PLAY",
    "ON_REVEAL_OTHER": "ON_REVEAL",
    "ON_LIVE_SUCCESS_OTHER": "ON_LIVE_SUCCESS",
    "ON_TURN_START": "TURN_START",
    "ON_TURN_END": "TURN_END",
    "ON_TAP": "ACTIVATED",
    "ON_REVEAL_SELF": "ON_REVEAL",
    "ON_LIVE_SUCCESS_SELF": "ON_LIVE_SUCCESS",
    "ACTIVATED_FROM_DISCARD": "ACTIVATED",
    "ON_ENERGY_CHARGE": "ACTIVATED",
    "ON_DRAW": "ACTIVATED",
    "ON_POSITION_CHANGE": "ON_LEAVES",
    "ON_MOVE": "ON_LEAVES",
}

# Effect type aliases (pseudocode -> canonical name)
# Simple name-only aliases (no param modifications)
EFFECT_ALIASES = {
    "TAP_PLAYER": "TAP_MEMBER",
    "CHARGE_ENERGY": "ENERGY_CHARGE",
    "MOVE_DISCARD": "MOVE_TO_DISCARD",
    "MOVE_HAND": "ADD_TO_HAND",
    "MOVE_TO_HAND": "ADD_TO_HAND",
    "ADD_HAND": "ADD_TO_HAND",
    "SELECT_LIMIT": "REDUCE_LIVE_SET_LIMIT",
    "POWER_UP": "BUFF_POWER",
    "REDUCE_SET_LIMIT": "REDUCE_LIVE_SET_LIMIT",
    "REDUCE_LIMIT": "REDUCE_LIVE_SET_LIMIT",
    "REDUCE_HEART": "REDUCE_HEART_REQ",
    "MOVE_DECK": "MOVE_TO_DECK",
    "SET_BASE_BLADES": "SET_BLADES",
    "GRANT_HEARTS": "ADD_HEARTS",
    "GRANT_HEART": "ADD_HEARTS",
    "CHANGE_BASE_HEART": "TRANSFORM_HEART",
    "SELECT_LIVE_CARD": "SELECT_LIVE",
    "POSITION_CHANGE": "MOVE_MEMBER",
    "INCREASE_HEART": "INCREASE_HEART_COST",
    "CHANGE_YELL_BLADE_COLOR": "TRANSFORM_COLOR",
    "OPPONENT_CHOICE": "OPPONENT_CHOOSE",
    "LOOK_AND_CHOOSE_ORDER": "ORDER_DECK",
    "LOOK_AND_CHOOSE_REVEAL": "LOOK_AND_CHOOSE",
    "SET_HEART_REQ": "SET_HEART_COST",
    "CYCLE_AREAS": "SWAP_AREA",
    "SELECT_OPTION": "SELECT_MODE",
    "CHOICE_MODE": "SELECT_MODE",
}

# Effect aliases that require additional param modifications
# Format: alias -> (canonical_name, params_dict)
EFFECT_ALIASES_WITH_PARAMS = {
    "CHARGE_SELF": ("ENERGY_CHARGE", {"target": "MEMBER_SELF"}),
    "PLACE_ENERGY_WAIT": ("PLACE_UNDER", {"type": "energy", "wait": True}),
    "RECOVER_FROM_CHEER": ("RECOVER_MEMBER", {"source": "yell"}),
    "BOOST_SCORE_PER_COLOR": ("BOOST_SCORE", {"multiplier": "color"}),
    "LOOK_AND_CHOOSE_REVEAL": ("LOOK_AND_CHOOSE", {"reveal": True}),
    "REMOVE_SELF": ("MOVE_TO_DISCARD", {"target": "MEMBER_SELF"}),
    "SWAP_SELF": ("SWAP_ZONE", {"target": "MEMBER_SELF"}),
    "TRIGGER_YELL_AGAIN": ("META_RULE", {"meta_type": "TRIGGER_YELL_AGAIN"}),
    "DISCARD_HAND": ("MOVE_TO_DISCARD", {"source": "HAND", "destination": "discard"}),
    "RECOVER_LIVE": ("RECOVER_LIVE", {"source": "discard"}),
    "RECOVER_MEMBER": ("RECOVER_MEMBER", {"source": "discard"}),
    "SELECT_RECOVER_LIVE": ("RECOVER_LIVE", {"source": "discard"}),
    "SELECT_RECOVER_MEMBER": ("RECOVER_MEMBER", {"source": "discard"}),
    "DISCARD_UNTIL": ("MOVE_TO_DISCARD", {"operation": "UNTIL_SIZE"}),
    "YELL_MULLIGAN": ("META_RULE", {"meta_type": "ACTION_YELL_MULLIGAN"}),
}

# Maximum value for "ALL" selector
MAX_SELECT_ALL = 99

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

# Condition type aliases (pseudocode -> canonical name)
# Format: alias -> (canonical_name, extra_params)
CONDITION_ALIASES = {
    # Simple name-only aliases
    "ONCE": ("TURN_1", {}),
    "TURN_1": ("TURN_1", {}),
    "ALL_MEMBERS": ("GROUP_FILTER", {"all": True}),
    "COUNT_LIVE": ("COUNT_LIVE_ZONE", {}),
    "HAS_SUCCESS_LIVE": ("COUNT_SUCCESS_LIVE", {}),
    "SUM_ENERGY": ("COUNT_ENERGY", {}),
    "BATON_FROM_NAME": ("BATON", {}),
    "MOVED_THIS_TURN": ("HAS_MOVED", {}),
    "DECK_REFRESHED_THIS_TURN": ("DECK_REFRESHED", {}),
    "HAND_SIZE_DIFF": ("OPPONENT_HAND_DIFF", {}),
    "BATON_TOUCH": ("BATON", {}),
    "BATON_COUNT": ("BATON", {}),
    "BATON": ("BATON", {}),
    "HAND_SIZE": ("COUNT_HAND", {}),
    "BLADES": ("COUNT_BLADES", {}),
    "TOTAL_BLADES": ("TOTAL_BLADES", {}),
    "HEART_LEAD": ("HEART_LEAD", {}),
    "OPPONENT_HAS_WAIT": ("OPPONENT_HAS_WAIT", {}),
    "IS_IN_DISCARD": ("IS_IN_DISCARD", {}),
    "COUNT_ENERGY_EXACT": ("COUNT_ENERGY_EXACT", {}),
    "COUNT_BLADE_HEART_TYPES": ("COUNT_BLADE_HEART_TYPES", {}),
    "OPPONENT_HAS_EXCESS_HEART": ("OPPONENT_HAS_EXCESS_HEART", {}),
    "SCORE_TOTAL": ("SCORE_TOTAL_CHECK", {}),
    "HAS_EXCESS_HEART": ("HAS_EXCESS_HEART", {}),
    "COUNT_MEMBER": ("COUNT_STAGE", {}),
    "TOTAL_HEARTS": ("COUNT_HEARTS", {}),
    "ALL_MEMBER": ("GROUP_FILTER", {}),
    "MEMBER_AT_SLOT": ("GROUP_FILTER", {}),
    "HAS_LIVE_HEART_COLORS": ("HAS_COLOR", {}),
    "COUNT_REVEALED": ("COUNT_HAND", {}),
    "COUNT_DISCARDED_THIS_TURN": ("COUNT_DISCARD", {}),
    "CHECK_GROUP_FILTER": ("GROUP_FILTER", {}),
    "FILTER": ("GROUP_FILTER", {}),
    "NAME_MATCH": ("GROUP_FILTER", {"filter": "NAME_MATCH"}),
    "SUCCESS": ("MODAL_ANSWER", {}),
    "MATCH_PREVIOUS": ("MODAL_ANSWER", {}),
    
    # Aliases with params
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
    "SCORE_TOTAL": ("SCORE_COMPARE", {"type": "score", "comparison": "GE"}),
    "COUNT_ACTIVATED": ("COUNT_STAGE", {"filter": "ACTIVATED"}),
    "HAS_REMAINING_HEART": ("COUNT_HEARTS", {"min": 1}),
    "COUNT_CHARGED_ENERGY": ("COUNT_ENERGY", {}),
    "SUM_SUCCESS_LIVE": ("COUNT_SUCCESS_LIVE", {}),
    "SUM_HEARTS": ("COUNT_HEARTS", {}),
    "EXTRA_HEARTS": ("COUNT_HEARTS", {"min": 1}),
    "HAS_ACTIVE_ENERGY": ("COUNT_ENERGY", {"filter": "active", "min": 1}),
    "ALL_ENERGY_ACTIVE": ("COUNT_ENERGY", {"filter": "active", "comparison": "ALL"}),
    "ENERGY": ("COUNT_ENERGY", {}),
    "HAS_TYPE_LIVE": ("TYPE_CHECK", {"card_type": "live"}),
    "NOT_MOVED_THIS_TURN": ("HAS_MOVED", {}),  # negated handled separately
    # COUNT_CARDS for unique member checks across zones
    "COUNT_CARDS": ("GROUP_FILTER", {}),
    "COUNT_UNIQUE_MEMBERS": ("GROUP_FILTER", {"unique": True}),
}

# Conditions that map to HAS_KEYWORD with a keyword param
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

# Conditions that should be ignored (map to NONE)
IGNORED_CONDITIONS = {
    "TARGET",
    "IS_MAIN_PHASE",
    "MAIN_PHASE",
    "ON_YELL",
    "ON_YELL_SUCCESS",
}


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
        return f"StructuredEffect(name={self.name!r}, value={self.value!r}, params={self.params}, target={self.target!r})"


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
    PAREN_OPEN = '('
    PAREN_CLOSE = ')'
    BRACE_OPEN = '{'
    BRACE_CLOSE = '}'
    
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
                    if text[pos] == '\\' and pos + 1 < len(text):
                        pos += 1  # Skip escaped character
                    pos += 1
            elif char == "'":
                # Handle single quotes too
                pos += 1
                while pos < len(text) and text[pos] != "'":
                    if text[pos] == '\\' and pos + 1 < len(text):
                        pos += 1
                    pos += 1
            pos += 1
        
        if depth == 0:
            return text[content_start:pos - 1], pos
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
            arrow_pos = remaining.find('->')
            if arrow_pos != -1:
                result.name = remaining[:arrow_pos].strip()
                remaining = remaining[arrow_pos:].strip()
            else:
                result.name = remaining.strip()
                remaining = ""
        
        # Step 3: Extract target (-> TARGET)
        arrow_pos = remaining.find('->')
        if arrow_pos != -1:
            target_part = remaining[arrow_pos + 2:].strip()
            # Target might have trailing content, just take first word
            target_parts = target_part.split()
            if target_parts:
                result.target = target_parts[0].strip(',')
            # Check if there's anything before the arrow that should be part of name
            if arrow_pos > 0 and not result.name:
                result.name = remaining[:arrow_pos].strip()
        
        # Clean up name - remove any trailing punctuation
        result.name = result.name.strip(' ,;')
        
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
            elif char == '{' and not in_double_quote and not in_single_quote:
                depth += 1
            elif char == '}' and not in_double_quote and not in_single_quote:
                depth -= 1
            elif char == ',' and not in_double_quote and not in_single_quote and depth == 0:
                parts.append(current.strip())
                current = ""
                continue
            current += char
        
        if current.strip():
            parts.append(current.strip())
        
        # Parse each KEY=VAL part
        for part in parts:
            if '=' in part:
                eq_pos = part.index('=')
                key = part[:eq_pos].strip().upper()
                val = part[eq_pos + 1:].strip()
                
                # Strip quotes
                if (val.startswith('"') and val.endswith('"')) or \
                   (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                
                # Type conversion
                if val.isdigit():
                    val = int(val)
                elif val.upper() == 'TRUE':
                    val = True
                elif val.upper() == 'FALSE':
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
        return cls.split_respecting_nesting(text, delimiter=';')
    
    @staticmethod
    def split_respecting_nesting(
        text: str, 
        delimiter: str = ';', 
        extra_delimiters: Optional[List[str]] = None
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
            elif char == '{' and not in_double_quote and not in_single_quote:
                depth += 1
            elif char == '}' and not in_double_quote and not in_single_quote:
                depth -= 1
            elif char == '(' and not in_double_quote and not in_single_quote:
                depth += 1
            elif char == ')' and not in_double_quote and not in_single_quote:
                depth -= 1
            
            # Check for delimiters only at depth 0 and not in quotes
            if depth == 0 and not in_double_quote and not in_single_quote:
                matched = False
                for delim in all_delimiters:
                    if text[i:i+len(delim)] == delim:
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

    def __init__(self, registry: Optional[PatternRegistry] = None):
        self.registry = registry or get_registry()

    def parse(self, text: str) -> List[Ability]:
        """Parse ability text into structured Ability objects."""
        # Detect pseudocode format
        triggers = ["TRIGGER:", "CONDITION:", "EFFECT:", "COST:"]
        if any(text.strip().upper().startswith(kw) for kw in triggers):
            return self._parse_pseudocode_block(text)

        # Preprocessing
        text = self._preprocess(text)

        # Split into sentences
        sentences = self._split_sentences(text)

        # Group sentences into ability blocks
        blocks = []
        current_block = []
        for i, sentence in enumerate(sentences):
            if i > 0 and self._is_continuation(sentence, i):
                current_block.append(sentence)
            else:
                if current_block:
                    blocks.append(" ".join(current_block))
                current_block = [sentence]
        if current_block:
            blocks.append(" ".join(current_block))

        abilities = []
        for block in blocks:
            ability = self._parse_block(block)
            if ability:
                abilities.append(ability)

        return abilities

    def _parse_block(self, block: str) -> Optional[Ability]:
        """Parse a single combined ability block."""
        # Split into cost and effect parts
        colon_idx = block.find("：")
        if colon_idx == -1:
            colon_idx = block.find(":")

        if colon_idx != -1:
            cost_part = block[:colon_idx].strip()
            effect_part = block[colon_idx + 1 :].strip()
        else:
            cost_part = ""
            effect_part = block

        # === PASS 1: Extract trigger ===
        trigger, trigger_match = self._extract_trigger(block)

        # Mask trigger text from effect part to avoid double-matching
        # (e.g. "when placed in discard" shouldn't trigger "place in discard")
        effective_effect_part = effect_part
        if trigger_match:
            # Standard Japanese card formatting: [Trigger/Condition]とき、[Effect]
            # Or [Trigger/Condition]：[Effect]
            # If we see "とき", everything before it is usually trigger/condition
            toki_idx = effective_effect_part.find("とき")
            if toki_idx == -1:
                toki_idx = effective_effect_part.find("場合")

            if toki_idx != -1:
                # Mask everything up to "とき" or "場合" (plus the word itself)
                # BUT ONLY if it's in the same sentence (no punctuation in between)
                preceding = effective_effect_part[:toki_idx]
                if "。" in preceding:
                    toki_idx = -1

            if toki_idx != -1:
                mask_end = toki_idx + 2  # Length of "とき" or "場合"
                effective_effect_part = " " * mask_end + effective_effect_part[mask_end:]
            else:
                # Fallback: just mask the trigger match itself
                start, end = trigger_match.span()
                if start >= (len(block) - len(effect_part)):
                    rel_start = start - (len(block) - len(effect_part))
                    rel_end = end - (len(block) - len(effect_part))
                    if rel_start >= 0 and rel_end <= len(effect_part):
                        effective_effect_part = (
                            effect_part[:rel_start] + " " * (rel_end - rel_start) + effect_part[rel_end:]
                        )

        # === PASS 2: Extract conditions ===
        # Scan the entire block for conditions as they can appear anywhere
        conditions = self._extract_conditions(block)

        # === PASS 3: Extract effects ===
        # Only extract effects from the masked part to avoid trigger/cost confusion
        effects = self._extract_effects(effective_effect_part)

        # === PASS 5: Extract costs ===
        costs = self._extract_costs(cost_part)

        # Determine Trigger and construct Ability
        if trigger == TriggerType.NONE and not (effects or conditions or costs):
            return None

        final_trigger = trigger
        if final_trigger == TriggerType.NONE:
            # Only default to CONSTANT if we have some indicators of an ability
            # (to avoid splitting errors defaulting to Constant)
            has_ability_indicators = any(
                kw in block
                for kw in [
                    "引",
                    "スコア",
                    "プラス",
                    "＋",
                    "ブレード",
                    "ハート",
                    "控",
                    "戻",
                    "エネ",
                    "デッキ",
                    "山札",
                    "見る",
                    "公開",
                    "選ぶ",
                    "扱",
                    "得る",
                    "移動",
                    "LOOK_AND_CHOOSE",
                    "LOOK_AND_CHOOSE_REVEAL",
                ]
            )
            if has_ability_indicators:
                final_trigger = TriggerType.CONSTANT
            else:
                return None

        # Prepare instructions (Execution Order)
        instructions = []
        instructions.extend(conditions)
        instructions.extend(costs)
        instructions.extend(effects)

        ability = Ability(
            raw_text=block,
            trigger=final_trigger,
            effects=effects,
            conditions=conditions,
            costs=costs,
            instructions=instructions,
            pseudocode=block,
        )

        # === PASS 4: Apply modifiers ===
        # Scan the entire block for modifiers (OPT, optionality, etc.)
        modifiers = self._extract_modifiers(block)
        self._apply_modifiers(ability, modifiers)

        # === PASS 6: Handle "Choose Player" transformation ===
        # If the ability starts with "自分か相手を選ぶ", transform following effects into SELECT_MODE
        if "自分か相手を選ぶ" in block and len(ability.effects) > 0:
            original_effects = []
            # Find the "choose player" dummy effect (META_RULE) if present and remove it
            other_effects = []
            for eff in ability.effects:
                if eff.effect_type == EffectType.META_RULE and eff.params.get("target") == "PLAYER_SELECT":
                    continue
                other_effects.append(eff)

            if other_effects:
                # Option 1: Yourself
                self_effects = []
                for eff in other_effects:
                    new_eff = copy.deepcopy(eff)
                    new_eff.target = TargetType.SELF
                    self_effects.append(new_eff)

                # Option 2: Opponent
                opp_effects = []
                for eff in other_effects:
                    new_eff = copy.deepcopy(eff)
                    new_eff.target = TargetType.OPPONENT
                    opp_effects.append(new_eff)

                # Replace effects with a single SELECT_MODE
                ability.effects = [
                    Effect(
                        EffectType.SELECT_MODE,
                        value=1,
                        target=TargetType.SELF,
                        params={"options_text": ["自分", "相手"]},
                        modal_options=[self_effects, opp_effects],
                    )
                ]

        return ability

    # =========================================================================
    # Preprocessing
    # =========================================================================

    def _preprocess(self, text: str) -> str:
        """Normalize text for parsing."""
        text = text.replace("<br>", "\n")
        return text

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into individual sentences."""
        # Split by newlines first
        blocks = re.split(r"\\n|\n", text)

        sentences = []
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            # Split on Japanese period, keeping the period
            parts = re.split(r"(。)\s*", block)
            # Reconstruct sentences with periods
            current = ""
            for part in parts:
                if part == "。":
                    current += part
                    if current.strip():
                        sentences.append(current.strip())
                    current = ""
                else:
                    current = part
            if current.strip():
                sentences.append(current.strip())

        return sentences

    def _is_continuation(self, sentence: str, index: int) -> bool:
        """Check if sentence is a continuation of previous ability."""
        # First sentence can't be a continuation
        if index == 0:
            return False

        # Explicit trigger icons should NEVER be continuations
        if any(
            icon in sentence
            for icon in ["{{live_success", "{{live_start", "{{toujyou", "{{kidou", "{{jyouji", "{{jidou"]
        ):
            return False

        # Check for continuation markers
        continuation_markers = [
            "・",
            "-",
            "－",
            "回答が",
            "選んだ場合",
            "条件が",
            "それ以外",
            "その",
            "それら",
            "残り",
            "そし",
            "その後",
            "そこから",
            "山札",
            "デッキ",
            "もよい",
            "を自分",
            "ライブ終了時まで",
            "この能力",
            "この効果",
            "（",
            "(",
            "そうした場合",
            "」",
            "』",
            "）」",
            "）",
            ")",
            "ただし",
            "かつ",
            "または",
            "もしくは",
            "および",
            "代わりに",
            "このメンバー",
            "そのメンバー",
            "選んだ",
            "選んだエリア",
            "自分は",
            "相手は",
        ]

        # Check if it starts with any common phrase that usually continues an ability
        for marker in continuation_markers:
            if sentence.startswith(marker):
                return True

        # Special case: "その" or "プレイヤー" often appears slightly after "自分は"
        if "その" in sentence[:10] or "プレイヤー" in sentence[:10]:
            return True

        return False

    def _extend_ability(self, ability: Ability, sentence: str) -> None:
        """Extend an existing ability with content from a continuation sentence."""
        # Extract additional effects
        effects = self._extract_effects(sentence)
        ability.effects.extend(effects)

        # Extract additional conditions
        conditions = self._extract_conditions(sentence)
        for cond in conditions:
            if cond not in ability.conditions:
                ability.conditions.append(cond)

        # Apply modifiers
        modifiers = self._extract_modifiers(sentence)
        self._apply_modifiers(ability, modifiers)

        # Update raw text
        ability.raw_text += " " + sentence

    # =========================================================================
    # Pass 1: Trigger Extraction
    # =========================================================================

    def _extract_trigger(self, sentence: str) -> Tuple[TriggerType, Optional[Match]]:
        """Extract trigger type and match object from sentence."""
        result = self.registry.match_first(sentence, PatternPhase.TRIGGER)
        if result:
            pattern, match, data = result
            type_str = data.get("type", "")
            return self._resolve_trigger_type(type_str), match
        return TriggerType.NONE, None

    def _resolve_trigger_type(self, type_str: str) -> TriggerType:
        """Convert type string to TriggerType enum."""
        mapping = {
            "TriggerType.ON_PLAY": TriggerType.ON_PLAY,
            "TriggerType.ON_LIVE_START": TriggerType.ON_LIVE_START,
            "TriggerType.ON_LIVE_SUCCESS": TriggerType.ON_LIVE_SUCCESS,
            "TriggerType.ACTIVATED": TriggerType.ACTIVATED,
            "TriggerType.CONSTANT": TriggerType.CONSTANT,
            "TriggerType.ON_LEAVES": TriggerType.ON_LEAVES,
            "TriggerType.ON_REVEAL": TriggerType.ON_REVEAL,
            "TriggerType.TURN_START": TriggerType.TURN_START,
            "TriggerType.TURN_END": TriggerType.TURN_END,
        }
        return mapping.get(type_str, TriggerType.NONE)

    # =========================================================================
    # Pass 2: Condition Extraction
    # =========================================================================

    def _extract_conditions(self, sentence: str) -> List[Condition]:
        """Extract all conditions from sentence."""
        conditions = []
        results = self.registry.match_all(sentence, PatternPhase.CONDITION)

        for pattern, match, data in results:
            cond_type = self._resolve_condition_type(data.get("type", ""))
            if cond_type is not None:
                params = data.get("params", {}).copy()

                # Use extracted value if not already in params
                if "value" in data and "min" not in params:
                    params["min"] = data["value"]
                elif "min" not in params and match.lastindex:
                    try:
                        # Fallback for simple numeric patterns with one group
                        params["min"] = int(match.group(1))
                    except (ValueError, IndexError):
                        pass

                conditions.append(Condition(cond_type, params))

        return conditions

    def _resolve_condition_type(self, type_str: str) -> Optional[ConditionType]:
        """Convert type string to ConditionType enum."""
        if not type_str:
            return None
        name = type_str.replace("ConditionType.", "")

        try:
            # Map common aliases
            if name == "ALL_MEMBERS":
                # For now map to GROUP_FILTER, but we will use the 'val' or 'attr' to flag 'ALL' in Pass 2/4
                return ConditionType.GROUP_FILTER

            return ConditionType[name]
        except KeyError:
            return None

    # =========================================================================
    # Pass 3: Effect Extraction
    # =========================================================================

    def _extract_effects(self, sentence: str) -> List[Effect]:
        """Extract all effects from sentence."""
        effects = []
        results = self.registry.match_all(sentence, PatternPhase.EFFECT)

        for pattern, match, data in results:
            eff_type = self._resolve_effect_type(data.get("type", ""))
            if eff_type is not None:  # Use 'is not None' because EffectType.DRAW = 0 is falsy
                value = data.get("value", 1)
                params = data.get("params", {}).copy()

                # Check for dynamic value condition
                value_cond = ConditionType.NONE
                if "value_cond" in data:
                    vc_str = data["value_cond"]
                    # If it's a string, try to resolve it
                    if isinstance(vc_str, str):
                        resolved_vc = self._resolve_condition_type(vc_str)
                        if resolved_vc:
                            value_cond = resolved_vc
                    elif isinstance(vc_str, int):
                        value_cond = ConditionType(vc_str)

                # Special case for "一番上" (top of deck) which means 1 card
                if "一番上" in sentence and value == 1:
                    pass  # Value 1 is already default

                # Determine target
                target = self._determine_target(sentence, params)

                effects.append(Effect(eff_type, value, value_cond, target, params))

        return effects

    def _resolve_effect_type(self, type_str: str) -> Optional[EffectType]:
        """Convert type string to EffectType enum."""
        if not type_str:
            return None
        name = type_str.replace("EffectType.", "")
        try:
            return EffectType[name]
        except KeyError:
            return None

    def _determine_target(self, sentence: str, params: Dict[str, Any]) -> TargetType:
        """Determine target type from sentence context."""
        if "相手" in sentence:
            return TargetType.OPPONENT
        if "自分と相手" in sentence:
            return TargetType.ALL_PLAYERS
        if "控え室" in sentence:
            return TargetType.CARD_DISCARD
        if "手札" in sentence:
            return TargetType.CARD_HAND
        return TargetType.PLAYER

    # =========================================================================
    # Pass 4: Modifier Extraction & Application
    # =========================================================================

    def _extract_modifiers(self, sentence: str) -> Dict[str, Any]:
        """Extract all modifiers from sentence."""
        modifiers = {}
        results = self.registry.match_all(sentence, PatternPhase.MODIFIER)

        for pattern, match, data in results:
            params = data.get("params", {})

            # Special handling for target_name accumulation
            if "target_name" in params:
                if "target_names" not in modifiers:
                    modifiers["target_names"] = []
                modifiers["target_names"].append(params["target_name"])
                # Remove target_name from params to avoid overwriting invalid data
                params = {k: v for k, v in params.items() if k != "target_name"}

            # Special handling for group accumulation
            if "group" in params:
                if "groups" not in modifiers:
                    modifiers["groups"] = []
                modifiers["groups"].append(params["group"])
                # Note: We do NOT remove "group" from params here because we want the last one
                # to persist in modifiers["group"] for singular backward compatibility,
                # which modifiers.update(params) below will handle.

            modifiers.update(params)

            # Extract numeric values if present
            if match.lastindex:
                try:
                    if "cost_max" not in modifiers and "コスト" in pattern.name:
                        modifiers["cost_max"] = int(match.group(1))
                    if "multiplier" not in modifiers and "multiplier" in pattern.name:
                        modifiers["multiplier_value"] = int(match.group(1))
                except (ValueError, IndexError):
                    pass

        return modifiers

    def _apply_modifiers(self, ability: Ability, modifiers: Dict[str, Any]):
        """Apply extracted modifiers to effects and conditions."""
        target_str = None
        # Apply optionality
        is_optional = modifiers.get("is_optional", False) or modifiers.get("cost_is_optional", False)
        if is_optional:
            # Apply to all costs if they exist
            for cost in ability.costs:
                cost.is_optional = True

            for effect in ability.effects:
                # Primary effects that are usually optional
                primary_optional_types = [
                    EffectType.ADD_TO_HAND,
                    EffectType.RECOVER_MEMBER,
                    EffectType.RECOVER_LIVE,
                    EffectType.PLAY_MEMBER_FROM_HAND,
                    EffectType.SEARCH_DECK,
                    EffectType.LOOK_AND_CHOOSE,
                    EffectType.DRAW,
                    EffectType.ENERGY_CHARGE,
                ]

                # Housekeeping effects that are usually NOT optional even if primary is
                # (unless they contain their own "may" keyword, which _extract_modifiers would catch)
                housekeeping_types = [
                    EffectType.SWAP_CARDS,  # Often "discard remainder"
                    EffectType.MOVE_TO_DECK,
                    EffectType.ORDER_DECK,
                ]

                if effect.effect_type in primary_optional_types:
                    effect.is_optional = True
                # If it's housekeeping, we check if the SPECIFIC text for this effect has "てもよい"
                # But since we don't have per-effect text easily here without more refactoring,
                # we'll stick to the heuristic.

        # Apply usage limits
        if modifiers.get("is_once_per_turn"):
            ability.is_once_per_turn = True

        # Apply duration
        duration = modifiers.get("duration")
        if duration:
            for effect in ability.effects:
                effect.params["until"] = duration

        # Apply target overrides
        if modifiers.get("target"):
            target_str = modifiers["target"]
            target_map = {
                "OPPONENT": TargetType.OPPONENT,
                "ALL_PLAYERS": TargetType.ALL_PLAYERS,
                "OPPONENT_HAND": TargetType.OPPONENT_HAND,
            }
            if target_str in target_map:
                for effect in ability.effects:
                    effect.target = target_map[target_str]

        # Apply both_players flag
        if modifiers.get("both_players"):
            for effect in ability.effects:
                effect.params["both_players"] = True

        # Apply "all" scope
        if modifiers.get("all"):
            for effect in ability.effects:
                effect.params["all"] = True

        # Apply multiplier flags
        for key in ["per_member", "per_live", "per_energy", "has_multiplier", "per_card"]:
            if modifiers.get(key):
                for effect in ability.effects:
                    effect.params[key] = modifiers[key] if modifiers[key] is not True else True

        # Apply filters
        if modifiers.get("cost_max"):
            for effect in ability.effects:
                effect.params["cost_max"] = modifiers["cost_max"]

        if modifiers.get("has_ability"):
            for effect in ability.effects:
                effect.params["has_ability"] = modifiers["has_ability"]

        # Apply group filter
        if modifiers.get("group") or modifiers.get("groups"):
            for effect in ability.effects:
                # Apply to effects that might need a group filter
                if effect.effect_type in [
                    EffectType.ADD_TO_HAND,
                    EffectType.RECOVER_MEMBER,
                    EffectType.RECOVER_LIVE,
                    EffectType.SEARCH_DECK,
                    EffectType.LOOK_AND_CHOOSE,
                    EffectType.PLAY_MEMBER_FROM_HAND,
                    EffectType.ADD_BLADES,
                    EffectType.ADD_HEARTS,
                    EffectType.BUFF_POWER,
                ]:
                    if "group" not in effect.params and modifiers.get("group"):
                        effect.params["group"] = modifiers["group"]

                    if "groups" not in effect.params and modifiers.get("groups"):
                        effect.params["groups"] = modifiers["groups"]

        # Apply name filter
        if modifiers.get("target_names"):
            for effect in ability.effects:
                # Apply to effects that might need a name filter
                if effect.effect_type in [
                    EffectType.ADD_TO_HAND,
                    EffectType.RECOVER_MEMBER,
                    EffectType.RECOVER_LIVE,
                    EffectType.SEARCH_DECK,
                    EffectType.LOOK_AND_CHOOSE,
                    EffectType.PLAY_MEMBER_FROM_HAND,
                ]:
                    if "names" not in effect.params:
                        effect.params["names"] = modifiers["target_names"]

        # Apply opponent trigger flag to conditions
        if modifiers.get("opponent_trigger_allowed"):
            ability.conditions.append(Condition(ConditionType.OPPONENT_HAS, {"opponent_trigger_allowed": True}))

    # =========================================================================
    # Pass 5: Cost Extraction
    # =========================================================================

    def _extract_costs(self, cost_part: str) -> List[Cost]:
        """Extract ability costs from cost text."""
        costs = []
        if not cost_part:
            return costs

        # Extract names if present (e.g. discard specific members)
        cost_names = re.findall(r"「(?!\{\{)(.*?)」", cost_part)

        # Check for tap self cost
        if "このメンバーをウェイトにし" in cost_part:
            costs.append(Cost(AbilityCostType.TAP_SELF))

        # Check for discard cost
        if "控え室に置" in cost_part and "手札" in cost_part:
            count = 1
            if m := re.search(r"(\d+)枚", cost_part):
                count = int(m.group(1))

            params = {}
            if cost_names:
                params["names"] = cost_names

            costs.append(Cost(AbilityCostType.DISCARD_HAND, count, params=params))

        # Check for sacrifice self cost
        if "このメンバーを" in cost_part and "控え室に置" in cost_part:
            costs.append(Cost(AbilityCostType.SACRIFICE_SELF))

        # Check for energy cost
        # Strip potential separators like '、' or '。' that might be between icons
        clean_cost_part = cost_part.replace("、", "").replace("。", "")
        energy_icons = len(re.findall(r"\{\{icon_energy.*?\}\}", clean_cost_part))
        if energy_icons:
            costs.append(Cost(AbilityCostType.ENERGY, energy_icons))

        # Check for reveal hand cost
        if "手札" in cost_part and "公開" in cost_part:
            count = 1
            if m := re.search(r"(\d+)枚", cost_part):
                count = int(m.group(1))
            params = {}
            if "ライブカード" in cost_part:
                params["filter"] = "live"
            elif "メンバー" in cost_part:
                params["filter"] = "member"
            costs.append(Cost(AbilityCostType.REVEAL_HAND, count, params))

        return costs

    # =========================================================================
    # Pseudocode Parsing (Inverse of tools/simplify_cards.py)
    # =========================================================================

    def _parse_pseudocode_block(self, text: str) -> List[Ability]:
        """Parse one or more abilities from pseudocode format."""
        # Split by keywords but respect quotes
        # We want to identify blocks that belong together.
        # A block starts with one or more TRIGGER: lines followed by a body.
        
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # Filter out reminder-only lines at the top level
        # (e.g. (エールで出たスコア...))
        filtered_lines = []
        for line in lines:
            cleaned = line.strip()
            if cleaned.startswith("(") and cleaned.endswith(")") and not any(kw in cleaned.upper() for kw in ["TRIGGER:", "EFFECT:", "COST:", "CONDITION:"]):
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
                t_name = line[len("TRIGGER:"):].strip().upper()
                # Strip all content in parentheses (e.g.Once per turn)
                t_name = re.sub(r"\(.*?\)", "", t_name).strip()

                # Use module-level constant for trigger aliases
                t_name = TRIGGER_ALIASES.get(t_name, t_name)
                try:
                    trigger = TriggerType[t_name]
                except (KeyError, ValueError):
                    trigger = getattr(TriggerType, t_name, TriggerType.NONE)

            elif upper_line.startswith("COST:"):
                cost_str = line[len("COST:"):].strip()
                new_costs = self._parse_pseudocode_costs(cost_str)
                costs.extend(new_costs)
                instructions.extend(new_costs)

            elif upper_line.startswith("CONDITION:"):
                cond_str = line[len("CONDITION:"):].strip()
                new_conditions = self._parse_pseudocode_conditions(cond_str)
                # Only add to pre-activation pre-check conditions if NO effects or costs have been encountered yet
                if not effects and not costs:
                    conditions.extend(new_conditions)
                instructions.extend(new_conditions)

            elif upper_line.startswith("EFFECT:"):
                eff_str = line[len("EFFECT:"):].strip()
                new_effects = self._parse_pseudocode_effects(eff_str, last_target=last_target)
                if new_effects:
                    last_target = new_effects[-1].target
                effects.extend(new_effects)
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
                        target = last_target # Keep last target for the first effect
                    else:
                        target = getattr(TargetType, target_or_eff_name, TargetType.PLAYER)
                        rest = extra_rest # Parameters belong to the first effect
                
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
                            val_int = 1 # v=1 for SCORE_RULE: ALL_ENERGY_ACTIVE
                        else:
                            if "=" in vp:
                                k, v = vp.split("=", 1)
                                params[k.strip().lower()] = v.strip().strip('"\'')
                            else:
                                try:
                                    if val_int == 0: val_int = int(vp)
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

        # Split by comma but respect quotes
        parts = []
        current = ""
        in_quotes = False
        for char in content:
            if char == '"':
                in_quotes = not in_quotes
            if char == "," and not in_quotes:
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

                # Handle numeric values
                if v.isdigit():
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
        parts = StructuralLexer.split_respecting_nesting(text, delimiter=',', extra_delimiters=[' OR ', ';'])

        for p in parts:
            if not p:
                continue
            # Format: NAME(VAL) {PARAMS} (Optional)
            m = re.match(r"(\w+)(?:\((.*?)\))?(.*)", p)
            if m:
                name, val_str, rest = m.groups()

                # Manual Mapping for specific cost names
                if name == "MOVE_TO_DECK":
                    if 'from="discard"' in rest.lower() or "from='discard'" in rest.lower():
                        name = "RETURN_DISCARD_TO_DECK"
                    else:
                        name = "RETURN_MEMBER_TO_DECK"

                cost_name = name.upper()
                if cost_name == "REMOVE_SELF":
                    cost_name = "SACRIFICE_SELF"
                
                # Special mapping for ENERGY_CHARGE as a cost (optional/conditional)
                if cost_name == "ENERGY_CHARGE":
                    # In engine, this is usually an effect, but if used as cost
                    # we map it to NONE and rely on params/value for custom logic
                    # OR we can map it to a specific effect if bytecode supports it.
                    # For now, let's treat it as a meta-cost.
                    ctype = AbilityCostType.NONE
                else:
                    ctype = getattr(AbilityCostType, cost_name, AbilityCostType.NONE)
                
                try:
                    val = int(val_str) if val_str else 0
                except ValueError:
                    val = 0
                is_opt = "(Optional)" in rest or " OR " in text  # OR implies selectivity
                params = self._parse_pseudocode_params(rest)
                
                # If it was ENERGY_CHARGE, ensure we have enough info
                if cost_name == "ENERGY_CHARGE":
                    params["cost_type_name"] = "ENERGY_CHARGE"
                
                costs.append(Cost(ctype, val, is_optional=is_opt, params=params))
        return costs

    def _parse_pseudocode_conditions(self, text: str) -> List[Condition]:
        conditions = []
        # Use the shared split method with multiple delimiters
        parts = StructuralLexer.split_respecting_nesting(text, delimiter=',', extra_delimiters=[' OR ', ';'])

        for p in parts:
            if not p:
                continue
            negated = p.startswith("NOT ")
            name_part = p[4:] if negated else p

            # Support ! as prefix for negation
            if not negated and name_part.startswith("!"):
                negated = True
                name_part = name_part[1:]

            # Match "NAME(VAL) {PARAMS}" or "NAME {PARAMS}" or "NAME"
            m = re.match(r"(\w+)(?:\((.*?)\))?\s*(?:\{(.*)\})?", name_part)
            if m:
                name = m.group(1).upper()
                val_in_parens = m.group(2)
                params_str = m.group(3)

                # Initialize params from the {KEY=VAL} part
                params = self._parse_pseudocode_params(f"{{{params_str}}}") if params_str else {}

                if val_in_parens:
                    # Handle positional arguments in parentheses like COUNT_MEMBER(UNIT_CATCHU, STAGE)
                    v_parts = [vp.strip() for vp in val_in_parens.split(",")]
                    for vp in v_parts:
                        vp_up = vp.upper()
                        if vp_up.startswith("UNIT_"):
                            params["unit"] = vp[5:]
                        elif vp_up.startswith("GROUP_"):
                            params["group"] = vp[6:]
                        elif vp_up in ["STAGE", "HAND", "DISCARD", "ENERGY", "SUCCESS_LIVE", "LIVE_ZONE", "SUCCESS_PILE"]:
                            params["zone"] = vp_up
                        elif "=" in vp:
                            sk, sv = [s.strip().strip('"').strip("'") for s in vp.split("=", 1)]
                            params[sk.lower()] = sv
                        elif ":" in vp:
                            sk, sv = [s.strip().strip('"').strip("'") for s in vp.split(":", 1)]
                            params[sk.lower()] = sv
                        else:
                            params["val"] = vp

                # Check for comparison operators outside of {PARAMS}
                remaining_part = name_part[len(m.group(0)) :].strip()
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
                        if "PLAYER" in params or "target" not in params:
                            pval = params.get("PLAYER", "0")
                            if str(pval) == "1":
                                params["target"] = "opponent"
                            else:
                                params["target"] = "self"
                            if "PLAYER" in params: del params["PLAYER"]
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
        parts = StructuralLexer.split_respecting_nesting(text, delimiter=';')

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
                        target = TargetType.MEMBER_SELECT # Fallback for complex targets
                    else:
                        try:
                            target = TargetType[target_name]
                        except:
                            pass
                
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
                            val_int = 1 # v=1 for SCORE_RULE: ALL_ENERGY_ACTIVE
                        else:
                            if "=" in vp:
                                k, v = vp.split("=", 1)
                                params[k.strip().lower()] = v.strip().strip('"\'')
                            else:
                                try:
                                    if val_int == 0: val_int = int(vp)
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
                    if params.get("mode") == "WAIT":
                        params["wait"] = True

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

                if is_chained:
                    chained_str = f"{target_name}{rest}"
                    effects.extend(self._parse_pseudocode_effects(chained_str, last_target=target))
        return effects


# Convenience function
def parse_ability_text(text: str) -> List[Ability]:
    """Parse ability text using the V2 parser."""
    parser = AbilityParserV2()
    return parser.parse(text)
