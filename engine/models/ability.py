"""Simple card ability models for a card game.

ABOUT: This module contains plain dataclasses for card abilities.
No bytecode. No bit packing. No complex IR. Just data.

DATA MODEL:
-----------
Ability
  ├── raw_text: str          - Original Japanese text
  ├── trigger: TriggerType   - When does this activate?
  ├── effects: List[Effect]  - What happens when activated?
  ├── conditions: List[Condition] - Requirements to activate
  ├── costs: List[Cost]       - What you must pay to activate
  └── is_once_per_turn: bool - Limitation flag

Effect
  ├── effect_type: EffectType - What kind of effect (DRAW, SEARCH, etc.)
  ├── value: int              - Numeric value (usually)
  ├── target: TargetType      - Who/what does this affect?
  └── params: Dict            - Additional context (zone, count, etc.)

Condition
  ├── type: ConditionType    - What to check (HAS_COLOR, COUNT_GROUP, etc.)
  ├── value: int              - Threshold/count to compare
  └── is_negated: bool        - Is this a "unless" condition?

Cost
  ├── type: AbilityCostType    - ENERGY, DISCARD_HAND, TAP_SELF, etc.
  └── value: int              - How much (energy count, cards to discard, etc.)

USAGE:
------
    ability = Ability(
        raw_text="{{スポットlight}} 手札を1枚控え室に置く：",
        trigger=TriggerType.ACTIVATED,
        effects=[Effect(EffectType.DRAW, value=2)],
        costs=[Cost(AbilityCostType.DISCARD_HAND, value=1)]
    )
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .generated_enums import AbilityCostType, ConditionType, EffectType, TargetType, TriggerType


@dataclass
class Condition:
    """A condition that must be met for an ability to activate."""
    type: ConditionType
    value: int = 0
    params: Dict[str, Any] = field(default_factory=dict)
    is_negated: bool = False


@dataclass  
class Effect:
    """An effect that modifies game state."""
    effect_type: EffectType
    value: int = 0
    target: TargetType = TargetType.SELF
    params: Dict[str, Any] = field(default_factory=dict)
    is_optional: bool = False


@dataclass
class Cost:
    """A cost to pay to activate an ability."""
    type: AbilityCostType
    value: int = 0
    params: Dict[str, Any] = field(default_factory=dict)
    is_optional: bool = False


@dataclass
class Ability:
    """An ability on a card with trigger, costs, conditions, and effects."""
    raw_text: str
    trigger: TriggerType
    effects: List[Effect]
    frame_program: Dict[str, Any] = field(default_factory=dict)
    bytecode: List[int] = field(default_factory=list)
    costs: List[Cost] = field(default_factory=list)
    conditions: List[Condition] = field(default_factory=list)
    is_once_per_turn: bool = False
    requires_selection: bool = False
    card_no: str = ""

    def __post_init__(self):
        """Ensure all fields are properly initialized."""
        if self.effects is None:
            self.effects = []
        if self.costs is None:
            self.costs = []
        if self.conditions is None:
            self.conditions = []

    def compile(self):
        """Compatibility shim for legacy callers that expect an eager compile step."""
        return self.to_frame_program()

    def to_frame_program(self):
        """Return authored frame instructions when present, otherwise synthesize a minimal program."""
        instructions = self.frame_program.get("instructions") if isinstance(self.frame_program, dict) else None
        if instructions:
            return instructions

        instructions = []
        for cost in self.costs:
            instructions.append(cost)
        for condition in self.conditions:
            instructions.append(condition)
        for effect in self.effects:
            instructions.append(effect)
        return instructions


@dataclass
class ResolvingEffect:
    """An effect currently being resolved."""
    effect: Effect
    source_card_id: int
    step_index: int = 0
    total_steps: int = 1
