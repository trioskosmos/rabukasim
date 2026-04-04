"""Simple YAML/JSON utilities for the compiler.

This module provides basic file I/O and ability frame normalization.
Previously 455 lines of complex codec logic - now simplified to essentials.
"""

from __future__ import annotations

import json
import yaml
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Any


def load_yaml(path: Path | str) -> dict[str, Any]:
    """Load YAML file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path | str) -> dict[str, Any]:
    """Load JSON file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path | str, payload: dict[str, Any]) -> None:
    """Write JSON file with UTF-8 encoding and pretty printing."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _utc_now() -> str:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _card_ref_label(card_ref: dict[str, Any]) -> str:
    """Create a human-readable label from a card reference."""
    card_no = str(card_ref.get("card_no", "")).strip()
    name = str(card_ref.get("name", "")).strip()
    ability_index = card_ref.get("ability_index", card_ref.get("ab_idx", card_ref.get("index", 0)))

    if not card_no:
        return ""

    label = card_no
    if name:
        label = label + " | " + name
    if ability_index is not None:
        label = label + " (ab#" + str(ability_index) + ")"
    return label


def _normalize_frame(frame: Any, idx: int) -> dict[str, Any]:
    """Normalize a single frame into standard format."""
    # Handle Return shorthand
    if frame == "Return" or frame == {"Return": {}}:
        return {"op": "RETURN", "frame_index": idx}

    if not isinstance(frame, dict):
        return {"op": "NOP", "frame_index": idx}

    # Extract opcode from various possible keys
    op = frame.get("op") or frame.get("opcode") or frame.get("opcode_name") or frame.get("kind") or "NOP"

    normalized = {"op": str(op).upper(), "frame_index": idx}

    # Copy options if present
    if isinstance(frame.get("options"), dict):
        normalized["options"] = frame["options"]

    # Preserve authored metadata that downstream tests and exporters still read.
    for key in ("source_words", "value", "filter", "slot", "params", "choice_flags", "choice_count"):
        if key in frame:
            normalized[key] = frame[key]

    return normalized


def _signature_hash(trigger_id: int, instructions: list[dict]) -> dict[str, str]:
    """Generate a signature hash for an ability."""
    # Build minimal signature payload
    sig_payload = {
        "trigger": trigger_id,
        "instructions": [{"op": f["op"]} for f in instructions]
    }
    sig_source = json.dumps(sig_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    sig_hash = sha1(sig_source.encode("utf-8")).hexdigest()

    return {
        "signature": "T" + str(trigger_id) + "|" + sig_hash,
        "signature_hash": sig_hash,
        "signature_source": sig_source,
    }


def _trigger_name_from_id(trigger_id: int, metadata: dict[str, Any]) -> str:
    triggers = metadata.get("triggers", {}) if isinstance(metadata, dict) else {}
    if isinstance(triggers, dict):
        for name, value in triggers.items():
            try:
                if int(value) == trigger_id:
                    return name
            except (TypeError, ValueError):
                continue
    return "TRIGGER_" + str(trigger_id)


def normalize_authored_ability_index(payload: dict[str, Any], metadata: dict[str, Any], card_db: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Normalize ability entries from the YAML source.

    FLOW:
    1. For each entry: normalize frames, compute signature
    2. Extract card references
    3. Sort by (trigger, card count, signature hash)
    4. Return normalized structure
    """
    entries = []

    for entry in payload.get("abilities", []):
        trigger_id = int(entry.get("trigger_id", 0))
        raw_frames = entry.get("instructions", entry.get("frames", [])) or []

        # Normalize frames
        instructions = [_normalize_frame(f, i) for i, f in enumerate(raw_frames)]

        # Get signature
        sig = _signature_hash(trigger_id, instructions)

        # Get card references
        card_refs = []
        cards = []
        for ref in entry.get("card_refs", []):
            if isinstance(ref, dict):
                card_refs.append(ref)
        for ref in entry.get("cards", []):
            if isinstance(ref, dict):
                card_refs.append(ref)
            elif isinstance(ref, str) and ref.strip():
                cards.append(ref.strip())

        cards.extend(_card_ref_label(ref) for ref in card_refs if _card_ref_label(ref))
        cards = list(dict.fromkeys(cards))

        normalized = {
            "signature": sig["signature"],
            "signature_hash": sig["signature_hash"],
            "signature_source": sig["signature_source"],
            "trigger_id": trigger_id,
            "trigger": _trigger_name_from_id(trigger_id, metadata),
            "frame_count": len(instructions),
            "opcode_sequence": [f["op"] for f in instructions],
            "instructions": instructions,
            "cards": cards,
            "card_refs": card_refs,
            "pseudocode": "",  # Simplified - no complex pseudocode generation
        }

        # Copy flags if present
        if "is_once_per_turn" in entry:
            normalized["is_once_per_turn"] = bool(entry.get("is_once_per_turn"))
        if "requires_selection" in entry:
            normalized["requires_selection"] = bool(entry.get("requires_selection"))

        entries.append(normalized)

    # Sort: by trigger, then by card count (desc), then by hash
    entries.sort(key=lambda e: (e["trigger_id"], -len(e["cards"]), e["signature_hash"]))

    total_card_refs = sum(len(entry["cards"]) for entry in entries)
    unique_cards = {
        card_label.split(" | ", 1)[0]
        for entry in entries
        for card_label in entry["cards"]
        if isinstance(card_label, str) and card_label
    }

    return {
        "generated_at": _utc_now(),
        "source": str(payload.get("source", "data/ability_frame_index.yaml")),
        "metadata_source": str(payload.get("metadata_source", "data/metadata.json")),
        "schema": "ability_frames.flat.v2",
        "_comment": "Derived frame/index output. The canonical semantic source is data/consolidated_abilities.json; this file is for frame-program compilation and lookup.",
        "summary": {
            "card_count": len(unique_cards),
            "ability_count": total_card_refs,
            "unique_ability_count": len(entries),
            "signature_group_count": len({e["signature_hash"] for e in entries}),
        },
        "abilities": entries,
    }


def build_runtime_ability_index(payload: dict[str, Any], metadata: dict[str, Any], card_db: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build runtime ability index - delegates to normalize."""
    normalized = normalize_authored_ability_index(payload, metadata, card_db)
    normalized["schema"] = "ability_frame_index.flat.v2"
    return normalized


def build_compact_ability_index(payload: dict[str, Any], metadata: dict[str, Any], card_db: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the compact authored frame index used by compatibility tests."""
    compact = normalize_authored_ability_index(payload, metadata, card_db)
    entries = compact.get("abilities", [])
    source_entries = payload.get("abilities", []) if isinstance(payload, dict) else []

    for idx, entry in enumerate(entries):
        source_entry = source_entries[idx] if idx < len(source_entries) and isinstance(source_entries[idx], dict) else {}
        entry["source_mode"] = "frame_authored"
        if "choice_flags" in source_entry:
            entry["choice_flags"] = int(source_entry.get("choice_flags", 0) or 0)
        if "choice_count" in source_entry:
            entry["choice_count"] = int(source_entry.get("choice_count", 0) or 0)
        if "is_once_per_turn" in source_entry:
            entry["is_once_per_turn"] = bool(source_entry.get("is_once_per_turn"))
        if "requires_selection" in source_entry:
            entry["requires_selection"] = bool(source_entry.get("requires_selection"))

    return compact

