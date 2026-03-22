from dataclasses import dataclass, fields
from typing import Any, Dict, List

from .generated_packer import pack_a_standard, unpack_a_standard

_BOOL_FILTER_FIELDS = {
    "group_enabled",
    "is_tapped",
    "has_blade_heart",
    "not_has_blade_heart",
    "unique_names",
    "unit_enabled",
    "value_enabled",
    "is_le",
    "is_cost_type",
    "is_setsuna",
    "compare_accumulated",
    "is_optional",
    "keyword_energy",
    "keyword_member",
}

_TARGET_PLAYER_LABELS = {
    0: "unspecified",
    1: "self",
    2: "opponent",
    3: "both",
}

_CARD_TYPE_LABELS = {
    0: "any",
    1: "member",
    2: "live",
}

_ZONE_MASK_LABELS = {
    1: "deck",
    2: "deck_bottom",
    3: "energy",
    4: "stage",
    5: "deck_top",
    6: "hand",
    7: "discard",
}

SPECIAL_ID_LABELS = {
    1: "Kanon",
    2: "Not MY舞",
    3: "Not Self",
    4: "Same Name",
    5: "Base Cost",
    6: "Selected",
    7: "Not Selected",
}

ZONE_MASK_LABELS = {
    1: "Main",
    2: "Guest",
    4: "Friend",
    3: "Main+Guest",
    5: "Main+Friend",
    6: "Guest+Friend",
    7: "ALL",
}

_COLOR_NAMES = ["pink", "red", "yellow", "green", "blue", "purple", "any"]


@dataclass(slots=True)
class PackedFilterSpec:
    target_player: int = 0
    card_type: int = 0
    group_enabled: bool = False
    group_id: int = 0
    is_tapped: bool = False
    has_blade_heart: bool = False
    not_has_blade_heart: bool = False
    unique_names: bool = False
    unit_enabled: bool = False
    unit_id: int = 0
    value_enabled: bool = False
    value_threshold: int = 0
    is_le: bool = False
    is_cost_type: bool = False
    color_mask: int = 0
    char_id_1: int = 0
    char_id_2: int = 0
    zone_mask: int = 0
    special_id: int = 0
    is_setsuna: bool = False
    compare_accumulated: bool = False
    is_optional: bool = False
    keyword_energy: bool = False
    keyword_member: bool = False

    def pack(self) -> int:
        return pack_a_standard(**{field_info.name: getattr(self, field_info.name) for field_info in fields(self)})

    @classmethod
    def unpack(cls, packed_attr: int) -> "PackedFilterSpec":
        return cls(**unpack_a_standard(packed_attr & 0xFFFFFFFFFFFFFFFF))

    def to_debug_dict(self) -> Dict[str, Any]:
        debug_data: Dict[str, Any] = {}
        for field_info in fields(self):
            value = getattr(self, field_info.name)
            if field_info.name in _BOOL_FILTER_FIELDS:
                value = bool(value)
            debug_data[field_info.name] = value

        packed_attr = self.pack()
        debug_data["packed_attr"] = packed_attr
        debug_data["packed_attr_hex"] = f"0x{packed_attr:016X}"
        debug_data["summary"] = format_filter_attr(packed_attr)
        return debug_data


def explain_filter_attr(packed_attr: int) -> Dict[str, Any]:
    return PackedFilterSpec.unpack(packed_attr).to_debug_dict()


def format_filter_attr(packed_attr: int) -> str:
    spec = PackedFilterSpec.unpack(packed_attr)
    parts: List[str] = []

    if spec.target_player:
        parts.append(f"target={_TARGET_PLAYER_LABELS.get(int(spec.target_player), spec.target_player)}")
    if spec.card_type:
        parts.append(f"type={_CARD_TYPE_LABELS.get(int(spec.card_type), spec.card_type)}")
    if spec.group_enabled:
        parts.append(f"group={int(spec.group_id)}")
    if spec.unit_enabled:
        parts.append(f"unit={int(spec.unit_id)}")
        if spec.unit_id >= 60:
            parts.append(f"char3={int(spec.unit_id)}")
    if spec.value_enabled:
        compare_op = "<=" if spec.is_le else ">="
        compare_subject = "cost" if spec.is_cost_type else "value"
        parts.append(f"{compare_subject}{compare_op}{int(spec.value_threshold)}")
    if spec.color_mask:
        colors = [name for idx, name in enumerate(_COLOR_NAMES) if spec.color_mask & (1 << idx)]
        parts.append(f"colors={'/'.join(colors) if colors else spec.color_mask}")
    if spec.char_id_1:
        parts.append(f"char1={int(spec.char_id_1)}")
    if spec.char_id_2:
        parts.append(f"char2={int(spec.char_id_2)}")
    if spec.zone_mask:
        parts.append(f"zone={_ZONE_MASK_LABELS.get(int(spec.zone_mask), spec.zone_mask)}")
    if spec.special_id:
        parts.append(f"special={SPECIAL_ID_LABELS.get(int(spec.special_id), spec.special_id)}")
    
    if spec.zone_mask:
        parts.append(f"zone_mask={ZONE_MASK_LABELS.get(int(spec.zone_mask), spec.zone_mask)}")
    if spec.is_tapped:
        parts.append("status=tapped")
    if spec.has_blade_heart:
        parts.append("has_blade_heart")
    if spec.not_has_blade_heart:
        parts.append("not_has_blade_heart")
    if spec.unique_names:
        parts.append("unique_names")
    if spec.is_setsuna:
        parts.append("setsuna")
    if spec.compare_accumulated:
        parts.append("compare_accumulated")
    if spec.is_optional:
        parts.append("optional")
    if spec.keyword_energy:
        parts.append("keyword_energy")
    if spec.keyword_member:
        parts.append("keyword_member")

    return ", ".join(parts) if parts else "none"
