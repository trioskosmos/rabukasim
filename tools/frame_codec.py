from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = os.path.abspath(str(ROOT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from tools import bytecode_codec as codec


def load_json(path: Path | str) -> dict[str, Any]:
    return codec.load_json(path)


def dump_json(path: Path | str, payload: dict[str, Any]) -> None:
    target = Path(path)
    if target.name == "ability_frames.json":
        raise ValueError("writing to data/ability_frames.json is disabled; use a generated index path instead")
    codec.dump_json(path, payload)


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
    return codec._name_for_id(trigger_id, lookups.triggers_by_id, "TRIGGER")


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"raw", "source_words", "signature", "signature_hash", "signature_source"}:
                continue
            normalized_item = _normalize_scalar(item)
            if normalized_item not in (None, False, 0, "", [], {}):
                normalized[key] = normalized_item
        return normalized
    if isinstance(value, list):
        normalized_list = [_normalize_scalar(item) for item in value]
        return [item for item in normalized_list if item not in (None, False, 0, "", [], {})]
    return value


def _resolve_opcode_name(frame: dict[str, Any], lookups: Any) -> str:
    opcode_name = frame.get("op") or frame.get("opcode") or frame.get("opcode_name") or frame.get("kind")
    if isinstance(opcode_name, str) and opcode_name:
        return opcode_name.upper()

    opcode_id = frame.get("opcode_id")
    if isinstance(opcode_id, int):
        return codec._name_for_id(opcode_id, lookups.opcodes_by_id, "OP")

    return "RETURN" if frame == {"Return": {}} else "OP_0"


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
        base: dict[str, Any] = {
            "op": "RETURN",
            "opcode_id": int(lookups.ids_by_opcode.get("RETURN", 1)),
            "rust_opcode": "O_RETURN",
        }
        if frame_index is not None:
            base["frame_index"] = frame_index
        return base

    if isinstance(frame, dict) and len(frame) == 1 and not ({"op", "opcode", "opcode_id", "opcode_name", "kind"} & set(frame.keys())):
        key, payload = next(iter(frame.items()))
        if key == "Return":
            return _normalize_authored_frame("Return", lookups, frame_index)
        if isinstance(payload, dict):
            frame = {"kind": key, **payload}
        else:
            frame = {"kind": key, "value": payload}

    if isinstance(frame, dict) and isinstance(frame.get("semantic"), dict):
        frame = codec.frame_to_compact(frame)

    if not isinstance(frame, dict):
        raise ValueError(f"unsupported frame payload: {frame!r}")

    opcode_name = _resolve_opcode_name(frame, lookups)
    opcode_id = _resolve_opcode_id(frame, opcode_name, lookups)
    normalized: dict[str, Any] = {
        "op": opcode_name,
        "opcode_id": opcode_id,
        "rust_opcode": str(frame.get("rust_opcode") or frame.get("rust_opcode_name") or f"O_{opcode_name}"),
    }

    for field in ("value", "attr", "slot", "params"):
        if field in frame:
            normalized_value = _normalize_scalar(frame.get(field))
            if normalized_value not in (None, False, 0, "", [], {}):
                normalized[field] = normalized_value

    negated = frame.get("negated", frame.get("is_negated", False))
    if bool(negated):
        normalized["negated"] = True

    explicit_index = frame.get("frame_index", frame.get("ability_frame_index", frame_index))
    if isinstance(explicit_index, int) and explicit_index >= 0:
        normalized["frame_index"] = explicit_index

    if isinstance(frame.get("source_words"), list) and frame["source_words"]:
        normalized["source_words"] = [int(word) for word in frame["source_words"]]

    return normalized


def _signature_payload(trigger_id: int, frames: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    signature_frames: list[dict[str, Any]] = []
    for frame in frames:
        signature_frame: dict[str, Any] = {"op": frame["op"]}
        for field in ("value", "attr", "slot", "negated", "params"):
            if field in frame:
                signature_frame[field] = frame[field]
        signature_frames.append(signature_frame)
    payload = {"trigger": trigger_id, "frames": signature_frames}
    if metadata:
        metadata_fields = ("is_once_per_turn", "requires_selection", "choice_flags", "choice_count")
        for field in metadata_fields:
            if field in metadata:
                payload[field] = metadata[field]
    return payload


def frame_signature(trigger_id: int, frames: list[dict[str, Any]], lookups: Any, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = _signature_payload(trigger_id, frames, metadata)
    signature_source = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    signature_hash = sha1(signature_source.encode("utf-8")).hexdigest()
    return {
        "signature": f"{_trigger_name(trigger_id, lookups)}|{signature_hash}",
        "signature_hash": signature_hash,
        "signature_source": signature_source,
    }


def _normalize_cards(entry: dict[str, Any]) -> tuple[list[Any], list[dict[str, Any]]]:
    cards = list(entry.get("cards", [])) if isinstance(entry.get("cards"), list) else []
    card_refs = list(entry.get("card_refs", [])) if isinstance(entry.get("card_refs"), list) else []
    return cards, card_refs


def _normalize_entry(entry: dict[str, Any], lookups: Any) -> dict[str, Any]:
    trigger_id = _resolve_trigger_id(entry.get("trigger_id", entry.get("trigger")), lookups)
    trigger = _trigger_name(trigger_id, lookups)
    raw_frames = entry.get("frames", []) if isinstance(entry.get("frames"), list) else []
    frames = [_normalize_authored_frame(frame, lookups, idx) for idx, frame in enumerate(raw_frames)]
    signature = frame_signature(trigger_id, frames, lookups, metadata=entry)
    cards, card_refs = _normalize_cards(entry)

    opcode_sequence = [frame["op"] for frame in frames]
    rust_opcode_sequence = [frame["rust_opcode"] for frame in frames]
    opcode_names = list(dict.fromkeys(opcode_sequence))

    normalized = {
        "signature": signature["signature"],
        "signature_hash": signature["signature_hash"],
        "signature_source": signature["signature_source"],
        "trigger_id": trigger_id,
        "trigger": trigger,
        "frame_count": len(frames),
        "opcode_sequence": opcode_sequence,
        "opcode_names": opcode_names,
        "rust_opcode_sequence": rust_opcode_sequence,
        "frames": frames,
        "cards": cards,
        "card_refs": card_refs,
        "pseudocode": str(entry.get("pseudocode", "")),
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
    if "bytecode_words" in entry and isinstance(entry.get("bytecode_words"), int):
        normalized["bytecode_words"] = int(entry["bytecode_words"])

    return normalized


def normalize_authored_ability_index(payload: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    lookups = codec.load_lookups(metadata)
    entries = [_normalize_entry(entry, lookups) for entry in payload.get("abilities", [])]
    entries.sort(key=lambda entry: (entry["trigger"], -len(entry["cards"]), entry["signature_hash"]))
    return {
        "generated_at": _utc_now(),
        "source": str(payload.get("source", ROOT_DIR / "data" / "ability_frames.json")),
        "metadata_source": str(payload.get("metadata_source", ROOT_DIR / "data" / "metadata.json")),
        "schema": "ability_frames.flat.v2",
        "summary": {
            "card_count": int(payload.get("summary", {}).get("card_count", 0)),
            "ability_count": int(payload.get("summary", {}).get("ability_count", 0)),
            "unique_ability_count": len(entries),
        },
        "abilities": entries,
    }


def build_compact_ability_index(compiled_data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(compiled_data.get("abilities"), list):
        raise ValueError("ability frame compaction now requires authored frame data")

    return normalize_authored_ability_index(compiled_data, metadata)


def build_runtime_ability_index(payload: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_authored_ability_index(payload, metadata)
    normalized["schema"] = "ability_frame_index.flat.v2"
    return normalized
