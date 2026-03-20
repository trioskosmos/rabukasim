import re
from typing import List

from engine.models.ability_filter import format_filter_attr
from engine.models.generated_metadata import (
    CARD_TYPES,
    CHARACTER_IDS,
    COMPARISONS,
    CONDITIONS,
    COSTS,
    COUNT_SOURCES,
    GROUP_IDS,
    HEART_COLOR_MAP,
    META_RULE_TYPES,
    OPCODES,
    SLOT_INDICES,
    TARGETS,
    TRIGGERS,
    UNIT_IDS,
    ZONES,
)
from engine.models.generated_packer import unpack_a_heart_cost, unpack_s_standard, unpack_v_heart_counts, unpack_v_look_choose

OP = {name: int(value) for name, value in OPCODES.items()}
OPCODE_NAMES = {int(value): name for name, value in OPCODES.items()}
TRIGGER_NAMES = {int(value): name for name, value in TRIGGERS.items()}
CONDITION_NAMES = {int(value): name for name, value in CONDITIONS.items()}
COST_NAMES = {int(value): name for name, value in COSTS.items()}
TARGET_NAMES = {int(value): name for name, value in TARGETS.items()}
ZONE_NAMES = {int(value): name for name, value in ZONES.items()}
COMPARISON_NAMES = {int(value): name for name, value in COMPARISONS.items()}
COUNT_SOURCE_NAMES = {int(value): name for name, value in COUNT_SOURCES.items()}
META_RULE_NAMES = {int(value): name for name, value in META_RULE_TYPES.items()}
HEART_COLOR_NAMES = {int(value): name.lower() for name, value in HEART_COLOR_MAP.items()}

CHARACTER_NAMES = {int(value): name.title() for name, value in CHARACTER_IDS.items()}
GROUP_NAMES = {int(value): name.title() for name, value in GROUP_IDS.items()}
UNIT_NAMES = {int(value): name.title().replace("_", " ") for name, value in UNIT_IDS.items()}
CARD_TYPE_NAMES = {int(value): name.title() for name, value in CARD_TYPES.items()}

SPECIAL_ID_NAMES = {
    0: "None",
    1: "Self",
    2: "Other than Self",
    3: "Other than Activator",
}

SLOT_NAMES = {int(value): name for name, value in SLOT_INDICES.items()}
SLOT_NAMES.update(
    {
        0: "Left Stage (0)",
        1: "Center Stage (1)",
        2: "Right Stage (2)",
        4: "Context Card",
        6: "Hand (Zone)",
        7: "Discard (Zone)",
        10: "Choice Target",
        13: "Live Slot 0",
        14: "Live Slot 1",
        15: "Live Slot 2",
        20: "Player Select",
    }
)

for name, value in CONDITIONS.items():
    OPCODE_NAMES.setdefault(int(value), f"CHECK_{name}")

for name, value in COSTS.items():
    OPCODE_NAMES.setdefault(int(value), f"COST_{name}")

# Manual overrides for unmapped or special opcodes
if "UNIQUE_NAMES_COUNT" not in CONDITIONS:
    # Use 316 as a virtual opcode for documentation if needed, 
    # but the interpreter often sees 0 for unmapped conditions.
    CONDITION_NAMES[316] = "UNIQUE_NAMES_COUNT"
    OPCODE_NAMES[316] = "CHECK_UNIQUE_NAMES_COUNT"


def opcode_name(opcode: int, v: int = 0, a: int = 0, s: int = 0) -> str:
    if 1000 <= opcode < 2000:
        base_opcode = opcode - 1000
        if base_opcode in CONDITION_NAMES:
            return CONDITION_NAMES[base_opcode]
        if base_opcode in OPCODE_NAMES:
            return OPCODE_NAMES[base_opcode]
        return f"OP_{base_opcode}"
    if opcode == 0 and (v != 0 or a != 0 or s != 0):
        # In SUNNY DAY SONG and others, opcode 0 with condition-like slot params 
        # is used for conditions handled by the interpreter's higher-level logic.
        return "CHECK_UNIQUE_NAMES_COUNT?"
    if int(opcode) in CONDITION_NAMES:
        return CONDITION_NAMES[int(opcode)]
    return OPCODE_NAMES.get(int(opcode), f"OP_{opcode}")


def trigger_name(trigger: int) -> str:
    return TRIGGER_NAMES.get(int(trigger), f"TRIGGER_{trigger}")


AREA_NAMES = {
    0: "any",
    1: "left",
    2: "center",
    3: "right",
}


_FLAG_25_BATON_OPS = {OP.get("PLAY_MEMBER_FROM_HAND"), OP.get("PLAY_MEMBER_FROM_DISCARD")}
_FLAG_25_CAPTURE_OPS = {OP.get("SELECT_MEMBER"), OP.get("MOVE_TO_DISCARD")}
_FLAG_25_REVEAL_OPS = {OP.get("REVEAL_UNTIL")}

RE_ID_REPLACEMENT = re.compile(r"(group|unit|char\d|type|special)=(\d+)")


def decode_filter(filter_attr: int) -> str:
    if filter_attr == 0:
        return "none"
    raw_filter = format_filter_attr(filter_attr)

    def replacer(match):
        key = match.group(1)
        val = int(match.group(2))
        if key == "group":
            return f"group={GROUP_NAMES.get(val, val)}"
        if key == "unit":
            return f"unit={UNIT_NAMES.get(val, val)}"
        if key.startswith("char"):
            return f"{key}={CHARACTER_NAMES.get(val, val)}"
        if key == "type":
            return f"type={CARD_TYPE_NAMES.get(val, val)}"
        return match.group(0)

    return RE_ID_REPLACEMENT.sub(replacer, raw_filter)


def _slot_name(slot_id: int) -> str:
    if slot_id in SLOT_NAMES:
        return SLOT_NAMES[slot_id]
    target_name = TARGET_NAMES.get(slot_id)
    if target_name:
        return target_name.title()
    return f"Slot_{slot_id}"


def _zone_name(zone_id: int) -> str:
    zone_name = ZONE_NAMES.get(zone_id)
    if zone_name:
        zone_aliases = {
            "DEFAULT": "Default",
            "DECK_TOP": "Deck Top",
            "DECK_BOTTOM": "Deck Bottom",
            "ENERGY": "Energy",
            "STAGE": "Stage",
            "DECK": "Deck",
            "HAND": "Hand",
            "DISCARD": "Discard",
            "LIVE_SET": "Live Set",
            "SUCCESS_PILE": "Success Pile",
            "YELL": "Yell",
        }
        return zone_aliases.get(zone_name, zone_name.title())
    return f"Zone_{zone_id}"


def _comparison_name(comp_id: int) -> str:
    comparison_name = COMPARISON_NAMES.get(comp_id)
    if comparison_name:
        return {
            "EQ": "EQ (==)",
            "GT": "GT (>)",
            "LT": "LT (<)",
            "GE": "GE (>=)",
            "LE": "LE (<=)",
        }.get(comparison_name, comparison_name)
    return f"C_{comp_id}"


def _flag_25_label(opcode: int | None) -> str:
    if opcode in _FLAG_25_BATON_OPS:
        return "baton_slot"
    if opcode in _FLAG_25_CAPTURE_OPS:
        return "capture_value"
    if opcode in _FLAG_25_REVEAL_OPS:
        return "reveal_until_live"
    return "flag25"


def decode_standard_slot(raw_slot: int, opcode: int | None = None) -> str:
    if raw_slot == 0:
        return "none"

    slot = unpack_s_standard(raw_slot & 0xFFFFFFFF)
    parts: List[str] = []

    if slot["target_slot"]:
        parts.append(f"target={_slot_name(slot['target_slot'])}")
    if slot["remainder_zone"]:
        if slot["is_dynamic"]:
            parts.append(
                f"multiplier_source={COUNT_SOURCE_NAMES.get(slot['remainder_zone'], _zone_name(slot['remainder_zone']))}"
            )
        else:
            parts.append(f"remainder={_zone_name(slot['remainder_zone'])}")
    if slot["source_zone"]:
        parts.append(f"source={_zone_name(slot['source_zone'])}")
    if slot["dest_zone"]:
        parts.append(f"dest={_zone_name(slot['dest_zone'])}")
    if slot["is_opponent"]:
        parts.append("opponent")
    if slot["is_reveal_until_live"]:
        parts.append(_flag_25_label(opcode))
    if slot["is_empty_slot"]:
        parts.append("empty_slot")
    if slot["is_wait"]:
        parts.append("wait")
    if slot["is_dynamic"]:
        parts.append("dynamic")
    if slot["area_idx"]:
        parts.append(f"area={AREA_NAMES.get(slot['area_idx'], slot['area_idx'])}")

    return ", ".join(parts)


def decode_condition_slot(raw_slot: int) -> str:
    comp_val = (raw_slot >> 4) & 0x0F
    base_slot = raw_slot & 0x0F
    area_val = (raw_slot >> 29) & 0x07

    parts = [
        f"compare={_comparison_name(comp_val)}",
        f"slot={_slot_name(base_slot)}",
    ]
    if area_val:
        parts.append(f"area={AREA_NAMES.get(area_val, area_val)}")
    return ", ".join(parts)


def get_legend_str() -> str:
    lines = ["\n--- BYTECODE LEGEND ---"]
    lines.append("Zones: " + ", ".join([f"{k}:{_zone_name(k)}" for k in sorted(ZONE_NAMES)]))
    lines.append("Slots: " + ", ".join([f"{k}:{_slot_name(k)}" for k in sorted(SLOT_NAMES)]))
    lines.append("Comparisons: " + ", ".join([f"{k}:{_comparison_name(k)}" for k in sorted(COMPARISON_NAMES)]))
    return "\n".join(lines)


def _decode_look_and_choose(value: int, attr: int, slot: int, opcode: int) -> str:
    look_v = unpack_v_look_choose(value)
    chars = []
    if look_v["char_id_1"]:
        chars.append(CHARACTER_NAMES.get(look_v["char_id_1"], str(look_v["char_id_1"])))
    if look_v["char_id_2"]:
        chars.append(CHARACTER_NAMES.get(look_v["char_id_2"], str(look_v["char_id_2"])))
    if look_v["char_id_3"]:
        chars.append(CHARACTER_NAMES.get(look_v["char_id_3"], str(look_v["char_id_3"])))

    filter_str = decode_filter(attr)
    filter_part = f"filter=[{filter_str}] " if attr else ""
    return (
        f"look={look_v['count']}, "
        f"{filter_part}"
        f"chars=[{'/'.join(chars)}], reveal={bool(look_v['reveal'])}, discard_remainder={bool(look_v['dest_discard'])}, "
        f"slot=[{decode_standard_slot(slot, opcode)}]"
    )


def _decode_meta_rule(value: int, attr: int, slot: int, opcode: int) -> str:
    meta_name = META_RULE_NAMES.get(attr, f"META_{attr}")
    parts = [f"type={meta_name}"]
    if meta_name in {"HEART_RULE", "ALL_BLADE_AS_ANY_HEART"}:
        source_name = {0: "none", 1: "all_blade", 2: "blade"}.get(value, str(value))
        parts.append(f"source={source_name}")
    elif value:
        parts.append(f"value={value}")
    if slot:
        parts.append(f"slot=[{decode_standard_slot(slot, opcode)}]")
    return ", ".join(parts)


def _decode_set_heart_cost(value: int, attr: int, slot: int, opcode: int) -> str:
    hearts = unpack_v_heart_counts(value)
    requirements = unpack_a_heart_cost(attr)
    count_parts = [f"{color}={amount}" for color, amount in hearts.items() if amount]
    req_parts = []
    for idx in range(1, 9):
        req = requirements[f"req_{idx}"]
        if req:
            req_parts.append(HEART_COLOR_NAMES.get(req, str(req)))
    if requirements.get("unit_enabled"):
        req_parts.append(f"unit={UNIT_NAMES.get(requirements.get('unit_id'), requirements.get('unit_id'))}")

    parts = []
    if count_parts:
        parts.append("counts=[" + ", ".join(count_parts) + "]")
    if req_parts:
        parts.append("requirements=[" + ", ".join(req_parts) + "]")
    if slot:
        parts.append(f"slot=[{decode_standard_slot(slot, opcode)}]")
    return ", ".join(parts) if parts else f"value={value}, attr={attr}, slot={slot}"


def _decode_heart_effect(count: int, attr: int, slot: int, opcode: int, label: str = "count") -> str:
    parts = [f"{label}={count}"]
    if 0 <= attr <= max(HEART_COLOR_NAMES):
        parts.append(f"heart_type={HEART_COLOR_NAMES.get(attr, attr)}")
    elif attr:
        parts.append(f"filter=[{decode_filter(attr)}]")
    if slot:
        parts.append(f"slot=[{decode_standard_slot(slot, opcode)}]")
    return ", ".join(parts)


def _decode_move_to_discard(value: int, attr: int, slot: int, opcode: int) -> str:
    unsigned_value = value & 0xFFFFFFFF
    parts = []
    if unsigned_value & 0x80000000:
        parts.append(f"until_size={unsigned_value & 0x7FFFFFFF}")
        parts.append("mode=until_size")
    else:
        parts.append(f"count={value}")
    parts.append(f"filter=[{decode_filter(attr)}]")
    if slot:
        parts.append(f"slot=[{decode_standard_slot(slot, opcode)}]")
    return ", ".join(parts)


def decode_chunk(chunk: List[int]) -> str:
    op, v, a_low, a_high, s = chunk
    a = ((a_high & 0xFFFFFFFF) << 32) | (a_low & 0xFFFFFFFF)
    is_negated = False
    base_op = op
    if 1000 <= op < 2000:
        is_negated = True
        base_op = op - 1000

    op_name = opcode_name(base_op, v, a, s)
    if is_negated:
        op_name = f"NOT {op_name}"

    # Determine descriptive parameter labels based on opcode
    v_label = "value"
    a_label = "filter"
    s_label = "slot"

    if base_op in (OP.get("DRAW"), OP.get("ADD_BLADES"), OP.get("ADD_HEARTS"), 
                   OP.get("RECOVER_MEMBER"), OP.get("RECOVER_LIVE"), 
                   OP.get("ACTIVATE_MEMBER"), OP.get("SET_TAPPED"), 
                   OP.get("ACTIVATE_ENERGY"), OP.get("ENERGY_CHARGE"), 
                   OP.get("REVEAL_UNTIL"), OP.get("SELECT_MEMBER"), 
                   OP.get("SELECT_CARDS"), OP.get("SELECT_LIVE"),
                   OP.get("LOOK_DECK"), OP.get("ORDER_DECK")):
        v_label = "count"
    elif base_op in (OP.get("JUMP"), OP.get("JUMP_IF_FALSE")):
        v_label = "offset"
    elif base_op == OP.get("BUFF_POWER"):
        v_label = "amount"
    elif base_op == OP.get("PAY_ENERGY"):
        v_label = "cost"
    elif base_op == OP.get("GRANT_ABILITY"):
        v_label = "granted_index"
    elif base_op == OP.get("SELECT_MODE"):
        v_label = "options"
    elif base_op == OP.get("SET_HEARTS"):
        v_label = "value"

    # Default params string
    params = f"{v_label}={v}, {a_label}=[{decode_filter(a)}], {s_label}=[{decode_standard_slot(s, base_op)}]"

    # Specialized decoding logic for complex opcodes
    if base_op == OP.get("LOOK_AND_CHOOSE"):
        params = _decode_look_and_choose(v, a, s, base_op)
    elif base_op == OP.get("META_RULE"):
        params = _decode_meta_rule(v, a, s, base_op)
    elif base_op == OP.get("SET_HEART_COST"):
        params = _decode_set_heart_cost(v, a, s, base_op)
    elif base_op == OP.get("MOVE_TO_DISCARD"):
        params = _decode_move_to_discard(v, a, s, base_op)
    elif base_op == OP.get("ADD_HEARTS") or base_op == OP.get("SET_HEARTS"):
        params = _decode_heart_effect(v, a, s, base_op, label=v_label)
    elif base_op == OP.get("MOVE_MEMBER"):
        params = f"from={_slot_name(v)}, to={_slot_name(a)}, slot=[{decode_standard_slot(s, base_op)}]"
    elif base_op == OP.get("SET_TARGET_SELF"):
        params = "target_context=self"
    elif base_op == OP.get("SET_TARGET_OPPONENT"):
        params = "target_context=opponent"
    elif base_op == OP.get("TRANSFORM_COLOR") or base_op == OP.get("TRANSFORM_HEART"):
        params = f"source={HEART_COLOR_NAMES.get(v, v)}, target={HEART_COLOR_NAMES.get(a, a)}, slot=[{decode_standard_slot(s, base_op)}]"
    elif base_op in (OP.get("JUMP"), OP.get("JUMP_IF_FALSE")):
        params = f"offset={v}"
    elif base_op == OP.get("RETURN"):
        params = "done"
    elif base_op == 0 and (v != 0 or a != 0 or s != 0):
        # Fallback for unmapped condition parameters (like UNIQUE_NAMES_COUNT)
        params = f"value={v}, filter=[{decode_filter(a)}], slot=[{decode_condition_slot(s)}]"
    elif 100 <= base_op < 200:
        # Action opcodes
        params = f"value={v}, filter=[{decode_filter(a)}], slot=[{decode_standard_slot(s, base_op)}]"
    elif 200 <= base_op < 400:
        # Condition opcodes
        params = f"value={v}, filter=[{decode_filter(a)}], slot=[{decode_condition_slot(s)}]"

    return f"{op_name:<25} | {params}"


def decode_bytecode(bytecode: List[int]) -> str:
    if not bytecode:
        return "None"

    chunks = [bytecode[i : i + 5] for i in range(0, len(bytecode), 5)]
    lines = []
    for i, chunk in enumerate(chunks):
        if len(chunk) < 5:
            chunk = chunk + [0] * (5 - len(chunk))
        lines.append(f"  {i * 5:02d}: {decode_chunk(chunk)}")
    lines.append(get_legend_str())
    return "\n".join(lines)


# ===== Version Gate Support =====
# Support for versioned bytecode decoding. Currently only v1 is implemented;
# v2 support is reserved for future extension.


def decode_bytecode_with_version(bytecode: List[int], layout_version: int = 1) -> str:
    """
    Decode bytecode with explicit version specification.
    
    Allows decoding different bytecode layout versions. Currently v1 and v2
    are defined, but only v1 is active. This function enables gradual migration
    when v2 layout is introduced.
    
    Args:
        bytecode: List of 32-bit integers comprising bytecode
        layout_version: Bytecode layout version (default: 1)
    
    Returns:
        Formatted, legible bytecode trace with zone/slot legends
    
    Raises:
        ValueError: If layout_version is not supported
    """
    if layout_version == 1:
        return decode_bytecode(bytecode)
    elif layout_version == 2:
        # Future: Decode v2 layout (currently same as v1, placeholder for expansion)
        return decode_bytecode_v2(bytecode)
    else:
        raise ValueError(f"Unsupported bytecode layout version: {layout_version}")


def decode_bytecode_v2(bytecode: List[int]) -> str:
    """
    Decode bytecode using v2 layout (future extension).
    
    Currently a placeholder that uses v1 logic. When v2 layout is finalized,
    this function will be updated to handle the new format.
    
    The v2 layout may:
    - Expand certain fields for better expressiveness
    - Add inline metadata markers
    - Support wider immediate values
    - Maintain backward compatibility with v1 decoders for common opcodes
    
    For now, v2 is defined but inactive. Switch to v2 compilation via VersionGate.
    """
    # Placeholder: Currently uses v1 decoding
    # When v2 layout is implemented, replace this with v2-specific logic
    if not bytecode:
        return "None"

    lines = [
        f"  [v2 layout - experimental, currently using v1 decoder]",
        f"  Bytecode length: {len(bytecode)} words",
    ]
    lines.append("")

    # For now, delegate to v1 decoder
    v1_output = decode_bytecode(bytecode)
    lines.append(v1_output)

    return "\n".join(lines)
