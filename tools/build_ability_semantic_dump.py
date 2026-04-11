"""Build a full semantic dump from ability_frame_source.json.

This produces one inspectable JSON file that shows:
- the original authored ability text and markup
- the grouped unique ability/card references from ability_frame_source.json
- the extracted semantic report
- the tokenized authored text
- the leftover clauses that were not matched
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.compiler.semantic_processor import (
    abstract_authored_text,
    extract_semantic_form_from_text,
    tokenize_authored_text,
)


def _load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _stable_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _build_clause_atoms(clause_text: str, start_index: int = 0) -> tuple[dict[str, Any], int]:
    """Break a clause into visible atoms plus switchable placeholders."""
    tokens = tokenize_authored_text(clause_text)
    atoms: list[dict[str, Any]] = []
    placeholder_count = start_index

    for token in tokens:
        if token.get("kind") == "template":
            atoms.append(
                {
                    "kind": "template",
                    "raw": token.get("raw", ""),
                    "source": token.get("source", ""),
                    "label": token.get("label", ""),
                    "placeholder": f"{{template_{placeholder_count}}}",
                }
            )
            placeholder_count += 1
            continue

        text = str(token.get("text", ""))
        start = 0
        for match in re.finditer(r"\d+", text):
            if match.start() > start:
                atoms.append(
                    {
                        "kind": "text",
                        "text": text[start:match.start()],
                    }
                )
            atoms.append(
                {
                    "kind": "number",
                    "text": match.group(0),
                    "placeholder": f"{{num_{placeholder_count}}}",
                }
            )
            placeholder_count += 1
            start = match.end()
        if start < len(text):
            atoms.append(
                {
                    "kind": "text",
                    "text": text[start:],
                }
            )

    pattern_parts: list[str] = []
    for atom in atoms:
        if atom["kind"] == "text":
            pattern_parts.append(atom["text"])
        else:
            pattern_parts.append(atom["placeholder"])

    return {
        "atoms": atoms,
        "pattern": "".join(pattern_parts),
    }, placeholder_count


_GROUP_NAME_RE = re.compile(r"『([^』]+)』")
_ZONE_COUNT_RE = re.compile(r"(\d+)枚")
_ZONE_LIMIT_RE = re.compile(r"(\d+)枚まで")


def _extract_group_names(text: str) -> list[dict[str, Any]]:
    """Extract bracketed group names like 『虹ヶ咲』."""
    names: list[dict[str, Any]] = []
    for match in _GROUP_NAME_RE.finditer(text):
        names.append(
            {
                "kind": "group_name",
                "raw": match.group(0),
                "text": match.group(1),
                "placeholder": "{group_name}",
            }
        )
    return names


def _extract_zone_patterns(text: str) -> list[dict[str, Any]]:
    """Extract zone-like patterns like 1枚, 3枚まで."""
    patterns: list[dict[str, Any]] = []
    for match in _ZONE_LIMIT_RE.finditer(text):
        patterns.append(
            {
                "kind": "zone_limit",
                "raw": match.group(0),
                "text": match.group(1),
                "placeholder": "{zone_limit}",
            }
        )
    for match in _ZONE_COUNT_RE.finditer(text):
        patterns.append(
            {
                "kind": "zone_count",
                "raw": match.group(0),
                "text": match.group(1),
                "placeholder": "{zone_count}",
            }
        )
    return patterns


def build_semantic_dump(source_path: Path, output_path: Path) -> dict[str, Any]:
    payload = _load_json(source_path)
    if not isinstance(payload, dict):
        raise TypeError(f"Expected object at {source_path}, got {type(payload).__name__}")

    ability_entries = payload.get("abilities", [])
    if not isinstance(ability_entries, list):
        raise TypeError(f"Expected abilities list at {source_path}")

    entries: list[dict[str, Any]] = []
    ability_count = 0
    matched_clause_count = 0
    unmatched_clause_count = 0
    total_card_refs = 0

    for ability_index, ability in enumerate(ability_entries):
        if not isinstance(ability, dict):
            continue

        raw_text = str(ability.get("primary_text_jp", "") or "")
        semantic_form = extract_semantic_form_from_text(raw_text)
        tokenized_text = tokenize_authored_text(raw_text)
        abstract_text = abstract_authored_text(raw_text)
        clause_texts = [clause for clause in semantic_form.get("clauses", []) if isinstance(clause, dict)]
        card_refs = ability.get("card_refs", [])
        if not isinstance(card_refs, list):
            card_refs = []
        signature_source = f"{ability.get('trigger_id', 0)}|{abstract_text}|{raw_text}"
        equivalence_source = f"{ability.get('trigger_id', 0)}|{abstract_text}"
        clause_reports: list[dict[str, Any]] = []
        placeholder_index = 0
        for clause in clause_texts:
            clause_text = str(clause.get("text", "") or "")
            clause_report = dict(clause)
            atoms, placeholder_index = _build_clause_atoms(clause_text, placeholder_index)
            clause_report["atoms"] = atoms
            clause_report["abstract_text"] = abstract_authored_text(clause_text)
            clause_reports.append(clause_report)

        switchable_fields: list[dict[str, Any]] = []
        for token_index, token in enumerate(tokenized_text):
            if token.get("kind") != "template":
                continue
            switchable_fields.append(
                {
                    "kind": "template",
                    "raw": token.get("raw", ""),
                    "text": token.get("label", token.get("source", "")),
                    "label": token.get("label", ""),
                    "placeholder": f"{{template_{token_index}}}",
                }
            )
        for clause in clause_reports:
            atoms = clause.get("atoms", {})
            if not isinstance(atoms, dict):
                continue
            for atom in atoms.get("atoms", []):
                if not isinstance(atom, dict):
                    continue
                if atom.get("kind") not in {"template", "number"}:
                    continue
                switchable_fields.append(
                    {
                        "kind": atom.get("kind"),
                        "raw": atom.get("raw", atom.get("text", "")),
                        "text": atom.get("text", ""),
                        "label": atom.get("label", atom.get("text", "")),
                        "placeholder": atom.get("placeholder", ""),
                    }
                )

        # Extract group names and zone patterns from the full text
        group_names = _extract_group_names(raw_text)
        zone_patterns = _extract_zone_patterns(raw_text)
        switchable_fields.extend(group_names)
        switchable_fields.extend(zone_patterns)

        entries.append(
            {
                "ability_index": ability_index,
                "signature": ability.get("signature", "") or _stable_hash(signature_source),
                "equivalence_key": _stable_hash(equivalence_source),
                "trigger_id": ability.get("trigger_id", 0),
                "trigger": ability.get("trigger", ""),
                "primary_text_jp": raw_text,
                "primary_text_en": ability.get("primary_text_en", ""),
                "source_ability_texts": ability.get("source_ability_texts", []),
                "text_tokens": tokenized_text,
                "abstract_text": abstract_text,
                "clauses": clause_reports,
                "semantic_form": semantic_form,
                "card_refs": card_refs,
                "switchable_fields": switchable_fields,
            }
        )

        ability_count += 1
        total_card_refs += len(card_refs)
        matched_clause_count += int(semantic_form["coverage"]["matched_clause_count"])
        unmatched_clause_count += int(semantic_form["coverage"]["unmatched_clause_count"])

    payload = {
        "schema": "ability_semantic_dump.v2",
        "source": str(source_path),
        "summary": {
            "ability_count": ability_count,
            "unique_ability_count": ability_count,
            "source_entry_count": ability_count,
            "total_card_refs": total_card_refs,
            "matched_clause_count": matched_clause_count,
            "unmatched_clause_count": unmatched_clause_count,
        },
        "abilities": entries,
    }
    _dump_json(output_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a full semantic dump from grouped ability source")
    parser.add_argument(
        "--input",
        default="data/ability_frame_source.json",
        help="Path to the grouped ability source JSON",
    )
    parser.add_argument(
        "--output",
        default="data/ability_semantic_dump.json",
        help="Path for the semantic dump",
    )
    args = parser.parse_args()

    build_semantic_dump(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()
