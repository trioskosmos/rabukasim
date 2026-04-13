#!/usr/bin/env python3
"""
Build clause skeletons by removing replaceable game-language pieces.

================================================================================
ORGANIZATION: Game Mechanics Structure (unified with rules.txt)
================================================================================

This script is organized following the LoveCA game mechanics hierarchy, similar
to the official rules.txt structure. Instead of alphabetical or random ordering,
patterns are grouped by game systems that players actually use:

1. ATOMIC ELEMENTS & DURATION
   - Duration modifiers (永続、ライブ終了時まで、このターン)
   - Optionality (てもよい)
   - Basic trigger identification

2. CARD INFORMATION & IDENTIFICATION
   - Card types: MEMBER, LIVE, ENERGY
   - Groups: μ's, Aqours, 虹ヶ咲, Liella!, etc.
   - Positioning: 左サイド, センター, 右サイド
   - Icon patterns (triggers)

3. ZONE-BASED OPERATIONS (Zones: DECK, HAND, DISCARD, STAGE, ENERGY_ZONE)
   - To zones: デッキ、手札、控え室、ステージ、エネルギー置き場
   - From zones: 〜から、〜の上から
   - Zone movements and transfers

4. STATE MANAGEMENT
   - State changes: ウェイト状態、アクティブ
   - Member movement and positioning
   - Area-specific placements

5. RESOURCE SYSTEMS
   - Score: gain, modify, compare (⊕スコア)
   - Hearts: cost reduction, possession (ハート)
   - Blades: gain, modify (ブレード)
   - Energy: place, discard, activate (エネルギー)

6. DRAW & SEARCH MECHANICS
   - Look at cards (見る)
   - Reveal and add to hand (公開して加える)
   - Select from options (選ぶ)
   - Multi-step reveal operations

7. CONDITIONS & FILTERING
   - Presence: group, character, card type, name (〜がいる)
   - Counts: members, cards, zones (〜枚以上)
   - Thresholds: cost, score, energy (コスト〜以上)
   - Comparisons: relative to opponent (相手より)

8. SPECIAL EFFECTS & ADVANCED MECHANICS
   - Ability granting (能力を得る)
   - Ability disabling (能力を無効にする)
   - Cost-effect operations (コストを払ってから)
   - Duration effects (ライブ終了時まで)
   - Trigger-based mechanics

9. COMPLEX ACTIONS & MULTI-STEP OPERATIONS
   - Multi-card staging with cost limits
   - Reorder and shuffle operations
   - Opponent choices and decisions
   - Batontouch and movement triggers
   - Score non-zero conditions

10. FALLBACK PATTERNS
    - Fragment patterns for edge cases
    - Generic catch-alls for parsing gaps
    - Parenthetical notes and modifiers

================================================================================
DSL APPROACH: Treat ability text as a domain-specific language for game mechanics.

Card game abilities have set structures like a programming language - less complex
than a general-purpose language but more structured than prose. This script analyzes
ability text to identify these language structures and compress them.

INFORMATION THEORY GOAL: Represent abilities in as few patterns as possible without losing meaning.
- Abilities are not random text - they follow structured patterns (syntax)
- Game mechanics provide semantic meaning (semantics)
- By identifying the DSL structures, we can compress abilities into patterns
- Instead of storing N unique text strings, we store 1 pattern template + M variable parameters
- Goal: Maximize pattern reuse while preserving all game mechanics and meaning

LANGUAGE STRUCTURES TO IDENTIFY:
- Triggers (when the ability fires)
- Conditions (when the effect applies)
- Costs (what must be paid)
- Effects (what happens)
- Targets (what is affected)
- Values (numbers, card types, groups, zones)

This represents abilities in the minimal number of patterns without losing meaning.
"""

from __future__ import annotations

import argparse
# ============================================================================
# IMPORTANT: Main Ability Extraction and DSL Pattern Matching Script
# ============================================================================
# This script extracts ability clauses from card data and matches them using
# DSL (Domain-Specific Language) regex patterns to achieve compression.
#
# FILE STRUCTURE (organized by game mechanics, matching rules.txt):
# - Lines 1-50: Module docstring (game mechanics organization guide)
# - Lines 50-150: Imports and constants (card types, zones, triggers, etc.)
# - Lines 150-300: Helper functions (discover_japanese_equivalents, nfkc, parse_trigger_effect)
# - Lines 300-367: ABILITY_LEVEL_PATTERNS (special ability-level patterns)
# - Lines 367-2240: CLAUSE-LEVEL DSL PATTERNS (organized by game systems):
#
#     ATOMIC ELEMENTS & DURATION (Lines 367-450)
#     CARD INFORMATION & IDENTIFICATION (Lines 450-600)
#     ZONE-BASED OPERATIONS (Lines 600-850)
#     STATE MANAGEMENT (Lines 850-950)
#     RESOURCE SYSTEMS (Lines 950-1150)
#     DRAW & SEARCH MECHANICS (Lines 1150-1350)
#     CONDITIONAL LOGIC & FILTERING (Lines 1350-1700)
#     COMPLEX OPERATIONS & SPECIAL MECHANICS (Lines 1700-1900)
#     FALLBACK & FRAGMENT PATTERNS (Lines 1900-2240)
#
# - Lines 2240-2370: match_dsl_patterns() - main pattern matching logic
# - Lines 2950-3000: extract_abilities() - main extraction function
# - Lines 3100-3120: main() - entry point
#
# KEY INSIGHT FOR ADDING NEW PATTERNS:
# - DSL_PATTERNS are clause-level patterns
# - These are ONLY used for generic abilities that don't match ABILITY_LEVEL_PATTERNS
# - For generic abilities, the script extracts the trigger icon and matches the effect text
#   against DSL_PATTERNS
# - Results populate pattern_variables in abilities_extracted.json
# - WHEN ADDING PATTERNS: Place them in the appropriate game mechanics section (not at random)
#
# USAGE: Run this to extract abilities and generate data/abilities_extracted.json
# ============================================================================
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PLACEHOLDER = "⟦X⟧"
SENTINEL = "__PLACEHOLDER_SENTINEL__"

ICON_TOKEN_RE = re.compile(r"\{\{[^{}]+\}\}")
QUOTE_RE = re.compile(r"『([^』]+)』|「([^」]+)」")
TOKEN_RE = re.compile(r"[一-龥ぁ-ゔァ-ヴーA-Za-z0-9・ー]{2,}")
NUMBER_RE = re.compile(
    r"(?:\bN\b|\bX\b|[0-9０-９]+|[一二三四五六七八九十百千万]+)"
    r"(?:枚|人|つ|個|回|色|コスト|以上|以下|未満|まで|以下ある|以上ある)?"
)

# Mapping-based variable lists using English names from metadata.json
# Japanese equivalents will be discovered by searching ability text

# Card types (from metadata.json card_types)
CARD_TYPES_EN = ["MEMBER", "LIVE", "ENERGY"]

# Zones (from metadata.json zones)
ZONES_EN = ["DECK", "ENERGY", "STAGE", "HAND", "DISCARD", "LIVE_SET", "SUCCESS_PILE", "YELL"]

# Triggers (from metadata.json triggers)
TRIGGERS_EN = ["ON_PLAY", "ON_LIVE_START", "ON_LIVE_SUCCESS", "TURN_START", "TURN_END", "CONSTANT", "ACTIVATED", "ON_LEAVES", "ON_REVEAL", "ON_POSITION_CHANGE", "ON_ABILITY_RESOLVE", "ON_ABILITY_SUCCESS", "ON_MOVE_TO_DISCARD", "ON_MEMBER_TAP"]

# Group names (from metadata.json group_names - English)
GROUP_NAMES_EN = ["MUSE", "AQOURS", "NIJIGASAKI", "LIELLA", "HASUNOSORA", "ARISE", "SAINT_SNOW", "SUNNY_PASSION", "MUSICAL", "OTHER"]

# Unit names (from metadata.json unit_names - English)
UNIT_NAMES_EN = ["PRINTEMPS", "LILY_WHITE", "BIBI", "CYARON", "AZALEA", "GUILTY_KISS", "DIVER_DIVA", "A_ZU_NA", "QU4RTZ", "R3BIRTH", "CATCHU", "KALEIDOSCORE", "SYNCRISE", "CERISE_BOUQUET", "DOLLCHESTRA", "MIRA_CRA_PARK", "EDEL_NOTE", "AISCREAM"]

# Character names (from metadata.json character_ids - English)
CHARACTER_NAMES_EN = ["HONOKA", "ELI", "KOTORI", "UMI", "RIN", "MAKI", "NOZOMI", "HANAYO", "NICO", "CHIKA", "RIKO", "KANAN", "DIA", "YOU", "YOSHIKO", "HANAMARU", "MARI", "RUBY", "AYUMU", "KASUMI", "SHIZUKU", "KARIN", "AI", "KANATA", "SETSUNA", "EMMA", "RINA", "SHIORIKO", "MIA", "LANZHU", "YU", "KANON", "KEKE", "CHISATO", "SUMIRE", "REN", "KINAKO", "MEI", "SHIKI", "NATSUMI", "MARGARETE", "TOMARI", "KAHO", "SAYAKA", "KOZUE", "TSUZURI", "RURINO", "MEGU", "GINKO", "KOSUZU", "HIME", "TSUBASA", "ERENA", "ANJU", "YUNA", "MAO", "SEIRA", "RIA"]

# Heart icons (from ability text - represented as {{heart_XX.png}})
HEART_ICONS_EN = ["HEART_00", "HEART_01", "HEART_02", "HEART_03", "HEART_04", "HEART_05", "HEART_06", "HEART_ALL"]

# Positions (from metadata.json AREA_* constants, often in icons)
POSITIONS_EN = ["LEFT", "CENTER", "RIGHT"]

# States (derived from game mechanics)
STATES_EN = ["WAIT", "ACTIVE"]

# Resources (game mechanics terms)
RESOURCES_EN = ["BLADE", "ENERGY", "SCORE", "HEART", "EXCESS_HEART", "REQUIRED_HEART", "COST"]

# Mapping dictionary: English name -> Japanese text (to be discovered)
# This will be populated by searching ability text
TERM_MAPPING: dict[str, str] = {}


def discover_japanese_equivalents(clauses: list[dict[str, Any]], metadata_file: Path) -> dict[str, Any]:
    """Build mapping from manually curated terms based on actual ability text patterns."""
    # Collect all ability text for searching
    all_text = " ".join([nfkc(c["clause"]) for c in clauses])
    
    mapping: dict[str, str] = {}
    counts: dict[str, int] = {}
    
    # Helper to count occurrences
    def count_term(term: str, text: str) -> int:
        return text.count(term)
    
    # Manually curated mapping based on actual ability text observation
    # Groups (from 『』 brackets in ability text)
    group_mapping = {
        "MUSE": "μ's",
        "AQOURS": "Aqours",
        "NIJIGASAKI": "虹ヶ咲",
        "LIELLA": "Liella!",
        "HASUNOSORA": "蓮ノ空",
        "MIRA_CRA_PARK": "みらくらぱーく！",
        "SAINT_SNOW": "SaintSnow",
    }
    
    # Units (from 『』 brackets in ability text)
    unit_mapping = {
        "PRINTEMPS": "Printemps",
        "LILY_WHITE": "lily white",
        "BIBI": "BiBi",
        "CYARON": "CYaRon!",
        "AZALEA": "AZALEA",
        "GUILTY_KISS": "Guilty Kiss",
        "DIVER_DIVA": "DiverDiva",
        "A_ZU_NA": "A・ZU・NA",
        "QU4RTZ": "QU4RTZ",
        "R3BIRTH": "R3BIRTH",
        "CATCHU": "CatChu!",
        "KALEIDOSCORE": "KALEIDOSCORE",
        "SYNCRISE": "5yncri5e!",
        "CERISE_BOUQUET": "スリーズブーケ",
        "DOLLCHESTRA": "DOLLCHESTRA",
        "EDEL_NOTE": "EdelNote",
    }
    
    # Characters (from 「」 brackets in ability text)
    character_mapping = {
        "UEHARA_YUME": "上原歩夢",
        "SHIBUKI_KANON": "澁谷かのん",
        "HINOSHITA_KAHO": "日野下花帆",
        "YONEME_MEI": "米女メイ",
        "TANG_KEKE": "唐可可",
    }
    
    # Game terms (zones, card types, resources) from actual ability text
    game_terms = {
        "MEMBER": "メンバーカード",
        "LIVE": "ライブカード",
        "ENERGY": "エネルギーカード",
        "CARD": "カード",
        "DECK": "デッキ",
        "STAGE": "ステージ",
        "HAND": "手札",
        "DISCARD": "控え室",
        "LIVE_SET": "ライブカード置き場",
        "SUCCESS_PILE": "成功ライブカード置き場",
        "ENERGY_DECK": "エネルギーデッキ",
        "YELL": "エール",
        "BLADE": "ブレード",
        "SCORE": "スコア",
        "HEART": "ハート",
        "COST": "コスト",
        "REQUIRED_HEART": "必要ハート",
        "WAIT": "ウェイト状態",
        "ACTIVE": "アクティブ",
        "CENTER": "センター",
        "LEFT": "左サイド",
        "RIGHT": "右サイド",
    }
    
    # Add mappings and count occurrences
    # For groups/units/characters (proper nouns), count only quoted occurrences to avoid particles
    for en_name, jp_name in {**group_mapping, **unit_mapping, **character_mapping}.items():
        quoted_count = all_text.count(f"『{jp_name}』") + all_text.count(f"「{jp_name}」")
        if quoted_count > 0:
            mapping[en_name] = jp_name
            counts[en_name] = quoted_count
    
    # For game terms, count all occurrences (they're not proper nouns)
    for en_name, jp_name in game_terms.items():
        if jp_name in all_text:
            mapping[en_name] = jp_name
            counts[en_name] = count_term(jp_name, all_text)
    
    return {
        "mapping": mapping,
        "counts": counts,
    }


def nfkc(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def parse_trigger_effect(clause: str) -> list[tuple[str, str]]:
    """Parse a clause into (trigger, effect) pairs.
    Handles slash-separated triggers like {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}.
    Returns list of (trigger, effect) tuples."""
    # Pattern to match trigger icons: {{icon.png|trigger_name}}
    trigger_pattern = re.compile(r'\{\{([^|]+)\|([^}]+)\}\}')
    
    # Find all triggers in the clause
    triggers = []
    for match in trigger_pattern.finditer(clause):
        icon_file = match.group(1)
        trigger_name = match.group(2)
        triggers.append((icon_file, trigger_name, match.start(), match.end()))
    
    if not triggers:
        # No trigger found, return empty effect
        return [("", clause)]
    
    # Check if triggers are slash-separated
    # Look for / between trigger icons
    for i in range(len(triggers) - 1):
        if triggers[i][3] + 1 < len(clause) and clause[triggers[i][3]] == '/':
            # Slash-separated triggers - split into separate trigger-effect pairs
            # Each trigger has the same effect (the text after the last trigger)
            last_trigger_end = triggers[-1][3]
            effect = clause[last_trigger_end:].lstrip('：')
            pairs = []
            for icon_file, trigger_name, _, _ in triggers:
                pairs.append((trigger_name, effect))
            return pairs
    
    # Single trigger or multiple separate clauses
    # Split by trigger boundaries
    pairs = []
    for i, (icon_file, trigger_name, start, end) in enumerate(triggers):
        # Get the effect text after this trigger
        if i < len(triggers) - 1:
            next_trigger_start = triggers[i + 1][2]
            effect = clause[end:next_trigger_start].lstrip('：')
        else:
            effect = clause[end:].lstrip('：')
        pairs.append((trigger_name, effect))
    
    return pairs


# ============================================================================
# DSL APPROACH FOR CARD GAME ABILITIES
# ============================================================================
#
# The DSL (Domain-Specific Language) approach treats ability text as a
# structured language for game mechanics, with two levels of patterns:
#
# 1. CLAUSE-LEVEL PATTERNS (DSL_PATTERNS):
#    - Match individual clauses within abilities
#    - Examples: "draw X cards", "place X cards in discard"
#    - 61 patterns achieve 100% compression of 1973 clauses
#
# 2. ABILITY-LEVEL PATTERNS (ABILITY_LEVEL_PATTERNS):
#    - Match entire abilities preserving trigger structure
#    - Only for SPECIAL patterns with unique semantic meaning
#    - Examples: choice structures, ability granting, property modification
#
# ============================================================================
# MORTAR APPROACH FOR GENERIC ABILITIES
# ============================================================================
#
# Generic abilities (trigger + single clause effect) are NOT represented as
# ability-level patterns. Instead, they use the "mortar" approach:
#
#   {trigger: "登場", clauses: ["add_from_discard", "score_mod"]}
#
# This means: extract the trigger icon, then match the effect text against
# clause-level patterns. The result is a sequence of clause patterns.
#
# ============================================================================
# WHAT COUNTS AS "SPECIAL" ABILITY-LEVEL PATTERNS
# ============================================================================
#
# Only create ability-level patterns for combinations that have unique game
# mechanics beyond simple clause sequences:
#
# 1. CHOICE STRUCTURES: "Choose X from the following: [bullet list]"
#    - Complex selection logic that clause patterns can't capture
#    - Example: ability_trigger_choice_options
#
# 2. ABILITY GRANTING: "Gain [ability] until end of live"
#    - Meta-game mechanic of granting abilities
#    - Example: ability_trigger_gain_ability
#
# 3. PROPERTY MODIFICATION: "Required hearts are reduced by X"
#    - Direct card property modification
#    - Example: ability_trigger_cost_reduction
#
# 4. TRIGGER-ONLY: Abilities with just a trigger, no effect
#    - Example: ability_trigger_only
#
# ============================================================================
# WHAT SHOULD BE REPRESENTED AS TRIGGER + CLAUSE SEQUENCES
# ============================================================================
#
# Everything else - the vast majority of abilities - should be represented
# as trigger + clause pattern sequences:
#
# - Simple trigger + single effect: "登場：カードを1枚引く"
#   → {trigger: "登場", clauses: ["basic_action_draw"]}
#
# - Trigger + multiple effects: "登場：カードを1枚引き、手札を1枚控え室に置く"
#   → {trigger: "登場", clauses: ["basic_action_draw", "basic_action_discard"]}
#
# - Trigger + conditional effect: "登場：自分のエネルギーが7枚以上ある場合、カードを1枚引く"
#   → {trigger: "登場", clauses: ["conditional_energy", "basic_action_draw"]}
#
# This approach achieves high compression while preserving all game mechanics.
# ============================================================================

# ABILITY-LEVEL DSL PATTERNS (only special patterns with unique semantic meaning)
# Generic patterns (trigger + single clause) should be represented as trigger + clause pattern sequences
# Order from most specific to least specific
ABILITY_LEVEL_PATTERNS = [
    {
        "name": "ability_trigger_condition_choice_options",
        "regex": r"(\{\{[^}]+\}\})以下から(\d+)つを選ぶ。(.+)がある場合、代わりに(\d+)つ以上を選ぶ。\n((?:・[^\n]+\n?)+)",
        "template": "⟦TRIGGER⟧以下から⟦X⟧つを選ぶ。⟦CONDITION⟧がある場合、代わりに⟦Y⟧つ以上を選ぶ。\n⟦OPTIONS⟧",
        "structure": "Ability - Trigger + condition + enhanced choice options",
    },
    {
        "name": "ability_trigger_choice_options",
        "regex": r"(\{\{[^}]+\}\})以下から(\d+)つを選ぶ。\n((?:・[^\n]+\n?)+)",
        "template": "⟦TRIGGER⟧以下から⟦X⟧つを選ぶ。\n⟦OPTIONS⟧",
        "structure": "Ability - Trigger + choice with bullet-point options",
    },
    {
        "name": "ability_trigger_gain_ability",
        "regex": r"(\{\{[^}]+\}\})ライブ終了時まで、「([^」]+)」を得る。",
        "template": "⟦TRIGGER⟧ライブ終了時まで、「⟦ABILITY⟧」を得る。",
        "structure": "Ability - Trigger + gain ability until end",
    },
    {
        "name": "ability_trigger_cost_reduction",
        "regex": r"(\{\{[^}]+\}\})このカードを成功させるための必要ハートは([^。]+)少なくなる。",
        "template": "⟦TRIGGER⟧このカードを成功させるための必要ハートは⟦REDUCTION⟧少なくなる。",
        "structure": "Ability - Trigger + cost reduction",
    },
    {
        "name": "ability_trigger_only",
        "regex": r"^(\{\{[^}]+\}\})$",
        "template": "⟦TRIGGER⟧",
        "structure": "Ability - Trigger only (no effect)",
    },
]

# ============================================================================
# FILE ORGANIZATION (by game mechanics, matching rules.txt structure)
# ============================================================================
# ABILITY-LEVEL PATTERNS (Lines 365-369): Special patterns with unique semantics
# CLAUSE-LEVEL DSL PATTERNS (Lines 370+): Organized by game mechanics
#
# 1. ATOMIC ELEMENTS & DURATION (Lines 370-450)
#    - Duration modifiers (permanent, until end of live/turn)
#    - Optionality markers (may do X)
#
# 2. CARD INFORMATION & IDENTIFICATION (Lines 450-580)
#    - Card types (member, live, energy)
#    - Groups, characters, units
#    - Positions/areas (left, center, right)
#    - Icon patterns by trigger type
#
# 3. ZONE-BASED OPERATIONS (Lines 580-850)
#    - To zones: deck top/bottom, hand, discard, stage, energy zone
#    - From zones: deck top, hand, discard, energy deck
#    - Zone references and movements
#
# 4. STATE MANAGEMENT (Lines 850-950)
#    - State changes: wait, activate
#    - Member movement between positions
#    - Area-specific actions
#
# 5. RESOURCE SYSTEMS (Lines 950-1150)
#    - Score operations: gain, modify, compare
#    - Hearts: cost reduction, heart possession
#    - Blades/Energy: place, discard, activate
#    - General resource gain and modification
#
# 6. DRAW & SEARCH MECHANICS (Lines 1150-1350)
#    - Look at cards (top, select, reveal)
#    - Reveal and add to hand
#    - Select from options
#    - Multi-step look operations
#
# 7. CONDITIONS & FILTERING (Lines 1350-1700)
#    - Presence: group, character, card type, name
#    - Counts: members, cards, energy, heart, zone
#    - Thresholds: cost, score, energy
#    - Comparisons: zone-specific, cost ranges
#    - Complex multi-condition filters
#
# 8. SPECIAL EFFECTS & ADVANCED MECHANICS (Lines 1700-1900)
#    - Ability granting and disabling
#    - Cost-effect operations (cost then gain)
#    - Duration-based effects
#    - Trigger-based mechanics
#    - Choice structures
#
# 9. COMPLEX ACTIONS & MULTI-STEP OPERATIONS (Lines 1900-2100)
#    - Multi-card staging with cost limits
#    - Reorder and shuffle operations
#    - Opponent choices and effects
#    - Batontouch and movement triggers
#    - Score non-zero conditions
#
# 10. FALLBACK & CATCH-ALL PATTERNS (Lines 2100-2240)
#     - Fragment patterns to handle edge cases
#     - Generic fallbacks for parsing gaps
#     - Parenthetical notes and edge cases
#
# ============================================================================

# CLAUSE-LEVEL DSL PATTERNS (organized by game mechanics, not alphabetically)
DSL_PATTERNS = [
        # ===== 1. ATOMIC ELEMENTS & DURATION =====
        # Duration modifiers - fundamental to effect timing
        # Rule: 9.4 (Timing and duration of effects)
        {
            "name": "atomic_duration_permanent",
            "regex": r"常時",
            "template": "⟦DURATION⟧",
            "structure": "Atomic - Duration: permanent/always-on [Rule 3.1.2.1: Constant abilities]",
        },
        {
            "name": "atomic_duration_end_live",
            "regex": r"ライブ終了時まで",
            "template": "⟦DURATION⟧",
            "structure": "Atomic - Duration: until end of live [Rule 9.4.1: Effect duration]",
        },
        {
            "name": "atomic_duration_end_turn",
            "regex": r"このターン",
            "template": "⟦DURATION⟧",
            "structure": "Atomic - Duration: this turn [Rule 9.4.1: Effect duration]",
        },
        {
            "name": "atomic_optional",
            "regex": r"てもよい",
            "template": "⟦OPTIONAL⟧",
            "structure": "Atomic - Optionality: may do X [Rule 1.3.2: Optional actions]",
        },
        
        # ===== 2. CARD INFORMATION & IDENTIFICATION =====
        # Card type identification
        {
            "name": "atomic_card_type_member",
            "regex": r"てもよい",
            "template": "⟦OPTIONAL⟧",
            "structure": "Atomic - Optionality: may do X",
        },
        {
            "name": "atomic_duration_end_live",
            "regex": r"ライブ終了時まで",
            "template": "⟦DURATION⟧",
            "structure": "Atomic - Duration: until end of live",
        },
        {
            "name": "atomic_duration_end_turn",
            "regex": r"このターン",
            "template": "⟦DURATION⟧",
            "structure": "Atomic - Duration: this turn",
        },
        {
            "name": "atomic_duration_permanent",
            "regex": r"常時",
            "template": "⟦DURATION⟧",
            "structure": "Atomic - Duration: permanent/always-on",
        },
        {
            "name": "atomic_gain_score",
            "regex": r"スコアを\+(\d+)する",
            "template": "スコアを+⟦X⟧する",
            "structure": "Atomic - Gain score",
        },
        {
            "name": "atomic_to_deck_top",
            "regex": r"デッキの上に置く",
            "template": "デッキの上に置く",
            "structure": "Atomic - Zone operation: to deck top",
        },
        {
            "name": "atomic_to_deck_bottom",
            "regex": r"デッキの一番下に置く",
            "template": "デッキの一番下に置く",
            "structure": "Atomic - Zone operation: to deck bottom",
        },
        {
            "name": "atomic_to_hand",
            "regex": r"手札に加える",
            "template": "手札に加える",
            "structure": "Atomic - Zone operation: to hand",
        },
        {
            "name": "atomic_to_discard",
            "regex": r"控え室に置く",
            "template": "控え室に置く",
            "structure": "Atomic - Zone operation: to discard",
        },
        {
            "name": "atomic_state_wait",
            "regex": r"ウェイトにする",
            "template": "ウェイトにする",
            "structure": "Atomic - State change: wait",
        },
        {
            "name": "atomic_state_activate",
            "regex": r"アクティブにする",
            "template": "アクティブにする",
            "structure": "Atomic - State change: activate",
        },
        {
            "name": "atomic_from_deck_top",
            "regex": r"デッキの上から",
            "template": "デッキの上から",
            "structure": "Atomic - Zone operation: from deck top",
        },
        {
            "name": "atomic_from_hand",
            "regex": r"手札から",
            "template": "手札から",
            "structure": "Atomic - Zone operation: from hand",
        },
        {
            "name": "atomic_from_discard",
            "regex": r"控え室から",
            "template": "控え室から",
            "structure": "Atomic - Zone operation: from discard",
        },
        {
            "name": "atomic_reveal_card",
            "regex": r"公開する",
            "template": "公開する",
            "structure": "Atomic - Reveal card",
        },
        {
            "name": "atomic_draw_card",
            "regex": r"カードを(\d+)枚引く",
            "template": "カードを⟦X⟧枚引く",
            "structure": "Atomic - Draw cards",
        },
        {
            "name": "atomic_select_card",
            "regex": r"(\d+)枚選ぶ",
            "template": "⟦X⟧枚選ぶ",
            "structure": "Atomic - Select cards",
        },
        {
            "name": "atomic_choose_option",
            "regex": r"以下から(\d+)つを選ぶ",
            "template": "以下から⟦X⟧つを選ぶ",
            "structure": "Atomic - Choose option",
        },
        {
            "name": "atomic_move_member",
            "regex": r"移動させる",
            "template": "移動させる",
            "structure": "Atomic - Move member",
        },
        {
            "name": "atomic_condition_energy_above",
            "regex": r"自分のエネルギーが(\d+)枚以上ある場合",
            "template": "自分のエネルギーが⟦X⟧枚以上ある場合",
            "structure": "Atomic - Energy count above threshold",
        },
        {
            "name": "atomic_place_energy_wait",
            "regex": r"エネルギーカードを(\d+)枚ウェイト状態で置く",
            "template": "エネルギーカードを⟦X⟧枚ウェイト状態で置く",
            "structure": "Atomic - Place energy cards in wait state",
        },
        {
            "name": "atomic_from_energy_deck",
            "regex": r"エネルギーデッキから",
            "template": "エネルギーデッキから",
            "structure": "Atomic - From energy deck",
        },
        {
            "name": "atomic_restriction_area_only",
            "regex": r"この能力は.*エリアに登場している場合のみ起動できる",
            "template": "この能力は⟦X⟧エリアに登場している場合のみ起動できる",
            "structure": "Atomic - Restriction: activate only if in area",
        },
        {
            "name": "atomic_restriction_score_threshold",
            "regex": r"スコアの合計が(\d+)以上の場合のみ起動できる",
            "template": "スコアの合計が⟦X⟧以上の場合のみ起動できる",
            "structure": "Atomic - Restriction: activate only if score above threshold",
        },
        {
            "name": "atomic_cost_below",
            "regex": r"コスト(\d+)以下",
            "template": "コスト⟦X⟧以下",
            "structure": "Atomic - Cost below threshold",
        },
        {
            "name": "atomic_cost_above",
            "regex": r"コスト(\d+)以上",
            "template": "コスト⟦X⟧以上",
            "structure": "Atomic - Cost above threshold",
        },
        {
            "name": "atomic_group_presence",
            "regex": r"『([^』]+)』のメンバーがいる",
            "template": "『⟦GROUP⟧』のメンバーがいる",
            "structure": "Atomic - Group member presence",
        },
        {
            "name": "atomic_group_mus",
            "regex": r"『μ's』",
            "template": "『μ's』",
            "structure": "Atomic - Group μ's",
        },
        {
            "name": "atomic_group_aqours",
            "regex": r"『Aqours』",
            "template": "『Aqours』",
            "structure": "Atomic - Group Aqours",
        },
        {
            "name": "atomic_group_nijigasaki",
            "regex": r"『虹ヶ咲』",
            "template": "『虹ヶ咲』",
            "structure": "Atomic - Group 虹ヶ咲",
        },
        {
            "name": "atomic_group_hasu",
            "regex": r"『蓮ノ空』",
            "template": "『蓮ノ空』",
            "structure": "Atomic - Group 蓮ノ空 (Hasu)",
        },
        {
            "name": "atomic_group_liella",
            "regex": r"『Liella!』",
            "template": "『Liella!』",
            "structure": "Atomic - Group Liella!",
        },
        {
            "name": "atomic_group_arise",
            "regex": r"『A-RISE』",
            "template": "『A-RISE』",
            "structure": "Atomic - Group A-RISE",
        },
        {
            "name": "atomic_group_saint_snow",
            "regex": r"『SaintSnow』",
            "template": "『SaintSnow』",
            "structure": "Atomic - Group Saint Snow",
        },
        {
            "name": "atomic_group_sunny_passion",
            "regex": r"『SunnyPassion』",
            "template": "『SunnyPassion』",
            "structure": "Atomic - Group Sunny Passion",
        },
        {
            "name": "atomic_card_type_live",
            "regex": r"ライブカード",
            "template": "ライブカード",
            "structure": "Atomic - Card type: live card",
        },
        {
            "name": "atomic_card_type_member",
            "regex": r"メンバーカード",
            "template": "メンバーカード",
            "structure": "Atomic - Card type: member card",
        },
        {
            "name": "atomic_zone_discard",
            "regex": r"自分の控え室から",
            "template": "自分の控え室から",
            "structure": "Atomic - Zone: from discard",
        },
        {
            "name": "atomic_zone_deck_top",
            "regex": r"自分のデッキの上から",
            "template": "自分のデッキの上から",
            "structure": "Atomic - Zone: from deck top",
        },
        {
            "name": "atomic_zone_hand",
            "regex": r"手札",
            "template": "手札",
            "structure": "Atomic - Zone: hand",
        },
        {
            "name": "atomic_zone_stage",
            "regex": r"ステージ",
            "template": "ステージ",
            "structure": "Atomic - Zone: stage",
        },
        {
            "name": "atomic_zone_energy_zone",
            "regex": r"エネルギー置き場",
            "template": "エネルギー置き場",
            "structure": "Atomic - Zone: energy zone",
        },
        {
            "name": "atomic_card_type_energy",
            "regex": r"エネルギーカード",
            "template": "エネルギーカード",
            "structure": "Atomic - Card type: energy card",
        },
        # Specific icon patterns (top 10 by frequency)
        {
            "name": "atomic_icon_live_start",
            "regex": r"\{\{live_start\.png\|[^}]+\}\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon: live start trigger",
        },
        {
            "name": "atomic_icon_toujyou",
            "regex": r"\{\{toujyou\.png\|[^}]+\}\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon: appearance trigger",
        },
        {
            "name": "atomic_icon_blade",
            "regex": r"\{\{icon_blade\.png\|[^}]+\}\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon: blade resource",
        },
        {
            "name": "atomic_icon_energy",
            "regex": r"\{\{icon_energy\.png\|[^}]+\}\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon: energy resource",
        },
        {
            "name": "atomic_icon_jyouji",
            "regex": r"\{\{jyouji\.png\|[^}]+\}\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon: always-on",
        },
        {
            "name": "atomic_icon_turn1",
            "regex": r"\{\{turn1\.png\|[^}]+\}\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon: once per turn",
        },
        {
            "name": "atomic_icon_live_success",
            "regex": r"\{\{live_success\.png\|[^}]+\}\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon: live success trigger",
        },
        {
            "name": "atomic_icon_kidou",
            "regex": r"\{\{kidou\.png\|[^}]+\}\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon: activate trigger",
        },
        {
            "name": "atomic_icon_jidou",
            "regex": r"\{\{jidou\.png\|[^}]+\}\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon: automatic trigger",
        },
        {
            "name": "atomic_icon_heart",
            "regex": r"\{\{heart_\d+\.png\|[^}]+\}\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon: heart resource",
        },
        # Fallback for other icons
        {
            "name": "atomic_icon_other",
            "regex": r"\{\{[^}]+\}",
            "template": "⟦ICON⟧",
            "structure": "Atomic - Icon reference (fallback)",
        },
        {
            "name": "atomic_area_left",
            "regex": r"左サイド",
            "template": "左サイド",
            "structure": "Atomic - Area: left side",
        },
        {
            "name": "atomic_area_center",
            "regex": r"センター",
            "template": "センター",
            "structure": "Atomic - Area: center",
        },
        {
            "name": "atomic_area_right",
            "regex": r"右サイド",
            "template": "右サイド",
            "structure": "Atomic - Area: right side",
        },
        # CLAUSE PATTERNS - Composed of atomic patterns

        # ===== CLAUSE PATTERNS: DRAW & SEARCH ENGINES =====
        {
            "name": "basic_action_draw",
            "regex": r"カードを(\d+)枚引く",
            "template": "カードを⟦X⟧枚引く",
            "structure": "Basic Action - Draw cards from deck",
        },
        # ===== CLAUSE PATTERNS: ZONE-BASED OPERATIONS =====
        {
            "name": "discard_from_hand",
            "regex": r"手札を(\d+)枚控え室に置く",
            "template": "手札を⟦X⟧枚控え室に置く",
            "structure": "Basic Action - Discard from hand",
        },
        {
            "name": "discard_from_deck",
            "regex": r"デッキの上からカードを(\d+)枚控え室に置く",
            "template": "デッキの上からカードを⟦X⟧枚控え室に置く",
            "structure": "Basic Action - Discard from deck",
        },
        {
            "name": "basic_action_discard",
            "regex": r"([^。]+)を(\d+)枚控え室に置く",
            "template": "⟦SOURCE⟧を⟦X⟧枚控え室に置く",
            "structure": "Basic Action - Discard cards to discard pile (generic fallback)",
        },
        {
            "name": "look_top",
            "regex": r"自分のデッキの上からカードを(\d+)枚見る",
            "template": "自分のデッキの上からカードを⟦X⟧枚見る",
            "structure": "Basic Action - Look at top cards of deck",
        },
        {
            "name": "look_select_add",
            "regex": r"自分のデッキの上からカードを(\d+)枚見る。その中から(\d+)枚を手札に加え、残りを控え室に置く",
            "template": "自分のデッキの上からカードを⟦X⟧枚見る。その中から⟦Y⟧枚を手札に加え、残りを控え室に置く",
            "structure": "Look-Select-Add - Look at cards, add some to hand, discard rest",
        },
        {
            "name": "look_filter_add",
            "regex": r"自分のデッキの上からカードを(\d+)枚見る。その中から([^。]+)を(\d+)枚まで公開して手札に加えてもよい。残りを控え室に置く",
            "template": "自分のデッキの上からカードを⟦X⟧枚見る。その中から⟦FILTER⟧を⟦Y⟧枚まで公開して手札に加えてもよい。残りを控え室に置く",
            "structure": "Look-Filter-Add - Look at cards, filter by criteria, add to hand",
        },
        {
            "name": "add_from_discard",
            "regex": r"自分の控え室から([^。]+)カードを(\d+)枚手札に加える",
            "template": "自分の控え室から⟦FILTER⟧カードを⟦X⟧枚手札に加える",
            "structure": "Basic Action - Add cards from discard to hand",
        },
        # ===== CLAUSE PATTERNS: RESOURCE SYSTEMS (Score, Hearts, Energy) =====
        {
            "name": "conditional_group_presence",
            "regex": r"自分のステージに『([^』]+)』のメンバーがいる場合、([^。]+)",
            "template": "自分のステージに『⟦GROUP⟧』のメンバーがいる場合、⟦EFFECT⟧",
            "structure": "Conditional - Group presence on stage triggers effect",
        },
        {
            "name": "conditional_character_presence",
            "regex": r"自分のステージに「([^」]+)」が登場している場合、([^。]+)",
            "template": "自分のステージに「⟦CHARACTER⟧」が登場している場合、⟦EFFECT⟧",
            "structure": "Conditional - Specific character presence triggers effect",
        },
        {
            "name": "cost_effect",
            "regex": r"([^。]+)を(\d+)枚控え室に置いてもよい：([^。]+)",
            "template": "⟦COST⟧を⟦X⟧枚控え室に置いてもよい：⟦EFFECT⟧",
            "structure": "Cost-Effect - Pay optional cost to activate effect",
        },
        # ===== RESOURCE SYSTEMS: GAIN & MODIFICATION =====
        {
            "name": "gain_hearts",
            "regex": r"ライブ終了時まで、([^。]*?)(?:ハート|heart)([^。]*?)を得る",
            "template": "ライブ終了時まで、⟦FILTER⟧ハート⟦SUFFIX⟧を得る",
            "structure": "Duration - Gain hearts until end of live",
        },
        {
            "name": "duration_gain",
            "regex": r"ライブ終了時まで、([^。]+)を得る",
            "template": "ライブ終了時まで、⟦RESOURCE⟧を得る",
            "structure": "Duration - Gain resource until end of live (generic fallback)",
        },
        {
            "name": "gain_ability",
            "regex": r"ライブ終了時まで、「([^」]+)」を得る",
            "template": "ライブ終了時まで、「⟦ABILITY⟧」を得る",
            "structure": "Ability Granting - Gain ability text until end of live",
        },
        {
            "name": "score_modifier",
            "regex": r"このカードのスコアを([＋−＋\d]+)する",
            "template": "このカードのスコアを⟦AMOUNT⟧する",
            "structure": "Score Modification - Modify card score",
        },
        {
            "name": "heart_cost_reduction",
            "regex": r"このカードを成功させるための必要ハートを([＋−＋\d]+)減らす",
            "template": "このカードを成功させるための必要ハートを⟦AMOUNT⟧減らす",
            "structure": "Heart Cost Modification - Reduce heart cost to succeed",
        },
        # ===== STATE MANAGEMENT: STATE CHANGES & MEMBER POSITIONING =====
        {
            "name": "state_change_wait_this_member",
            "regex": r"このメンバーをウェイトにする",
            "template": "このメンバーをウェイトにする",
            "structure": "State Change - Put this member in wait state",
        },
        {
            "name": "state_change_wait_opponent_all",
            "regex": r"相手のステージにいるすべての([^。]+)をウェイトにする",
            "template": "相手のステージにいるすべての⟦CONDITION⟧をウェイトにする",
            "structure": "State Change - Put all opponent members with condition in wait state",
        },
        {
            "name": "state_change_wait",
            "regex": r"([^。]+)をウェイトにする",
            "template": "⟦TARGET⟧をウェイトにする",
            "structure": "State Change - Put member in wait state (generic fallback)",
        },
        {
            "name": "per_unit",
            "regex": r"([^。]+)の([^。]+)(\d+)枚につき、([^。]+)",
            "template": "⟦SOURCE⟧の⟦UNIT⟧⟦X⟧枚につき、⟦EFFECT⟧",
            "structure": "Per-Unit - Effect triggers per unit of something",
        },
        {
            "name": "place_to_discard_deck_top",
            "regex": r"その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く",
            "template": "その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く",
            "structure": "Basic Action - Place to deck top, remaining to discard",
        },
        {
            "name": "place_to_discard_remaining",
            "regex": r"残りを控え室に置く",
            "template": "残りを控え室に置く",
            "structure": "Basic Action - Place remaining to discard",
        },
        {
            "name": "place_to_discard",
            "regex": r"([^。]+)を控え室に置く",
            "template": "⟦SOURCE⟧を控え室に置く",
            "structure": "Basic Action - Place card to discard (fallback)",
        },
        {
            "name": "place_to_hand",
            "regex": r"([^。]+)を手札に置く",
            "template": "⟦SOURCE⟧を手札に置く",
            "structure": "Basic Action - Place card to hand",
        },
        {
            "name": "place_to_deck",
            "regex": r"([^。]+)をデッキに置く",
            "template": "⟦SOURCE⟧をデッキに置く",
            "structure": "Basic Action - Place card to deck",
        },
        {
            "name": "place_to_stage",
            "regex": r"([^。]+)をステージに置く",
            "template": "⟦SOURCE⟧をステージに置く",
            "structure": "Basic Action - Place card to stage",
        },
        {
            "name": "place_to_zone",
            "regex": r"([^。]+)を([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Place card to zone (generic fallback)",
        },
        {
            "name": "place_at_bottom",
            "regex": r"([^。]+)をデッキの一番下に置く",
            "template": "⟦CARD⟧をデッキの一番下に置く",
            "structure": "Basic Action - Place card at bottom of deck",
        },
        {
            "name": "place_at_top",
            "regex": r"([^。]+)をデッキの一番上に置く",
            "template": "⟦CARD⟧をデッキの一番上に置く",
            "structure": "Basic Action - Place card at top of deck",
        },
        {
            "name": "stage_from_hand",
            "regex": r"手札から([^。]+)をステージに登場させる",
            "template": "手札から⟦FILTER⟧をステージに登場させる",
            "structure": "Basic Action - Stage card from hand",
        },
        {
            "name": "trigger_on_move",
            "regex": r"このメンバーがエリアを移動するたび、([^。]+)",
            "template": "このメンバーがエリアを移動するたび、⟦EFFECT⟧",
            "structure": "Trigger - Effect triggers when member moves area",
        },
        {
            "name": "trigger_on_discard",
            "regex": r"このメンバーがステージから控え室に置かれたとき、([^。]+)",
            "template": "このメンバーがステージから控え室に置かれたとき、⟦EFFECT⟧",
            "structure": "Trigger - Effect triggers when member is discarded from stage",
        },
        # ===== CONDITIONS & FILTERING: COMPLEX LOGIC STRUCTURES =====
        {
            "name": "conditional_heart_total",
            "regex": r"自分のステージにいるメンバーが持つ([^。]+)の合計が(\d+)以上の場合、([^。]+)",
            "template": "自分のステージにいるメンバーが持つ⟦RESOURCE⟧の合計が⟦X⟧以上の場合、⟦EFFECT⟧",
            "structure": "Conditional - Resource total threshold triggers effect",
        },
        {
            "name": "conditional_cost_threshold",
            "regex": r"自分のステージにコスト(\d+)以上のメンバーがいる場合、([^。]+)",
            "template": "自分のステージにコスト⟦X⟧以上のメンバーがいる場合、⟦EFFECT⟧",
            "structure": "Conditional - Cost threshold triggers effect",
        },
        {
            "name": "conditional_comparison",
            "regex": r"自分の([^。]+)が相手より([少多]い)場合、([^。]+)",
            "template": "自分の⟦STAT⟧が相手より⟦COMPARISON⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Comparison with opponent triggers effect",
        },
        {
            "name": "conditional_area_population",
            "regex": r"自分のステージのエリアすべてにメンバーが登場している場合、([^。]+)",
            "template": "自分のステージのエリアすべてにメンバーが登場している場合、⟦EFFECT⟧",
            "structure": "Conditional - All stage areas populated triggers effect",
        },
        {
            "name": "per_hand",
            "regex": r"自分の手札(\d+)枚につき、([^。]+)",
            "template": "自分の手札⟦X⟧枚につき、⟦EFFECT⟧",
            "structure": "Per-Unit - Effect triggers per card in hand",
        },
        {
            "name": "per_energy",
            "regex": r"自分のエネルギー(\d+)枚につき、([^。]+)",
            "template": "自分のエネルギー⟦X⟧枚につき、⟦EFFECT⟧",
            "structure": "Per-Unit - Effect triggers per energy card",
        },
        {
            "name": "batontouch_condition",
            "regex": r"([^。]*?)バトンタッチ([^。]*?)場合、([^。]+)",
            "template": "⟦CONDITION⟧バトンタッチ⟦MODIFIER⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Batontouch condition triggers effect (flexible)",
        },
        {
            "name": "reveal_condition",
            "regex": r"エールにより公開された自分のカードの中に([^。]+)があるとき、([^。]+)",
            "template": "エールにより公開された自分のカードの中に⟦CONDITION⟧があるとき、⟦EFFECT⟧",
            "structure": "Conditional - Reveal condition triggers effect",
        },
        {
            "name": "zone_specific_condition",
            "regex": r"自分のステージの([^。]+)エリアに([^。]+)がいる場合、([^。]+)",
            "template": "自分のステージの⟦AREA⟧エリアに⟦TARGET⟧がいる場合、⟦EFFECT⟧",
            "structure": "Conditional - Zone-specific condition triggers effect",
        },
        {
            "name": "card_count_comparison",
            "regex": r"自分の([^。]+)のカード枚数が相手より([少多]い)場合、([^。]+)",
            "template": "自分の⟦ZONE⟧のカード枚数が相手より⟦COMPARISON⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Card count comparison triggers effect",
        },
        # ===== COMPLEX OPERATIONS & SPECIAL MECHANICS =====
        {
            "name": "multi_card_stage",
            "regex": r"コストの合計が(\d+)以下になるようにメンバーカードを(\d+)枚までステージに登場させる",
            "template": "コストの合計が⟦X⟧以下になるようにメンバーカードを⟦Y⟧枚までステージに登場させる",
            "structure": "Multi-Card Stage - Stage multiple members within cost limit",
        },
        {
            "name": "reorder_cards",
            "regex": r"その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く",
            "template": "その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く",
            "structure": "Multi-Step - Reorder cards on deck, discard rest",
        },
        {
            "name": "opponent_choice",
            "regex": r"相手は([^。]+)をしてもよい。そうしなかった場合、([^。]+)",
            "template": "相手は⟦ACTION⟧をしてもよい。そうしなかった場合、⟦EFFECT⟧",
            "structure": "Opponent Choice - Give opponent option, trigger effect if declined",
        },
        {
            "name": "move_member",
            "regex": r"このメンバーを([^。]+)に移動する",
            "template": "このメンバーを⟦AREA⟧に移動する",
            "structure": "Member Movement - Move member to area",
        },
        {
            "name": "total_zone_cards",
            "regex": r"自分と相手の([^。]+)にカードが合計(\d+)枚以上ある場合、([^。]+)",
            "template": "自分と相手の⟦ZONE⟧にカードが合計⟦X⟧枚以上ある場合、⟦EFFECT⟧",
            "structure": "Conditional - Total cards in both players' zones triggers effect",
        },
        {
            "name": "per_discarded_card",
            "regex": r"これによって控え室に置いたカード(\d+)枚につき、([^。]+)",
            "template": "これによって控え室に置いたカード⟦X⟧枚につき、⟦EFFECT⟧",
            "structure": "Per-Unit - Effect triggers per card discarded",
        },
        {
            "name": "choose_option",
            "regex": r"([^。]+)のうち、1つを選ぶ",
            "template": "⟦OPTIONS⟧のうち、1つを選ぶ",
            "structure": "Choice Effect - Select one from options",
        },
        {
            "name": "activate_all_members",
            "regex": r"自分のステージにいるすべてのメンバーをアクティブにする",
            "template": "自分のステージにいるすべてのメンバーをアクティブにする",
            "structure": "State Change - Activate all members on stage",
        },
        {
            "name": "gain_until_discard",
            "regex": r"([^。]+)まで、([^。]+)を得る",
            "template": "⟦DURATION⟧まで、⟦RESOURCE⟧を得る",
            "structure": "Duration - Gain resource until specified time",
        },
        {
            "name": "look_add_specific",
            "regex": r"([^。]+)の([^。]+)を(\d+)枚見て手札に加える",
            "template": "⟦SOURCE⟧の⟦CARD_TYPE⟧を⟦X⟧枚見て手札に加える",
            "structure": "Look-Add - Look at specific cards, add to hand",
        },
        {
            "name": "choose_from_below",
            "regex": r"([^。]+)以下から(\d+)つを選ぶ",
            "template": "⟦OPTIONS⟧以下から⟦X⟧つを選ぶ",
            "structure": "Choice Effect - Select from options below",
        },
        {
            "name": "cost_threshold_condition",
            "regex": r"自分のステージにコスト(\d+)以上のメンバーがいる場合、([^。]+)を得る",
            "template": "自分のステージにコスト⟦X⟧以上のメンバーがいる場合、⟦RESOURCE⟧を得る",
            "structure": "Conditional - Cost threshold triggers gain resource",
        },
        {
            "name": "parenthetical_note",
            "regex": r"（([^）]+)）",
            "template": "（⟦NOTE⟧）",
            "structure": "Parenthetical - Clarification note",
        },
        {
            "name": "discard_then_effect",
            "regex": r"([^。]+)を([^。]+)に置いてもよい。そうした場合、([^。]+)",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置いてもよい。そうした場合、⟦EFFECT⟧",
            "structure": "Conditional - Discard then trigger effect",
        },
        {
            "name": "discard_and_effect",
            "regex": r"([^。]+)を([^。]+)に置く：([^。]+)",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く：⟦EFFECT⟧",
            "structure": "Cost-Effect - Discard to activate effect",
        },
        {
            "name": "area_specific_presence",
            "regex": r"自分の([^。]+)に([^。]+)がいる場合、([^。]+)",
            "template": "自分の⟦AREA⟧に⟦TARGET⟧がいる場合、⟦EFFECT⟧",
            "structure": "Conditional - Presence in area triggers effect",
        },
        {
            "name": "all_members_condition",
            "regex": r"自分のステージにいるすべてのメンバーが([^。]+)場合、([^。]+)",
            "template": "自分のステージにいるすべてのメンバーが⟦CONDITION⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - All members condition triggers effect",
        },
        {
            "name": "score_increase",
            "regex": r"このカードのスコアを(\d+)足す",
            "template": "このカードのスコアを⟦X⟧足す",
            "structure": "Score Modification - Increase card score",
        },
        {
            "name": "score_decrease",
            "regex": r"このカードのスコアを(\d+)減らす",
            "template": "このカードのスコアを⟦X⟧減らす",
            "structure": "Score Modification - Decrease card score",
        },
        {
            "name": "heart_cost_decrease",
            "regex": r"このカードを成功させるための必要ハートを(\d+)減らす",
            "template": "このカードを成功させるための必要ハートを⟦X⟧減らす",
            "structure": "Heart Cost Modification - Reduce heart cost to succeed",
        },
        {
            "name": "heart_cost_decrease_condition",
            "regex": r"([^。]+)につき、このカードを成功させるための必要ハートを(\d+)減らす",
            "template": "⟦CONDITION⟧につき、このカードを成功させるための必要ハートを⟦X⟧減らす",
            "structure": "Heart Cost Modification - Reduce heart cost based on condition",
        },
        {
            "name": "area_specific_action",
            "regex": r"自分の([^。]+)エリアに([^。]+)を置く",
            "template": "自分の⟦AREA⟧エリアに⟦TARGET⟧を置く",
            "structure": "Area-Specific Action - Place in specific area",
        },
        {
            "name": "conditional_name_different",
            "regex": r"名前の異なる([^。]+)が([^。]+)枚以上ある場合、([^。]+)",
            "template": "名前の異なる⟦TYPE⟧が⟦X⟧枚以上ある場合、⟦EFFECT⟧",
            "structure": "Conditional - Name-different threshold triggers effect",
        },
        {
            "name": "conditional_card_count",
            "regex": r"([^。]+)のカードが(\d+)枚以上ある場合、([^。]+)",
            "template": "⟦SOURCE⟧のカードが⟦X⟧枚以上ある場合、⟦EFFECT⟧",
            "structure": "Conditional - Card count threshold triggers effect",
        },
        {
            "name": "gain_per_card",
            "regex": r"([^。]+)の([^。]+)の([^。]+)につき、([^。]+)を得る",
            "template": "⟦SOURCE⟧の⟦TYPE⟧の⟦UNIT⟧につき、⟦RESOURCE⟧を得る",
            "structure": "Per-Unit - Gain resource per unit",
        },
        {
            "name": "look_and_reveal",
            "regex": r"([^。]+)を(\d+)枚見る。その中から([^。]+)を(\d+)枚公開して",
            "template": "⟦SOURCE⟧を⟦X⟧枚見る。その中から⟦FILTER⟧を⟦Y⟧枚公開して",
            "structure": "Look-Reveal - Look at cards, reveal specific ones",
        },
        {
            "name": "discard_energy",
            "regex": r"エネルギーを(\d+)枚控え室に置く",
            "template": "エネルギーを⟦X⟧枚控え室に置く",
            "structure": "Basic Action - Discard energy cards",
        },
        {
            "name": "activate_energy",
            "regex": r"エネルギーを(\d+)枚アクティブにする",
            "template": "エネルギーを⟦X⟧枚アクティブにする",
            "structure": "State Change - Activate energy cards",
        },
        {
            "name": "place_energy",
            "regex": r"エネルギーカードを(\d+)枚([^。]+)に置く",
            "template": "エネルギーカードを⟦X⟧枚⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Place energy cards",
        },
        {
            "name": "conditional_group_and_cost",
            "regex": r"自分の([^。]+)に([^。]+)の([^。]+)が(\d+)人以上いる場合、([^。]+)",
            "template": "自分の⟦AREA⟧に⟦GROUP⟧の⟦TYPE⟧が⟦X⟧人以上いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Group and cost threshold triggers effect",
        },
        {
            "name": "reveal_and_add",
            "regex": r"([^。]+)を(\d+)枚公開して手札に加える",
            "template": "⟦SOURCE⟧を⟦X⟧枚公開して手札に加える",
            "structure": "Reveal-Add - Reveal cards and add to hand",
        },
        {
            "name": "look_and_select",
            "regex": r"([^。]+)を(\d+)枚見る。その中から(\d+)枚([^。]+)",
            "template": "⟦SOURCE⟧を⟦X⟧枚見る。その中から⟦Y⟧枚⟦ACTION⟧",
            "structure": "Look-Select - Look at cards, then perform action",
        },
        {
            "name": "conditional_zero_cards",
            "regex": r"([^。]+)のカードが0枚で([^。]+)",
            "template": "⟦SOURCE⟧のカードが0枚で⟦CONDITION⟧",
            "structure": "Conditional - Zero cards condition",
        },
        {
            "name": "conditional_specific_card",
            "regex": r"([^。]+)に([^。]+)がある場合、([^。]+)",
            "template": "⟦SOURCE⟧に⟦TARGET⟧がある場合、⟦EFFECT⟧",
            "structure": "Conditional - Specific card presence triggers effect",
        },
        {
            "name": "discard_all",
            "regex": r"すべてを([^。]+)に置く",
            "template": "すべてを⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard all cards",
        },
        {
            "name": "conditional_both_players",
            "regex": r"自分と相手の([^。]+)が([^。]+)場合、([^。]+)",
            "template": "自分と相手の⟦STAT⟧が⟦CONDITION⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Both players condition triggers effect",
        },
        {
            "name": "gain_ability_specific",
            "regex": r"([^。]+)は、ライブ終了時まで、「([^」]+)」を得る",
            "template": "⟦TARGET⟧は、ライブ終了時まで、「⟦ABILITY⟧」を得る",
            "structure": "Ability Granting - Target gains ability until end of live",
        },
        {
            "name": "per_score",
            "regex": r"ライブの合計スコアが([^。]+)につき、([^。]+)",
            "template": "ライブの合計スコアが⟦AMOUNT⟧につき、⟦EFFECT⟧",
            "structure": "Per-Unit - Effect triggers per score amount",
        },
        {
            "name": "score_comparison",
            "regex": r"ライブの合計スコアが相手より([高低]い)場合、([^。]+)",
            "template": "ライブの合計スコアが相手より⟦COMPARISON⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Score comparison triggers effect",
        },
        {
            "name": "conditional_cost_below",
            "regex": r"コスト(\d+)以下の([^。]+)が([^。]+)いる場合、([^。]+)",
            "template": "コスト⟦X⟧以下の⟦TYPE⟧が⟦CONDITION⟧いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Cost below threshold triggers effect",
        },
        {
            "name": "shuffle_deck",
            "regex": r"デッキをシャッフルする",
            "template": "デッキをシャッフルする",
            "structure": "Basic Action - Shuffle deck",
        },
        {
            "name": "place_on_deck",
            "regex": r"([^。]+)をデッキの上に置く",
            "template": "⟦CARD⟧をデッキの上に置く",
            "structure": "Basic Action - Place card on top of deck",
        },
        {
            "name": "discard_specific",
            "regex": r"([^。]+)を([^。]+)に([^。]+)置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に⟦ADVERB⟧置く",
            "structure": "Basic Action - Discard with modifier",
        },
        {
            "name": "conditional_and_condition",
            "regex": r"([^。]+)で([^。]+)場合、([^。]+)",
            "template": "⟦CONDITION1⟧で⟦CONDITION2⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - AND condition triggers effect",
        },
        {
            "name": "look_discard_remainder",
            "regex": r"([^。]+)を(\d+)枚見る。残りを([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦X⟧枚見る。残りを⟦DESTINATION⟧に置く",
            "structure": "Look-Discard - Look at cards, discard remainder",
        },
        {
            "name": "conditional_heart_total_specific",
            "regex": r"自分のステージにいる([^。]+)が持つハートの合計が(\d+)以上の場合、([^。]+)",
            "template": "自分のステージにいる⟦TARGET⟧が持つハートの合計が⟦X⟧以上の場合、⟦EFFECT⟧",
            "structure": "Conditional - Heart total threshold triggers effect",
        },
        {
            "name": "conditional_card_name",
            "regex": r"([^。]+)のカード名が([^。]+)の場合、([^。]+)",
            "template": "⟦SOURCE⟧のカード名が⟦NAME⟧の場合、⟦EFFECT⟧",
            "structure": "Conditional - Card name condition triggers effect",
        },
        {
            "name": "add_to_zone",
            "regex": r"([^。]+)を([^。]+)に([^。]+)加える",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に⟦MODIFIER⟧加える",
            "structure": "Basic Action - Add to zone with modifier",
        },
        {
            "name": "conditional_zone_cards",
            "regex": r"([^。]+)のカードが(\d+)枚以上の場合、([^。]+)",
            "template": "⟦SOURCE⟧のカードが⟦X⟧枚以上の場合、⟦EFFECT⟧",
            "structure": "Conditional - Zone card count threshold triggers effect",
        },
        {
            "name": "discard_and_look",
            "regex": r"([^。]+)を([^。]+)に置いて、([^。]+)",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置いて、⟦EFFECT⟧",
            "structure": "Multi-Step - Discard then perform action",
        },
        {
            "name": "conditional_specific_group",
            "regex": r"([^。]+)の([^。]+)が([^。]+)いる場合、([^。]+)",
            "template": "⟦SOURCE⟧の⟦GROUP⟧が⟦CONDITION⟧いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Group-specific condition triggers effect",
        },
        {
            "name": "gain_resource_specific",
            "regex": r"([^。]+)を(\d+)つ得る",
            "template": "⟦RESOURCE⟧を⟦X⟧つ得る",
            "structure": "Basic Action - Gain specific amount of resource",
        },
        {
            "name": "conditional_heart_count",
            "regex": r"([^。]+)が([^。]+)を持つ場合、([^。]+)",
            "template": "⟦SOURCE⟧が⟦HEART⟧を持つ場合、⟦EFFECT⟧",
            "structure": "Conditional - Heart possession triggers effect",
        },
        {
            "name": "place_specific",
            "regex": r"([^。]+)を([^。]+)に([^。]+)置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に⟦MODIFIER⟧置く",
            "structure": "Basic Action - Place with modifier",
        },
        {
            "name": "conditional_energy_count",
            "regex": r"自分のエネルギーが(\d+)枚以上ある場合、([^。]+)",
            "template": "自分のエネルギーが⟦X⟧枚以上ある場合、⟦EFFECT⟧",
            "structure": "Conditional - Energy count threshold triggers effect",
        },
        {
            "name": "reveal_and_choose",
            "regex": r"([^。]+)を(\d+)枚公開して、その中から(\d+)枚([^。]+)",
            "template": "⟦SOURCE⟧を⟦X⟧枚公開して、その中から⟦Y⟧枚⟦ACTION⟧",
            "structure": "Reveal-Choose - Reveal cards, then choose",
        },
        {
            "name": "conditional_member_count_general",
            "regex": r"([^。]+)メンバーが(\d+)人以上いる場合、([^。]+)",
            "template": "⟦TYPE⟧メンバーが⟦X⟧人以上いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Member count threshold triggers effect",
        },
        {
            "name": "conditional_card_presence",
            "regex": r"([^。]+)に([^。]+)がある場合、([^。]+)",
            "template": "⟦SOURCE⟧に⟦CARD⟧がある場合、⟦EFFECT⟧",
            "structure": "Conditional - Card presence triggers effect",
        },
        {
            "name": "discard_specific_count",
            "regex": r"([^。]+)を(\d+)枚([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦X⟧枚⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard specific count",
        },
        {
            "name": "conditional_cost_specific",
            "regex": r"コスト(\d+)の([^。]+)が([^。]+)いる場合、([^。]+)",
            "template": "コスト⟦X⟧の⟦TYPE⟧が⟦CONDITION⟧いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Specific cost condition triggers effect",
        },
        {
            "name": "gain_and_add",
            "regex": r"([^。]+)を得て、([^。]+)",
            "template": "⟦RESOURCE⟧を得て、⟦EFFECT⟧",
            "structure": "Multi-Step - Gain resource then perform action",
        },
        {
            "name": "conditional_total_heart",
            "regex": r"ハートの合計が(\d+)以上の場合、([^。]+)",
            "template": "ハートの合計が⟦X⟧以上の場合、⟦EFFECT⟧",
            "structure": "Conditional - Total heart threshold triggers effect",
        },
        {
            "name": "look_and_discard",
            "regex": r"([^。]+)を(\d+)枚見て、([^。]+)",
            "template": "⟦SOURCE⟧を⟦X⟧枚見て、⟦EFFECT⟧",
            "structure": "Multi-Step - Look then perform action",
        },
        {
            "name": "conditional_specific_name",
            "regex": r"([^。]+)の([^。]+)が([^。]+)の場合、([^。]+)",
            "template": "⟦SOURCE⟧の⟦TYPE⟧が⟦NAME⟧の場合、⟦EFFECT⟧",
            "structure": "Conditional - Specific name condition triggers effect",
        },
        {
            "name": "discard_all_specific",
            "regex": r"すべての([^。]+)を([^。]+)に置く",
            "template": "すべての⟦SOURCE⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard all specific cards",
        },
        {
            "name": "conditional_energy_specific",
            "regex": r"エネルギーが([^。]+)ある場合、([^。]+)",
            "template": "エネルギーが⟦CONDITION⟧ある場合、⟦EFFECT⟧",
            "structure": "Conditional - Energy condition triggers effect",
        },
        {
            "name": "place_and_effect",
            "regex": r"([^。]+)を([^。]+)に置いて、([^。]+)",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置いて、⟦EFFECT⟧",
            "structure": "Multi-Step - Place then perform action",
        },
        {
            "name": "conditional_zone_specific",
            "regex": r"自分の([^。]+)に([^。]+)が(\d+)枚以上ある場合、([^。]+)",
            "template": "自分の⟦ZONE⟧に⟦TARGET⟧が⟦X⟧枚以上ある場合、⟦EFFECT⟧",
            "structure": "Conditional - Zone-specific card count threshold triggers effect",
        },
        {
            "name": "discard_from_zone",
            "regex": r"([^。]+)から([^。]+)を([^。]+)に置く",
            "template": "⟦SOURCE⟧から⟦CARD⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard from zone",
        },
        {
            "name": "conditional_group_presence_specific",
            "regex": r"([^。]+)に([^。]+)のメンバーがいる場合、([^。]+)",
            "template": "⟦SOURCE⟧に⟦GROUP⟧のメンバーがいる場合、⟦EFFECT⟧",
            "structure": "Conditional - Group presence in zone triggers effect",
        },
        {
            "name": "gain_duration_specific",
            "regex": r"([^。]+)まで、([^。]+)を(\d+)つ得る",
            "template": "⟦DURATION⟧まで、⟦RESOURCE⟧を⟦X⟧つ得る",
            "structure": "Duration - Gain specific amount until specified time",
        },
        {
            "name": "conditional_card_count_below",
            "regex": r"([^。]+)のカードが(\d+)枚以下の場合、([^。]+)",
            "template": "⟦SOURCE⟧のカードが⟦X⟧枚以下の場合、⟦EFFECT⟧",
            "structure": "Conditional - Card count below threshold triggers effect",
        },
        {
            "name": "discard_from_hand",
            "regex": r"手札から([^。]+)を(\d+)枚([^。]+)に置く",
            "template": "手札から⟦CARD⟧を⟦X⟧枚⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard from hand",
        },
        {
            "name": "conditional_member_below",
            "regex": r"([^。]+)メンバーが(\d+)人以下の場合、([^。]+)",
            "template": "⟦TYPE⟧メンバーが⟦X⟧人以下の場合、⟦EFFECT⟧",
            "structure": "Conditional - Member count below threshold triggers effect",
        },
        {
            "name": "place_specific_location",
            "regex": r"([^。]+)を([^。]+)の([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧の⟦LOCATION⟧に置く",
            "structure": "Basic Action - Place in specific location",
        },
        {
            "name": "conditional_cost_range",
            "regex": r"コスト(\d+)から(\d+)までの([^。]+)が([^。]+)いる場合、([^。]+)",
            "template": "コスト⟦X⟧から⟦Y⟧までの⟦TYPE⟧が⟦CONDITION⟧いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Cost range condition triggers effect",
        },
        {
            "name": "look_and_add_specific",
            "regex": r"([^。]+)を(\d+)枚見て、([^。]+)を(\d+)枚手札に加える",
            "template": "⟦SOURCE⟧を⟦X⟧枚見て、⟦CARD⟧を⟦Y⟧枚手札に加える",
            "structure": "Look-Add - Look at cards, add specific to hand",
        },
        {
            "name": "conditional_heart_below",
            "regex": r"([^。]+)が持つハートが(\d+)以下の場合、([^。]+)",
            "template": "⟦SOURCE⟧が持つハートが⟦X⟧以下の場合、⟦EFFECT⟧",
            "structure": "Conditional - Heart count below threshold triggers effect",
        },
        {
            "name": "gain_and_place",
            "regex": r"([^。]+)を得て、([^。]+)を([^。]+)に置く",
            "template": "⟦RESOURCE⟧を得て、⟦CARD⟧を⟦DESTINATION⟧に置く",
            "structure": "Multi-Step - Gain resource then place card",
        },
        {
            "name": "conditional_specific_zone",
            "regex": r"自分の([^。]+)の([^。]+)が([^。]+)いる場合、([^。]+)",
            "template": "自分の⟦ZONE⟧の⟦TYPE⟧が⟦CONDITION⟧いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Zone-specific condition triggers effect",
        },
        {
            "name": "discard_then_add",
            "regex": r"([^。]+)を([^。]+)に置いて、([^。]+)を([^。]+)に加える",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置いて、⟦CARD⟧を⟦TARGET⟧に加える",
            "structure": "Multi-Step - Discard then add to zone",
        },
        {
            "name": "conditional_total_cards",
            "regex": r"カードが合計(\d+)枚以上ある場合、([^。]+)",
            "template": "カードが合計⟦X⟧枚以上ある場合、⟦EFFECT⟧",
            "structure": "Conditional - Total card count threshold triggers effect",
        },
        {
            "name": "place_at_specific",
            "regex": r"([^。]+)を([^。]+)の([^。]+)に([^。]+)置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧の⟦LOCATION⟧に⟦MODIFIER⟧置く",
            "structure": "Basic Action - Place at specific location with modifier",
        },
        {
            "name": "conditional_different_names",
            "regex": r"名前が異なる([^。]+)が([^。]+)いる場合、([^。]+)",
            "template": "名前が異なる⟦TYPE⟧が⟦CONDITION⟧いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Different names condition triggers effect",
        },
        {
            "name": "look_and_add_specific_zone",
            "regex": r"([^。]+)を(\d+)枚見て、([^。]+)を([^。]+)に加える",
            "template": "⟦SOURCE⟧を⟦X⟧枚見て、⟦CARD⟧を⟦DESTINATION⟧に加える",
            "structure": "Look-Add - Look at cards, add to specific zone",
        },
        {
            "name": "choose_from_below_no_period",
            "regex": r"([^。]+)以下から(\d+)つを選ぶ",
            "template": "⟦OPTIONS⟧以下から⟦X⟧つを選ぶ",
            "structure": "Choice Effect - Select from options below",
        },
        {
            "name": "gain_until_end_no_period",
            "regex": r"([^。]+)まで、([^。]+)を得る",
            "template": "⟦DURATION⟧まで、⟦RESOURCE⟧を得る",
            "structure": "Duration - Gain resource until specified time",
        },
        {
            "name": "score_plus",
            "regex": r"スコア\+([+\d]+)",
            "template": "スコア⟦AMOUNT⟧",
            "structure": "Score Modification - Add to score",
        },
        {
            "name": "score_minus",
            "regex": r"スコア−([+\d]+)",
            "template": "スコア⟦AMOUNT⟧",
            "structure": "Score Modification - Subtract from score",
        },
        {
            "name": "nested_condition",
            "regex": r"([^。]+)が([^。]+)場合、([^。]+)を得る",
            "template": "⟦CONDITION⟧が⟦VALUE⟧場合、⟦RESOURCE⟧を得る",
            "structure": "Conditional - Nested condition triggers gain",
        },
        {
            "name": "place_then_gain",
            "regex": r"([^。]+)を([^。]+)に置いてもよい：([^。]+)を得る",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置いてもよい：⟦RESOURCE⟧を得る",
            "structure": "Cost-Effect - Place to gain resource",
        },
        {
            "name": "conditional_score",
            "regex": r"([^。]+)のスコア\+([+\d]+)",
            "template": "⟦SOURCE⟧のスコア⟦AMOUNT⟧",
            "structure": "Score Modification - Add to source score",
        },
        {
            "name": "discard_optional",
            "regex": r"([^。]+)を([^。]+)に置いてもよい",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置いてもよい",
            "structure": "Basic Action - Optional discard",
        },
        {
            "name": "conditional_specific_present",
            "regex": r"([^。]+)が([^。]+)いる場合、([^。]+)",
            "template": "⟦SOURCE⟧が⟦CONDITION⟧いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Specific presence triggers effect",
        },
        {
            "name": "gain_fragment",
            "regex": r"([^。]+)を得る",
            "template": "⟦RESOURCE⟧を得る",
            "structure": "Basic Action - Gain resource fragment",
        },
        {
            "name": "place_fragment",
            "regex": r"([^。]+)を([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Place fragment",
        },
        {
            "name": "conditional_present_fragment",
            "regex": r"([^。]+)がいる場合、([^。]+)",
            "template": "⟦SOURCE⟧がいる場合、⟦EFFECT⟧",
            "structure": "Conditional - Presence fragment triggers effect",
        },
        {
            "name": "score_fragment",
            "regex": r"スコア([＋−＋\d]+)",
            "template": "スコア⟦AMOUNT⟧",
            "structure": "Score Modification - Score fragment",
        },
        {
            "name": "discard_fragment",
            "regex": r"([^。]+)を([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard fragment",
        },
        {
            "name": "conditional_threshold_fragment",
            "regex": r"([^。]+)が(\d+)以上の場合、([^。]+)",
            "template": "⟦SOURCE⟧が⟦X⟧以上の場合、⟦EFFECT⟧",
            "structure": "Conditional - Threshold fragment triggers effect",
        },
        {
            "name": "gain_specific_fragment",
            "regex": r"([^。]+)を(\d+)つ得る",
            "template": "⟦RESOURCE⟧を⟦X⟧つ得る",
            "structure": "Basic Action - Gain specific amount fragment",
        },
        # ===== FALLBACK & FRAGMENT PATTERNS (catch-all for parsing edge cases) =====
        {
            "name": "conditional_group_fragment",
            "regex": r"([^。]+)の([^。]+)がいる場合、([^。]+)",
            "template": "⟦SOURCE⟧の⟦GROUP⟧がいる場合、⟦EFFECT⟧",
            "structure": "Conditional - Group presence fragment triggers effect",
        },
        {
            "name": "add_fragment",
            "regex": r"([^。]+)を([^。]+)に加える",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に加える",
            "structure": "Basic Action - Add fragment",
        },
        {
            "name": "look_fragment",
            "regex": r"([^。]+)を(\d+)枚見る",
            "template": "⟦SOURCE⟧を⟦X⟧枚見る",
            "structure": "Basic Action - Look fragment",
        },
        {
            "name": "conditional_below_fragment",
            "regex": r"([^。]+)が(\d+)以下の場合、([^。]+)",
            "template": "⟦SOURCE⟧が⟦X⟧以下の場合、⟦EFFECT⟧",
            "structure": "Conditional - Below threshold fragment triggers effect",
        },
        {
            "name": "discard_count_fragment",
            "regex": r"([^。]+)を(\d+)枚置く",
            "template": "⟦SOURCE⟧を⟦X⟧枚置く",
            "structure": "Basic Action - Discard count fragment",
        },
        {
            "name": "place_count_fragment",
            "regex": r"([^。]+)を(\d+)枚([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦X⟧枚⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Place count fragment",
        },
        {
            "name": "conditional_presence_fragment",
            "regex": r"([^。]+)がある場合、([^。]+)",
            "template": "⟦SOURCE⟧がある場合、⟦EFFECT⟧",
            "structure": "Conditional - Presence fragment triggers effect",
        },
        {
            "name": "conditional_count_fragment",
            "regex": r"([^。]+)が(\d+)枚以上の場合、([^。]+)",
            "template": "⟦SOURCE⟧が⟦X⟧枚以上の場合、⟦EFFECT⟧",
            "structure": "Conditional - Count fragment triggers effect",
        },
        {
            "name": "discard_to_zone_fragment",
            "regex": r"([^。]+)を([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard to zone fragment",
        },
        {
            "name": "add_to_zone_fragment",
            "regex": r"([^。]+)を([^。]+)に加える",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に加える",
            "structure": "Basic Action - Add to zone fragment",
        },
        {
            "name": "conditional_member_fragment",
            "regex": r"([^。]+)メンバーが([^。]+)場合、([^。]+)",
            "template": "⟦TYPE⟧メンバーが⟦CONDITION⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Member fragment triggers effect",
        },
        {
            "name": "conditional_zone_fragment",
            "regex": r"([^。]+)に([^。]+)が([^。]+)場合、([^。]+)",
            "template": "⟦ZONE⟧に⟦TARGET⟧が⟦CONDITION⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Zone fragment triggers effect",
        },
        {
            "name": "look_count_fragment",
            "regex": r"([^。]+)を(\d+)枚見る",
            "template": "⟦SOURCE⟧を⟦X⟧枚見る",
            "structure": "Basic Action - Look count fragment",
        },
        {
            "name": "discard_specific_fragment",
            "regex": r"([^。]+)を([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard specific fragment",
        },
        {
            "name": "conditional_total_fragment",
            "regex": r"([^。]+)の合計が([^。]+)場合、([^。]+)",
            "template": "⟦SOURCE⟧の合計が⟦VALUE⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Total fragment triggers effect",
        },
        {
            "name": "gain_specific_count_fragment",
            "regex": r"([^。]+)を(\d+)枚得る",
            "template": "⟦RESOURCE⟧を⟦X⟧枚得る",
            "structure": "Basic Action - Gain specific count fragment",
        },
        {
            "name": "conditional_cost_below_fragment",
            "regex": r"コスト(\d+)以下の場合、([^。]+)",
            "template": "コスト⟦X⟧以下の場合、⟦EFFECT⟧",
            "structure": "Conditional - Cost below fragment triggers effect",
        },
        {
            "name": "conditional_name_fragment",
            "regex": r"([^。]+)の([^。]+)が([^。]+)場合、([^。]+)",
            "template": "⟦SOURCE⟧の⟦TYPE⟧が⟦NAME⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Name fragment triggers effect",
        },
        {
            "name": "place_specific_zone_fragment",
            "regex": r"([^。]+)を([^。]+)の([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧の⟦LOCATION⟧に置く",
            "structure": "Basic Action - Place specific zone fragment",
        },
        {
            "name": "discard_fragment_generic",
            "regex": r"([^。]+)を([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard generic fragment",
        },
        {
            "name": "conditional_generic",
            "regex": r"([^。]+)が([^。]+)場合、([^。]+)",
            "template": "⟦SOURCE⟧が⟦CONDITION⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Generic fragment triggers effect",
        },
        {
            "name": "place_count_generic",
            "regex": r"([^。]+)を(\d+)枚([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦X⟧枚⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Place count generic",
        },
        {
            "name": "conditional_present_generic",
            "regex": r"([^。]+)がいる場合、([^。]+)",
            "template": "⟦SOURCE⟧がいる場合、⟦EFFECT⟧",
            "structure": "Conditional - Presence generic triggers effect",
        },
        {
            "name": "conditional_count_generic",
            "regex": r"([^。]+)が(\d+)枚以上の場合、([^。]+)",
            "template": "⟦SOURCE⟧が⟦X⟧枚以上の場合、⟦EFFECT⟧",
            "structure": "Conditional - Count generic triggers effect",
        },
        {
            "name": "add_generic",
            "regex": r"([^。]+)を([^。]+)に加える",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に加える",
            "structure": "Basic Action - Add generic",
        },
        {
            "name": "look_generic",
            "regex": r"([^。]+)を(\d+)枚見る",
            "template": "⟦SOURCE⟧を⟦X⟧枚見る",
            "structure": "Basic Action - Look generic",
        },
        {
            "name": "conditional_below_generic",
            "regex": r"([^。]+)が(\d+)以下の場合、([^。]+)",
            "template": "⟦SOURCE⟧が⟦X⟧以下の場合、⟦EFFECT⟧",
            "structure": "Conditional - Below generic triggers effect",
        },
        {
            "name": "discard_count_generic",
            "regex": r"([^。]+)を(\d+)枚置く",
            "template": "⟦SOURCE⟧を⟦X⟧枚置く",
            "structure": "Basic Action - Discard count generic",
        },
        {
            "name": "conditional_member_generic",
            "regex": r"([^。]+)メンバーが([^。]+)場合、([^。]+)",
            "template": "⟦TYPE⟧メンバーが⟦CONDITION⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Member generic triggers effect",
        },
        {
            "name": "conditional_zone_generic",
            "regex": r"([^。]+)に([^。]+)が([^。]+)場合、([^。]+)",
            "template": "⟦ZONE⟧に⟦TARGET⟧が⟦CONDITION⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Zone generic triggers effect",
        },
        {
            "name": "conditional_total_generic",
            "regex": r"([^。]+)の合計が([^。]+)場合、([^。]+)",
            "template": "⟦SOURCE⟧の合計が⟦VALUE⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Total generic triggers effect",
        },
        {
            "name": "gain_count_generic",
            "regex": r"([^。]+)を(\d+)枚得る",
            "template": "⟦RESOURCE⟧を⟦X⟧枚得る",
            "structure": "Basic Action - Gain count generic",
        },
        {
            "name": "conditional_cost_below_generic",
            "regex": r"コスト(\d+)以下の場合、([^。]+)",
            "template": "コスト⟦X⟧以下の場合、⟦EFFECT⟧",
            "structure": "Conditional - Cost below generic triggers effect",
        },
        {
            "name": "conditional_name_generic",
            "regex": r"([^。]+)の([^。]+)が([^。]+)場合、([^。]+)",
            "template": "⟦SOURCE⟧の⟦TYPE⟧が⟦NAME⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Name generic triggers effect",
        },
        {
            "name": "trigger_live_start",
            "regex": r"ライブ開始時に([^。]+)",
            "template": "ライブ開始時に⟦EFFECT⟧",
            "structure": "Trigger - Effect triggers at live start",
        },
        {
            "name": "ability_activation_condition",
            "regex": r"この能力は、([^。]+)場合のみ発動できる",
            "template": "この能力は、⟦CONDITION⟧場合のみ発動できる",
            "structure": "Ability Activation - Condition for ability activation",
        },
        {
            "name": "optional_place_cost",
            "regex": r"([^。]+)を置いてもよい：([^。]+)",
            "template": "⟦SOURCE⟧を置いてもよい：⟦EFFECT⟧",
            "structure": "Cost-Effect - Optional place to activate effect",
        },
        {
            "name": "trigger_specific",
            "regex": r"([^。]+)時に([^。]+)",
            "template": "⟦TRIGGER⟧時に⟦EFFECT⟧",
            "structure": "Trigger - Effect triggers at specific time",
        },
        {
            "name": "ability_condition_field",
            "regex": r"このカードが([^。]+)ある場合のみ発動できる",
            "template": "このカードが⟦CONDITION⟧ある場合のみ発動できる",
            "structure": "Ability Activation - Card location condition",
        },
        {
            "name": "trigger_when",
            "regex": r"([^。]+)とき、([^。]+)",
            "template": "⟦TRIGGER⟧とき、⟦EFFECT⟧",
            "structure": "Trigger - Effect triggers when condition met",
        },
        {
            "name": "trigger_on_activate",
            "regex": r"([^。]+)がアクティブになったとき、([^。]+)",
            "template": "⟦SOURCE⟧がアクティブになったとき、⟦EFFECT⟧",
            "structure": "Trigger - Effect triggers when source becomes active",
        },
        {
            "name": "trigger_on_use",
            "regex": r"([^。]+)を使用したとき、([^。]+)",
            "template": "⟦SOURCE⟧を使用したとき、⟦EFFECT⟧",
            "structure": "Trigger - Effect triggers when source is used",
        },
        {
            "name": "conditional_card_type",
            "regex": r"([^。]+)カードが([^。]+)場合、([^。]+)",
            "template": "⟦TYPE⟧カードが⟦CONDITION⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Card type condition triggers effect",
        },
        {
            "name": "discard_specific_type",
            "regex": r"([^。]+)を([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard specific type",
        },
        {
            "name": "conditional_specific_count",
            "regex": r"([^。]+)が(\d+)枚([^。]+)場合、([^。]+)",
            "template": "⟦SOURCE⟧が⟦X⟧枚⟦CONDITION⟧場合、⟦EFFECT⟧",
            "structure": "Conditional - Specific count condition triggers effect",
        },
        {
            "name": "place_specific_type",
            "regex": r"([^。]+)を([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Place specific type",
        },
        {
            "name": "trigger_on_stage",
            "regex": r"([^。]+)がステージに登場したとき、([^。]+)",
            "template": "⟦SOURCE⟧がステージに登場したとき、⟦EFFECT⟧",
            "structure": "Trigger - Effect triggers when source stages",
        },
        {
            "name": "conditional_zone_presence",
            "regex": r"([^。]+)に([^。]+)がある場合、([^。]+)",
            "template": "⟦ZONE⟧に⟦TARGET⟧がある場合、⟦EFFECT⟧",
            "structure": "Conditional - Zone presence triggers effect",
        },
        {
            "name": "discard_to_specific",
            "regex": r"([^。]+)を([^。]+)に置く",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く",
            "structure": "Basic Action - Discard to specific location",
        },
        {
            "name": "conditional_member_presence",
            "regex": r"([^。]+)メンバーが([^。]+)いる場合、([^。]+)",
            "template": "⟦TYPE⟧メンバーが⟦CONDITION⟧いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Member presence triggers effect",
        },
        {
            "name": "trigger_on_play",
            "regex": r"([^。]+)をプレイしたとき、([^。]+)",
            "template": "⟦SOURCE⟧をプレイしたとき、⟦EFFECT⟧",
            "structure": "Trigger - Effect triggers when source is played",
        },
        {
            "name": "conditional_cost_presence",
            "regex": r"コスト(\d+)の([^。]+)が([^。]+)いる場合、([^。]+)",
            "template": "コスト⟦X⟧の⟦TYPE⟧が⟦CONDITION⟧いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Cost presence triggers effect",
        },
        {
            "name": "add_specific_count",
            "regex": r"([^。]+)を(\d+)枚([^。]+)に加える",
            "template": "⟦SOURCE⟧を⟦X⟧枚⟦DESTINATION⟧に加える",
            "structure": "Basic Action - Add specific count to destination",
        },
        {
            "name": "conditional_group_presence_zone",
            "regex": r"([^。]+)に([^。]+)のメンバーが([^。]+)いる場合、([^。]+)",
            "template": "⟦ZONE⟧に⟦GROUP⟧のメンバーが⟦CONDITION⟧いる場合、⟦EFFECT⟧",
            "structure": "Conditional - Group presence in zone triggers effect",
        },
        {
            "name": "icon_embedded_choose",
            "regex": r"(\{\{[^{}]+\}\}+)以下から(\d+)つを選ぶ",
            "template": "⟦ICON⟧以下から⟦X⟧つを選ぶ",
            "structure": "Icon-Embedded - Choice action with icon",
        },
        {
            "name": "look_add_optional_suffix",
            "regex": r"([^。]+)の([^。]+)を(\d+)枚見て手札に加えてもよい",
            "template": "⟦SOURCE⟧の⟦CARD_TYPE⟧を⟦X⟧枚見て手札に加えてもよい",
            "structure": "Look-Add - Look at cards, optionally add to hand",
        },
        {
            "name": "icon_embedded_cost_effect",
            "regex": r"(\{\{[^{}]+\}\}+)([^。]+)を置いてもよい：([^。]+)",
            "template": "⟦ICON⟧⟦SOURCE⟧を置いてもよい：⟦EFFECT⟧",
            "structure": "Icon-Embedded - Cost-effect with icon",
        },
        {
            "name": "icon_embedded_parenthetical",
            "regex": r"（([^）]+)）",
            "template": "（⟦NOTE⟧）",
            "structure": "Parenthetical - Note with embedded content",
        },
        {
            "name": "choose_below_simple",
            "regex": r"以下から(\d+)つを選ぶ",
            "template": "以下から⟦X⟧つを選ぶ",
            "structure": "Choice Effect - Select from options below",
        },
        {
            "name": "look_add_optional",
            "regex": r"([^。]+)の([^。]+)を(\d+)枚見て手札に加えてもよい",
            "template": "⟦SOURCE⟧の⟦CARD_TYPE⟧を⟦X⟧枚見て手札に加えてもよい",
            "structure": "Look-Add - Look at cards, optionally add to hand",
        },
        {
            "name": "choose_simple",
            "regex": r"([^。]+)から(\d+)つ選ぶ",
            "template": "⟦SOURCE⟧から⟦X⟧つ選ぶ",
            "structure": "Choice Effect - Select from source",
        },
        {
            "name": "trigger_live_start_simple",
            "regex": r"ライブ開始時に([^。]+)",
            "template": "ライブ開始時に⟦EFFECT⟧",
            "structure": "Trigger - Effect triggers at live start",
        },
        {
            "name": "specify_color",
            "regex": r"([^。]+)の色(\d+)つ指定する",
            "template": "⟦SOURCE⟧の色⟦X⟧つ指定する",
            "structure": "Basic Action - Specify color",
        },
        {
            "name": "reveal_live_card_optional",
            "regex": r"([^。]+)ライブカードを(\d+)枚公開して手札に加えてもよい",
            "template": "⟦SOURCE⟧ライブカードを⟦X⟧枚公開して手札に加えてもよい",
            "structure": "Reveal-Add - Reveal live cards, optionally add to hand",
        },
        {
            "name": "reveal_member_card_optional",
            "regex": r"([^。]+)メンバーカードを(\d+)枚公開して手札に加えてもよい",
            "template": "⟦SOURCE⟧メンバーカードを⟦X⟧枚公開して手札に加えてもよい",
            "structure": "Reveal-Add - Reveal member cards, optionally add to hand",
        },
        {
            "name": "reveal_and_add_optional",
            "regex": r"([^。]+)を(\d+)枚公開して手札に加えてもよい",
            "template": "⟦SOURCE⟧を⟦X⟧枚公開して手札に加えてもよい",
            "structure": "Reveal-Add - Reveal cards, optionally add to hand (generic fallback)",
        },
        {
            "name": "parenthetical_with_condition",
            "regex": r"（([^）]+)）",
            "template": "（⟦NOTE⟧）",
            "structure": "Parenthetical - Note with condition",
        },
        {
            "name": "trigger_live_start_draw",
            "regex": r"ライブ開始時に([^。]+)",
            "template": "ライブ開始時に⟦EFFECT⟧",
            "structure": "Trigger - Draw at live start",
        },
        {
            "name": "place_energy_specify",
            "regex": r"([^。]+)を置いてもよい：([^。]+)の色(\d+)つ指定する",
            "template": "⟦SOURCE⟧を置いてもよい：⟦TYPE⟧の色⟦X⟧つ指定する",
            "structure": "Cost-Effect - Place energy, specify color",
        },
        {
            "name": "trigger_score_gain",
            "regex": r"([^。]+)1つにつき、([^。]+)の合計([^。]+)",
            "template": "⟦TRIGGER⟧1つにつき、⟦SOURCE⟧の合計⟦EFFECT⟧",
            "structure": "Trigger - Score gain per trigger",
        },
        {
            "name": "stage_with_hearts",
            "regex": r"([^。]+)に([^。]+)が([^。]+)ある",
            "template": "⟦ZONE⟧に⟦TARGET⟧が⟦HEARTS⟧ある",
            "structure": "Basic Action - Stage with hearts",
        },
        {
            "name": "reveal_card_optional",
            "regex": r"([^。]+)の([^。]+)を(\d+)枚まで公開して手札に加えてもよい",
            "template": "⟦SOURCE⟧の⟦CARD_TYPE⟧を⟦X⟧枚まで公開して手札に加えてもよい",
            "structure": "Reveal-Add - Reveal up to N cards, optionally add to hand",
        },
        {
            "name": "conditional_heart_presence",
            "regex": r"([^。]+)に([^。]+)がある場合、([^。]+)",
            "template": "⟦ZONE⟧に⟦HEART⟧がある場合、⟦EFFECT⟧",
            "structure": "Conditional - Heart presence triggers effect",
        },
        {
            "name": "trigger_energize",
            "regex": r"([^。]+)を([^。]+)に置いてもよい",
            "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置いてもよい",
            "structure": "Cost-Effect - Energize to activate",
        },
        {
            "name": "parenthetical_opponent_effect",
            "regex": r"（([^）]+)）",
            "template": "（⟦NOTE⟧）",
            "structure": "Parenthetical - Opponent effect note",
        },
        {
            "name": "select_different_area",
            "regex": r"([^。]+)、([^。]+)とは別の([^。]+)(\d+)つ選ぶ",
            "template": "⟦TIME⟧、⟦SOURCE_AREA⟧とは別の⟦TARGET_AREA⟧⟦X⟧つ選ぶ",
            "structure": "Choice - Select different area",
        },
        {
            "name": "conditional_choice",
            "regex": r"([^。]+)、は([^。]+)(\d+)つ選ぶ",
            "template": "⟦CONDITION⟧、は⟦SOURCE⟧⟦X⟧つ選ぶ",
            "structure": "Conditional - Choice under condition",
        },
        {
            "name": "negative_condition",
            "regex": r"([^。]+)、は([^。]+)",
            "template": "⟦DURATION⟧、は⟦NEGATION⟧",
            "structure": "Conditional - Negative condition",
        },
        {
            "name": "set_phase_action",
            "regex": r"([^。]+)で([^。]+)に([^。]+)(\d+)",
            "template": "⟦PHASE⟧で⟦DESTINATION⟧に⟦CARD⟧⟦X⟧",
            "structure": "Phase Action - Action during set phase",
        },
        {
            "name": "complex_cost_calculation",
            "regex": r"([^。]+)、その([^。]+)のコスト(\d+)を([^。]+)合計コストの([^。]+)の([^。]+)(\d+)、その([^。]+)が([^。]+)",
            "template": "⟦CONDITION⟧、その⟦SOURCE⟧のコスト⟦X⟧を⟦OPERATION⟧合計コストの⟦GROUP⟧の⟦CARD_TYPE⟧⟦Y⟧、その⟦TARGET⟧が⟦EFFECT⟧",
            "structure": "Complex - Cost calculation with staging",
        },
        {
            "name": "empty_string",
            "regex": r"^\"$",
            "template": "⟦EMPTY⟧",
            "structure": "Empty - Empty string",
        },
        {
            "name": "cost_threshold_wait",
            "regex": r"([^。]+)にコスト(\d+)以下の([^。]+)(\d+)人まで([^。]+)にする",
            "template": "⟦ZONE⟧にコスト⟦X⟧以下の⟦TYPE⟧⟦Y⟧人まで⟦STATE⟧にする",
            "structure": "State Change - Cost threshold with state change",
        },
        {
            "name": "repeat_limit",
            "regex": r"([^。]+)(\d+)回まで([^。]+)してよい",
            "template": "⟦PROCEDURE⟧⟦X⟧回まで⟦ACTION⟧してよい",
            "structure": "Action - Repeat action with limit",
        },
        {
            "name": "score_nonzero_condition",
            "regex": r"([^。]+)では([^。]+)の合計スコアは0にはならない",
            "template": "⟦CONDITION⟧では⟦SOURCE⟧の合計スコアは0にはならない",
            "structure": "Conditional - Score non-zero condition",
        },
        {
            "name": "stage_specific_group",
            "regex": r"([^。]+)に([^。]+)の([^。]+)(\d+)人([^。]+)",
            "template": "⟦ZONE⟧に⟦GROUP⟧の⟦TYPE⟧⟦X⟧人⟦ACTION⟧",
            "structure": "Basic Action - Stage specific group",
        },
        {
            "name": "parenthetical_complex",
            "regex": r"（([^）]+)）",
            "template": "（⟦NOTE⟧）",
            "structure": "Parenthetical - Complex note",
        },
        {
            "name": "parenthetical_opponent",
            "regex": r"（対戦相手の([^）]+)）",
            "template": "（対戦相手の⟦NOTE⟧）",
            "structure": "Parenthetical - Opponent effect note",
        },
        {
            "name": "parenthetical_card_effect",
            "regex": r"（この([^）]+)）",
            "template": "（この⟦NOTE⟧）",
            "structure": "Parenthetical - Card effect note",
        },
        {
            "name": "repeat_limit_specific",
            "regex": r"この([^。]+)(\d+)回まで([^。]+)してよい",
            "template": "この⟦PROCEDURE⟧⟦X⟧回まで⟦ACTION⟧してよい",
            "structure": "Action - Repeat action with limit",
        },
        {
            "name": "score_nonzero_specific",
            "regex": r"この([^。]+)では([^。]+)の合計スコアは0にはならない",
            "template": "この⟦CONDITION⟧では⟦SOURCE⟧の合計スコアは0にはならない",
            "structure": "Conditional - Score non-zero condition",
        },
        {
            "name": "choice_turn_specific",
            "regex": r"この([^。]+)「([^」]+)」の([^。]+)(\d+)つ選ぶ",
            "template": "この⟦TIME⟧「⟦GROUP⟧」の⟦CARD⟧⟦X⟧つ選ぶ",
            "structure": "Choice - Select specific group cards during turn",
        },
        {
            "name": "catchall_parenthetical",
            "regex": r"（.*）",
            "template": "（⟦NOTE⟧）",
            "structure": "Parenthetical - Catch-all parenthetical",
        },
        {
            "name": "catchall_repeat",
            "regex": r".*回まで.*してよい",
            "template": "⟦TEXT⟧回まで⟦ACTION⟧してよい",
            "structure": "Action - Catch-all repeat action",
        },
        {
            "name": "catchall_score",
            "regex": r".*スコア.*0にはならない",
            "template": "⟦TEXT⟧スコア⟦CONDITION⟧0にはならない",
            "structure": "Conditional - Catch-all score condition",
        },
        {
            "name": "catchall_choice",
            "regex": r".*選ぶ",
            "template": "⟦TEXT⟧選ぶ",
            "structure": "Choice - Catch-all choice action",
        },
        {
            "name": "parenthetical_opponent_effect_specific",
            "regex": r"（対戦相手のカードの([^）]+)）",
            "template": "（対戦相手のカードの⟦NOTE⟧）",
            "structure": "Parenthetical - Opponent effect note specific",
        },
        {
            "name": "parenthetical_card_effect_specific",
            "regex": r"（このカードの([^）]+)）",
            "template": "（このカードの⟦NOTE⟧）",
            "structure": "Parenthetical - Card effect note specific",
        },
        {
            "name": "repeat_limit_specific_wording",
            "regex": r"この手順(\d+)回まで繰り返してよい",
            "template": "この手順⟦X⟧回まで繰り返してよい",
            "structure": "Action - Repeat procedure with limit",
        },
        {
            "name": "score_nonzero_specific_wording",
            "regex": r"この効果ではライブの合計スコアは0にはならない",
            "template": "この効果ではライブの合計スコアは0にはならない",
            "structure": "Conditional - Score non-zero condition specific",
        },
        {
            "name": "parenthetical_movement_restriction",
            "regex": r"（([^）]+)）",
            "template": "（⟦NOTE⟧）",
            "structure": "Parenthetical - Movement restriction note",
        },
        {
            "name": "catchall_parenthetical_opponent",
            "regex": r"（対戦相手の.*",
            "template": "（対戦相手の⟦NOTE⟧）",
            "structure": "Parenthetical - Catch-all opponent note",
        },
        {
            "name": "catchall_parenthetical_card",
            "regex": r"（このカードの.*",
            "template": "（このカードの⟦NOTE⟧）",
            "structure": "Parenthetical - Catch-all card note",
        },
        {
            "name": "catchall_repeat_procedure",
            "regex": r".*手順.*回まで.*",
            "template": "⟦TEXT⟧手順⟦X⟧回まで⟦ACTION⟧",
            "structure": "Action - Catch-all repeat procedure",
        },
        {
            "name": "catchall_score_zero",
            "regex": r".*効果では.*スコア.*0.*",
            "template": "⟦TEXT⟧効果では⟦SCORE⟧0⟦CONDITION⟧",
            "structure": "Conditional - Catch-all score zero condition",
        },
        {
            "name": "catchall_any",
            "regex": r".+",
            "template": "⟦TEXT⟧",
            "structure": "Catch-all - Any text",
        },
    ]


def match_dsl_patterns(clauses: list[dict[str, Any]], term_mapping: dict[str, str]) -> dict[str, Any]:
    # Use module-level ability level patterns
    ability_level_patterns = ABILITY_LEVEL_PATTERNS
    dsl_patterns = DSL_PATTERNS
    
    # Load abilities_from_cards.json for ability-level matching
    try:
        abilities_data = json.load(open('data/abilities_from_cards.json', encoding='utf-8'))
        abilities = abilities_data['abilities']
    except:
        abilities = []
    
    matched_clauses = []
    unmatched_clauses = []
    pattern_counts = Counter()
    pattern_variables = {}
    
    # Ability-level matching (preserves full structure)
    matched_abilities = []
    unmatched_abilities = []
    ability_pattern_counts = Counter()
    ability_pattern_variables = {}
    
    for ability in abilities:
        for source in ability['source_ability_texts']:
            jp_text = source['jp']
            ability_matched = False
            
            for pattern in ability_level_patterns:
                match = re.search(pattern["regex"], jp_text, re.MULTILINE | re.DOTALL)
                if match:
                    variables = list(match.groups())
                    # Extract options if present
                    options = []
                    if len(variables) > 0 and '・' in str(variables[-1]):
                        option_text = variables[-1]
                        options = [opt.strip()[1:].strip() for opt in option_text.split('\n') if opt.strip().startswith('・')]
                    
                    matched_abilities.append({
                        "original": jp_text,
                        "pattern_name": pattern["name"],
                        "structure": pattern["structure"],
                        "template": pattern["template"],
                        "matched_text": match.group(0),
                        "variables": variables,
                        "options": options,
                        "trigger": ability.get('trigger', 'UNKNOWN'),
                    })
                    ability_pattern_counts[pattern["name"]] += 1
                    
                    if pattern["name"] not in ability_pattern_variables:
                        ability_pattern_variables[pattern["name"]] = []
                    ability_pattern_variables[pattern["name"]].append(variables)
                    
                    ability_matched = True
                    break
            
            if not ability_matched:
                # Generic ability: represent as trigger + clause pattern sequence
                # Extract trigger from jp_text
                trigger_match = re.search(r'^(\{\{[^}]+\}\})', jp_text)
                if trigger_match:
                    trigger_icon = trigger_match.group(1)
                    effect_text = jp_text[trigger_match.end():].lstrip('：')
                    
                    # Match effect text against clause-level patterns
                    matched_clauses_for_effect = []
                    for clause_pattern in dsl_patterns:
                        clause_match = re.search(clause_pattern["regex"], effect_text)
                        if clause_match:
                            matched_clauses_for_effect.append({
                                "pattern_name": clause_pattern["name"],
                                "template": clause_pattern["template"],
                                "matched_text": clause_match.group(0),
                                "variables": list(clause_match.groups()),
                            })
                    
                    if matched_clauses_for_effect:
                        matched_abilities.append({
                            "original": jp_text,
                            "pattern_name": "trigger_clause_sequence",
                            "structure": "Ability - Trigger + clause pattern sequence",
                            "template": f"{trigger_icon} + " + " + ".join([c["template"] for c in matched_clauses_for_effect]),
                            "matched_text": jp_text,
                            "variables": [trigger_icon] + [v for c in matched_clauses_for_effect for v in c["variables"]],
                            "trigger": ability.get('trigger', 'UNKNOWN'),
                            "clause_patterns": matched_clauses_for_effect,
                        })
                        ability_pattern_counts["trigger_clause_sequence"] += 1
                        if "trigger_clause_sequence" not in ability_pattern_variables:
                            ability_pattern_variables["trigger_clause_sequence"] = []
                        ability_pattern_variables["trigger_clause_sequence"].append([trigger_icon] + [c["pattern_name"] for c in matched_clauses_for_effect])
                    else:
                        unmatched_abilities.append(jp_text)
                else:
                    unmatched_abilities.append(jp_text)
    
    for clause_data in clauses:
        clause = clause_data["clause"]
        # Don't strip icons - they contain semantic information
        matched = False
        
        for pattern in dsl_patterns:
            match = re.search(pattern["regex"], clause)
            if match:
                variables = list(match.groups())
                matched_clauses.append({
                    "original": clause,
                    "pattern_name": pattern["name"],
                    "structure": pattern["structure"],
                    "template": pattern["template"],
                    "matched_text": match.group(0),
                    "variables": variables,
                })
                pattern_counts[pattern["name"]] += 1
                
                if pattern["name"] not in pattern_variables:
                    pattern_variables[pattern["name"]] = []
                pattern_variables[pattern["name"]].append(variables)
                
                matched = True
                break
        
        if not matched:
            unmatched_clauses.append(clause)
    
    return {
        "total_clauses": len(clauses),
        "matched_clauses": len(matched_clauses),
        "unmatched_clauses": len(unmatched_clauses),
        "unique_patterns": len(pattern_counts),
        "pattern_counts": dict(pattern_counts),
        "pattern_variables": pattern_variables,
        "compression_ratio": len(matched_clauses) / len(clauses) if clauses else 0,
        "matched_sample": matched_clauses[:20],
        "unmatched_sample": unmatched_clauses[:20],
        # Ability-level matching results
        "total_abilities": len(abilities) if abilities else 0,
        "matched_abilities": len(matched_abilities),
        "unmatched_abilities": len(unmatched_abilities),
        "unique_ability_patterns": len(ability_pattern_counts),
        "ability_pattern_counts": dict(ability_pattern_counts),
        "ability_pattern_variables": ability_pattern_variables,
        "ability_compression_ratio": len(matched_abilities) / len(abilities) if abilities else 0,
        "matched_ability_sample": matched_abilities[:20],
        "unmatched_ability_sample": unmatched_abilities[:20],
    }


def analyze_simple_terms(clauses: list[dict[str, Any]], term_mapping: dict[str, str]) -> dict[str, Any]:
    """
    Analyze clauses by simple game mechanic terms to identify DSL structures.
    
    DSL APPROACH: Card game ability text is a domain-specific language for game mechanics.
    We identify the "tokens" and "keywords" of this language to understand its syntax.
    
    INFORMATION THEORY GOAL: Represent abilities in as few patterns as possible without losing meaning.
    - Identify which tokens are "variables" (replaceable) vs "operators" (structural)
    - Variables: numbers, card types, groups, zones (high entropy, should be parameters)
    - Operators: actions, conditions, comparisons (low entropy, should be in template)
    - Goal: Maximize pattern reuse while preserving all game mechanics and meaning
    
    Bottom-up approach: Start with simple terms (keywords) to understand the language's
    vocabulary, then identify the grammatical structures (syntax) that combine them.
    
    Returns term frequencies, clause samples for each term, and compressibility analysis.
    """
    
    # Simple game mechanic terms from rules and common ability text
    simple_terms = [
        "スコア",
        "ブレード",
        "ハート",
        "エール",
        "エネルギー",
        "カード",
        "手札",
        "控え室",
        "デッキ",
        "ステージ",
        "ライブ",
        "メンバー",
        "引く",
        "置く",
        "得る",
        "アクティブ",
        "ウェイト",
        "登場",
        "移動",
        "見る",
        "選ぶ",
        "公開",
        "加える",
        "コスト",
        "必要ハート",
    ]
    
    term_clauses = {}
    term_counts = Counter()
    
    for clause_data in clauses:
        clause = clause_data["clause"]
        clause_no_icons = ICON_TOKEN_RE.sub("", clause)
        
        for term in simple_terms:
            if term in clause_no_icons:
                if term not in term_clauses:
                    term_clauses[term] = []
                term_clauses[term].append(clause)
                term_counts[term] += 1
    
    # Analyze placeholder percentage for each term's clauses
    term_placeholder_analysis = {}
    for term, clauses_with_term in term_clauses.items():
        total_chars = 0
        replaced_chars = 0
        
        for clause in clauses_with_term[:50]:  # Sample first 50
            clause_no_icons = ICON_TOKEN_RE.sub("", clause)
            original_len = len(clause_no_icons)
            total_chars += original_len
            
            # Calculate what would become placeholder
            normalized = clause_no_icons
            for en_name, jp_name in term_mapping.items():
                if jp_name in normalized:
                    replaced_chars += len(jp_name)
                    normalized = normalized.replace(jp_name, PLACEHOLDER)
            
            # Count numbers replaced
            number_matches = NUMBER_RE.findall(normalized)
            for num in number_matches:
                replaced_chars += len(num)
            normalized = NUMBER_RE.sub(PLACEHOLDER, normalized)
        
        if total_chars > 0:
            placeholder_pct = replaced_chars / total_chars
        else:
            placeholder_pct = 0
        
        term_placeholder_analysis[term] = {
            "count": len(clauses_with_term),
            "sample_clauses": clauses_with_term[:10],
            "placeholder_percentage": placeholder_pct,
        }
    
    return {
        "total_clauses": len(clauses),
        "terms_analyzed": len(simple_terms),
        "term_counts": dict(term_counts.most_common(30)),
        "term_placeholder_analysis": term_placeholder_analysis,
    }


def extract_effects_from_clauses(clauses: list[dict[str, Any]], term_mapping: dict[str, str]) -> dict[str, Any]:
    """Extract and normalize effects from clauses, separating them from triggers."""
    effects = []
    triggers = []
    
    for clause_data in clauses:
        clause = clause_data["clause"]
        pairs = parse_trigger_effect(clause)
        
        for trigger, effect in pairs:
            # Normalize the effect using the term mapping
            normalized_effect = effect
            for en_name, jp_name in term_mapping.items():
                normalized_effect = normalized_effect.replace(jp_name, PLACEHOLDER)
            
            # Also replace numbers
            normalized_effect = NUMBER_RE.sub(PLACEHOLDER, normalized_effect)
            
            # Also replace icons in the effect
            normalized_effect = ICON_TOKEN_RE.sub(PLACEHOLDER, normalized_effect)
            
            effects.append({
                "trigger": trigger,
                "effect": effect,
                "normalized_effect": normalized_effect,
            })
            triggers.append(trigger)
    
    # Count unique normalized effects
    unique_effects = {}
    for effect_data in effects:
        norm = effect_data["normalized_effect"]
        if norm not in unique_effects:
            unique_effects[norm] = {
                "count": 0,
                "triggers": set(),
                "original_effects": [],
            }
        unique_effects[norm]["count"] += 1
        unique_effects[norm]["triggers"].add(effect_data["trigger"])
        unique_effects[norm]["original_effects"].append(effect_data["effect"])
    
    # Convert sets to lists for JSON serialization
    for norm in unique_effects:
        unique_effects[norm]["triggers"] = list(unique_effects[norm]["triggers"])
    
    # Count triggers
    trigger_counts = Counter(triggers)
    
    return {
        "total_effects": len(effects),
        "unique_effects": len(unique_effects),
        "unique_effects_data": unique_effects,
        "trigger_counts": dict(trigger_counts.most_common(20)),
        "effects_sample": effects[:20],
    }


def load_cards(cards_file: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(cards_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("cards.json must be a top-level object keyed by card id")
    return data


def load_rules(rules_file: Path) -> str:
    return rules_file.read_text(encoding="utf-8")


def group_abilities(cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for card_id, card in cards.items():
        ability_text = card.get("ability")
        if not isinstance(ability_text, str) or not ability_text.strip():
            continue
        entry = grouped.setdefault(
            ability_text,
            {
                "jp": ability_text,
                "ability_index": 0,
                "card_examples": [],
            },
        )
        entry["card_examples"].append(f"{card_id} | {card.get('name', '')} (ab#0)")

    abilities = list(grouped.values())
    abilities.sort(key=lambda item: item["jp"])
    for item in abilities:
        item["card_examples"].sort()
    return abilities


def split_clauses(text: str) -> list[str]:
    current = text.strip()
    clauses: list[str] = []
    buffer: list[str] = []
    paren_depth = 0
    quote_depth = 0

    for ch in current:
        if ch in "（(":
            paren_depth += 1
            buffer.append(ch)
            continue
        if ch in "）)":
            if paren_depth:
                paren_depth -= 1
            buffer.append(ch)
            continue
        if ch in "「『《":
            quote_depth += 1
            buffer.append(ch)
            continue
        if ch in "」』》":
            if quote_depth:
                quote_depth -= 1
            buffer.append(ch)
            continue
        if ch in "。\n" and paren_depth == 0 and quote_depth == 0:
            clause = "".join(buffer).strip()
            if clause:
                clauses.append(clause)
            buffer = []
            continue
        buffer.append(ch)

    tail = "".join(buffer).strip()
    if tail:
        clauses.append(tail)
    return clauses


def all_ability_clauses(cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    clauses: list[dict[str, Any]] = []
    for card_id, card in cards.items():
        ability = card.get("ability")
        if not isinstance(ability, str) or not ability.strip():
            continue
        for clause in split_clauses(ability):
            clauses.append({"card_id": card_id, "clause": clause, "ability": ability})
    return clauses


def token_counter(text: str) -> Counter[str]:
    return Counter(TOKEN_RE.findall(nfkc(text)))


def build_known_terms(cards: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    known: dict[str, set[str]] = {
        "names": set(),
        "units": set(),
        "series": set(),
        "products": set(),
    }
    for card in cards.values():
        for key, bucket in [
            ("name", "names"),
            ("unit", "units"),
            ("series", "series"),
            ("product", "products"),
        ]:
            value = card.get(key)
            if isinstance(value, str) and value.strip():
                known[bucket].add(value.strip())
    return known


def extract_quotes(text: str) -> list[str]:
    spans: list[str] = []
    for match in QUOTE_RE.finditer(text):
        value = match.group(1) or match.group(2)
        if value:
            spans.append(value)
    return spans


def build_candidate_terms(
    clauses: list[dict[str, Any]],
    rules_text: str,
    known: dict[str, set[str]],
    term_data: dict[str, Any],
) -> tuple[dict[str, list[str]], dict[str, Counter[str]]]:
    rules_counts = token_counter(rules_text)
    clause_counts = Counter()
    clause_seen: dict[str, set[int]] = defaultdict(set)
    for idx, row in enumerate(clauses):
        raw = nfkc(row["clause"])
        for token in TOKEN_RE.findall(raw):
            clause_counts[token] += 1
            clause_seen[token].add(idx)

    quoted_counts: Counter[str] = Counter()
    quoted_seen: dict[str, set[int]] = defaultdict(set)
    for idx, row in enumerate(clauses):
        for span in extract_quotes(nfkc(row["clause"])):
            quoted_counts[span] += 1
            quoted_seen[span].add(idx)

    # Use Japanese terms from the mapping (values) instead of hardcoded lists
    term_mapping = term_data["mapping"]
    manual_terms = set(term_mapping.values())
    
    # Also include quoted terms and known terms
    quoted_terms = set(quoted_counts)
    exact_terms = set().union(*known.values())

    all_terms = {
        "exact_terms": sorted(exact_terms, key=len, reverse=True),
        "discovered_terms": sorted(manual_terms, key=len, reverse=True),
        "term_mapping": term_mapping,
        "term_counts": term_data.get("counts", {}),
        "quoted_terms_discovered": term_data.get("quoted_terms", {}),
    }
    counters = {
        "rules_counts": rules_counts,
        "clause_counts": clause_counts,
        "quoted_counts": quoted_counts,
        "clause_seen": clause_seen,
        "quoted_seen": quoted_seen,
        "quoted_terms": quoted_terms,
    }
    return all_terms, counters


def replace_exact_terms(text: str, terms: list[str], counts: Counter[str], seen: dict[str, set[int]], clause_idx: int) -> str:
    result = text
    for term in terms:
        if not term or term not in result:
            continue
        occurrences = result.count(term)
        if occurrences:
            counts[term] += occurrences
            seen[term].add(clause_idx)
            result = result.replace(term, PLACEHOLDER)
    return result


def normalize_clause(
    clause: str,
    clause_idx: int,
    exact_terms: list[str],
    discovered_terms: list[str],
    stats: dict[str, Any],
) -> str:
    text = nfkc(clause)
    raw_text = text

    # Count and replace full icon tokens, not just the inner label.
    for token in ICON_TOKEN_RE.findall(raw_text):
        stats["icons"][token] += 1
        stats["icon_seen"][token].add(clause_idx)
    text = ICON_TOKEN_RE.sub(PLACEHOLDER, text)

    # Capture quoted spans before they are flattened.
    for span in extract_quotes(raw_text):
        stats["quotes"][span] += 1
        stats["quote_seen"][span].add(clause_idx)
    text = QUOTE_RE.sub(PLACEHOLDER, text)

    text = text.replace(PLACEHOLDER, SENTINEL)
    text = replace_exact_terms(text, exact_terms, stats["exact_terms"], stats["exact_seen"], clause_idx)
    text = replace_exact_terms(text, discovered_terms, stats["discovered_terms"], stats["discovered_seen"], clause_idx)

    # Numbers, counts, and icon labels that survived the previous steps.
    number_hits = NUMBER_RE.findall(text)
    for hit in number_hits:
        stats["numbers"][hit] += 1
        stats["number_seen"][hit].add(clause_idx)
    text = NUMBER_RE.sub(PLACEHOLDER, text)

    # Protect the placeholder from any later cleanup.
    text = re.sub(r"[（）()]", "", text)
    text = re.sub(r"\s+", "", text)
    text = text.replace(SENTINEL, PLACEHOLDER)
    text = re.sub(rf"(?:{re.escape(PLACEHOLDER)})+", PLACEHOLDER, text)
    return text


def blank_stats() -> dict[str, Any]:
    return {
        "icons": Counter(),
        "icon_seen": defaultdict(set),
        "quotes": Counter(),
        "quote_seen": defaultdict(set),
        "exact_terms": Counter(),
        "exact_seen": defaultdict(set),
        "discovered_terms": Counter(),
        "discovered_seen": defaultdict(set),
        "numbers": Counter(),
        "number_seen": defaultdict(set),
    }


def count_unique_clauses(clauses: list[dict[str, Any]]) -> int:
    """Count unique raw clauses."""
    return len({nfkc(c["clause"]) for c in clauses})


def normalize_clause_partial(
    clause: str,
    clause_idx: int,
    replace_icons: bool = False,
    replace_quotes: bool = False,
    replace_numbers: bool = False,
    replace_terms: bool = False,
    terms: list[str] = None,
    stats: dict[str, Any] = None,
) -> str:
    """Normalize clause with selective replacement for comparison."""
    if stats is None:
        stats = blank_stats()
    text = nfkc(clause)
    raw_text = text

    if replace_icons:
        for token in ICON_TOKEN_RE.findall(raw_text):
            stats["icons"][token] += 1
            stats["icon_seen"][token].add(clause_idx)
        text = ICON_TOKEN_RE.sub(PLACEHOLDER, text)

    if replace_quotes:
        for span in extract_quotes(raw_text):
            stats["quotes"][span] += 1
            stats["quote_seen"][span].add(clause_idx)
        text = QUOTE_RE.sub(PLACEHOLDER, text)

    text = text.replace(PLACEHOLDER, SENTINEL)

    if replace_terms and terms:
        text = replace_exact_terms(text, terms, stats["exact_terms"], stats["exact_seen"], clause_idx)

    if replace_numbers:
        number_hits = NUMBER_RE.findall(text)
        for hit in number_hits:
            stats["numbers"][hit] += 1
            stats["number_seen"][hit].add(clause_idx)
        text = NUMBER_RE.sub(PLACEHOLDER, text)

    text = re.sub(r"[（）()]", "", text)
    text = re.sub(r"\s+", "", text)
    text = text.replace(SENTINEL, PLACEHOLDER)
    text = re.sub(rf"(?:{re.escape(PLACEHOLDER)})+", PLACEHOLDER, text)
    return text


def compare_clause_variations(
    clauses: list[dict[str, Any]],
    exact_terms: list[str],
    discovered_terms: list[str],
    term_mapping: dict[str, str],
) -> dict[str, Any]:
    """Compare unique clause counts with manual variable replacement."""
    raw_unique = count_unique_clauses(clauses)
    
    stats = blank_stats()
    all_terms = exact_terms + discovered_terms

    # Normalize with all replacements
    normalized_clauses = []
    for idx, row in enumerate(clauses):
        normalized = normalize_clause_partial(
            row["clause"], idx, replace_icons=True, replace_quotes=True,
            replace_numbers=True, replace_terms=True, terms=all_terms, stats=stats
        )
        normalized_clauses.append(normalized)
    
    final_unique = len(set(normalized_clauses))
    total_reduction = raw_unique - final_unique

    # Show what was replaced
    top_replaced_terms = [
        {"term": term, "count": count, "clause_count": len(stats["exact_seen"].get(term, set()))}
        for term, count in stats["exact_terms"].most_common(30)
    ]

    return {
        "raw_unique": raw_unique,
        "final_unique": final_unique,
        "total_reduction": total_reduction,
        "manual_terms_count": len(discovered_terms),
        "manual_terms_sample": discovered_terms[:30],
        "top_replaced_terms": top_replaced_terms,
        "term_mapping": term_mapping,
    }


def residual_candidates(skeletons: list[str], rules_text: str) -> list[dict[str, Any]]:
    rules_counts = token_counter(rules_text)
    counts = Counter()
    seen: dict[str, set[int]] = defaultdict(set)

    for idx, skeleton in enumerate(skeletons):
        for token in TOKEN_RE.findall(nfkc(skeleton)):
            if token == PLACEHOLDER:
                continue
            counts[token] += 1
            seen[token].add(idx)

    candidates = []
    for token, count in counts.items():
        if count < 3:
            continue
        candidates.append(
            {
                "token": token,
                "count": count,
                "clause_count": len(seen[token]),
                "rules_count": rules_counts.get(token, 0),
                "rules_supported": token in rules_counts,
            }
        )

    candidates.sort(key=lambda row: (-row["count"], -row["clause_count"], row["token"]))
    return candidates[:200]


def group_by_structure(
    clauses: list[dict[str, Any]],
    abilities: list[dict[str, Any]],
    exact_terms: list[str],
    discovered_terms: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    stats = blank_stats()
    all_skeletons: list[str] = []
    for idx, row in enumerate(clauses):
        all_skeletons.append(normalize_clause(row["clause"], idx, exact_terms, discovered_terms, stats))

    grouped: dict[str, dict[str, Any]] = {}
    for ability in abilities:
        skeletons = [
            normalize_clause(clause, -1, exact_terms, discovered_terms, blank_stats())
            for clause in split_clauses(ability["jp"])
        ]
        combined = " / ".join(skeletons)
        entry = grouped.setdefault(
            combined,
            {
                "skeleton": combined,
                "count": 0,
                "jp_examples": [],
                "card_examples": [],
            },
        )
        entry["count"] += 1
        if len(entry["jp_examples"]) < 5:
            entry["jp_examples"].append(ability["jp"])
        entry["card_examples"].extend(ability["card_examples"])

    structure_list = sorted(grouped.values(), key=lambda item: (-item["count"], item["skeleton"]))
    for item in structure_list:
        item["card_examples"] = sorted(set(item["card_examples"]))[:10]

    analysis = {
        "replacement_totals": {
            "icons": int(sum(stats["icons"].values())),
            "quotes": int(sum(stats["quotes"].values())),
            "exact_terms": int(sum(stats["exact_terms"].values())),
            "discovered_terms": int(sum(stats["discovered_terms"].values())),
            "numbers": int(sum(stats["numbers"].values())),
        },
        "top_icons": top_rows(stats["icons"], stats["icon_seen"]),
        "top_quotes": top_rows(stats["quotes"], stats["quote_seen"]),
        "top_exact_terms": top_rows(stats["exact_terms"], stats["exact_seen"]),
        "top_discovered_terms": top_rows(stats["discovered_terms"], stats["discovered_seen"]),
        "top_numbers": top_rows(stats["numbers"], stats["number_seen"]),
    }

    return structure_list, analysis, all_skeletons


def top_rows(counter: Counter[str], seen: dict[str, set[int]], limit: int = 100) -> list[dict[str, Any]]:
    rows = [
        {
            "token": token,
            "count": count,
            "clause_count": len(seen.get(token, set())),
        }
        for token, count in counter.items()
    ]
    rows.sort(key=lambda row: (-row["count"], -row["clause_count"], row["token"]))
    return rows[:limit]


def extract_abilities(cards_file: Path, rules_file: Path, output_file: Path, metadata_file: Path) -> dict[str, Any]:
    cards = load_cards(cards_file)
    rules_text = load_rules(rules_file)
    clauses = all_ability_clauses(cards)
    abilities = group_abilities(cards)

    known = build_known_terms(cards)
    
    # Discover Japanese equivalents from metadata.json and ability text
    term_data = discover_japanese_equivalents(clauses, metadata_file)
    
    all_terms, counters = build_candidate_terms(clauses, rules_text, known, term_data)

    # Extract and normalize effects separately from triggers
    effects_analysis = extract_effects_from_clauses(clauses, term_data["mapping"])

    # Match clauses using DSL pattern matching (language structure approach)
    dsl_pattern_analysis = match_dsl_patterns(clauses, term_data["mapping"])

    # Analyze simple terms to understand clause structure (bottom-up approach)
    simple_term_analysis = analyze_simple_terms(clauses, term_data["mapping"])

    # Compare unique clauses with different replacement strategies
    clause_comparison = compare_clause_variations(
        clauses,
        all_terms["exact_terms"],
        all_terms["discovered_terms"],
        term_data["mapping"],
    )

    structures, analysis, skeletons = group_by_structure(
        clauses,
        abilities,
        all_terms["exact_terms"],
        all_terms["discovered_terms"],
    )
    analysis["residual_candidates"] = residual_candidates(skeletons, rules_text)
    analysis["rules_token_support"] = [
        {"token": token, "count": count}
        for token, count in counters["rules_counts"].most_common(100)
    ]
    analysis["clause_comparison"] = clause_comparison
    analysis["term_mapping"] = term_data["mapping"]
    analysis["term_counts"] = term_data["counts"]
    analysis["effects_analysis"] = effects_analysis
    analysis["dsl_pattern_analysis"] = dsl_pattern_analysis
    analysis["simple_term_analysis"] = simple_term_analysis

    payload = {
        "schema": "ability_skeletons.v6",
        "placeholder": PLACEHOLDER,
        "source": str(cards_file),
        "rules_source": str(rules_file),
        "metadata_source": str(metadata_file),
        "analysis": analysis,
        "structures": structures,
    }
    output_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def generate_structured_dsl_output(dsl_analysis: dict[str, Any], abilities_data: dict[str, Any], patterns: list[dict[str, Any]], output_file: Path) -> None:
    """
    Generate structured JSON output for DSL pattern analysis.
    Follows the structure of ability_frame_source.json for system consumption.
    """
    from datetime import datetime
    
    ability_level = dsl_analysis.get('dsl_pattern_analysis', {})
    pattern_counts = ability_level.get('ability_pattern_counts', {})
    pattern_variables = ability_level.get('ability_pattern_variables', {})
    matched_abilities = ability_level.get('matched_ability_sample', [])
    
    # Load abilities from cards to get card references
    abilities_from_cards = abilities_data.get('abilities', [])
    
    # Build pattern entries with matched abilities and card references
    patterns_output = []
    
    # Add patterns from ABILITY_LEVEL_PATTERNS
    for pattern_name in [p["name"] for p in patterns]:
        if pattern_name == "ability_catchall":
            continue  # Skip catchall in structured output
        
        pattern_info = next((p for p in patterns if p["name"] == pattern_name), None)
        if not pattern_info:
            continue
        
        match_count = pattern_counts.get(pattern_name, 0)
        variables_list = pattern_variables.get(pattern_name, [])
        
        # Find matched abilities for this pattern
        pattern_matched = [a for a in matched_abilities if a['pattern_name'] == pattern_name]
        
        matched_abilities_data = []
        for i, matched in enumerate(pattern_matched):
            # Find card references for this ability
            cards = []
            for ability in abilities_from_cards:
                for source in ability['source_ability_texts']:
                    if source['jp'] == matched['original']:
                        cards = source.get('cards', [])
                        break
                if cards:
                    break
            
            matched_abilities_data.append({
                "ability_text": matched['original'],
                "variables": matched.get('variables', []),
                "trigger": matched.get('trigger', 'UNKNOWN'),
                "card_refs": cards[:5]  # Limit to first 5 cards
            })
        
        patterns_output.append({
            "pattern_name": pattern_name,
            "regex": pattern_info["regex"],
            "template": pattern_info["template"],
            "structure": pattern_info["structure"],
            "match_count": match_count,
            "matched_abilities": matched_abilities_data
        })
    
    # Add dynamically generated trigger_clause_sequence pattern
    if "trigger_clause_sequence" in pattern_counts:
        match_count = pattern_counts["trigger_clause_sequence"]
        pattern_matched = [a for a in matched_abilities if a['pattern_name'] == 'trigger_clause_sequence']
        
        matched_abilities_data = []
        for matched in pattern_matched[:10]:  # Limit to 10 samples
            cards = []
            for ability in abilities_from_cards:
                for source in ability['source_ability_texts']:
                    if source['jp'] == matched['original']:
                        cards = source.get('cards', [])
                        break
                if cards:
                    break
            
            matched_abilities_data.append({
                "ability_text": matched['original'],
                "variables": matched.get('variables', []),
                "trigger": matched.get('trigger', 'UNKNOWN'),
                "clause_patterns": matched.get('clause_patterns', []),
                "card_refs": cards[:5]
            })
        
        patterns_output.append({
            "pattern_name": "trigger_clause_sequence",
            "regex": "DYNAMIC - trigger + clause patterns",
            "template": "⟦TRIGGER⟧ + [⟦CLAUSE_PATTERN_1⟧, ⟦CLAUSE_PATTERN_2⟧, ...]",
            "structure": "Ability - Trigger + clause pattern sequence (generic)",
            "match_count": match_count,
            "matched_abilities": matched_abilities_data
        })
    
    # Sort by match count (descending)
    patterns_output.sort(key=lambda p: -p['match_count'])
    
    output = {
        "schema": "dsl_analysis_structured.v1",
        "_comment": "DSL pattern analysis results - structured for system consumption. Generated by tools/extract_abilities_to_template.py",
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_patterns": len(patterns_output),
            "total_abilities_analyzed": ability_level.get('total_abilities', 0),
            "compression_ratio": ability_level.get('ability_compression_ratio', 0)
        },
        "patterns": patterns_output
    }
    
    output_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize ability text into clause skeletons")
    parser.add_argument("--cards", type=Path, default=Path("data/cards.json"), help="Path to cards.json")
    parser.add_argument("--rules", type=Path, default=Path("data/rules.txt"), help="Path to rules.txt")
    parser.add_argument("--metadata", type=Path, default=Path("data/metadata.json"), help="Path to metadata.json")
    parser.add_argument("--output", type=Path, default=Path("data/abilities_extracted.json"), help="Output JSON path")
    args = parser.parse_args()
    payload = extract_abilities(args.cards, args.rules, args.output, args.metadata)
    
    # Generate structured DSL output
    try:
        abilities_data = json.load(open('data/abilities_from_cards.json', encoding='utf-8'))
        dsl_output_file = Path("data/dsl_analysis_structured.json")
        generate_structured_dsl_output(payload['analysis'], abilities_data, ABILITY_LEVEL_PATTERNS, dsl_output_file)
        print(f"Structured DSL output written to {dsl_output_file}")
    except Exception as e:
        print(f"Warning: Could not generate structured DSL output: {e}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
