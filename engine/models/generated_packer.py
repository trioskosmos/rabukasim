"""Bitfield helpers for packed ability frames."""


def _get_bits(value: int, shift: int, mask: int) -> int:
    return (int(value) >> shift) & mask


def _set_bits(value: int, shift: int, mask: int, field: int) -> int:
    return value | ((int(field) & mask) << shift)


def unpack_a_heart_cost(value: int) -> dict:
    return {
        "req_1": _get_bits(value, 0, 0xF),
        "req_2": _get_bits(value, 4, 0xF),
        "req_3": _get_bits(value, 8, 0xF),
        "req_4": _get_bits(value, 12, 0xF),
        "req_5": _get_bits(value, 16, 0xF),
        "req_6": _get_bits(value, 20, 0xF),
        "req_7": _get_bits(value, 24, 0xF),
        "req_8": _get_bits(value, 28, 0xF),
        "unit_enabled": bool(_get_bits(value, 48, 0x1)),
        "unit_id": _get_bits(value, 49, 0x7F),
    }


def pack_a_heart_cost(**kwargs) -> int:
    value = 0
    for index in range(1, 9):
        value = _set_bits(value, (index - 1) * 4, 0xF, kwargs.get(f"req_{index}", 0))
    value = _set_bits(value, 48, 0x1, kwargs.get("unit_enabled", 0))
    value = _set_bits(value, 49, 0x7F, kwargs.get("unit_id", 0))
    return value


def unpack_a_standard(value: int) -> dict:
    return {
        "target_player": _get_bits(value, 0, 0x3),
        "group_enabled": bool(_get_bits(value, 4, 0x1)),
        "group_id": _get_bits(value, 5, 0x7F),
        "has_blade_heart": bool(_get_bits(value, 13, 0x1)),
        "not_has_blade_heart": bool(_get_bits(value, 14, 0x1)),
        "unique_names": bool(_get_bits(value, 15, 0x1)),
        "unit_enabled": bool(_get_bits(value, 16, 0x1)),
        "unit_id": _get_bits(value, 17, 0x7F),
        "value_enabled": bool(_get_bits(value, 24, 0x1)),
        "value_threshold": _get_bits(value, 25, 0x1F),
        "zone_mask": _get_bits(value, 53, 0x7),
        "card_type": _get_bits(value, 2, 0x3),
        "color_mask": _get_bits(value, 32, 0x7F),
        "char_id_1": _get_bits(value, 39, 0x7F),
        "char_id_2": _get_bits(value, 46, 0x7F),
        "special_id": _get_bits(value, 56, 0x7),
        "compare_accumulated": bool(_get_bits(value, 60, 0x1)),
        "is_le": bool(_get_bits(value, 30, 0x1)),
        "is_cost_type": bool(_get_bits(value, 31, 0x1)),
        "is_optional": bool(_get_bits(value, 61, 0x1)),
        "is_setsuna": bool(_get_bits(value, 59, 0x1)),
        "keyword_energy": bool(_get_bits(value, 62, 0x1)),
        "keyword_member": bool(_get_bits(value, 63, 0x1)),
        "is_tapped": bool(_get_bits(value, 12, 0x1)),
    }


def pack_a_standard(**kwargs) -> int:
    value = 0
    value = _set_bits(value, 0, 0x3, kwargs.get("target_player", 0))
    value = _set_bits(value, 4, 0x1, kwargs.get("group_enabled", 0))
    value = _set_bits(value, 5, 0x7F, kwargs.get("group_id", 0))
    value = _set_bits(value, 13, 0x1, kwargs.get("has_blade_heart", 0))
    value = _set_bits(value, 14, 0x1, kwargs.get("not_has_blade_heart", 0))
    value = _set_bits(value, 15, 0x1, kwargs.get("unique_names", 0))
    value = _set_bits(value, 16, 0x1, kwargs.get("unit_enabled", 0))
    value = _set_bits(value, 17, 0x7F, kwargs.get("unit_id", 0))
    value = _set_bits(value, 24, 0x1, kwargs.get("value_enabled", 0))
    value = _set_bits(value, 25, 0x1F, kwargs.get("value_threshold", 0))
    value = _set_bits(value, 30, 0x1, kwargs.get("is_le", 0))
    value = _set_bits(value, 31, 0x1, kwargs.get("is_cost_type", 0))
    value = _set_bits(value, 32, 0x7F, kwargs.get("color_mask", 0))
    value = _set_bits(value, 39, 0x7F, kwargs.get("char_id_1", 0))
    value = _set_bits(value, 46, 0x7F, kwargs.get("char_id_2", 0))
    value = _set_bits(value, 53, 0x7, kwargs.get("zone_mask", 0))
    value = _set_bits(value, 56, 0x7, kwargs.get("special_id", 0))
    value = _set_bits(value, 59, 0x1, kwargs.get("is_setsuna", 0))
    value = _set_bits(value, 60, 0x1, kwargs.get("compare_accumulated", 0))
    value = _set_bits(value, 61, 0x1, kwargs.get("is_optional", 0))
    value = _set_bits(value, 62, 0x1, kwargs.get("keyword_energy", 0))
    value = _set_bits(value, 63, 0x1, kwargs.get("keyword_member", 0))
    value = _set_bits(value, 12, 0x1, kwargs.get("is_tapped", 0))
    return value


def unpack_s_standard(slot: int) -> dict:
    return {
        "target_slot": _get_bits(slot, 0, 0xFF),
        "remainder_zone": _get_bits(slot, 8, 0xFF),
        "source_zone": _get_bits(slot, 16, 0xF),
        "is_opponent": bool(_get_bits(slot, 24, 0x1)),
        "is_baton_slot": bool(_get_bits(slot, 25, 0x1)),
        "is_reveal_until_live": bool(_get_bits(slot, 25, 0x1)),
        "is_empty_slot": bool(_get_bits(slot, 26, 0x1)),
        "is_wait": bool(_get_bits(slot, 27, 0x1)),
        "is_dynamic": bool(_get_bits(slot, 28, 0x1)),
        "area_idx": _get_bits(slot, 29, 0x7),
    }


def pack_s_standard(**kwargs) -> int:
    value = 0
    value = _set_bits(value, 0, 0xFF, kwargs.get("target_slot", 0))
    value = _set_bits(value, 8, 0xFF, kwargs.get("remainder_zone", kwargs.get("dest_zone", 0)))
    value = _set_bits(value, 16, 0xF, kwargs.get("source_zone", 0))
    value = _set_bits(value, 24, 0x1, kwargs.get("is_opponent", 0))
    value = _set_bits(value, 25, 0x1, kwargs.get("is_baton_slot", kwargs.get("is_reveal_until_live", 0)))
    value = _set_bits(value, 26, 0x1, kwargs.get("is_empty_slot", 0))
    value = _set_bits(value, 27, 0x1, kwargs.get("is_wait", 0))
    value = _set_bits(value, 28, 0x1, kwargs.get("is_dynamic", 0))
    value = _set_bits(value, 29, 0x7, kwargs.get("area_idx", 0))
    return value


def unpack_v_heart_counts(value: int) -> dict:
    return {
        "pink": _get_bits(value, 0, 0xF),
        "red": _get_bits(value, 4, 0xF),
        "yellow": _get_bits(value, 8, 0xF),
        "green": _get_bits(value, 12, 0xF),
        "blue": _get_bits(value, 16, 0xF),
        "purple": _get_bits(value, 20, 0xF),
        "any": _get_bits(value, 24, 0xF),
    }


def pack_v_heart_counts(**kwargs) -> int:
    value = 0
    value = _set_bits(value, 0, 0xF, kwargs.get("pink", 0))
    value = _set_bits(value, 4, 0xF, kwargs.get("red", 0))
    value = _set_bits(value, 8, 0xF, kwargs.get("yellow", 0))
    value = _set_bits(value, 12, 0xF, kwargs.get("green", 0))
    value = _set_bits(value, 16, 0xF, kwargs.get("blue", 0))
    value = _set_bits(value, 20, 0xF, kwargs.get("purple", 0))
    value = _set_bits(value, 24, 0xF, kwargs.get("any", 0))
    return value


def unpack_v_look_choose(value: int) -> dict:
    return {
        "count": _get_bits(value, 0, 0xFF),
        "char_id_2": _get_bits(value, 8, 0x7F),
        "char_id_1": _get_bits(value, 16, 0x7F),
        "char_id_3": _get_bits(value, 23, 0x7F),
        "reveal": bool(_get_bits(value, 30, 0x1)),
        "dest_discard": bool(_get_bits(value, 31, 0x1)),
    }


def pack_v_look_choose(**kwargs) -> int:
    value = 0
    value = _set_bits(value, 0, 0xFF, kwargs.get("count", 0))
    value = _set_bits(value, 8, 0x7F, kwargs.get("char_id_2", 0))
    value = _set_bits(value, 16, 0x7F, kwargs.get("char_id_1", 0))
    value = _set_bits(value, 23, 0x7F, kwargs.get("char_id_3", 0))
    value = _set_bits(value, 30, 0x1, kwargs.get("reveal", 0))
    value = _set_bits(value, 31, 0x1, kwargs.get("dest_discard", 0))
    return value


def unpack_v_scalar_dynamic(value: int) -> dict:
    return {"base_value": _get_bits(value, 0, 0xFFFF), "divisor": _get_bits(value, 16, 0xFFFF)}


def pack_v_scalar_dynamic(**kwargs) -> int:
    value = 0
    value = _set_bits(value, 0, 0xFFFF, kwargs.get("base_value", kwargs.get("base", 0)))
    value = _set_bits(value, 16, 0xFFFF, kwargs.get("divisor", 0))
    return value
