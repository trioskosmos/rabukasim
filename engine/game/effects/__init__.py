"""Small effect-resolution helpers split out of the main game-state mixin."""

from engine.game.effects.metadata import resolve_source_metadata
from engine.game.effects.costs import can_pay_costs, pay_costs
from engine.game.effects.choices import (
    is_cost_payment_choice,
    normalize_choice_metadata,
    store_choice_answer,
)
from engine.game.effects.movement import move_member


