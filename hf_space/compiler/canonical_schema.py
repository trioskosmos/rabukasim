from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from engine.models.generated_metadata import COSTS, CONDITIONS, OPCODES, TRIGGERS, TARGETS, ZONES


KNOWN_TRIGGERS = frozenset(TRIGGERS.keys())
KNOWN_COSTS = frozenset(COSTS.keys())
KNOWN_EFFECTS = frozenset(OPCODES.keys())
KNOWN_CONDITIONS = frozenset(CONDITIONS.keys())
KNOWN_TARGETS = frozenset(TARGETS.keys())
KNOWN_ZONES = frozenset(ZONES.keys())

ALLOWED_STEP_KINDS = frozenset(
    {
        "cost",
        "condition",
        "effect",
        "select",
        "assign",
        "if",
        "choose_one",
        "repeat",
    }
)

RESERVED_BINDINGS = frozenset(
    {
        "SELF",
        "PLAYER",
        "OPPONENT",
        "TARGET",
        "TARGET_MEMBER",
        "TARGET_STAGE",
        "TARGET_DISCARD",
    }
)

ALLOWED_REVIEW_MARKERS = frozenset(
    {
        "needs_review",
        "unknown_operand",
        "unknown_filter_fragment",
        "unknown_binding",
        "unsupported_pattern",
    }
)


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReferenceExpr(StrictBaseModel):
    kind: Literal["reference"] = "reference"
    name: str


class LiteralExpr(StrictBaseModel):
    kind: Literal["literal"] = "literal"
    value: Union[int, bool, str]


class BinaryExpr(StrictBaseModel):
    kind: Literal["binary"] = "binary"
    op: Literal["add", "sub", "eq", "gt", "lt", "ge", "le"]
    left: "ValueExpr"
    right: "ValueExpr"


ValueExpr = Annotated[Union[ReferenceExpr, LiteralExpr, BinaryExpr], Field(discriminator="kind")]


class FilterClause(StrictBaseModel):
    field: str
    op: Literal["eq", "ne", "gt", "lt", "ge", "le", "contains", "in", "exists"]
    value: Optional[Union[int, bool, str, List[Union[int, str]]]] = None


class FilterSpec(StrictBaseModel):
    all_of: List[FilterClause] = Field(default_factory=list)
    any_of: List[FilterClause] = Field(default_factory=list)
    review_markers: List[str] = Field(default_factory=list)


class StepBase(StrictBaseModel):
    kind: str
    notes: List[str] = Field(default_factory=list)
    review_markers: List[str] = Field(default_factory=list)


class CostStep(StepBase):
    kind: Literal["cost"] = "cost"
    op: str
    count: Optional[ValueExpr] = None
    optional: bool = False
    target: Optional[str] = None
    zone: Optional[str] = None
    filter: Optional[FilterSpec] = None
    store_as: Optional[str] = None


class ConditionStep(StepBase):
    kind: Literal["condition"] = "condition"
    op: str
    args: Dict[str, Union[ValueExpr, int, bool, str, List[Union[int, str]]]] = Field(default_factory=dict)
    negated: bool = False
    store_as: Optional[str] = None


class EffectStep(StepBase):
    kind: Literal["effect"] = "effect"
    op: str
    count: Optional[ValueExpr] = None
    target: Optional[str] = None
    zone: Optional[str] = None
    duration: Optional[str] = None
    filter: Optional[FilterSpec] = None
    store_as: Optional[str] = None
    args: Dict[str, Union[ValueExpr, int, bool, str, List[Union[int, str]]]] = Field(default_factory=dict)


class SelectStep(StepBase):
    kind: Literal["select"] = "select"
    op: str
    count: Optional[ValueExpr] = None
    target: Optional[str] = None
    zone: Optional[str] = None
    filter: Optional[FilterSpec] = None
    store_as: str


class AssignStep(StepBase):
    kind: Literal["assign"] = "assign"
    store_as: str
    expr: ValueExpr


class IfStep(StepBase):
    kind: Literal["if"] = "if"
    condition: ConditionStep
    then: List["CanonicalStep"]
    else_: List["CanonicalStep"] = Field(default_factory=list, alias="else")


class ChoiceBranch(StrictBaseModel):
    label: Optional[str] = None
    icon: Optional[str] = None
    steps: List["CanonicalStep"]


class ChooseOneStep(StepBase):
    kind: Literal["choose_one"] = "choose_one"
    choose: Literal["one"] = "one"
    target: Optional[str] = None
    branches: List[ChoiceBranch]
    store_as: Optional[str] = None


class RepeatStep(StepBase):
    kind: Literal["repeat"] = "repeat"
    times: Optional[ValueExpr] = None
    while_condition: Optional[ConditionStep] = None
    body: List["CanonicalStep"]


CanonicalStep = Annotated[
    Union[CostStep, ConditionStep, EffectStep, SelectStep, AssignStep, IfStep, ChooseOneStep, RepeatStep],
    Field(discriminator="kind"),
]


class CanonicalAbilityModel(StrictBaseModel):
    schema_version: Literal["v0"] = "v0"
    trigger: str
    once_per_turn: bool = False
    pseudocode: str = ""
    raw_text: str = ""
    confidence: Literal["high", "medium", "low"] = "medium"
    review_reasons: List[str] = Field(default_factory=list)
    steps: List[CanonicalStep]


CanonicalAbilityAdapter = TypeAdapter(CanonicalAbilityModel)


def parse_canonical_ability_model(data: Dict[str, Any]) -> CanonicalAbilityModel:
    return CanonicalAbilityAdapter.validate_python(data)


ReferenceExpr.model_rebuild()
LiteralExpr.model_rebuild()
BinaryExpr.model_rebuild()
ConditionStep.model_rebuild()
IfStep.model_rebuild()
ChoiceBranch.model_rebuild()
ChooseOneStep.model_rebuild()
RepeatStep.model_rebuild()
CanonicalAbilityModel.model_rebuild()
