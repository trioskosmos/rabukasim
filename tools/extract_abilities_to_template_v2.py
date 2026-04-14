#!/usr/bin/env python3
"""
Simple extraction of abilities from cards.json.
"""

import json
import re
from pathlib import Path
from typing import Any


def load_cards(cards_file: Path) -> dict[str, dict[str, Any]]:
    """Load cards from JSON file."""
    data = json.loads(cards_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("cards.json must be a top-level object keyed by card id")
    return data


def split_clauses(text: str) -> list[str]:
    """Split text by \n only when followed by trigger icon {{."""
    current = text.strip()
    clauses: list[str] = []
    buffer: list[str] = []
    
    for i, ch in enumerate(current):
        buffer.append(ch)
        # Split on \n only if next character starts a trigger icon
        if ch == '\n' and i + 1 < len(current) and current[i + 1] == '{':
            clause = "".join(buffer).strip()
            if clause:
                clauses.append(clause)
            buffer = []
    
    tail = "".join(buffer).strip()
    if tail:
        clauses.append(tail)
    return clauses


def group_abilities(cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Group abilities by their text to count unique abilities."""
    grouped: dict[str, dict[str, Any]] = {}
    
    for card_id, card in cards.items():
        ability_text = card.get("ability")
        if not isinstance(ability_text, str) or not ability_text.strip():
            continue
        
        # Split by clauses (periods and newlines)
        clauses = split_clauses(ability_text)
        
        for idx, clause in enumerate(clauses):
            entry = grouped.setdefault(
                clause,
                {
                    "jp": clause,
                    "ability_index": 0,
                    "card_examples": [],
                },
            )
            entry["card_examples"].append(f"{card_id} | {card.get('name', '')} (ab#{idx})")

    # Add count field
    for item in grouped.values():
        item["count"] = len(item["card_examples"])
    
    abilities = list(grouped.values())
    # Sort by count descending (most used first)
    abilities.sort(key=lambda item: -item["count"])
    for item in abilities:
        item["card_examples"].sort()
    
    return abilities


def main():
    cards_file = Path("data/cards.json")
    output_file = Path("data/abilities_extracted_simple.json")
    
    cards = load_cards(cards_file)
    abilities = group_abilities(cards)
    
    output = {
        "total_unique_abilities": len(abilities),
        "abilities": abilities,
    }
    
    output_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(abilities)} unique abilities to {output_file}")


if __name__ == "__main__":
    main()
