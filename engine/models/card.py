from dataclasses import field
from typing import Annotated, Any, Dict, List

import numpy as np
import pydantic
from pydantic import BeforeValidator, ConfigDict, field_serializer

from engine.models.ability import Ability
from engine.models.enums import Group, Unit, ensure_group_list, ensure_unit_list


def ensure_ndarray(v: Any) -> Any:
    """Validator to convert list/dict to numpy array"""
    if isinstance(v, list):
        return np.array(v, dtype=np.int32)
    return v


@pydantic.dataclasses.dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class MemberCard:
    """Represents a member card with all attributes"""

    card_id: int
    card_no: str
    name: str
    cost: int
    hearts: Annotated[
        np.ndarray, BeforeValidator(ensure_ndarray)
    ]  # Shape (7,) for each color count (0-5: colors, 6: any/unassigned)
    blade_hearts: Annotated[
        np.ndarray, BeforeValidator(ensure_ndarray)
    ]  # Shape (7,) blade hearts by color (Index 6 = ALL)
    blades: int
    groups: Annotated[List[Group], BeforeValidator(ensure_group_list)] = field(default_factory=list)
    units: Annotated[List[Unit], BeforeValidator(ensure_unit_list)] = field(default_factory=list)
    abilities: List[Ability] = field(default_factory=list)
    img_path: str = ""
    rare: str = "N"  # Default to Normal (updated from rarity to match tests)
    # Rule 2.12: カードテキスト (Card Text)
    ability_text: str = ""
    original_text: str = ""
    original_text_en: str = ""
    # Rule 2.7: ブレードハート (Blade Heart Icons)
    volume_icons: int = 0
    draw_icons: int = 0
    semantic_flags: int = 0
    ability_flags: int = 0
    synergy_flags: int = 0
    cost_flags: int = 0
    faq: List[Dict[str, Any]] = field(default_factory=list)

    @field_serializer("hearts", "blade_hearts")
    def serialize_array(self, v: np.ndarray, _info):
        return v.tolist()

    def total_hearts(self) -> int:
        return int(np.sum(self.hearts))

    def total_blade_hearts(self) -> int:
        return int(np.sum(self.blade_hearts))


@pydantic.dataclasses.dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class LiveCard:
    """Represents a live/song card"""

    card_id: int
    card_no: str
    name: str
    score: int
    required_hearts: Annotated[
        np.ndarray, BeforeValidator(ensure_ndarray)
    ]  # Shape (7,) required hearts by color (6 colors + any)
    abilities: List[Ability] = field(default_factory=list)
    groups: Annotated[List[Group], BeforeValidator(ensure_group_list)] = field(default_factory=list)
    units: Annotated[List[Unit], BeforeValidator(ensure_unit_list)] = field(default_factory=list)
    img_path: str = ""
    rare: str = "N"
    ability_text: str = ""
    original_text: str = ""
    original_text_en: str = ""
    volume_icons: int = 0
    draw_icons: int = 0
    semantic_flags: int = 0
    synergy_flags: int = 0
    blade_hearts: Annotated[np.ndarray, BeforeValidator(ensure_ndarray)] = field(
        default_factory=lambda: np.zeros(7, dtype=np.int32)
    )
    faq: List[Dict[str, Any]] = field(default_factory=list)

    @field_serializer("required_hearts", "blade_hearts")
    def serialize_array(self, v: np.ndarray, _info):
        return v.tolist()

    def total_required(self) -> int:
        return int(np.sum(self.required_hearts[:6]))  # Exclude star/any

    def total_blade_hearts(self) -> int:
        return int(np.sum(self.blade_hearts))


@pydantic.dataclasses.dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class EnergyCard:
    """Represents an energy card with metadata"""

    card_id: int
    card_no: str = ""
    name: str = "Energy"
    img_path: str = ""
    ability_text: str = ""
    original_text: str = ""
    original_text_en: str = ""
    rare: str = "N"
