import sys
from io import TextIOWrapper

from engine.models.ability import format_filter_attr
from engine.models.generated_metadata import CONDITIONS, COSTS, OPCODES
from engine.models.generated_packer import unpack_s_standard

OP = {name: int(value) for name, value in OPCODES.items()}
OPCODE_NAMES = {int(value): name for name, value in OPCODES.items()}

for name, value in CONDITIONS.items():
    OPCODE_NAMES.setdefault(int(value), f"CHECK_{name}")

for name, value in COSTS.items():
    OPCODE_NAMES.setdefault(int(value), f"COST_{name}")


def decode_filter(f):
    if f == 0:
        return "none"
    return format_filter_attr(f)


# --- Legends (For human-readable decoding) ---

ZONES = {
    0: "Deck",
    1: "Deck Top",
    2: "Deck Bottom",
    3: "Energy Zone",
    4: "Stage",
    6: "Hand",
    7: "Discard",
    8: "Deck (Generic)",
    13: "Success Live Pile",
    15: "Yell Cards",
}

SLOTS = {
    0: "Left Slot",
    1: "Center Slot",
    2: "Right Slot",
    4: "Context Area",
    6: "Hand (Generic)",
    7: "Discard (Generic)",
    10: "Choice Target",
}

COMPARISONS = {
    0: "EQ (==)",
    1: "GT (>)",
    2: "LT (<)",
    3: "GE (>=)",
    4: "LE (<=)",
}

AREA_NAMES = {
    0: "any",
    1: "left",
    2: "center",
    3: "right",
}


def _slot_name(slot_id):
    return SLOTS.get(slot_id, f"Slot_{slot_id}")


def _zone_name(zone_id):
    return ZONES.get(zone_id, f"Zone_{zone_id}")


def decode_standard_slot(raw_slot):
    if raw_slot == 0:
        return "none"

    slot = unpack_s_standard(raw_slot & 0xFFFFFFFF)
    parts = []

    if slot["target_slot"]:
        parts.append(f"target={_slot_name(slot['target_slot'])}")
    if slot["remainder_zone"]:
        parts.append(f"remainder={_zone_name(slot['remainder_zone'])}")
    if slot["source_zone"]:
        parts.append(f"source={_zone_name(slot['source_zone'])}")
    if slot["dest_zone"]:
        parts.append(f"dest={_zone_name(slot['dest_zone'])}")
    if slot["is_opponent"]:
        parts.append("opponent")
    if slot["is_reveal_until_live"]:
        parts.append("reveal_until_live")
    if slot["is_empty_slot"]:
        parts.append("empty_slot")
    if slot["is_wait"]:
        parts.append("wait")
    if slot["is_dynamic"]:
        parts.append("dynamic")
    if slot["area_idx"]:
        parts.append(f"area={AREA_NAMES.get(slot['area_idx'], slot['area_idx'])}")
    if slot["is_baton_slot"]:
        parts.append("baton_slot")

    parts.append(f"raw={raw_slot}")
    return ", ".join(parts)


def decode_condition_slot(raw_slot):
    comp_val = (raw_slot >> 4) & 0x0F
    base_slot = raw_slot & 0x0F
    area_val = (raw_slot >> 29) & 0x07

    parts = [
        f"compare={COMPARISONS.get(comp_val, f'C_{comp_val}')}",
        f"slot={_slot_name(base_slot)}",
    ]
    if area_val:
        parts.append(f"area={AREA_NAMES.get(area_val, area_val)}")
    parts.append(f"raw={raw_slot}")
    return ", ".join(parts)


def get_legend_str():
    lines = ["\n--- BYTECODE LEGEND ---"]
    lines.append("Zones: " + ", ".join([f"{k}:{v}" for k, v in ZONES.items()]))
    lines.append("Slots: " + ", ".join([f"{k}:{v}" for k, v in SLOTS.items()]))
    lines.append("Comparisons: " + ", ".join([f"{k}:{v}" for k, v in COMPARISONS.items()]))
    return "\n".join(lines)


def decode_chunk(chunk):
    op, v, a_low, a_high, s = chunk
    a = ((a_high & 0xFFFFFFFF) << 32) | (a_low & 0xFFFFFFFF)
    is_negated = False
    base_op = op
    if op >= 1000 and op < 1300:
        is_negated = True
        base_op = op - 1000

    op_name = OPCODE_NAMES.get(base_op, f"OP_{base_op}")

    if is_negated:
        op_name = f"NOT {op_name}"

    params = f"value={v}, attr={a}, slot={s}"

    if base_op == OP["LOOK_AND_CHOOSE"]:
        params = (
            f"look={v & 0xFF}, pick={(v >> 8) & 0xFF}, "
            f"filter=[{decode_filter(a)}], slot=[{decode_standard_slot(s)}]"
        )
    elif base_op == OP["BUFF_POWER"]:
        params = f"value={v}, filter=[{decode_filter(a)}], slot=[{decode_standard_slot(s)}]"
    elif base_op == OP["RECOVER_MEMBER"] or base_op == OP["RECOVER_LIVE"]:
        params = f"count={v}, filter=[{decode_filter(a)}], slot=[{decode_standard_slot(s)}]"
    elif (
        base_op == OP["DRAW"]
        or base_op == OP["MOVE_TO_DISCARD"]
        or base_op == OP["ADD_HEARTS"]
        or base_op == OP["ADD_BLADES"]
    ):
        params = f"count={v}, filter=[{decode_filter(a)}], slot=[{decode_standard_slot(s)}]"
    elif base_op == OP["PAY_ENERGY"]:
        params = f"cost={v}, filter=[{decode_filter(a)}], slot=[{decode_standard_slot(s)}]"
    elif base_op == OP["SELECT_MEMBER"]:
        params = f"value={v}, filter=[{decode_filter(a)}], slot=[{decode_standard_slot(s)}]"
    elif base_op == OP["GRANT_ABILITY"]:
        params = f"granted_index={v}, source_card={a}, slot=[{decode_standard_slot(s)}]"
    elif base_op == OP["MOVE_MEMBER"]:
        params = f"from={_slot_name(v)}, to={_slot_name(a)}, raw_slot={s}"
    elif base_op in (OP["JUMP"], OP["JUMP_IF_FALSE"]):
        params = f"offset={v}"
    elif base_op == OP["RETURN"]:
        params = "done"
    elif base_op >= 100 and base_op < 200:
        params = f"value={v}, attr={a}, slot={s}"
    elif base_op >= 200 and base_op < 300:
        params = f"value={v}, filter=[{decode_filter(a)}], slot=[{decode_condition_slot(s)}]"
    elif base_op >= 300 and base_op < 400:
        params = f"value={v}, filter=[{decode_filter(a)}], slot=[{decode_condition_slot(s)}]"
    else:
        parts = [f"value={v}"]
        if a:
            parts.append(f"filter=[{decode_filter(a)}]")
        if s:
            parts.append(f"slot=[{decode_standard_slot(s)}]")
        params = ", ".join(parts)

    return f"{op_name:<20} | {params}"


def decode_bytecode(bytecode):
    if not bytecode:
        return "None"

    chunks = [bytecode[i : i + 5] for i in range(0, len(bytecode), 5)]
    lines = []
    for i, chunk in enumerate(chunks):
        if len(chunk) < 5:
            chunk = chunk + [0] * (5 - len(chunk))
        lines.append(f"  {i * 5:02d}: {decode_chunk(chunk)}")

    # Add Legend to the end
    lines.append(get_legend_str())
    return "\n".join(lines)


if __name__ == "__main__":
    # Standardized UTF-8 Handling
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print('Usage: python bytecode_decoder.py "[41, 3, 385876097, 0, 1, 0, 0, 0]"')
        sys.exit(1)

    raw = sys.argv[1]
    # Clean up input if it's bracketed
    raw = raw.strip("[] ")
    try:
        data = [int(x.strip()) for x in raw.split(",")]
        print(decode_bytecode(data))
    except Exception as e:
        print(f"Error decoding: {e}")
