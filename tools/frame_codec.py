"""Normalize authored ability instructions into a compact debug-friendly index."""

from __future__ import annotations

import json
import yaml
import os
import re
import sys
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Any, Dict, List, Union, Tuple
from copy import deepcopy
from engine.models.generated_packer import unpack_v_scalar_dynamic

# ROOT_DIR for relative lookups
ROOT_DIR = Path(__file__).resolve().parents[1]
class MetadataLookups:
    def __init__(self, metadata: dict):
        self.metadata = metadata
        self.ids_by_trigger = {str(k).upper(): v for k, v in metadata.get("triggers", {}).items()}
        self.triggers_by_id = {int(v): k for k, v in metadata.get("triggers", {}).items()}
        self.ids_by_opcode = {str(k).upper(): v for k, v in metadata.get("opcodes", {}).items()}
        self.opcodes_by_id = {int(v): k for k, v in metadata.get("opcodes", {}).items()}
        self.ids_by_zone = {str(k).upper(): v for k, v in metadata.get("zones", {}).items()}
        self.ids_by_slot = {str(k).upper(): v for k, v in metadata.get("slots", {}).items()}
        self.ids_by_special = {str(k).upper(): v for k, v in metadata.get("specials", {}).items()}
        self.ids_by_zone_mask = {str(k).upper(): v for k, v in metadata.get("zone_masks", {}).items()}
def load_yaml(path: Path | str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path | str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def dump_json(path: Path | str, payload: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_trigger_id(trigger: Any, lookups: Any) -> int:
    if isinstance(trigger, bool):
        return int(trigger)
    if isinstance(trigger, int):
        return trigger
    if isinstance(trigger, str):
        text = trigger.strip()
        if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
            return int(text)
        return int(lookups.ids_by_trigger.get(text, lookups.ids_by_trigger.get(text.upper(), 0)))
    return 0


def _trigger_name(trigger_id: int, lookups: Any) -> str:
    return lookups.triggers_by_id.get(trigger_id, f"TRIGGER_{trigger_id}")


def _card_ref_label(card_ref: dict[str, Any]) -> str:
    card_no = str(card_ref.get("card_no", "")).strip()
    name = str(card_ref.get("name", "")).strip()
    db = str(card_ref.get("db", "")).strip()
    card_id = card_ref.get("card_id")
    ability_index = card_ref.get("ability_index", card_ref.get("ab_idx", card_ref.get("index", 0)))
    trigger = str(card_ref.get("trigger", "")).strip()

    if not card_no:
        return ""

    label = card_no
    if name:
        label = f"{label} | {name}"
    if db and card_id is not None:
        label = f"{label} [{db}:{card_id}]"
    if ability_index is not None:
        label = f"{label} (ab#{ability_index}"
        if trigger:
            label = f"{label} {trigger})"
        else:
            label = f"{label})"
    elif trigger:
        label = f"{label} ({trigger})"
    return label


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"raw", "source_words", "signature", "signature_hash", "signature_source"}:
                continue
            normalized_item = _normalize_scalar(item)
            if normalized_item not in (None, "", [], {}):
                normalized[key] = normalized_item
        return normalized
    if isinstance(value, list):
        normalized_list = [_normalize_scalar(item) for item in value]
        return [item for item in normalized_list if item not in (None, "", [], {})]
    return value


def frame_to_compact(frame: dict[str, Any]) -> dict[str, Any]:
    """Convert a verbose frame (potentially with bytecode/semantic) to a compact authored-style frame."""
    compact: dict[str, Any] = {}

    # Try to extract from semantic first (preferred)
    semantic = frame.get("semantic", {})
    if isinstance(semantic, dict) and semantic:
        compact["op"] = semantic.get("opcode_name") or frame.get("op")
        options: dict[str, Any] = {}
        for key in (
            "value",
            "count",
            "choose_count",
            "reveal",
            "dest_discard",
            "char_id_1",
            "char_id_2",
            "char_id_3",
            "attr",
            "filter",
            "slot",
            "params",
            "target",
            "comparison",
            "rule_type",
            "is_cost",
            "optional",
            "is_negated",
            "negated",
            "decoded",
        ):
            if key in semantic and semantic[key] not in (None, "", [], {}):
                mapped_key = "filter" if key == "attr" else ("negated" if key == "is_negated" else key)
                options[mapped_key] = semantic[key]
        if isinstance(frame.get("decoded"), str) and frame["decoded"]:
            compact["decoded"] = frame["decoded"]
        if options:
            compact["options"] = options
        return _normalize_scalar(compact)

    # Fallback to direct fields
    compact["op"] = frame.get("op") or frame.get("opcode_name")
    options: dict[str, Any] = {}
    for field in [
        "value",
        "count",
        "choose_count",
        "reveal",
        "dest_discard",
        "char_id_1",
        "char_id_2",
        "char_id_3",
        "attr",
        "slot",
        "params",
        "filter",
        "target",
        "comparison",
        "rule_type",
        "is_cost",
        "optional",
        "is_negated",
        "negated",
        "decoded",
    ]:
        if field in frame:
            key = "filter" if field == "attr" else ("negated" if field == "is_negated" else field)
            options[key] = frame[field]
    if frame.get("negated", frame.get("is_negated", False)):
        options["negated"] = True
    if options:
        compact["options"] = options
    if isinstance(frame.get("decoded"), str) and frame["decoded"]:
        compact["decoded"] = frame["decoded"]

    return _normalize_scalar(compact)
def _resolve_opcode_name(frame: dict[str, Any], lookups: Any) -> str:
    if isinstance(frame.get("op"), str) and frame.get("op"):
        return str(frame["op"]).upper()

    if frame == {"Return": {}}:
        return "RETURN"

    opcode_name = frame.get("op") or frame.get("opcode") or frame.get("opcode_name") or frame.get("kind")
    if isinstance(opcode_name, str) and opcode_name:
        return opcode_name.upper()

    opcode_id = frame.get("opcode_id")
    if isinstance(opcode_id, int):
        return lookups.opcodes_by_id.get(opcode_id, f"OP_{opcode_id}")

    return "OP_0"


def _resolve_opcode_id(frame: dict[str, Any], opcode_name: str, lookups: Any) -> int:
    opcode_id = frame.get("opcode_id")
    if isinstance(opcode_id, int):
        return opcode_id

    raw_opcode = frame.get("opcode")
    if isinstance(raw_opcode, int):
        return raw_opcode

    return int(lookups.ids_by_opcode.get(opcode_name, 0))


def _normalize_authored_frame(frame: Any, lookups: Any, frame_index: int | None = None) -> dict[str, Any]:
    if frame == "Return":
        base: dict[str, Any] = {"op": "RETURN", "rust_opcode": "O_RETURN"}
        if frame_index is not None:
            base["frame_index"] = frame_index
        return base

    if isinstance(frame, dict) and len(frame) == 1 and not ({"op", "opcode", "opcode_id", "opcode_name", "kind"} & set(frame.keys())):
        key, payload = next(iter(frame.items()))
        if key == "Return":
            return _normalize_authored_frame("Return", lookups, frame_index)
        if isinstance(payload, dict):
            frame = {"op": key, **payload}
        else:
            frame = {"op": key, "value": payload}

    if isinstance(frame, dict) and isinstance(frame.get("semantic"), dict):
        frame = frame_to_compact(frame)

    if not isinstance(frame, dict):
        raise ValueError(f"unsupported frame payload: {frame!r}")

    opcode_name = _resolve_opcode_name(frame, lookups)
    normalized: dict[str, Any] = {
        "op": opcode_name,
    }

    if isinstance(frame.get("options"), dict):
        options = _normalize_scalar(frame["options"])
        if isinstance(options, dict) and options:
            normalized["options"] = options
            for alias in ("value", "count", "filter", "slot", "params", "target", "comparison"):
                if alias in options:
                    normalized[alias] = _normalize_scalar(options[alias])
            for alias in ("choose_count", "reveal", "dest_discard", "char_id_1", "char_id_2", "char_id_3", "rule_type", "is_cost"):
                if alias in options:
                    normalized[alias] = _normalize_scalar(options[alias])
            if options.get("negated"):
                normalized["negated"] = True
    else:
        options = {}
        for field in ("value", "attr", "slot", "params", "filter", "count", "target", "comparison"):
            if field in frame:
                normalized_value = _normalize_scalar(frame.get(field))
                if normalized_value not in (None, "", [], {}):
                    options["filter" if field == "attr" else field] = normalized_value
        if frame.get("negated", frame.get("is_negated", False)):
            options["negated"] = True
        if options:
            normalized["options"] = options
            for alias in ("value", "count", "filter", "slot", "params", "target", "comparison"):
                if alias in options:
                    normalized[alias] = options[alias]
            for alias in ("choose_count", "reveal", "dest_discard", "char_id_1", "char_id_2", "char_id_3", "rule_type", "is_cost"):
                if alias in options:
                    normalized[alias] = options[alias]
            if options.get("negated"):
                normalized["negated"] = True

    options = normalized.get("options")
    slot = options.get("slot") if isinstance(options, dict) else None
    if isinstance(slot, dict) and slot.get("is_dynamic") and isinstance(options, dict) and isinstance(options.get("value"), int):
        options["value"] = int(unpack_v_scalar_dynamic(int(options["value"]))["base_value"])
        normalized["value"] = options["value"]

    if isinstance(frame.get("rust_opcode"), str) and frame["rust_opcode"]:
        normalized["rust_opcode"] = frame["rust_opcode"]
    elif opcode_name != "RETURN":
        normalized["rust_opcode"] = f"O_{opcode_name}"

    explicit_index = frame.get("frame_index", frame.get("ability_frame_index", frame_index))
    if isinstance(explicit_index, int) and explicit_index >= 0:
        normalized["frame_index"] = explicit_index

    if isinstance(frame.get("source_words"), list) and frame["source_words"]:
        normalized["source_words"] = [int(word) for word in frame["source_words"]]

    return normalized


def _signature_payload(trigger_id: int, instructions: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    signature_instructions: list[dict[str, Any]] = []
    for frame in instructions:
        signature_frame: dict[str, Any] = {"op": frame["op"]}
        if isinstance(frame.get("options"), dict) and frame["options"]:
            signature_frame["options"] = frame["options"]
        signature_instructions.append(signature_frame)
    payload = {"trigger": trigger_id, "instructions": signature_instructions}
    if metadata:
        metadata_fields = ("is_once_per_turn", "requires_selection", "choice_flags", "choice_count")
        for field in metadata_fields:
            if field in metadata:
                payload[field] = metadata[field]
    return payload


def frame_signature(trigger_id: int, instructions: list[dict[str, Any]], lookups: Any, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = _signature_payload(trigger_id, instructions, metadata)
    signature_source = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    signature_hash = sha1(signature_source.encode("utf-8")).hexdigest()
    return {
        "signature": f"{_trigger_name(trigger_id, lookups)}|{signature_hash}",
        "signature_hash": signature_hash,
        "signature_source": signature_source,
    }


def _normalize_cards(entry: dict[str, Any]) -> tuple[list[Any], list[dict[str, Any]]]:
    raw_cards = list(entry.get("cards", [])) if isinstance(entry.get("cards"), list) else []
    card_refs = []
    for card_ref in entry.get("card_refs", []) if isinstance(entry.get("card_refs"), list) else []:
        if isinstance(card_ref, dict):
            card_refs.append(dict(card_ref))

    cards = raw_cards
    if not cards and card_refs:
        cards = [_card_ref_label(card_ref) for card_ref in card_refs]
        cards = [card for card in cards if card]
    return cards, card_refs


def _render_pseudocode(instructions: list[dict[str, Any]], lookups: Any) -> str:
    return ""


def _extract_ability_text(card_refs: list[dict[str, Any]], card_db: dict[str, Any] | None) -> str:
    if not card_db or not card_refs:
        return ""
    
    # Try to find the first card reference that has an ability index
    for ref in card_refs:
        db_name = ref.get("db")
        card_id = str(ref.get("card_id"))
        ab_idx = ref.get("ability_index")
        
        if not db_name or not card_id or ab_idx is None:
            continue
            
        db = card_db.get(db_name)
        if not db:
            continue
            
        card_data = db.get(card_id)
        if not card_data:
            continue
            
        original_text = card_data.get("original_text", "")
        if not original_text:
            continue
            
        # Try to split by lines and pick the one for ab_idx
        lines = [line.strip() for line in original_text.split("\n") if line.strip()]
        if 0 <= ab_idx < len(lines):
            return lines[ab_idx]
            
        return original_text
        
    return ""


def _normalize_entry(entry: dict[str, Any], lookups: Any, card_db: dict[str, Any] | None = None) -> dict[str, Any]:
    trigger_id = _resolve_trigger_id(entry.get("trigger_id", entry.get("trigger")), lookups)
    trigger = _trigger_name(trigger_id, lookups)
    raw_instructions = entry.get("instructions", entry.get("frames", [])) if isinstance(entry.get("instructions", entry.get("frames", [])), list) else []
    instructions = [_normalize_authored_frame(frame, lookups, idx) for idx, frame in enumerate(raw_instructions)]
    signature = frame_signature(trigger_id, instructions, lookups, metadata=entry)
    cards, card_refs = _normalize_cards(entry)

    opcode_sequence = [frame["op"] for frame in instructions]
    opcode_names = list(dict.fromkeys(opcode_sequence))
    rust_opcode_sequence = [f"O_{op}" for op in opcode_sequence]

    normalized = {
        "signature": signature["signature"],
        "signature_hash": signature["signature_hash"],
        "signature_source": signature["signature_source"],
        "trigger_id": trigger_id,
        "trigger": trigger,
        "frame_count": len(instructions),
        "opcode_sequence": opcode_sequence,
        "opcode_names": opcode_names,
        "rust_opcode_sequence": rust_opcode_sequence,
        "instructions": instructions,
        "cards": cards,
        "card_refs": card_refs,
        "original_text": entry.get("original_text", _extract_ability_text(card_refs, card_db)),
        "pseudocode": _render_pseudocode(instructions, lookups) or str(entry.get("pseudocode", "")),
        "source_mode": entry.get("source_mode", "frame_authored"),
    }

    if "is_once_per_turn" in entry:
        normalized["is_once_per_turn"] = bool(entry.get("is_once_per_turn"))
    if "requires_selection" in entry:
        normalized["requires_selection"] = bool(entry.get("requires_selection"))
    if "choice_flags" in entry:
        normalized["choice_flags"] = int(entry.get("choice_flags", 0) or 0)
    if "choice_count" in entry:
        normalized["choice_count"] = int(entry.get("choice_count", 0) or 0)

    if "round_trip_matches" in entry:
        normalized["round_trip_matches"] = bool(entry.get("round_trip_matches"))
    return normalized


def normalize_authored_ability_index(payload: dict[str, Any], metadata: dict[str, Any], card_db: dict[str, Any] | None = None) -> dict[str, Any]:
    lookups = MetadataLookups(metadata)
    entries = [_normalize_entry(entry, lookups, card_db) for entry in payload.get("abilities", [])]
    entries.sort(key=lambda entry: (entry["trigger"], -len(entry["cards"]), entry["signature_hash"]))
    return {
        "generated_at": _utc_now(),
        "source": str(payload.get("source", ROOT_DIR / "data" / "ability_frames.json")),
        "metadata_source": str(payload.get("metadata_source", ROOT_DIR / "data" / "metadata.json")),
        "schema": "ability_frames.flat.v2",
        "documentation": {
            "purpose": "Normalized semantic frame source used to build runtime card data.",
            "read_first": "Each ability is instruction-based. Empty bytecode is expected here; inspect instructions and frame_count instead.",
            "related_files": {
                "data/ability_frames.json": "Authored frame input",
                "data/metadata.json": "Opcode, slot, and filter metadata",
                "data/cards_compiled.json": "Compiled runtime card database",
            },
        },
        "summary": {
            "card_count": int(payload.get("summary", {}).get("card_count", 0)),
            "ability_count": int(payload.get("summary", {}).get("ability_count", 0)),
            "unique_ability_count": len(entries),
        },
        "abilities": entries,
    }


def build_compact_ability_index(compiled_data: dict[str, Any], metadata: dict[str, Any], card_db: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(compiled_data.get("abilities"), list):
        raise ValueError("ability frame compaction now requires authored frame data")

    return normalize_authored_ability_index(compiled_data, metadata, card_db)


def build_runtime_ability_index(payload: dict[str, Any], metadata: dict[str, Any], card_db: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = normalize_authored_ability_index(payload, metadata, card_db)
    normalized["schema"] = "ability_frame_index.flat.v2"
    return normalized
