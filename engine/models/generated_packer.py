"""Stub for generated_packer module to fix import errors."""

def unpack_a_heart_cost(value: int) -> dict:
    return {"cost": value}

def unpack_s_standard(slot: int) -> dict:
    return {"slot": slot}

def unpack_v_heart_counts(value: int) -> dict:
    return {"hearts": value}

def unpack_v_look_choose(value: int) -> dict:
    return {"count": value & 0xFF, "choose": (value >> 8) & 0xFF}

def unpack_v_scalar_dynamic(value: int) -> dict:
    return {"base": value & 0xFFFF, "divisor": (value >> 16) & 0xFF}
