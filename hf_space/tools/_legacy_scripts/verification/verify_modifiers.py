import numpy as np

from engine.game.player_state import PlayerState
from engine.game.serializer import get_card_modifiers, serialize_player
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

# 1. Test Player Restriction (Cannot Live)
p = PlayerState(0)
p.cannot_live = True
mods = get_card_modifiers(p, 0, 101, member_db, live_db)
print("Modifiers with cannot_live:", [m["description"] for m in mods])
assert any("Cannot perform Live" in m["description"] for m in mods)

# 2. Test Live Card Modifier
p.cannot_live = False
p.continuous_effects.append(
    {
        "effect": Effect(EffectType.REDUCE_HEART_REQ, value=1, params={"color": "any"}),
        "target_slot": -1,
        "expiry": "TURN_END",
    }
)
# For a live card (slot_idx = -1)
live_mods = get_card_modifiers(p, -1, 201, member_db, live_db)
print("Live Modifiers:", [m["description"] for m in live_mods])
assert any("Reduce Heart Requirement" in m["description"] for m in live_mods)

# 3. Test serialize_player includes live modifiers
p.live_zone = [201]
p.live_zone_revealed = [True]


# Need a mock GameState enough for serialize_player
class MockGS:
    def __init__(self):
        self.member_db = member_db
        self.live_db = live_db
        self.turn_number = 1
        self.current_player = 0

    def get_legal_actions(self):
        return np.zeros(1000)


gs = MockGS()
sp = serialize_player(p, gs, 0)
live_card = sp["live_zone"][0]
print("Serialized Live Card Modifiers:", [m["description"] for m in live_card.get("modifiers", [])])
assert "modifiers" in live_card
assert len(live_card["modifiers"]) > 0

print("Verification SUCCESS")
