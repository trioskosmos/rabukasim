from __future__ import annotations

import re
from typing import List

from engine.models.ability import ConditionType, Effect, EffectType, TargetType


def parse_grant_ability_effect(p: str) -> List[Effect]:
    grant_match = re.search(r'GRANT_ABILITY\((.*?),\s*"(.*?)"\)', p)
    if not grant_match:
        return []

    target_str, ability_str = grant_match.groups()
    params = {"target_str": target_str, "ability_text": ability_str}
    target = TargetType.PLAYER
    if "MEMBER" in target_str:
        target = TargetType.MEMBER_SELECT
    return [Effect(EffectType.GRANT_ABILITY, 0, ConditionType.NONE, target, params)]