import numpy as np

from engine.game.player_state import PlayerState
from engine.game.serializer import get_card_modifiers
from engine.models.ability import Effect, EffectType
from engine.models.card import LiveCard, MemberCard

# Mock DBs
member_db = {
    101: MemberCard(
        card_id=101,
        card_no="M-01",
        name="Member A",
        cost=1,
        blades=1,
        hearts=np.array([1, 0, 0, 0, 0, 0, 0]),
        blade_hearts=np.array([0, 0, 0, 0, 0, 0, 0]),
        img_path="a.png",
    )
}
live_db = {
    201: LiveCard(
        card_id=201,
        card_no="L-01",
        name="Live A",
        score=1,
        required_hearts=np.array([0, 0, 0, 0, 0, 0, 1]),
        img_path="l.png",
    )
}

p = PlayerState(player_id=0)
p.continuous_effects.append(
    {
        "effect": Effect(EffectType.REDUCE_HEART_REQ, value=1, params={"color": "any"}),
        "target_slot": -1,
        "expiry": "TURN_END",
    }
)

print(f"Debug: continuous_effects length = {len(p.continuous_effects)}")
for i, ce in enumerate(p.continuous_effects):
    print(f"Debug: ce[{i}] = {ce}")
    eff = ce["effect"]
    print(f"Debug: eff.effect_type = {eff.effect_type} (type: {type(eff.effect_type)})")
    print(f"Debug: EffectType.REDUCE_HEART_REQ = {EffectType.REDUCE_HEART_REQ}")

live_mods = get_card_modifiers(p, -1, 201, member_db, live_db)
print("Live Modifiers:", live_mods)

if not live_mods:
    print("FAILURE: live_mods is empty")
else:
    print("SUCCESS: live_mods found")
