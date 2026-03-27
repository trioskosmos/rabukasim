from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(slots=True)
class AbilityFrame:
    """Canonical frame shape for ability export and sparse frame storage."""

    op: str
    options: Dict[str, Any] = field(default_factory=dict)
    frame_index: int | None = None
    source_words: list[int] | None = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"op": str(self.op).upper()}
        if self.options:
            data["options"] = copy.deepcopy(self.options)
        if self.frame_index is not None:
            data["frame_index"] = int(self.frame_index)
        if self.source_words:
            data["source_words"] = [int(word) for word in self.source_words]
        return data


def _strip_empty(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: Dict[str, Any] = {}
        for key, item in value.items():
            if key in {"raw", "signature", "signature_hash", "signature_source"}:
                continue
            normalized = _strip_empty(item)
            if normalized not in (None, False, 0, "", [], {}):
                cleaned[key] = normalized
        return cleaned
    if isinstance(value, list):
        cleaned_list = [_strip_empty(item) for item in value]
        return [item for item in cleaned_list if item not in (None, False, 0, "", [], {})]
    return value


def _coerce_op(frame: Any) -> str:
    if frame == "Return":
        return "RETURN"

    if isinstance(frame, dict):
        if len(frame) == 1 and not ({"op", "opcode", "opcode_name", "kind"} & set(frame.keys())):
            key, payload = next(iter(frame.items()))
            if key == "Return":
                return "RETURN"
            if isinstance(payload, dict) and payload.get("op"):
                return str(payload.get("op")).upper()
            if isinstance(payload, dict) and payload.get("opcode_name"):
                return str(payload.get("opcode_name")).upper()
            return str(key).upper()

        for key in ("op", "opcode", "opcode_name", "kind"):
            value = frame.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().upper()

    return "OP_0"


def _coerce_options(frame: Any) -> Dict[str, Any]:
    if not isinstance(frame, dict):
        return {}

    options: Dict[str, Any] = {}
    if isinstance(frame.get("options"), dict):
        options.update(copy.deepcopy(frame["options"]))

    if isinstance(frame.get("semantic"), dict):
        semantic = frame["semantic"]
        if semantic.get("value") is not None:
            options.setdefault("value", semantic.get("value"))
        if semantic.get("attr") is not None:
            options.setdefault("filter", semantic.get("attr"))
        if semantic.get("slot") is not None:
            options.setdefault("slot", semantic.get("slot"))
        if semantic.get("params") is not None:
            options.setdefault("params", semantic.get("params"))

    for key in ("value", "count", "filter", "attr", "slot", "params", "target", "comparison", "is_cost", "cost"):
        if key in frame and frame[key] not in (None, "", [], {}):
            mapped_key = "filter" if key == "attr" else ("is_cost" if key == "cost" else key)
            options.setdefault(mapped_key, copy.deepcopy(frame[key]))

    if frame.get("is_negated", frame.get("negated", False)):
        options.setdefault("negated", True)

    if "op" in frame and frame["op"] == "RETURN":
        return {}

    return {key: value for key, value in _strip_empty(options).items() if value not in (None, False, 0, "", [], {})}


def normalize_frame(frame: Any, frame_index: int | None = None) -> Dict[str, Any]:
    if frame == "Return":
        normalized: Dict[str, Any] = {"op": "RETURN", "rust_opcode": "O_RETURN"}
        if frame_index is not None:
            normalized["frame_index"] = frame_index
        return normalized

    if isinstance(frame, dict) and len(frame) == 1 and not ({"op", "opcode", "opcode_name", "kind"} & set(frame.keys())):
        key, payload = next(iter(frame.items()))
        if key == "Return":
            return normalize_frame("Return", frame_index)
        if isinstance(payload, dict):
            frame = {"op": key, **payload}
        else:
            frame = {"op": key, "value": payload}

    if not isinstance(frame, dict):
        raise ValueError(f"unsupported frame payload: {frame!r}")

    opcode = _coerce_op(frame)
    if opcode == "OP_0":
        raise ValueError(f"unsupported frame payload: {frame!r}")

    normalized: Dict[str, Any] = {"op": opcode}
    options = _coerce_options(frame)
    if options:
        normalized["options"] = options
        for alias in ("value", "count", "filter", "slot", "params", "target", "comparison", "is_cost"):
            if alias in options:
                normalized[alias] = copy.deepcopy(options[alias])
        if options.get("negated"):
            normalized["negated"] = True

    if isinstance(frame.get("rust_opcode"), str) and frame["rust_opcode"]:
        normalized["rust_opcode"] = frame["rust_opcode"]
    elif opcode != "RETURN":
        normalized["rust_opcode"] = f"O_{opcode}"

    explicit_index = frame.get("frame_index", frame.get("ability_frame_index", frame_index))
    if isinstance(explicit_index, int) and explicit_index >= 0:
        normalized["frame_index"] = explicit_index

    source_words = frame.get("source_words")
    if isinstance(source_words, list) and source_words:
        normalized["source_words"] = [int(word) for word in source_words]

    return normalized


def frame_opcode_sequence(frames: list[Dict[str, Any]]) -> list[str]:
    return [str(frame.get("op", "")).upper() for frame in frames if str(frame.get("op", "")).strip()]
