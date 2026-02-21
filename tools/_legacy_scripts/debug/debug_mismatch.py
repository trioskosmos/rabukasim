"""Debug specific mismatches between V1 and V2."""

import json
import os
import sys
from typing import List

# Ensure we can import from local modules
sys.path.append(os.getcwd())

from compiler.parser import AbilityParser as AbilityParserV1
from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import Ability


def abilities_to_str(abilities: List[Ability]) -> str:
    if not abilities:
        return "None"
    parts = []
    for i, ab in enumerate(abilities):
        eff_strs = [f"{e.effect_type.name}({e.value})" for e in ab.effects]
        cond_strs = [f"{c.type.name}" for c in ab.conditions]
        cost_strs = [f"{c.type.name}({c.value})" for c in ab.costs]
        parts.append(f"[{i}] T:{ab.trigger.name}")
        if eff_strs:
            parts.append(f"    E:{', '.join(eff_strs)}")
        if cond_strs:
            parts.append(f"    C:{', '.join(cond_strs)}")
        if cost_strs:
            parts.append(f"    K:{', '.join(cost_strs)}")
        if ab.effects and any(e.is_optional for e in ab.effects):
            parts.append("    OPT:True")
    return "\n".join(parts)


def debug_card(card_id):
    with open("engine/data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    card_data = cards.get(card_id)
    if not card_data:
        print(f"Card {card_id} not found")
        return

    text = card_data["ability"]
    print(f"Card: {card_data['name']} ({card_id})")
    print(f"Ability Text: {text}")
    print("-" * 50)

    p1 = AbilityParserV1()
    p2 = AbilityParserV2()

    print(f"Registry Stats: {p2.registry.stats()}")

    res1 = p1.parse_ability_text(text)
    res2 = p2.parse(text)

    print("Legacy (V1):")
    print(abilities_to_str(res1))
    print("-" * 20)
    print("New (V2):")
    # Verbose debug for V2
    from compiler.patterns.base import PatternPhase

    sents = p2._split_sentences(text)
    for i, sent in enumerate(sents):
        parts = p2._split_sentences(sent)  # Wait, sents is already split
        colon_idx = sent.find("：")
        if colon_idx == -1:
            colon_idx = sent.find(":")
        effect_part = sent[colon_idx + 1 :] if colon_idx != -1 else sent

        print(f"  Sentence {i}: {sent}")
        print(f"  Effect Part: {effect_part}")
        matches = p2.registry.match_all(effect_part, PatternPhase.EFFECT)
        print(f"  Matches found: {[m[0].name for m in matches]}")
        for p, m, d in matches:
            print(f"    - {p.name}: {m.group(0)} -> {d}")

    res2 = p2.parse(text)
    print("  Result:")
    print(abilities_to_str(res2))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_card(sys.argv[1])
    else:
        # Default to first few mismatches if known
        debug_card("PL!-sd1-001-SD")
