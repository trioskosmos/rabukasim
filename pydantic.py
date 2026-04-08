from __future__ import annotations

"""Tiny compatibility shim for the handful of Pydantic APIs this repo uses.

The sandbox that runs the training env does not ship with the real `pydantic`
package, but the frontend/back-end game models only need a very small subset of
its surface area:

- `pydantic.dataclasses.dataclass(...)`
- `BeforeValidator(...)`
- `ConfigDict(...)`
- `field_serializer(...)`
- `TypeAdapter(...).validate_python(...)`

This module keeps those imports working without pulling in the full dependency.
"""

import dataclasses as _dc
from dataclasses import dataclass as _stdlib_dataclass
from enum import Enum
from typing import Any, Callable, TypeVar, get_args, get_origin

import numpy as np


T = TypeVar("T")


def ConfigDict(**kwargs: Any) -> dict[str, Any]:
    return dict(kwargs)


class BeforeValidator:
    def __init__(self, func: Callable[[Any], Any]):
        self.func = func


def field_serializer(*_fields: str, **_kwargs: Any):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return decorator


class _DataclassesNamespace:
    @staticmethod
    def dataclass(_cls: type[T] | None = None, /, **kwargs: Any):
        kwargs.pop("config", None)
        kwargs.pop("slots", None)

        def wrap(cls: type[T]) -> type[T]:
            return _stdlib_dataclass(cls, **kwargs)

        return wrap if _cls is None else wrap(_cls)


dataclasses = _DataclassesNamespace()


def _convert_enum(value: Any, enum_type: type[Enum]) -> Enum:
    if isinstance(value, enum_type):
        return value
    return enum_type(value)


def _convert_dataclass(value: Any, model_type: type[Any]) -> Any:
    if isinstance(value, model_type):
        return value
    if not isinstance(value, dict):
        return value

    from engine.models.ability import Ability, Condition, Cost, Effect
    from engine.models.enums import Group, Unit
    from engine.models.generated_enums import AbilityCostType, ConditionType, EffectType, TargetType, TriggerType

    if model_type is Ability:
        effects = [_convert_dataclass(item, Effect) for item in value.get("effects", [])]
        costs = [_convert_dataclass(item, Cost) for item in value.get("costs", [])]
        conditions = [_convert_dataclass(item, Condition) for item in value.get("conditions", [])]
        return Ability(
            raw_text=value.get("raw_text", ""),
            trigger=_convert_enum(value.get("trigger", 0), TriggerType),
            effects=effects,
            frame_program=value.get("frame_program", {}),
            bytecode=list(value.get("bytecode", [])),
            costs=costs,
            conditions=conditions,
            is_once_per_turn=bool(value.get("is_once_per_turn", False)),
            requires_selection=bool(value.get("requires_selection", False)),
            card_no=value.get("card_no", ""),
        )
    if model_type is Effect:
        return Effect(
            effect_type=_convert_enum(value.get("effect_type", 0), EffectType),
            value=value.get("value", 0),
            target=_convert_enum(value.get("target", 0), TargetType),
            params=dict(value.get("params", {})),
            is_optional=bool(value.get("is_optional", False)),
        )
    if model_type is Cost:
        return Cost(
            type=_convert_enum(value.get("type", 0), AbilityCostType),
            value=int(value.get("value", 0)),
            params=dict(value.get("params", {})),
            is_optional=bool(value.get("is_optional", False)),
        )
    if model_type is Condition:
        return Condition(
            type=_convert_enum(value.get("type", 0), ConditionType),
            value=int(value.get("value", 0)),
            params=dict(value.get("params", {})),
            is_negated=bool(value.get("is_negated", False)),
            attr=int(value.get("attr", 0)),
        )
    if model_type.__name__ == "MemberCard":
        return model_type(
            card_id=int(value.get("card_id", 0)),
            card_no=value.get("card_no", ""),
            name=value.get("name", ""),
            cost=int(value.get("cost", 0)),
            hearts=np.asarray(value.get("hearts", [0] * 7), dtype=np.int32),
            blade_hearts=np.asarray(value.get("blade_hearts", [0] * 7), dtype=np.int32),
            blades=int(value.get("blades", 0)),
            original_text=value.get("original_text", ""),
            original_text_en=value.get("original_text_en", ""),
            groups=[_convert_enum(group, Group) for group in value.get("groups", [])],
            units=[_convert_enum(unit, Unit) for unit in value.get("units", [])],
            abilities=[_convert_dataclass(item, Ability) for item in value.get("abilities", [])],
            img_path=value.get("img_path", ""),
            rare=value.get("rare", "N"),
            ability_text=value.get("ability_text", ""),
            volume_icons=int(value.get("volume_icons", 0)),
            draw_icons=int(value.get("draw_icons", 0)),
            semantic_flags=int(value.get("semantic_flags", 0)),
            ability_flags=int(value.get("ability_flags", 0)),
            synergy_flags=int(value.get("synergy_flags", 0)),
            cost_flags=int(value.get("cost_flags", 0)),
            faq=list(value.get("faq", [])),
        )
    if model_type.__name__ == "LiveCard":
        return model_type(
            card_id=int(value.get("card_id", 0)),
            card_no=value.get("card_no", ""),
            name=value.get("name", ""),
            score=int(value.get("score", 0)),
            required_hearts=np.asarray(value.get("required_hearts", [0] * 7), dtype=np.int32),
            original_text=value.get("original_text", ""),
            original_text_en=value.get("original_text_en", ""),
            abilities=[_convert_dataclass(item, Ability) for item in value.get("abilities", [])],
            groups=[_convert_enum(group, Group) for group in value.get("groups", [])],
            units=[_convert_enum(unit, Unit) for unit in value.get("units", [])],
            img_path=value.get("img_path", ""),
            rare=value.get("rare", "N"),
            ability_text=value.get("ability_text", ""),
            volume_icons=int(value.get("volume_icons", 0)),
            draw_icons=int(value.get("draw_icons", 0)),
            semantic_flags=int(value.get("semantic_flags", 0)),
            synergy_flags=int(value.get("synergy_flags", 0)),
            blade_hearts=np.asarray(value.get("blade_hearts", [0] * 7), dtype=np.int32),
            faq=list(value.get("faq", [])),
        )
    if model_type.__name__ == "EnergyCard":
        return model_type(
            card_id=int(value.get("card_id", 0)),
            original_text=value.get("original_text", ""),
            original_text_en=value.get("original_text_en", ""),
            card_no=value.get("card_no", ""),
            name=value.get("name", "Energy"),
            img_path=value.get("img_path", ""),
            ability_text=value.get("ability_text", ""),
            rare=value.get("rare", "N"),
        )
    return model_type(**value)


class TypeAdapter:
    def __init__(self, model: type[Any]):
        self.model = model

    def validate_python(self, value: Any) -> Any:
        return _convert_dataclass(value, self.model)

    def dump_python(self, value: Any, *args: Any, **kwargs: Any) -> Any:
        """Serialize a supported model into JSON-compatible Python data."""

        exclude = kwargs.get("exclude")
        return _apply_exclude(_to_jsonable(value), exclude)


def _to_jsonable(value: Any) -> Any:
    if _dc.is_dataclass(value):
        return {field.name: _to_jsonable(getattr(value, field.name)) for field in _dc.fields(value)}
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(item) for item in value]
    return value


def _apply_exclude(value: Any, exclude: Any) -> Any:
    if not exclude:
        return value

    if isinstance(value, list):
        item_exclude = exclude.get("__all__") if isinstance(exclude, dict) else None
        return [_apply_exclude(item, item_exclude) for item in value]

    if not isinstance(value, dict):
        return value

    if exclude is True:
        return None

    if not isinstance(exclude, dict):
        return value

    result: dict[str, Any] = {}
    shared_exclude = exclude.get("__all__")
    for key, item in value.items():
        if key in exclude:
            sub_exclude = exclude[key]
            if sub_exclude is True:
                continue
            result[key] = _apply_exclude(item, sub_exclude)
            continue
        if shared_exclude is not None:
            result[key] = _apply_exclude(item, shared_exclude)
            continue
        result[key] = item
    return result
