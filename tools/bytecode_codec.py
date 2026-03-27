from __future__ import annotations

from typing import Any, Dict, List


def _opcode_id(name: str, metadata: dict[str, Any]) -> int:
    opcodes = metadata.get("opcodes", {}) if isinstance(metadata, dict) else {}
    if isinstance(opcodes, dict):
        value = opcodes.get(str(name).upper())
        if value is not None:
            return int(value)
    return 0


def _slot_id(slot: Any, metadata: dict[str, Any]) -> int:
    if isinstance(slot, int):
        return int(slot)
    if isinstance(slot, dict):
        for key in ("target_slot", "slot", "id"):
            if key in slot and slot[key] is not None:
                try:
                    return int(slot[key])
                except (TypeError, ValueError):
                    continue
    slot_indices = metadata.get("slot_indices", {}) if isinstance(metadata, dict) else {}
    if isinstance(slot, str) and isinstance(slot_indices, dict):
        value = slot_indices.get(slot.upper())
        if value is not None:
            return int(value)
    return 0


def _frame_options(frame: dict[str, Any]) -> dict[str, Any]:
    if isinstance(frame.get("options"), dict):
        return dict(frame["options"])
    options: dict[str, Any] = {}
    for key in ("value", "filter", "slot", "params", "target", "comparison"):
        if key in frame:
            options[key] = frame[key]
    return options


def frame_to_sparse(frame: dict[str, Any]) -> dict[str, Any]:
    opcode = str(frame.get("opcode_name") or frame.get("op") or "").upper()
    payload = frame.get("payload", {}) if isinstance(frame.get("payload"), dict) else {}

    sparse: dict[str, Any] = {"opcode": opcode}

    v_payload = payload.get("v")
    if isinstance(v_payload, dict):
        value = {str(key): item for key, item in v_payload.items() if item not in (None, 0, False, "", [], {})}
        if value:
            sparse["value"] = value
    elif "value" in payload and payload["value"] not in (None, 0, False, "", [], {}):
        sparse["value"] = payload["value"]

    a_payload = payload.get("a")
    if isinstance(a_payload, dict):
        attr = {str(key): item for key, item in a_payload.items() if item not in (None, 0, False, "", [], {})}
        if attr:
            sparse["attr"] = attr
    elif "attr" in payload and payload["attr"] not in (None, 0, False, "", [], {}):
        sparse["attr"] = payload["attr"]

    s_payload = payload.get("s")
    if isinstance(s_payload, dict):
        slot = {str(key): item for key, item in s_payload.items() if item not in (None, 0, False, "", [], {})}
        if slot:
            sparse["slot"] = slot
    elif "slot" in payload and payload["slot"] not in (None, 0, False, "", [], {}):
        sparse["slot"] = payload["slot"]

    return sparse


def model_to_bytecode(model: dict[str, Any], metadata: dict[str, Any]) -> List[int]:
    frames = model.get("frames", []) if isinstance(model, dict) else []
    bytecode: List[int] = []

    for frame in frames:
        if not isinstance(frame, dict):
            continue

        op = str(frame.get("op") or frame.get("opcode_name") or frame.get("opcode") or "").upper()
        if not op:
            continue

        options = _frame_options(frame)
        opcode_id = _opcode_id(op, metadata)
        value = int(options.get("value", 0) or options.get("count", 0) or 0)
        slot = _slot_id(options.get("slot"), metadata)

        if op == "RETURN":
            bytecode.extend([opcode_id or _opcode_id("RETURN", metadata), 0, 0, 0, 0])
            continue

        bytecode.extend([opcode_id, value, 0, 0, slot])

    return bytecode

