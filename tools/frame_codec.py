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


def load_authored_payload(path: Path | str) -> dict[str, Any]:
    """Load the canonical authored ability source from JSON or legacy YAML."""
    path = Path(path)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return load_yaml(path)
    return load_json(path)


def iter_authored_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return authored ability entries from either list-style or object-style payloads."""
    abilities = payload.get("abilities")
    if isinstance(abilities, list):
        return [entry for entry in abilities if isinstance(entry, dict)]

    entries: list[dict[str, Any]] = []
    for key, value in payload.items():
        if key.startswith("_"):
            continue
        if key in {"generated_at", "source", "metadata_source", "summary", "schema"}:
            continue
        if isinstance(value, dict):
            entry = dict(value)
            entry.setdefault("source_text", key)
            entries.append(entry)
    return entries


def load_yaml(path: Path | str) -> dict[str, Any]:
    """Load YAML file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8-sig") as f:
        return yaml.safe_load(f)


def load_json(path: Path | str) -> dict[str, Any]:
    """Load JSON file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8-sig") as f:
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

    # Preserve authored metadata that downstream compiler/runtime hydration still read.
    for key in (
        "source_words",
        "value",
        "filter",
        "attr",
        "slot",
        "params",
        "choice_flags",
        "choice_count",
        "is_negated",
        "is_cost",
        "is_optional",
    ):
        if key in frame:
            normalized[key] = frame[key]

    return normalized


def _signature_hash(trigger_id: int, frames: list[dict]) -> dict[str, str]:
    """Generate a signature hash for an ability."""
    def _canonicalize_signature_frame(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: _canonicalize_signature_frame(nested)
                for key, nested in sorted(value.items())
                if key not in {"frame_index", "source_words", "semantic", "readable", "decoded"}
            }
        if isinstance(value, list):
            return [_canonicalize_signature_frame(item) for item in value]
        return value

    sig_payload = {
        "trigger": trigger_id,
        "frames": [_canonicalize_signature_frame(frame) for frame in frames],
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


def _normalize_card_no(card_no: str) -> str:
    return str(card_no or "").strip().replace("＋", "+").upper()


def _split_ability_sections(raw_text: str) -> list[str]:
    if not raw_text:
        return []

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return []

    sections: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if line.startswith("{{") and current:
            sections.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append(current)

    return ["\n".join(section).strip() for section in sections if section]


def _iter_card_db_entries(card_db: dict[str, Any] | None) -> list[tuple[str, str, dict[str, Any]]]:
    if not isinstance(card_db, dict):
        return []

    nested_entries: list[tuple[str, str, dict[str, Any]]] = []
    for db_name in ("member_db", "live_db"):
        db_entries = card_db.get(db_name)
        if not isinstance(db_entries, dict):
            continue
        for card_id, card in db_entries.items():
            if isinstance(card, dict):
                nested_entries.append((db_name, str(card_id), card))
    if nested_entries:
        return nested_entries

    flat_entries: list[tuple[str, str, dict[str, Any]]] = []
    for card_id, card in card_db.items():
        if isinstance(card, dict):
            flat_entries.append((str(card.get("db", "cards")), str(card_id), card))
    return flat_entries


def _build_card_text_lookup(card_db: dict[str, Any] | None) -> dict[tuple[str, int], dict[str, Any]]:
    lookup: dict[tuple[str, int], dict[str, Any]] = {}

    for db_name, card_id, card in _iter_card_db_entries(card_db):
        card_no = _normalize_card_no(card.get("card_no", ""))
        if not card_no:
            continue

        original_text = str(card.get("original_text", "") or "").strip()
        original_text_en = str(card.get("original_text_en", "") or "").strip()
        sections_jp = _split_ability_sections(original_text)
        sections_en = _split_ability_sections(original_text_en)
        abilities = card.get("abilities", []) if isinstance(card.get("abilities"), list) else []
        ability_count = len(abilities)
        section_count = max(ability_count, len(sections_jp), len(sections_en), 1)

        for ability_index in range(section_count):
            jp_text = ""
            en_text = ""
            if ability_index < len(sections_jp):
                jp_text = sections_jp[ability_index]
            elif len(sections_jp) == 1:
                jp_text = sections_jp[0]
            else:
                jp_text = original_text

            if ability_index < len(sections_en):
                en_text = sections_en[ability_index]
            elif len(sections_en) == 1:
                en_text = sections_en[0]
            else:
                en_text = original_text_en

            lookup[(card_no, ability_index)] = {
                "card_no": card.get("card_no", ""),
                "card_id": int(card.get("card_id", card_id) or 0),
                "db": db_name,
                "name": str(card.get("name", "") or ""),
                "jp": jp_text,
                "en": en_text,
            }

    return lookup


def _build_card_ref_lookup(card_db: dict[str, Any] | None) -> dict[tuple[str, int], dict[str, Any]]:
    lookup: dict[tuple[str, int], dict[str, Any]] = {}

    for db_name, card_id, card in _iter_card_db_entries(card_db):
        card_no = _normalize_card_no(card.get("card_no", ""))
        if not card_no:
            continue

        abilities = card.get("abilities", []) if isinstance(card.get("abilities"), list) else []
        section_count = max(len(abilities), 1)
        for ability_index in range(section_count):
            card_ref = {
                "card_no": str(card.get("card_no", "") or card_no),
                "ability_index": ability_index,
                "db": db_name,
                "card_id": int(card.get("card_id", card_id) or 0),
                "name": str(card.get("name", "") or ""),
            }
            if ability_index < len(abilities) and isinstance(abilities[ability_index], dict):
                trigger = abilities[ability_index].get("trigger")
                if trigger is not None:
                    card_ref["trigger"] = trigger
            lookup[(card_no, ability_index)] = card_ref

    return lookup


def _parse_card_label(label: str) -> tuple[str, int | None]:
    text = str(label or "").strip()
    if not text:
        return "", None

    card_no = text.split(" | ", 1)[0].strip()
    ability_index = None
    if "(ab#" in text:
        suffix = text.split("(ab#", 1)[1]
        digits = ""
        for ch in suffix:
            if ch.isdigit():
                digits += ch
            else:
                break
        if digits:
            ability_index = int(digits)
    return _normalize_card_no(card_no), ability_index


def _entry_card_handles(entry: dict[str, Any]) -> list[tuple[str, int, str]]:
    handles: list[tuple[str, int, str]] = []
    seen: set[tuple[str, int]] = set()

    for ref in entry.get("card_refs", []):
        if not isinstance(ref, dict):
            continue
        card_no = _normalize_card_no(ref.get("card_no", ""))
        if not card_no:
            continue
        ability_index = int(ref.get("ability_index", ref.get("ab_idx", ref.get("index", 0))) or 0)
        key = (card_no, ability_index)
        if key in seen:
            continue
        seen.add(key)
        handles.append((card_no, ability_index, _card_ref_label(ref)))

    for label in entry.get("cards", []):
        if not isinstance(label, str):
            continue
        card_no, ability_index = _parse_card_label(label)
        if not card_no:
            continue
        ability_index = 0 if ability_index is None else ability_index
        key = (card_no, ability_index)
        if key in seen:
            continue
        seen.add(key)
        handles.append((card_no, ability_index, label.strip()))

    return handles


def _collect_entry_card_refs(entry: dict[str, Any], card_ref_lookup: dict[tuple[str, int], dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    for ref in entry.get("card_refs", []):
        if not isinstance(ref, dict):
            continue
        card_no = _normalize_card_no(ref.get("card_no", ""))
        if not card_no:
            continue
        ability_index = int(ref.get("ability_index", ref.get("ab_idx", ref.get("index", 0))) or 0)
        key = (card_no, ability_index)
        if key in seen:
            continue
        seen.add(key)
        merged = dict(card_ref_lookup.get(key, {}))
        merged.update(ref)
        merged["ability_index"] = ability_index
        refs.append(merged)

    for label in entry.get("cards", []):
        if not isinstance(label, str):
            continue
        card_no, ability_index = _parse_card_label(label)
        if not card_no:
            continue
        ability_index = 0 if ability_index is None else ability_index
        key = (card_no, ability_index)
        if key in seen:
            continue
        seen.add(key)
        merged = dict(card_ref_lookup.get(key, {}))
        if not merged:
            merged = {
                "card_no": card_no,
                "ability_index": ability_index,
            }
        refs.append(merged)

    return refs


def _collect_entry_texts(entry: dict[str, Any], card_text_lookup: dict[tuple[str, int], dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for card_no, ability_index, label in _entry_card_handles(entry):
        text_info = card_text_lookup.get((card_no, ability_index))
        if not text_info:
            continue
        jp_text = str(text_info.get("jp", "") or "").strip()
        en_text = str(text_info.get("en", "") or "").strip()
        if not jp_text and not en_text:
            continue
        key = (jp_text, en_text)
        bucket = grouped.setdefault(
            key,
            {
                "jp": jp_text,
                "en": en_text,
                "card_examples": [],
            },
        )
        if label and label not in bucket["card_examples"]:
            bucket["card_examples"].append(label)

    return sorted(grouped.values(), key=lambda item: ((item.get("card_examples") or [""])[0], item.get("jp", "")))


def _build_opcode_catalog(entries: list[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    opcode_ids = {str(name).upper(): int(value) for name, value in (metadata.get("opcodes", {}) or {}).items()}
    condition_ids = {str(name).upper(): int(value) for name, value in (metadata.get("conditions", {}) or {}).items()}
    usage: dict[tuple[str, str, int | None], dict[str, Any]] = {}
    unknown: dict[str, dict[str, Any]] = {}

    for entry in entries:
        entry_seen: set[tuple[str, str, int | None]] = set()
        for frame in entry.get("frames", []) or []:
            if not isinstance(frame, dict):
                continue
            name = str(frame.get("op") or frame.get("opcode") or frame.get("opcode_name") or frame.get("kind") or "").strip().upper()
            frame_opcode_id = frame.get("opcode_id")
            frame_opcode_id = int(frame_opcode_id) if isinstance(frame_opcode_id, int) else None

            if name in opcode_ids:
                key = (name, "opcodes", opcode_ids[name])
            elif name in condition_ids:
                key = (name, "conditions", condition_ids[name])
            elif frame_opcode_id is not None:
                key = (name or f"UNKNOWN_{frame_opcode_id}", "unknown", frame_opcode_id)
            else:
                key = (name or "UNKNOWN", "unknown", None)

            if key[1] == "unknown":
                bucket = unknown.setdefault(
                    key[0],
                    {
                        "name": key[0],
                        "opcode_id": key[2],
                        "entry_count": 0,
                        "frame_count": 0,
                    },
                )
                bucket["frame_count"] += 1
                if key not in entry_seen:
                    bucket["entry_count"] += 1
                entry_seen.add(key)
                continue

            bucket = usage.setdefault(
                key,
                {
                    "name": key[0],
                    "section": key[1],
                    "opcode_id": key[2],
                    "entry_count": 0,
                    "frame_count": 0,
                },
            )
            bucket["frame_count"] += 1
            if key not in entry_seen:
                bucket["entry_count"] += 1
            entry_seen.add(key)

    used_entries = sorted(usage.values(), key=lambda item: (item["section"], item["opcode_id"] if item["opcode_id"] is not None else 10**9, item["name"]))
    unknown_entries = sorted(unknown.values(), key=lambda item: (item["opcode_id"] if item["opcode_id"] is not None else 10**9, item["name"]))

    return {
        "used_count": len(used_entries),
        "unknown_count": len(unknown_entries),
        "used_entries": used_entries,
        "unknown_entries": unknown_entries,
    }


def _invert_metadata_map(mapping: dict[str, Any] | None) -> dict[int, str]:
    inverted: dict[int, str] = {}
    if not isinstance(mapping, dict):
        return inverted
    for name, value in mapping.items():
        try:
            inverted[int(value)] = str(name)
        except (TypeError, ValueError):
            continue
    return inverted


def _metadata_name_for_id(metadata: dict[str, Any], section: str, value: Any) -> str | None:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None
    return _invert_metadata_map(metadata.get(section, {})).get(numeric)


def _metadata_label_for_group(metadata: dict[str, Any], group_id: Any) -> str | None:
    name = _metadata_name_for_id(metadata, "group_ids", group_id)
    if name is None:
        return None
    group_names = metadata.get("group_names", {}) if isinstance(metadata, dict) else {}
    label = group_names.get(str(int(group_id)), {}) if isinstance(group_names, dict) else {}
    if isinstance(label, dict):
        return str(label.get("en") or label.get("jp") or name)
    return name


def _decode_color_mask(mask: Any, metadata: dict[str, Any]) -> list[str]:
    try:
        numeric_mask = int(mask)
    except (TypeError, ValueError):
        return []

    color_bits = _invert_metadata_map(metadata.get("heart_color_map", {}))
    colors: list[str] = []
    for bit, name in sorted(color_bits.items()):
        if numeric_mask & (1 << bit):
            colors.append(name)
    return colors


def _decode_zone_mask(mask: Any, metadata: dict[str, Any]) -> str | int | None:
    try:
        numeric_mask = int(mask)
    except (TypeError, ValueError):
        return None

    extra = metadata.get("extra_constants", {}) if isinstance(metadata, dict) else {}
    zone_masks = {
        int(value): name.replace("ZONE_MASK_", "")
        for name, value in (extra.items() if isinstance(extra, dict) else [])
        if str(name).startswith("ZONE_MASK_")
    }
    return zone_masks.get(numeric_mask, numeric_mask)


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
    card_text_lookup = _build_card_text_lookup(card_db)
    card_ref_lookup = _build_card_ref_lookup(card_db)

    source_entries = iter_authored_entries(payload)

    for entry in source_entries:
        trigger_id = int(entry.get("trigger_id", 0))
        raw_frames = entry.get("frames", []) or []

        # Normalize frames
        normalized_frames = [_normalize_frame(f, i) for i, f in enumerate(raw_frames)]

        # Get signature
        sig = _signature_hash(trigger_id, normalized_frames)

        # Get card references
        card_refs = _collect_entry_card_refs(entry, card_ref_lookup)
        cards = []
        for ref in entry.get("cards", []):
            if isinstance(ref, str) and ref.strip():
                cards.append(ref.strip())

        cards.extend(_card_ref_label(ref) for ref in card_refs if _card_ref_label(ref))
        cards = list(dict.fromkeys(cards))

        normalized = {
            "signature": sig["signature"],
            "signature_hash": sig["signature_hash"],
            "signature_source": sig["signature_source"],
            "trigger_id": trigger_id,
            "trigger": _trigger_name_from_id(trigger_id, metadata),
            "frame_count": len(normalized_frames),
            "opcode_sequence": [frame["op"] for frame in normalized_frames],
            "frames": normalized_frames,
            "cards": cards,
            "card_refs": card_refs,
            "pseudocode": "",  # Simplified - no complex pseudocode generation
        }

        source_ability_texts = _collect_entry_texts(entry, card_text_lookup)
        normalized["primary_text_jp"] = source_ability_texts[0]["jp"] if source_ability_texts else ""
        normalized["primary_text_en"] = source_ability_texts[0]["en"] if source_ability_texts else ""
        normalized["source_ability_texts"] = source_ability_texts

        # Copy authored-only metadata before sorting so it stays aligned.
        if "choice_flags" in entry:
            normalized["choice_flags"] = int(entry.get("choice_flags", 0) or 0)
        if "choice_count" in entry:
            normalized["choice_count"] = int(entry.get("choice_count", 0) or 0)
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
    text_covered_count = sum(1 for entry in entries if entry.get("primary_text_jp") or entry.get("primary_text_en"))

    return {
        "generated_at": _utc_now(),
        "source": str(payload.get("source", "data/ability_frame_source.json")),
        "metadata_source": str(payload.get("metadata_source", "data/metadata.json")),
        "schema": "ability_frames.flat.v2",
        "_comment": "Generated ability index. Edit data/ability_frame_source.json directly.",
        "summary": {
            "card_count": len(unique_cards),
            "ability_count": total_card_refs,
            "unique_ability_count": len(entries),
            "signature_group_count": len({e["signature_hash"] for e in entries}),
            "text_covered_ability_count": text_covered_count,
            "text_missing_ability_count": len(entries) - text_covered_count,
        },
        "opcode_catalog": _build_opcode_catalog(entries, metadata),
        "abilities": entries,
    }

