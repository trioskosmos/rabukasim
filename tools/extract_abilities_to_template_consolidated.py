#!/usr/bin/env python3
"""
Extract abilities from cards.json into clause skeletons.

Consolidated version with minimal, non-overlapping skeleton patterns that combine to form full abilities.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


SENTENCE_BREAK_RE = re.compile(r"[。！？\n]")
ICON_RE = re.compile(r"\{\{[^{}]+\}\}")
QUOTE_RE = re.compile(r"『[^』]+』|「[^」]+」")
NUMBER_RE = re.compile(r"(?:\bN\b|\bX\b|[0-9０-９]+|[一二三四五六七八九十百千万]+)")

# ABILITY-LEVEL PATTERNS (special patterns with unique semantic meaning)
ABILITY_LEVEL_PATTERNS = [
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

# CLAUSE-LEVEL SKELETON PATTERNS (consolidated, no overlaps)
# These are minimal skeleton components that combine to form full abilities
DSL_PATTERNS = [
    # ===== DURATION & MODIFIERS =====
    {
        "name": "duration_permanent",
        "regex": r"常時",
        "template": "⟦DURATION⟧",
        "structure": "Duration - Permanent",
    },
    {
        "name": "duration_end_live",
        "regex": r"ライブ終了時まで",
        "template": "⟦DURATION⟧",
        "structure": "Duration - Until end of live",
    },
    {
        "name": "duration_end_turn",
        "regex": r"このターン",
        "template": "⟦DURATION⟧",
        "structure": "Duration - This turn",
    },
    {
        "name": "optional",
        "regex": r"てもよい",
        "template": "⟦OPTIONAL⟧",
        "structure": "Modifier - Optional",
    },
    
    # ===== BASIC ACTIONS =====
    {
        "name": "draw_cards",
        "regex": r"カードを(\d+)枚引く",
        "template": "カードを⟦X⟧枚引く",
        "structure": "Action - Draw cards",
    },
    {
        "name": "discard_to_zone",
        "regex": r"([^。]+)を([^。]+)に置く",
        "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置く",
        "structure": "Action - Discard to zone",
    },
    {
        "name": "add_to_zone",
        "regex": r"([^。]+)を([^。]+)に加える",
        "template": "⟦SOURCE⟧を⟦DESTINATION⟧に加える",
        "structure": "Action - Add to zone",
    },
    {
        "name": "look_at_cards",
        "regex": r"([^。]+)を(\d+)枚見る",
        "template": "⟦SOURCE⟧を⟦X⟧枚見る",
        "structure": "Action - Look at cards",
    },
    {
        "name": "reveal_cards",
        "regex": r"([^。]+)を(\d+)枚公開して",
        "template": "⟦SOURCE⟧を⟦X⟧枚公開して",
        "structure": "Action - Reveal cards",
    },
    {
        "name": "select_cards",
        "regex": r"(\d+)枚選ぶ",
        "template": "⟦X⟧枚選ぶ",
        "structure": "Action - Select cards",
    },
    {
        "name": "gain_resource",
        "regex": r"([^。]+)を得る",
        "template": "⟦RESOURCE⟧を得る",
        "structure": "Action - Gain resource",
    },
    {
        "name": "change_state",
        "regex": r"([^。]+)を([^。]+)にする",
        "template": "⟦TARGET⟧を⟦STATE⟧にする",
        "structure": "Action - Change state",
    },
    {
        "name": "move_member",
        "regex": r"([^。]+)を([^。]+)に移動する",
        "template": "⟦TARGET⟧を⟦AREA⟧に移動する",
        "structure": "Action - Move member",
    },
    {
        "name": "shuffle_deck",
        "regex": r"デッキをシャッフルする",
        "template": "デッキをシャッフルする",
        "structure": "Action - Shuffle deck",
    },
    
    # ===== CONDITIONAL PATTERNS =====
    {
        "name": "conditional_presence",
        "regex": r"([^。]+)に([^。]+)がいる場合、([^。]+)",
        "template": "⟦ZONE⟧に⟦TARGET⟧がいる場合、⟦EFFECT⟧",
        "structure": "Conditional - Presence triggers effect",
    },
    {
        "name": "conditional_group_presence",
        "regex": r"([^。]+)に『([^』]+)』のメンバーがいる場合、([^。]+)",
        "template": "⟦ZONE⟧に『⟦GROUP⟧』のメンバーがいる場合、⟦EFFECT⟧",
        "structure": "Conditional - Group presence triggers effect",
    },
    {
        "name": "conditional_threshold",
        "regex": r"([^。]+)が(\d+)枚以上の場合、([^。]+)",
        "template": "⟦SOURCE⟧が⟦X⟧枚以上の場合、⟦EFFECT⟧",
        "structure": "Conditional - Threshold triggers effect",
    },
    {
        "name": "conditional_cost",
        "regex": r"コスト(\d+)(以下|以上)の([^。]+)が([^。]+)いる場合、([^。]+)",
        "template": "コスト⟦X⟧⟦OP⟧の⟦TYPE⟧が⟦CONDITION⟧いる場合、⟦EFFECT⟧",
        "structure": "Conditional - Cost threshold triggers effect",
    },
    {
        "name": "conditional_comparison",
        "regex": r"([^。]+)が相手より([少多]い)場合、([^。]+)",
        "template": "⟦STAT⟧が相手より⟦COMPARISON⟧場合、⟦EFFECT⟧",
        "structure": "Conditional - Comparison triggers effect",
    },
    {
        "name": "conditional_total",
        "regex": r"([^。]+)の合計が(\d+)以上の場合、([^。]+)",
        "template": "⟦SOURCE⟧の合計が⟦X⟧以上の場合、⟦EFFECT⟧",
        "structure": "Conditional - Total threshold triggers effect",
    },
    
    # ===== COST-EFFECT PATTERNS =====
    {
        "name": "cost_effect",
        "regex": r"([^。]+)を([^。]+)に置いてもよい：([^。]+)",
        "template": "⟦COST⟧を⟦DESTINATION⟧に置いてもよい：⟦EFFECT⟧",
        "structure": "Cost-Effect - Optional cost to activate",
    },
    {
        "name": "cost_effect_mandatory",
        "regex": r"([^。]+)を([^。]+)に置く：([^。]+)",
        "template": "⟦COST⟧を⟦DESTINATION⟧に置く：⟦EFFECT⟧",
        "structure": "Cost-Effect - Mandatory cost to activate",
    },
    
    # ===== MULTI-STEP PATTERNS =====
    {
        "name": "look_select_add",
        "regex": r"([^。]+)を(\d+)枚見る。その中から(\d+)枚([^。]+)",
        "template": "⟦SOURCE⟧を⟦X⟧枚見る。その中から⟦Y⟧枚⟦ACTION⟧",
        "structure": "Multi-Step - Look, select, act",
    },
    {
        "name": "look_add_discard",
        "regex": r"([^。]+)を(\d+)枚見る。その中から([^。]+)を(\d+)枚まで([^。]+)。残りを([^。]+)に置く",
        "template": "⟦SOURCE⟧を⟦X⟧枚見る。その中から⟦FILTER⟧を⟦Y⟧枚まで⟦ACTION⟧。残りを⟦DESTINATION⟧に置く",
        "structure": "Multi-Step - Look, add, discard rest",
    },
    {
        "name": "discard_then_effect",
        "regex": r"([^。]+)を([^。]+)に置いてもよい。そうした場合、([^。]+)",
        "template": "⟦SOURCE⟧を⟦DESTINATION⟧に置いてもよい。そうした場合、⟦EFFECT⟧",
        "structure": "Multi-Step - Discard then trigger",
    },
    {
        "name": "gain_then_place",
        "regex": r"([^。]+)を得て、([^。]+)を([^。]+)に置く",
        "template": "⟦RESOURCE⟧を得て、⟦CARD⟧を⟦DESTINATION⟧に置く",
        "structure": "Multi-Step - Gain then place",
    },
    
    # ===== PER-UNIT PATTERNS =====
    {
        "name": "per_unit",
        "regex": r"([^。]+)(\d+)枚につき、([^。]+)",
        "template": "⟦SOURCE⟧⟦X⟧枚につき、⟦EFFECT⟧",
        "structure": "Per-Unit - Effect per unit",
    },
    {
        "name": "per_score",
        "regex": r"ライブの合計スコアが([^。]+)につき、([^。]+)",
        "template": "ライブの合計スコアが⟦AMOUNT⟧につき、⟦EFFECT⟧",
        "structure": "Per-Unit - Effect per score",
    },
    
    # ===== TRIGGER PATTERNS =====
    {
        "name": "trigger_timing",
        "regex": r"([^。]+)とき、([^。]+)",
        "template": "⟦TRIGGER⟧とき、⟦EFFECT⟧",
        "structure": "Trigger - Timing based",
    },
    {
        "name": "trigger_on_action",
        "regex": r"([^。]+)が([^。]+)とき、([^。]+)",
        "template": "⟦SOURCE⟧が⟦ACTION⟧とき、⟦EFFECT⟧",
        "structure": "Trigger - Action based",
    },
    {
        "name": "trigger_per_action",
        "regex": r"([^。]+)たび、([^。]+)",
        "template": "⟦ACTION⟧たび、⟦EFFECT⟧",
        "structure": "Trigger - Per action",
    },
    
    # ===== CHOICE PATTERNS =====
    {
        "name": "choose_from_options",
        "regex": r"([^。]+)から(\d+)つ選ぶ",
        "template": "⟦OPTIONS⟧から⟦X⟧つ選ぶ",
        "structure": "Choice - Select from options",
    },
    {
        "name": "choose_one_of",
        "regex": r"([^。]+)のうち、1つを選ぶ",
        "template": "⟦OPTIONS⟧のうち、1つを選ぶ",
        "structure": "Choice - Select one of",
    },
    
    # ===== SPECIAL MECHANICS =====
    {
        "name": "multi_card_stage",
        "regex": r"コストの合計が(\d+)以下になるように([^。]+)を(\d+)枚までステージに登場させる",
        "template": "コストの合計が⟦X⟧以下になるように⟦TYPE⟧を⟦Y⟧枚までステージに登場させる",
        "structure": "Special - Multi-card stage with cost limit",
    },
    {
        "name": "opponent_choice",
        "regex": r"相手は([^。]+)をしてもよい。そうしなかった場合、([^。]+)",
        "template": "相手は⟦ACTION⟧をしてもよい。そうしなかった場合、⟦EFFECT⟧",
        "structure": "Special - Opponent choice",
    },
    {
        "name": "repeat_limit",
        "regex": r"([^。]+)(\d+)回まで([^。]+)してよい",
        "template": "⟦PROCEDURE⟧⟦X⟧回まで⟦ACTION⟧してよい",
        "structure": "Special - Repeat with limit",
    },
    {
        "name": "score_nonzero",
        "regex": r"([^。]+)では([^。]+)の合計スコアは0にはならない",
        "template": "⟦CONDITION⟧では⟦SOURCE⟧の合計スコアは0にはならない",
        "structure": "Special - Score non-zero condition",
    },
    
    # ===== PARENTHETICAL =====
    {
        "name": "parenthetical",
        "regex": r"（([^）]+)）",
        "template": "（⟦NOTE⟧）",
        "structure": "Parenthetical - Note",
    },
    
    # ===== CATCH-ALL =====
    {
        "name": "catchall_any",
        "regex": r".+",
        "template": "⟦TEXT⟧",
        "structure": "Catch-all - Any text",
    },
]


def nfkc(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def load_cards(cards_file: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(cards_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("cards.json must be a top-level object keyed by card id")
    return data


def ability_rows(cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for card_no, card in cards.items():
        ability_text = card.get("ability_text", "")
        if not ability_text:
            continue
        rows.append({
            "card_no": card_no,
            "card_name": card.get("name", ""),
            "ability_text": ability_text,
        })
    return rows


def split_clauses(ability_text: str) -> list[str]:
    text = nfkc(ability_text).strip()
    if not text:
        return []
    parts: list[str] = []
    for chunk in SENTENCE_BREAK_RE.split(text):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts.extend(piece.strip() for piece in chunk.split("：") if piece.strip())
    return parts


def extract_variables(text: str) -> list[dict[str, str]]:
    """
    Pull direct variables out of the raw ability text.
    This is intentionally shallow: it records what appears, not what it means.
    """
    vars_found: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, value: str) -> None:
        key = (kind, value)
        if key in seen:
            return
        seen.add(key)
        vars_found.append({"kind": kind, "value": value})

    for match in ICON_RE.findall(text):
        add("icon", match)

    for match in QUOTE_RE.findall(text):
        value = match if isinstance(match, str) else next((m for m in match if m), "")
        if value:
            add("quoted", value)

    for match in NUMBER_RE.findall(text):
        add("number", match)

    return vars_found


def clause_skeleton(clauses: list[str]) -> str:
    """Create a skeleton representation of clauses."""
    return " | ".join(clauses)


def group_abilities(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        clauses = split_clauses(row["ability_text"])
        if not clauses:
            continue
        variables = extract_variables(row["ability_text"])
        skeleton = clause_skeleton(clauses)
        entry = grouped.setdefault(
            skeleton,
            {
                "ability_text": row["ability_text"],
                "clauses": clauses,
                "variables": variables,
                "skeleton": skeleton,
                "template": skeleton,
                "count": 0,
                "card_refs": [],
                "examples": [],
            },
        )
        entry["count"] += 1
        entry["card_refs"].append(f'{row["card_no"]} | {row["card_name"]}')
        if len(entry["examples"]) < 5:
            entry["examples"].append(row["ability_text"])
    abilities = sorted(grouped.values(), key=lambda item: (-item["count"], item["skeleton"]))
    for entry in abilities:
        entry["card_refs"] = sorted(set(entry["card_refs"]))[:10]
    return abilities


def write_output(output_file: Path, abilities: list[dict[str, Any]]) -> None:
    output_file.write_text(json.dumps(abilities, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract abilities into clause skeletons")
    parser.add_argument("--cards", type=Path, default=Path("data/cards.json"))
    parser.add_argument("--output", type=Path, default=Path("data/abilities_extracted.json"))
    args = parser.parse_args()

    cards = load_cards(args.cards)
    rows = ability_rows(cards)
    abilities = group_abilities(rows)
    write_output(args.output, abilities)
    
    print(f"Extracted {len(abilities)} unique ability skeletons from {len(rows)} abilities")
    print(f"Output written to {args.output}")


if __name__ == "__main__":
    main()
