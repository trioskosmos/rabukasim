"""Legacy parser module kept for compatibility with older imports."""

from __future__ import annotations

import re
from typing import List

from engine.models.ability import Ability, Effect
from engine.models.generated_enums import EffectType, TriggerType


def parse_ability_text(text: str) -> List[Ability]:
    """Parse a minimal trigger/effect block for compatibility tests."""
    trigger = TriggerType.NONE
    effects: list[Effect] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("TRIGGER:"):
            trigger_name = line.split(":", 1)[1].strip().split()[0].upper()
            trigger = getattr(TriggerType, trigger_name, TriggerType.NONE)
            continue
        if upper.startswith("EFFECT:"):
            effect_text = line.split(":", 1)[1].strip()
            match = re.match(r"([A-Z_]+)(?:\(([-\d]+)\))?", effect_text.upper())
            if match:
                effect_name = match.group(1)
                value = int(match.group(2) or 0)
                effect_type = getattr(EffectType, effect_name, EffectType.NONE)
                effects.append(Effect(effect_type, value))

    if trigger == TriggerType.NONE and not effects:
        return []

    return [Ability(raw_text=text, trigger=trigger, effects=effects)]
