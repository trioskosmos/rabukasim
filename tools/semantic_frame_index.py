from __future__ import annotations

"""Build a sparse semantic ability index from compiled cards.

The output keeps abilities grouped by their ordered sparse semantic frame
sequence, decoded from bytecode words using metadata.json. This is the canonical
runtime input used by the Rust engine to load `Ability.frame_program`.
"""

import hashlib
import json
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = os.path.abspath(str(ROOT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from engine.models.opcodes import Opcode
from tools import bytecode_codec as codec

DEFAULT_INPUT_PATH = ROOT_DIR / "data" / "cards_compiled.json"
DEFAULT_METADATA_PATH = ROOT_DIR / "data" / "metadata.json"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data" / "ability_frame_index.json"


def load_json(path: Path | str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path | str, payload: dict[str, Any]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _opcode_id(name: str) -> int:
    if not name:
        return 0
    if hasattr(Opcode, name):
        return int(getattr(Opcode, name))
    return 0


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize(value[key]) for key in sorted(value.keys())}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _frame_kind(frame: Any) -> str:
    if isinstance(frame, str):
        return frame
    if isinstance(frame, dict):
        kind = frame.get("kind")
        if isinstance(kind, str) and kind:
            return kind
        if len(frame) == 1:
            key = next(iter(frame.keys()))
            if isinstance(key, str):
                return key
    return "Semantic"


def _frame_payload(frame: Any) -> dict[str, Any]:
    if isinstance(frame, dict):
        kind = _frame_kind(frame)
        if kind in frame and isinstance(frame[kind], dict):
            return dict(frame[kind])
        if kind == "Semantic" and isinstance(frame.get("Semantic"), dict):
            return dict(frame["Semantic"])
        return dict(frame)
    return {}


def _frame_kind_from_opcode_name(opcode_name: str) -> str:
    return {
        "RETURN": "Return",
        "DRAW": "Draw",
        "RECOVER_LIVE": "RecoverLive",
        "RECOVER_MEMBER": "RecoverMember",
        "LOOK_AND_CHOOSE": "LookAndChoose",
        "SELECT_MEMBER": "SelectMember",
        "MOVE_MEMBER": "MoveMember",
        "META_RULE": "MetaRule",
    }.get(opcode_name, "Semantic")


def _sparse_frame_from_model_frame(frame: Any) -> dict[str, Any] | None:
    if not isinstance(frame, dict):
        return None

    opcode_name = str(frame.get("opcode_name", "")).strip()
    if not opcode_name:
        opcode_name = str(frame.get("opcode", "")).strip()
    opcode_id = int(frame.get("opcode", frame.get("opcode_id", _opcode_id(opcode_name))))
    semantic = frame.get("semantic", {})
    if not isinstance(semantic, dict):
        semantic = {}
    payload = frame.get("payload", {})
    if not isinstance(payload, dict):
        payload = {}
    kind = _frame_kind_from_opcode_name(opcode_name)
    decoded = semantic.get("decoded", frame.get("decoded", ""))
    metadata_refs = semantic.get("metadata_refs", frame.get("metadata_refs", []))
    is_negated = bool(frame.get("negated", semantic.get("negated", False)))

    if kind == "Return":
        return {
            "kind": "Return",
            "opcode": "RETURN",
            "opcode_id": _opcode_id("RETURN"),
            "value": 0,
            "filter": {},
            "slot": {},
            "is_negated": False,
            "params": None,
            "decoded": decoded,
            "metadata_refs": _normalize(metadata_refs),
        }

    if kind == "Draw":
        value = semantic.get("value", payload.get("v", 0))
        return {
            "kind": "Draw",
            "opcode": "DRAW",
            "opcode_id": _opcode_id("DRAW"),
            "value": int(value) if not isinstance(value, dict) else 0,
            "filter": _normalize(semantic.get("attr", {})),
            "slot": _normalize(semantic.get("slot", {})),
            "is_negated": is_negated,
            "params": None,
            "decoded": decoded,
            "metadata_refs": _normalize(metadata_refs),
        }

    if kind == "LookAndChoose":
        params = payload.get("v")
        value = params.get("count", 0) if isinstance(params, dict) else semantic.get("value", 0)
        return {
            "kind": "LookAndChoose",
            "opcode": "LOOK_AND_CHOOSE",
            "opcode_id": _opcode_id("LOOK_AND_CHOOSE"),
            "value": int(value) if not isinstance(value, dict) else 0,
            "filter": _normalize(semantic.get("attr", {})),
            "slot": _normalize(semantic.get("slot", {})),
            "is_negated": is_negated,
            "params": _normalize(params),
            "decoded": decoded,
            "metadata_refs": _normalize(metadata_refs),
        }

    if kind in {"RecoverLive", "RecoverMember", "SelectMember", "MetaRule", "MoveMember"}:
        opcode = {
            "RecoverLive": "RECOVER_LIVE",
            "RecoverMember": "RECOVER_MEMBER",
            "SelectMember": "SELECT_MEMBER",
            "MoveMember": "MOVE_MEMBER",
            "MetaRule": "META_RULE",
        }[kind]
        value_key = "count" if kind != "MetaRule" else "rule_type"
        value = semantic.get("value", payload.get("v", 0))
        if isinstance(value, dict):
            value = value.get(value_key, 0)
        if kind == "MetaRule" and not value:
            value = payload.get("v", 0)
        return {
            "kind": kind,
            "opcode": opcode,
            "opcode_id": _opcode_id(opcode),
            "value": int(value) if not isinstance(value, dict) else 0,
            "filter": _normalize(semantic.get("attr", {})),
            "slot": _normalize(semantic.get("slot", {})),
            "is_negated": is_negated,
            "params": _normalize(payload.get("v")),
            "decoded": decoded,
            "metadata_refs": _normalize(metadata_refs),
        }

    if opcode_name:
        value = semantic.get("value", payload.get("v", 0))
        if isinstance(value, dict):
            value = 0
        params = payload.get("v")
        if params is None:
            params = semantic.get("params")
        if params is None:
            params = payload.get("raw")
        return {
            "kind": "Semantic",
            "opcode": opcode_name,
            "opcode_id": opcode_id,
            "value": int(value) if not isinstance(value, dict) else 0,
            "filter": _normalize(semantic.get("attr", {})),
            "slot": _normalize(semantic.get("slot", {})),
            "is_negated": is_negated,
            "params": _normalize(params),
            "decoded": decoded,
            "metadata_refs": _normalize(metadata_refs),
        }

    return None


def _flat_frame_from_variant(frame: Any) -> dict[str, Any] | None:
    if frame == "Return":
        return {
            "kind": "Return",
            "opcode": "RETURN",
            "opcode_id": _opcode_id("RETURN"),
            "value": 0,
            "filter": {},
            "slot": {},
            "is_negated": False,
            "params": None,
        }

    if not isinstance(frame, dict):
        return None

    kind = _frame_kind(frame)
    payload = _frame_payload(frame)

    if kind == "Draw":
        count = int(payload.get("count", 0))
        return {
            "kind": "Draw",
            "opcode": "DRAW",
            "opcode_id": _opcode_id("DRAW"),
            "value": count,
            "filter": {},
            "slot": {},
            "is_negated": bool(payload.get("is_negated", False)),
            "params": None,
        }

    if kind in {"RecoverLive", "RecoverMember", "LookAndChoose", "SelectMember", "MoveMember", "MetaRule"}:
        opcode = {
            "RecoverLive": "RECOVER_LIVE",
            "RecoverMember": "RECOVER_MEMBER",
            "LookAndChoose": "LOOK_AND_CHOOSE",
            "SelectMember": "SELECT_MEMBER",
            "MoveMember": "MOVE_MEMBER",
            "MetaRule": "META_RULE",
        }[kind]
        value_key = "count" if kind != "MetaRule" else "rule_type"
        value = payload.get(value_key, 0)
        params = payload.get("params")
        if kind == "LookAndChoose" and params is None:
            params = payload.get("value")
        return {
            "kind": kind,
            "opcode": opcode,
            "opcode_id": _opcode_id(opcode),
            "value": int(value) if not isinstance(value, dict) else 0,
            "filter": _normalize(payload.get("filter", {})),
            "slot": _normalize(payload.get("slot", {})),
            "is_negated": bool(payload.get("is_negated", False)),
            "params": _normalize(params),
        }

    if "opcode" in frame or "opcode_id" in frame:
        opcode = str(frame.get("opcode", "")).strip()
        opcode_id = int(frame.get("opcode_id", _opcode_id(opcode)))
        value = frame.get("value", 0)
        filter_value = frame.get("filter", frame.get("attr", {}))
        slot_value = frame.get("slot", frame.get("slot_params", {}))
        return {
            "kind": kind,
            "opcode": opcode,
            "opcode_id": opcode_id,
            "value": int(value) if not isinstance(value, dict) else 0,
            "filter": _normalize(filter_value),
            "slot": _normalize(slot_value),
            "is_negated": bool(frame.get("is_negated", False)),
            "params": _normalize(frame.get("params")),
        }

    return None


def _extract_semantic_frames(ability: dict[str, Any], metadata: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    frame_program = ability.get("frame_program")
    if isinstance(frame_program, dict):
        try:
            model = codec.frame_program_to_model(frame_program)
            semantic_frames: list[dict[str, Any]] = []
            for frame in model.get("frames", []):
                flat = _flat_frame_from_variant(frame)
                if flat is not None:
                    semantic_frames.append(flat)
            return semantic_frames, False
        except Exception:
            pass

    frames: Iterable[Any] = []
    if isinstance(frame_program, dict):
        frames = frame_program.get("frames", []) or []

    semantic_frames: list[dict[str, Any]] = []
    for frame in frames:
        flat = _flat_frame_from_variant(frame)
        if flat is not None:
            semantic_frames.append(flat)
    return semantic_frames, False


def _iter_cards(compiled_data: dict[str, Any]):
    for db_name in ("member_db", "live_db", "energy_db"):
        for card_id, card in compiled_data.get(db_name, {}).items():
            yield db_name, card_id, card


def build_semantic_ability_index(compiled_data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    payload = codec.build_sparse_ability_index(compiled_data, metadata)
    payload["schema"] = "ability_frame_index.semantic.v1"
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a sparse semantic ability index from compiled cards")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Compiled card JSON")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH, help="Metadata JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    compiled_data = codec.load_json(args.input)
    metadata = codec.load_json(args.metadata)
    payload = build_semantic_ability_index(compiled_data, metadata)
    codec.dump_json(args.output, payload)
    print(f"Wrote semantic ability index to {args.output}")
    print(f"Unique abilities: {payload['summary']['unique_ability_count']}")
    print(f"Abilities processed: {payload['summary']['ability_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
