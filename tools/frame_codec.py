"""Simple YAML/JSON utilities for the compiler.

This module provides basic file I/O and ability frame normalization.
Previously 455 lines of complex codec logic - now simplified to essentials.
"""

from __future__ import annotations

from collections import defaultdict
import json
import re
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


def _decode_slot_display(slot: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(slot, dict):
        return {}

    slot_names = _invert_metadata_map(metadata.get("slot_indices", {}))
    zone_names = _invert_metadata_map(metadata.get("zones", {}))
    multiplier_sources = _invert_metadata_map(metadata.get("multiplier_count_sources", {}))
    display: dict[str, Any] = {}

    target_slot = slot.get("target_slot")
    if target_slot is not None:
        try:
            numeric_target = int(target_slot)
        except (TypeError, ValueError):
            display["target_slot"] = target_slot
        else:
            slot_name = slot_names.get(numeric_target)
            if slot_name is not None:
                display["target_slot"] = slot_name
            elif numeric_target >= 16:
                compare_names = _invert_metadata_map(metadata.get("comparisons", {}))
                compare_id = numeric_target >> 4
                compare_name = compare_names.get(compare_id)
                raw_slot = numeric_target & 0x0F
                raw_slot_name = slot_names.get(raw_slot, raw_slot)
                if compare_name is not None:
                    display["target_slot"] = raw_slot_name
                    display["comparison"] = compare_name
                else:
                    display["target_slot"] = numeric_target
            else:
                display["target_slot"] = numeric_target

    for key in ("source_zone", "dest_zone", "remainder_zone"):
        value = slot.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            display[key] = value
            continue
        try:
            numeric_value = int(value)
        except (TypeError, ValueError):
            display[key] = value
            continue
        if key == "remainder_zone" and slot.get("is_dynamic"):
            display["multiplier_source"] = multiplier_sources.get(numeric_value, numeric_value)
            continue
        display[key] = zone_names.get(numeric_value, numeric_value)

    if slot.get("is_dynamic"):
        display["is_dynamic"] = True
    if slot.get("is_opponent"):
        display["is_opponent"] = True
    if slot.get("is_reveal_until_live"):
        display["is_reveal_until_live"] = True
    if slot.get("is_empty_slot"):
        display["is_empty_slot"] = True
    if slot.get("is_wait"):
        display["is_wait"] = True
    if slot.get("is_baton_slot"):
        display["is_baton_slot"] = True

    area_idx = slot.get("area_idx")
    if area_idx is not None:
        area_map = {1: "LEFT", 2: "CENTER", 3: "RIGHT"}
        try:
            display["area_idx"] = area_map.get(int(area_idx), int(area_idx))
        except (TypeError, ValueError):
            display["area_idx"] = area_idx

    return display


def _decode_attr_display(attr: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(attr, dict):
        return {}

    display: dict[str, Any] = {}
    target_player = attr.get("target_player")
    if target_player is not None:
        name = _metadata_name_for_id(metadata, "target_players", target_player)
        display["target_player"] = name or target_player

    card_type = attr.get("card_type")
    if card_type is not None:
        name = _metadata_name_for_id(metadata, "card_types", card_type)
        display["card_type"] = name or card_type

    if attr.get("group_enabled") and attr.get("group_id") is not None:
        group_id = attr.get("group_id")
        group_label = _metadata_label_for_group(metadata, group_id)
        display["group"] = group_label or group_id

    if attr.get("unit_enabled") and attr.get("unit_id") is not None:
        unit_id = attr.get("unit_id")
        display["unit"] = _metadata_name_for_id(metadata, "unit_ids", unit_id) or unit_id

    for key in ("char_id_1", "char_id_2"):
        value = attr.get(key)
        if value:
            display[key] = _metadata_name_for_id(metadata, "character_ids", value) or value

    color_mask = attr.get("color_mask")
    if color_mask is not None:
        colors = _decode_color_mask(color_mask, metadata)
        display["color_mask"] = colors if colors else color_mask

    zone_mask = attr.get("zone_mask")
    if zone_mask is not None:
        decoded_zone_mask = _decode_zone_mask(zone_mask, metadata)
        display["zone_mask"] = decoded_zone_mask if decoded_zone_mask is not None else zone_mask

    if attr.get("value_enabled"):
        comparison = "<=" if attr.get("is_le") else ">="
        threshold = attr.get("value_threshold", 0)
        value_kind = "cost" if attr.get("is_cost_type") else "value"
        display["threshold"] = f"{value_kind} {comparison} {threshold}"

    for key in (
        "compare_accumulated",
        "is_optional",
        "is_tapped",
        "has_blade_heart",
        "not_has_blade_heart",
        "unique_names",
        "keyword_energy",
        "keyword_member",
        "is_setsuna",
    ):
        if attr.get(key):
            display[key] = True

    return display


def _decode_value_display(frame: dict[str, Any], metadata: dict[str, Any], slot_display: dict[str, Any]) -> dict[str, Any]:
    value = frame.get("value")
    opcode = str(frame.get("op") or frame.get("opcode") or frame.get("opcode_name") or "").upper()
    if isinstance(value, dict):
        return dict(value)
    if value is None:
        return {}

    display: dict[str, Any] = {"raw": value}
    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        return display

    params = frame.get("params")
    scalar_dynamic = params.get("scalar_dynamic") if isinstance(params, dict) else None
    scalar_dynamic = scalar_dynamic if isinstance(scalar_dynamic, dict) else params if isinstance(params, dict) else None

    def _read_int(payload: dict[str, Any] | None, key: str) -> int | None:
        if not isinstance(payload, dict):
            return None
        raw = payload.get(key, payload.get(key.upper()))
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    explicit_base = _read_int(scalar_dynamic, "base_value")
    if explicit_base is None:
        explicit_base = _read_int(scalar_dynamic, "base")
    explicit_divisor = _read_int(scalar_dynamic, "divisor")

    overrides = metadata.get("packed_layout", {}).get("overrides", {}) if isinstance(metadata, dict) else {}
    override = overrides.get(opcode, {}) if isinstance(overrides, dict) else {}
    if explicit_base is not None or explicit_divisor is not None or (isinstance(override, dict) and override.get("V") == "scalar_dynamic"):
        base_value = explicit_base if explicit_base is not None else numeric_value & 0xFFFF
        divisor = explicit_divisor if explicit_divisor is not None else (numeric_value >> 16) & 0xFFFF
        display["kind"] = "scalar_dynamic"
        display["base_value"] = base_value
        display["divisor"] = divisor
        multiplier_source = slot_display.get("multiplier_source")
        resolved = str(base_value)
        if multiplier_source:
            resolved = resolved + " x " + str(multiplier_source)
        if divisor not in (0, 1):
            resolved = resolved + " / " + str(divisor)
        display["resolved"] = resolved
    return display


def _build_readable_frame(frame: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(frame, dict):
        return {}

    slot_display = _decode_slot_display(frame.get("slot", {}), metadata)
    attr_display = _decode_attr_display(frame.get("attr", {}), metadata)
    value_display = _decode_value_display(frame, metadata, slot_display)
    readable: dict[str, Any] = {}
    if value_display:
        readable["value"] = value_display
    if attr_display:
        readable["attr"] = attr_display
    if slot_display:
        readable["slot"] = slot_display
    return readable


def _rewrite_decoded_text(decoded: str, readable: dict[str, Any]) -> str:
    if not decoded or not isinstance(decoded, str):
        return decoded

    value_display = readable.get("value", {}) if isinstance(readable, dict) else {}
    if not isinstance(value_display, dict):
        return decoded
    raw_value = value_display.get("raw")
    resolved = value_display.get("resolved")
    if raw_value is None or not resolved or raw_value == resolved:
        return decoded

    pattern = re.compile(r"\b(count|value)=" + re.escape(str(raw_value)) + r"\b")
    return pattern.sub(lambda match: match.group(1) + "=" + str(resolved), decoded)


def _enrich_runtime_frame(frame: Any, metadata: dict[str, Any]) -> Any:
    if not isinstance(frame, dict):
        return frame

    enriched = dict(frame)
    readable = _build_readable_frame(frame, metadata)
    if readable:
        enriched["readable"] = readable

    semantic = frame.get("semantic")
    if isinstance(semantic, dict):
        semantic_copy = dict(semantic)
        semantic_copy.pop("metadata_refs", None)
        if readable:
            semantic_copy["display"] = readable
            if isinstance(semantic_copy.get("decoded"), str):
                semantic_copy["decoded"] = _rewrite_decoded_text(semantic_copy["decoded"], readable)
        enriched["semantic"] = semantic_copy

    return enriched


def strip_duplicate_instruction_entries(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove legacy `instructions` keys when a canonical `frames` list is present."""
    cleaned = dict(payload)
    abilities = payload.get("abilities")
    if isinstance(abilities, list):
        cleaned_abilities: list[Any] = []
        changed = False
        for item in abilities:
            if not isinstance(item, dict):
                cleaned_abilities.append(item)
                continue
            cleaned_item = dict(item)
            frames = cleaned_item.get("frames")
            if isinstance(frames, list) and "instructions" in cleaned_item:
                cleaned_item.pop("instructions", None)
                changed = True
            if isinstance(frames, list):
                sig = _signature_hash(
                    int(cleaned_item.get("trigger_id", 0) or 0),
                    [_normalize_frame(frame, idx) for idx, frame in enumerate(frames)],
                )
                for key in ("signature", "signature_hash", "signature_source"):
                    if cleaned_item.get(key) != sig[key]:
                        cleaned_item[key] = sig[key]
                        changed = True
            cleaned_abilities.append(cleaned_item)
        if changed:
            cleaned["abilities"] = cleaned_abilities
        return cleaned

    changed = False
    for key, value in payload.items():
        if not isinstance(value, dict):
            continue
        if isinstance(value.get("frames"), list) and "instructions" in value:
            entry = dict(value)
            entry.pop("instructions", None)
            cleaned[key] = entry
            changed = True
    return cleaned if changed else payload


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
            "frames": raw_frames,
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


def build_runtime_ability_index(payload: dict[str, Any], metadata: dict[str, Any], card_db: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate the shared ability index while preserving authored frame objects."""
    normalized = normalize_authored_ability_index(payload, metadata, card_db)
    normalized["schema"] = "ability_runtime_index.flat.v2"
    normalized["_comment"] = "Generated runtime ability index. Edit data/ability_frame_source.json directly."
    for entry in normalized.get("abilities", []):
        frames = entry.get("frames")
        if isinstance(frames, list):
            entry["frames"] = [_enrich_runtime_frame(frame, metadata) for frame in frames]
    return normalized


def _build_review_frame(frame: Any) -> Any:
    if not isinstance(frame, dict):
        return frame

    review: dict[str, Any] = {}
    for key in ("opcode_id", "opcode", "op", "ability_frame_index", "semantic", "readable"):
        if key in frame:
            review[key] = frame[key]

    if "opcode" not in review and isinstance(review.get("op"), str):
        review["opcode"] = review.pop("op")
    else:
        review.pop("op", None)

    if "semantic" not in review and "readable" in review:
        review["semantic"] = {"display": review["readable"]}

    return review if review else frame


def build_review_ability_index(payload: dict[str, Any], metadata: dict[str, Any], card_db: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a human-facing review index from the generated runtime payload."""
    review_payload = normalize_authored_ability_index(payload, metadata, card_db)
    review_payload["schema"] = "ability_frame_index.flat.v2"
    review_payload["_comment"] = "Generated review index. Edit data/ability_frame_source.json directly."

    review_entries: list[Any] = []
    for entry in review_payload.get("abilities", []):
        if not isinstance(entry, dict):
            review_entries.append(entry)
            continue
        review_entry = dict(entry)
        frames = entry.get("frames")
        if isinstance(frames, list):
            review_entry["frames"] = [_build_review_frame(_enrich_runtime_frame(frame, metadata)) for frame in frames]
        review_entries.append(review_entry)

    review_payload["abilities"] = review_entries
    return review_payload


def build_compact_ability_index(payload: dict[str, Any], metadata: dict[str, Any], card_db: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the compact authored frame index used by compatibility tests."""
    compact = normalize_authored_ability_index(payload, metadata, card_db)
    compact["schema"] = "ability_frame_source.flat.v2"
    compact["_comment"] = "Authored sparse ability source. Edit this file directly."
    entries = compact.get("abilities", [])

    for entry in entries:
        entry["source_mode"] = "frame_authored"
        entry["frames"] = [_normalize_frame(frame, frame_idx) for frame_idx, frame in enumerate(entry.get("frames", []))]

    return compact

