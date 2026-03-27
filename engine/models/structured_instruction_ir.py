from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List


SEMANTIC_FORM_VERSION = 1


class OperandKind(str, Enum):
    INT = "int"
    BOOL = "bool"
    ENUM = "enum"
    FILTER = "filter"
    SLOT = "slot"
    TARGET = "target"
    JSON = "json"
    TEXT = "text"


@dataclass
class StructuredOperand:
    name: str
    kind: OperandKind
    value: Any
    packed_from: str | None = None
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": self.name,
            "kind": self.kind.value,
            "value": self.value,
        }
        if self.packed_from:
            data["packed_from"] = self.packed_from
        if self.note:
            data["note"] = self.note
        return data


@dataclass
class StructuredInstruction:
    role: str
    opcode_name: str
    operands: List[StructuredOperand] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    source_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "role": self.role,
            "opcode_name": self.opcode_name,
            "operands": [operand.to_dict() for operand in self.operands],
        }
        if self.labels:
            data["labels"] = self.labels
        if self.source_text:
            data["source_text"] = self.source_text
        return data

    def to_line(self) -> str:
        rendered_operands = ", ".join(
            f"{operand.name}={operand.value!r}" for operand in self.operands
        )
        label_suffix = f" [{' | '.join(self.labels)}]" if self.labels else ""
        return f"{self.role.upper()} {self.opcode_name}({rendered_operands}){label_suffix}"


@dataclass
class StructuredAbilityIR:
    trigger: str
    instructions: List[StructuredInstruction] = field(default_factory=list)
    once_per_turn: bool = False
    pseudocode: str = ""
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger": self.trigger,
            "once_per_turn": self.once_per_turn,
            "pseudocode": self.pseudocode,
            "raw_text": self.raw_text,
            "instructions": [instruction.to_dict() for instruction in self.instructions],
        }

    def to_lines(self) -> List[str]:
        prefix = [f"TRIGGER {self.trigger}"]
        if self.once_per_turn:
            prefix[0] += " [once_per_turn]"
        return prefix + [instruction.to_line() for instruction in self.instructions]


def _enum_name(value: Any) -> str:
    return getattr(value, "name", str(value))


def _append_if_present(
    operands: List[StructuredOperand],
    name: str,
    kind: OperandKind,
    value: Any,
    *,
    packed_from: str | None = None,
    note: str = "",
) -> None:
    if value in (None, "", [], {}, False):
        return
    if isinstance(value, int) and value == 0:
        return
    operands.append(
        StructuredOperand(
            name=name,
            kind=kind,
            value=value,
            packed_from=packed_from,
            note=note,
        )
    )


def _operands_from_params(params: Dict[str, Any]) -> Iterable[StructuredOperand]:
    for key, value in params.items():
        if value in (None, "", [], {}):
            continue
        kind = OperandKind.JSON
        if isinstance(value, bool):
            kind = OperandKind.BOOL
        elif isinstance(value, int):
            kind = OperandKind.INT
        elif isinstance(value, str):
            kind = OperandKind.TEXT
        yield StructuredOperand(name=key.lower(), kind=kind, value=value)


def build_structured_instruction_ir(ability: Any) -> StructuredAbilityIR:
    instructions = getattr(ability, "instructions", None) or []
    if not instructions:
        instructions = [
            *getattr(ability, "costs", []),
            *getattr(ability, "conditions", []),
            *getattr(ability, "effects", []),
        ]

    structured: List[StructuredInstruction] = []
    for instruction in instructions:
        role = "instruction"
        opcode_name = "UNKNOWN"
        operands: List[StructuredOperand] = []
        labels: List[str] = []

        if hasattr(instruction, "effect_type"):
            role = "effect"
            opcode_name = _enum_name(instruction.effect_type)
            _append_if_present(operands, "value", OperandKind.INT, getattr(instruction, "value", 0))
            _append_if_present(
                operands,
                "target",
                OperandKind.TARGET,
                _enum_name(getattr(instruction, "target", "")),
            )
            _append_if_present(
                operands,
                "runtime_opcode",
                OperandKind.ENUM,
                getattr(instruction, "runtime_opcode", 0),
                packed_from="bytecode.op",
            )
            _append_if_present(
                operands,
                "runtime_value",
                OperandKind.INT,
                getattr(instruction, "runtime_value", 0),
                packed_from="bytecode.v",
            )
            _append_if_present(
                operands,
                "runtime_attr",
                OperandKind.FILTER,
                getattr(instruction, "runtime_attr", 0),
                packed_from="bytecode.a",
                note="Prefer structured params over packed attr in new layout",
            )
            _append_if_present(
                operands,
                "runtime_slot",
                OperandKind.SLOT,
                getattr(instruction, "runtime_slot", 0),
                packed_from="bytecode.s",
                note="Prefer named slot operands in new layout",
            )
            if getattr(instruction, "is_optional", False):
                labels.append("optional")
        elif hasattr(instruction, "cost_type") or hasattr(instruction, "type"):
            role = "cost"
            opcode_name = _enum_name(getattr(instruction, "cost_type", getattr(instruction, "type", "")))
            _append_if_present(operands, "value", OperandKind.INT, getattr(instruction, "value", 0))
            if getattr(instruction, "is_optional", False):
                labels.append("optional")
        elif hasattr(instruction, "is_negated"):
            role = "condition"
            opcode_name = _enum_name(getattr(instruction, "type", ""))
            _append_if_present(operands, "value", OperandKind.INT, getattr(instruction, "value", 0))
            _append_if_present(
                operands,
                "packed_attr",
                OperandKind.FILTER,
                getattr(instruction, "attr", 0),
                packed_from="bytecode.a",
                note="Readable layout should split this into named operands",
            )
            if getattr(instruction, "is_negated", False):
                labels.append("negated")

        operands.extend(_operands_from_params(getattr(instruction, "params", {}) or {}))
        structured.append(
            StructuredInstruction(
                role=role,
                opcode_name=opcode_name,
                operands=operands,
                labels=labels,
            )
        )

    return StructuredAbilityIR(
        trigger=_enum_name(getattr(ability, "trigger", "")),
        instructions=structured,
        once_per_turn=bool(getattr(ability, "is_once_per_turn", False)),
        pseudocode=str(getattr(ability, "pseudocode", "")),
        raw_text=str(getattr(ability, "raw_text", "")),
    )
