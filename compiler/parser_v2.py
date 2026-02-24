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
        parts = []
        current = ""
        depth = 0
        in_double_quote = False
        in_single_quote = False
        
        for char in text:
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
            elif char == ';' and not in_double_quote and not in_single_quote and depth == 0:
                if current.strip():
                    parts.append(current.strip())
                current = ""
                continue
            current += char
        
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

    def _extend_ability(self, ability: Ability, sentence: str):
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
        print(f"DEBUG_LOUD: Resolving '{type_str}' -> '{name}'")

        # Debug members
        # if name == "COUNT_STAGE":
        #    print(f"DEBUG_MEMBERS: {[m.name for m in ConditionType]}")

        try:
            # Map common aliases
            if name == "ALL_MEMBERS":
                # For now map to GROUP_FILTER, but we will use the 'val' or 'attr' to flag 'ALL' in Pass 2/4
                return ConditionType.GROUP_FILTER

            val = ConditionType[name]
            print(f"DEBUG_LOUD: SUCCESS {name} -> {val}")
            return val
        except KeyError:
            print(f"DEBUG_LOUD: FAILED {name}")
            return None

    # =========================================================================
    # Pass 3: Effect Extraction
    # =========================================================================

    def _extract_effects(self, sentence: str) -> List[Effect]:
        """Extract all effects from sentence."""
        effects = []
        results = self.registry.match_all(sentence, PatternPhase.EFFECT)

        # Debug: Show what's being parsed
        # if "DRAW(" in sentence:
        print(f"DEBUG_EFFECTS: Parsing sentence: '{sentence[:50]}'")
        results = self.registry.match_all(sentence, PatternPhase.EFFECT)
        print(f"DEBUG_EFFECTS: Got {len(results)} pattern matches")
        for pattern, match, data in results:
            print(f"DEBUG_EFFECTS: Pattern={pattern.name}, Data={data}")

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
        # Split by "TRIGGER:" but respect quotes to support GRANT_ABILITY
        blocks = []
        current_block = ""
        in_quote = False

        i = 0
        while i < len(text):
            if text[i] == '"':
                in_quote = not in_quote

            # Check for TRIGGER: start (case-insensitive)
            if not in_quote and text[i:].upper().startswith("TRIGGER:"):
                if current_block.strip():
                    blocks.append(current_block)
                    current_block = ""
                # Find the actual case and move forward
                trigger_kw_match = re.match(r"TRIGGER:", text[i:], re.I)
                kw_len = len(trigger_kw_match.group(0))
                current_block += "TRIGGER:"
                i += kw_len
                continue

            current_block += text[i]
            i += 1

        if current_block.strip():
            blocks.append(current_block)

        abilities = []
        for block in blocks:
            if not block.strip():
                continue
            ability = self._parse_single_pseudocode(block)
            # Default trigger to ACTIVATED if missing but has content
            if ability.trigger == TriggerType.NONE and (ability.costs or ability.effects):
                ability.trigger = TriggerType.ACTIVATED
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

                # Aliases for triggers
                alias_map = {
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
                t_name = alias_map.get(t_name, t_name)
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
            # Format: NAME(VAL)->TARGET {PARAMS}
            m = re.match(r"(\w+)\((.*?)\)\s*->\s*(\w+)(.*)", p)
            if m:
                name, val, target_name, rest = m.groups()
                name_up = name.upper()
                etype = getattr(EffectType, name_up, EffectType.DRAW)
                target = getattr(TargetType, target_name.upper() if target_name else "PLAYER", TargetType.PLAYER)
                params = self._parse_pseudocode_params(rest)

                val_int = 0
                val_cond = ConditionType.NONE

                # Check if val is a condition type
                val_up = str(val).upper()
                if hasattr(ConditionType, val_up):
                    val_cond = getattr(ConditionType, val_up)
                else:
                    try:
                        val_int = int(val)
                    except ValueError:
                        val_int = 1
                        # Preserve raw val for special effects like SET_HEART_COST
                        params["raw_val"] = val

                effects.append(Effect(etype, val_int, val_cond, target, params))
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
        return params

    def _parse_pseudocode_costs(self, text: str) -> List[Cost]:
        costs = []
        # Split by ' OR ' first, but for now we might just take the first one or treat as optional?
        # Actually, let's treat 'OR' as splitting into separate options if needed,
        # but the Cost model is AND-only.
        # We'll split by comma AND ' OR ' for now and mark them all.
        parts = []
        current = ""
        depth = 0
        i = 0
        while i < len(text):
            char = text[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            elif depth == 0:
                if text[i : i + 4] == " OR ":
                    parts.append(current.strip())
                    current = ""
                    i += 4
                    continue
                elif char == "," or char == ";":
                    parts.append(current.strip())
                    current = ""
                    i += 1
                    continue
            current += char
            i += 1
        if current:
            parts.append(current.strip())

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
                ctype = getattr(AbilityCostType, cost_name, AbilityCostType.NONE)
                try:
                    val = int(val_str) if val_str else 0
                except ValueError:
                    val = 0
                is_opt = "(Optional)" in rest or " OR " in text  # OR implies selectivity
                params = self._parse_pseudocode_params(rest)
                costs.append(Cost(ctype, val, is_optional=is_opt, params=params))
        return costs

    def _parse_pseudocode_conditions(self, text: str) -> List[Condition]:
        conditions = []
        parts = []
        current = ""
        depth = 0
        i = 0
        while i < len(text):
            char = text[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            elif depth == 0:
                if text[i : i + 4] == " OR ":
                    parts.append(current.strip())
                    current = ""
                    i += 4
                    continue
                elif char == "," or char == ";":
                    parts.append(current.strip())
                    current = ""
                    i += 1
                    continue
            current += char
            i += 1
        if current:
            parts.append(current.strip())

        for p in parts:
            if not p:
                continue
            negated = p.startswith("NOT ")
            name_part = p[4:] if negated else p

            # Support ! as prefix for negation
            if not negated and name_part.startswith("!"):
                negated = True
                name_part = name_part[1:]

            # Match "NAME {PARAMS}" or "NAME"
            m = re.match(r"(\w+)(?:\s*\{(.*)\})?", name_part)
            if m:
                name = m.group(1).upper()
                params_str = m.group(2)

                # Initialize params from the {KEY=VAL} part
                params = self._parse_pseudocode_params(f"{{{params_str}}}") if params_str else {}

                # Default ctype
                ctype = getattr(ConditionType, name.upper(), ConditionType.NONE)

                # Special mapping for Once per turn
                if name == "ONCE" or name == "TURN_1":
                    ctype = ConditionType.TURN_1

                # Special handling for ALL_MEMBERS alias
                if name == "ALL_MEMBERS":
                    ctype = ConditionType.GROUP_FILTER
                    # Bit 2 of val (value 4) flags 'ALL' instead of 'CONTEXT'
                    params["all"] = True

                # Check for (VAL) or =VAL outside of {PARAMS}
                remaining_part = name_part[len(m.group(0)) :].strip()
                if remaining_part:
                    p_m = re.search(r"\((.*?)\)", remaining_part)
                    if p_m:
                        params["val"] = p_m.group(1)
                    else:
                        # Check for =VAL
                        e_m = re.search(r"=\s*[\"']?(.*?)[\"']?$", remaining_part)
                        if e_m:
                            params["val"] = e_m.group(1)

                params["raw_cond"] = name
                if name == "COST_LEAD":
                    ctype = ConditionType.SCORE_COMPARE
                    params["type"] = "cost"
                    params["target"] = "opponent"
                    params["comparison"] = "GT"
                    if params.get("area") == "CENTER":
                        params["zone"] = "CENTER_STAGE"
                        del params["area"]

                # Fix for SCORE_LEAD -> SCORE_COMPARE
                if name == "SCORE_LEAD":
                    ctype = ConditionType.SCORE_COMPARE
                    params["type"] = "score"
                    # Default comparison GT (Lead)
                    if "comparison" not in params:
                        params["comparison"] = "GT"
                    # If target is opponent, it implies checking relative to opponent
                    if "target" not in params:
                        params["target"] = "opponent"

                # TYPE_MEMBER/TYPE_LIVE -> TYPE_CHECK
                if name == "TYPE_MEMBER":
                    ctype = ConditionType.TYPE_CHECK
                    params["card_type"] = "member"
                if name == "TYPE_LIVE":
                    ctype = ConditionType.TYPE_CHECK
                    params["card_type"] = "live"

                # Fix for COUNT_LIVE -> COUNT_LIVE_ZONE
                if name == "COUNT_LIVE":
                    ctype = ConditionType.COUNT_LIVE_ZONE

                # ENERGY_LAGGING / ENERGY_LEAD -> OPPONENT_ENERGY_DIFF
                if name == "ENERGY_LAGGING":
                    ctype = ConditionType.OPPONENT_ENERGY_DIFF
                    params["comparison"] = "GE"
                    if "diff" not in params:
                        params["diff"] = 1
                if name == "ENERGY_LEAD":
                    ctype = ConditionType.OPPONENT_ENERGY_DIFF
                    params["comparison"] = "LE"
                    if "diff" not in params:
                        params["diff"] = 0

                # Aliases
                if name == "SUM_SCORE":
                    ctype = ConditionType.SCORE_COMPARE
                    params["type"] = "score"
                    if "comparison" not in params:
                        params["comparison"] = "GE"
                    if "min" in params and "value" not in params:
                        # Map min to value for SCORE_COMPARE absolute check?
                        # Assuming SCORE_COMPARE supports absolute value if target is set?
                        # Actually logic.rs might compare vs opponent score if no value is set?
                        # If value IS set, it might compare vs value?
                        # I'll rely on value mapping logic.
                        pass

                if name == "COUNT_PLAYED_THIS_TURN":
                    # Pending engine support, use HAS_KEYWORD to silence linter
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = "PLAYED_THIS_TURN"

                if name == "SUM_COST":
                    ctype = ConditionType.SCORE_COMPARE
                    params["type"] = "cost"
                    if "comparison" not in params:
                        params["comparison"] = "GE"
                    # Default target to ME if not specified?
                    # If params has TARGET="OPPONENT", it will be parsed.

                if name == "REVEALED_CONTAINS":
                    # No generic HAS_CARD_IN_ZONE condition yet
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = "REVEALED_CONTAINS"
                    if "TYPE_LIVE" in params:
                        params["value"] = "live"
                    if "TYPE_MEMBER" in params:
                        params["value"] = "member"

                if name == "ZONE":
                    # Heuristic for ZONE condition (e.g. ZONE="YELL_REVEALED")
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = "ZONE_CHECK"
                    params["value"] = params.get("val", "Unknown")  # Default param processing might put it in val?
                    # The parser puts the value in params based on default logic?
                    # Actually _parse_pseudocode_conditions logic puts keys in params.
                    # params is passed in? No, params is dict.
                    # We rely on default param parsing for the "YELL_REVEALED" value which should be in params?
                    # Actually parsing of condition params happens AFTER this block usually?
                    # No, this block converts Name to Params.
                    # If ZONE="YELL_REVEALED", input `name` is "ZONE".
                    # params is empty.
                    pass

                if name == "IS_MAIN_PHASE" or name == "MAIN_PHASE":
                    # Implicit in activated abilities usually, map to NONE to ignore
                    ctype = ConditionType.NONE

                if name == "COUNT_SUCCESS_LIVES" or name == "COUNT_SUCCESS_LIVE":
                    ctype = ConditionType.COUNT_SUCCESS_LIVE
                    # Handle PLAYER=0/1 param mapping
                    if "PLAYER" in params:
                        pval = params["PLAYER"]
                        if str(pval) == "1":
                            params["target"] = "opponent"
                        else:
                            params["target"] = "self"
                        del params["PLAYER"]
                    if "COUNT" in params:
                        params["value"] = params["COUNT"]
                        params["comparison"] = "EQ"
                        del params["COUNT"]

                if name == "HAS_SUCCESS_LIVE":
                    ctype = ConditionType.COUNT_SUCCESS_LIVE

                if name == "SUM_ENERGY":
                    ctype = ConditionType.COUNT_ENERGY

                if name == "BATON_FROM_NAME":
                    ctype = ConditionType.BATON

                if name == "MOVED_THIS_TURN":
                    ctype = ConditionType.HAS_MOVED

                if name == "DECK_REFRESHED_THIS_TURN":
                    ctype = ConditionType.DECK_REFRESHED

                if name == "HAND_SIZE_DIFF":
                    ctype = ConditionType.OPPONENT_HAND_DIFF

                if name == "COST_LE_9":
                    ctype = ConditionType.COST_CHECK
                    params["comparison"] = "LE"
                    params["value"] = 9

                if name == "TARGET":
                    # Data error where params separated by comma
                    ctype = ConditionType.NONE

                if name.startswith("MATCH_"):
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = name

                if name.startswith("DID_ACTIVATE_"):
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = name

                if name == "SUCCESS_LIVES_CONTAINS":
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = "SUCCESS_LIVES_CONTAINS"

                if name == "YELL_COUNT" or name == "COUNT_YELL_REVEALED":
                    # Pending engine support for Yell Count
                    ctype = ConditionType.HAS_KEYWORD
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = "YELL_COUNT"

                if name == "HAS_REMAINING_HEART":
                    ctype = ConditionType.COUNT_HEARTS
                    params["min"] = 1

                if name == "COUNT_CHARGED_ENERGY":
                    ctype = ConditionType.COUNT_ENERGY

                if name == "SUM_SUCCESS_LIVE":
                    ctype = ConditionType.COUNT_SUCCESS_LIVE  # Approx

                if name == "SUM_HEARTS":
                    ctype = ConditionType.COUNT_HEARTS

                if name == "SCORE_EQUAL_OPPONENT":
                    ctype = ConditionType.SCORE_COMPARE
                    params["comparison"] = "EQ"
                    params["target"] = "opponent"

                if name == "AREA":
                    ctype = ConditionType.HAS_KEYWORD  # Likely filtering by area
                    params["keyword"] = "AREA_CHECK"

                if name == "EFFECT_NEGATED_THIS_TURN":
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = "EFFECT_NEGATED"

                if name == "HIGHEST_COST_ON_STAGE":
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = "HIGHEST_COST"

                if name == "BATON_TOUCH":
                    ctype = ConditionType.BATON

                if name == "HAND_SIZE":
                    ctype = ConditionType.COUNT_HAND

                if name == "COUNT_UNIQUE_NAMES":
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = "UNIQUE_NAMES"

                if name == "HAS_TYPE_LIVE":
                    ctype = ConditionType.TYPE_CHECK
                    params["card_type"] = "live"

                if name == "OPPONENT_EXTRA_HEARTS":
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = "OPPONENT_EXTRA_HEARTS"

                if name == "EXTRA_HEARTS":
                    ctype = ConditionType.COUNT_HEARTS
                    # Typically means checking if we have extra hearts
                    if "min" not in params:
                        params["min"] = 1

                if name == "BLADES":
                    ctype = ConditionType.COUNT_BLADES

                if name == "AREA_IN" or name == "AREA":
                    val = params.get("val", "").upper().strip('"')
                    if val == "CENTER" or params.get("zone") == "CENTER" or params.get("area") == "CENTER":
                        ctype = ConditionType.IS_CENTER
                    else:
                        ctype = ConditionType.AREA_CHECK
                        params["keyword"] = "AREA_CHECK"
                        # Map area names to indices (0=Left, 1=Center, 2=Right)
                        area_map = {"LEFT_SIDE": 0, "LEFT": 0, "RIGHT_SIDE": 2, "RIGHT": 2}
                        if val in area_map:
                            params["value"] = area_map[val]

                if name == "BATON_COUNT" or name == "BATON" or name == "BATON_TOUCH":
                    ctype = ConditionType.BATON

                if name == "HAS_ACTIVE_ENERGY":
                    ctype = ConditionType.COUNT_ENERGY
                    params["filter"] = "active"
                    if "min" not in params:
                        params["min"] = 1

                if name == "HAS_LIVE_SET":
                    ctype = ConditionType.HAS_KEYWORD
                    params["keyword"] = "HAS_LIVE_SET"

                if name == "ALL_ENERGY_ACTIVE":
                    ctype = ConditionType.COUNT_ENERGY
                    params["filter"] = "active"
                    params["comparison"] = "ALL"  # Custom logic in engine likely

                if name == "ENERGY":
                    ctype = ConditionType.COUNT_ENERGY

                # Aliases
                if name == "ON_YELL" or name == "ON_YELL_SUCCESS":
                    ctype = ConditionType.NONE  # Triggers handled separately, but avoid ERROR

                if name == "CHECK_GROUP_FILTER":
                    ctype = ConditionType.GROUP_FILTER

                if name == "FILTER":
                    ctype = ConditionType.GROUP_FILTER

                if name == "TOTAL_BLADES":
                    ctype = ConditionType.TOTAL_BLADES

                if name == "HEART_LEAD":
                    ctype = ConditionType.HEART_LEAD

                if name == "SCORE_TOTAL":
                    ctype = ConditionType.SCORE_COMPARE
                    params["type"] = "score"
                    if "comparison" not in params:
                        params["comparison"] = "GE"

                if name == "COUNT_ACTIVATED":
                    ctype = ConditionType.COUNT_STAGE
                    params["filter"] = "ACTIVATED"

                if name == "OPPONENT_HAS_WAIT":
                    ctype = ConditionType.OPPONENT_HAS_WAIT

                if name == "CHECK_IS_IN_DISCARD":
                    ctype = ConditionType.IS_IN_DISCARD

                if name == "HAS_EXCESS_HEART":
                    ctype = ConditionType.HAS_EXCESS_HEART

                if name == "COUNT_MEMBER":
                    ctype = ConditionType.COUNT_STAGE

                if name == "TOTAL_HEARTS":
                    ctype = ConditionType.COUNT_HEARTS

                if name == "ALL_MEMBER":
                    ctype = ConditionType.GROUP_FILTER

                if name == "MEMBER_AT_SLOT":
                    ctype = ConditionType.GROUP_FILTER

                if name == "SUCCESS":
                    ctype = ConditionType.MODAL_ANSWER

                if name == "HAS_LIVE_HEART_COLORS":
                    ctype = ConditionType.HAS_COLOR

                if name == "COUNT_REVEALED":
                    ctype = ConditionType.COUNT_HAND  # Approximate or META_RULE

                if name == "COUNT_DISCARDED_THIS_TURN":
                    ctype = ConditionType.COUNT_DISCARD

                if name == "IS_MAIN_PHASE":
                    ctype = ConditionType.NONE

                if name == "MATCH_PREVIOUS":
                    ctype = ConditionType.MODAL_ANSWER  # Heuristic

                if name == "NOT_MOVED_THIS_TURN":
                    ctype = ConditionType.HAS_MOVED
                    negated = True

                if name == "NAME_MATCH":
                    ctype = ConditionType.GROUP_FILTER
                    params["filter"] = "NAME_MATCH"

                conditions.append(Condition(ctype, params, is_negated=negated))
        return conditions

    def _parse_pseudocode_effects(self, text: str, last_target: TargetType = TargetType.PLAYER) -> List[Effect]:
        effects = []
        # Split by semicolon but not inside {}
        parts = []
        current = ""
        depth = 0
        for char in text:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            elif char == ";" and depth == 0:
                parts.append(current.strip())
                current = ""
                continue
            current += char
        if current:
            parts.append(current.strip())

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
            # More robust regex that handles underscores and varies spacing
            m = re.match(r"^([\w_]+)(?:\((.*?)\))?\s*(?:(\{.*?\})\s*)?(?:->\s*([\w, _]+))?(.*)$", p)
            if m:
                name, val, param_block, target_name, rest = m.groups()

                # Extract params only from the isolated {...} block if found
                params = self._parse_pseudocode_params(param_block) if param_block else {}

                # Target Resolution
                target = last_target
                if target_name:
                    target_name = target_name.strip().upper()
                    if target_name == "SELF" or target_name == "MEMBER_SELF":
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

                # Aliases from parser_pseudocode
                name_up = name.upper()
                if name_up == "TAP_PLAYER":
                    name_up = "TAP_MEMBER"
                if name_up == "CHARGE_SELF":
                    name_up = "ENERGY_CHARGE"
                    target = TargetType.MEMBER_SELF
                
                if name_up == "PLACE_ENERGY_WAIT":
                    name_up = "PLACE_UNDER"
                    params["type"] = "energy"
                    params["wait"] = True
                if name_up == "RECOVER_FROM_CHEER":
                    name_up = "RECOVER_MEMBER"
                    params["source"] = "yell"
                if name_up == "BOOST_SCORE_PER_COLOR":
                    name_up = "BOOST_SCORE"
                    params["multiplier"] = "color"
                
                if name_up == "LOOK_AND_CHOOSE_ORDER":
                    name_up = "ORDER_DECK"
                if name_up == "LOOK_AND_CHOOSE_REVEAL":
                    name_up = "LOOK_AND_CHOOSE"
                    params["reveal"] = True

                etype = getattr(EffectType, name_up, None)
                if name_up == "CHARGE_ENERGY":
                    name_up = "ENERGY_CHARGE"
                if name_up == "MOVE_DISCARD":
                    name_up = "MOVE_TO_DISCARD"
                if name_up == "REMOVE_SELF":
                    name_up = "MOVE_TO_DISCARD"
                    target = TargetType.MEMBER_SELF
                if name_up == "SWAP_SELF":
                    name_up = "SWAP_ZONE"
                    target = TargetType.MEMBER_SELF
                if name_up == "MOVE_HAND" or name_up == "MOVE_TO_HAND":
                    name_up = "ADD_TO_HAND"
                if name_up == "ADD_HAND":
                    name_up = "ADD_TO_HAND"
                if name_up == "TRIGGER_YELL_AGAIN":
                    name_up = "META_RULE"
                    params["meta_type"] = "TRIGGER_YELL_AGAIN"
                if name_up == "DISCARD_HAND":
                    name_up = "MOVE_TO_DISCARD"
                    params["source"] = "HAND"
                    params["destination"] = "discard"
                if name_up == "RECOVER_LIVE":
                    # Usually means from discard
                    params["source"] = "discard"
                if name_up == "RECOVER_MEMBER":
                    # Usually means from discard
                    params["source"] = "discard"
                if name_up == "SELECT_LIMIT":
                    name_up = "REDUCE_LIVE_SET_LIMIT"
                if name_up == "POWER_UP":
                    name_up = "BUFF_POWER"
                if name_up == "REDUCE_SET_LIMIT":
                    name_up = "REDUCE_LIVE_SET_LIMIT"
                if name_up == "REDUCE_LIMIT":
                    name_up = "REDUCE_LIVE_SET_LIMIT"
                if name_up == "REDUCE_HEART":
                    name_up = "REDUCE_HEART_REQ"
                if name_up == "ADD_TAG":
                    name_up = "META_RULE"
                    params["tag"] = val
                if name_up == "PREVENT_LIVE":
                    name_up = "RESTRICTION"
                    params["type"] = "no_live"
                if name_up == "MOVE_DECK":
                    name_up = "MOVE_TO_DECK"
                if name == "OPPONENT_CHOICE":
                    etype = EffectType.OPPONENT_CHOOSE
                    # OPPONENT_CHOICE implies complex options which parse_pseudocode_block/effects handles?
                    # Actually SELECT_MODE handles options. OPPONENT_CHOICE likely structured similarly.
                if name_up == "RESET_YELL_HEARTS":
                    name_up = "META_RULE"
                    params["meta_type"] = "RESET_YELL_HEARTS"
                if name_up == "TRIGGER_YELL_AGAIN":
                    name_up = "META_RULE"
                    params["meta_type"] = "TRIGGER_YELL_AGAIN"
                if name_up == "ADD_HAND":
                    name_up = "ADD_TO_HAND"
                if name_up == "ACTION_YELL_MULLIGAN":
                    name_up = "META_RULE"
                    params["meta_type"] = "ACTION_YELL_MULLIGAN"
                if name_up == "OPPONENT_CHOICE":
                    name_up = "OPPONENT_CHOOSE"
                if name_up == "SET_BASE_BLADES":
                    name_up = "SET_BLADES"
                if name_up == "GRANT_HEARTS" or name_up == "GRANT_HEART":
                    name_up = "ADD_HEARTS"
                if name_up == "SELECT_REVEALED":
                    name_up = "LOOK_AND_CHOOSE"
                    params["source"] = "revealed"
                if name_up == "LOOK_AND_CHOOSE_REVEALED":
                    name_up = "LOOK_AND_CHOOSE"
                    params["source"] = "revealed"
                if name_up == "TAP_SELF":
                    name_up = "TAP_MEMBER"
                    target = TargetType.MEMBER_SELF
                if name_up == "CHANGE_BASE_HEART":
                    name_up = "TRANSFORM_HEART"
                if name_up == "SELECT_LIVE_CARD":
                    name_up = "SELECT_LIVE"
                if name_up == "MOVE_TO_HAND":
                    name_up = "ADD_TO_HAND"
                if name_up == "POSITION_CHANGE":
                    name_up = "MOVE_MEMBER"
                if name_up == "INCREASE_HEART":
                    name_up = "INCREASE_HEART_COST"
                if name_up == "CHANGE_YELL_BLADE_COLOR":
                    name_up = "TRANSFORM_COLOR"
                if name_up == "MOVE_SUCCESS":
                    name_up = "META_RULE"
                    params["meta_type"] = "MOVE_SUCCESS"
                if name_up == "PREVENT_SET_TO_SUCCESS_PILE":
                    name_up = "PREVENT_SET_TO_SUCCESS_PILE"
                if name_up.startswith("PLAY_MEMBER"):
                    if params.get("zone") == "DISCARD" or "DISCARD" in p.upper() or "DISCARD" in text.upper():
                        name_up = "PLAY_MEMBER_FROM_DISCARD"
                    else:
                        name_up = "PLAY_MEMBER_FROM_HAND"

                etype = getattr(EffectType, name_up, None)
                if name.upper() == "LOOK_AND_CHOOSE_ORDER":
                    etype = EffectType.ORDER_DECK
                if name.upper() == "LOOK_AND_CHOOSE_REVEAL":
                    etype = EffectType.LOOK_AND_CHOOSE

                if name.upper() == "DISCARD_HAND":
                    etype = EffectType.MOVE_TO_DISCARD
                    params["source"] = "HAND"
                    params["destination"] = "discard"

                if target_name:
                    target_name_up = target_name.upper()
                    if "CARD_HAND" in target_name_up:
                        target = TargetType.CARD_HAND
                    elif "CARD_DISCARD" in target_name_up:
                        target = TargetType.CARD_DISCARD
                    else:
                        t_part = target_name.split(",")[0].strip()
                        target = getattr(TargetType, t_part.upper(), TargetType.PLAYER)

                    if "DISCARD_REMAINDER" in target_name_up:
                        params["destination"] = "discard"

                    # Variable targeting support: if target is "TARGET" or "TARGET_MEMBER", use last_target
                    if target_name_up in ["TARGET", "TARGET_MEMBER"]:
                        target = last_target
                    elif target_name_up == "ACTIVATE_AND_SELF":
                        # Special case for "activate and self" -> targets player but implied multi-target
                        # For now default to player or member self
                        target = TargetType.PLAYER
                else:
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

                # Check if val is a condition type (e.g. COUNT_STAGE)
                if val and hasattr(ConditionType, val):
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
                        print(f"DEBUG: Effect parsing - name={name}, val={val}, val_int={val_int}")
                        if name.upper() == "DISCARD_HAND" and val_int == 1:
                            pass
                    except ValueError:
                        val_int = 1  # Fallback for non-numeric val (e.g. "ALL")
                        if val == "ALL":
                            val_int = 99
                if etype == EffectType.ENERGY_CHARGE:
                    if params.get("mode") == "WAIT":
                        params["wait"] = True

                if etype == EffectType.LOOK_AND_CHOOSE and "choose_count" not in params:
                    params["choose_count"] = 1

                effects.append(Effect(etype, val_int, val_cond, target, params, is_optional=is_opt))
                last_target = target
        return effects


# Convenience function
def parse_ability_text(text: str) -> List[Ability]:
    """Parse ability text using the V2 parser."""
    parser = AbilityParserV2()
    return parser.parse(text)
