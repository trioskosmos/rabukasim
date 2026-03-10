import sys

sys.path.append(".")
from engine.models.ability import Ability, ConditionType, Effect, EffectType, TargetType, TriggerType

eff1 = Effect(EffectType.DRAW, 2, ConditionType.NONE, TargetType.PLAYER, {})
eff2 = Effect(
    EffectType.MOVE_TO_DISCARD, 1, ConditionType.NONE, TargetType.PLAYER, {"source": "HAND", "destination": "discard"}
)

ab = Ability("test", TriggerType.ON_LIVE_SUCCESS, [eff1, eff2])
ab.instructions = ab.effects

try:
    print(ab.compile())
except Exception:
    import traceback

    traceback.print_exc()
