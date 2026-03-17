from engine.game.player_state import PlayerState
from engine.models.ability import Effect, EffectType


def test_get_member_cost():
    p = PlayerState(0)

    # Mock DB
    class MockMember:
        def __init__(self, cost):
            self.cost = cost

    db = {1: MockMember(5)}

    # Test base cost
    cost = p.get_member_cost(1, db)
    print(f"Base Cost: {cost}")
    assert cost == 5, f"Expected 5, got {cost}"

    # Test reduction
    p.continuous_effects.append({"effect": Effect(EffectType.REDUCE_COST, value=2)})

    cost_reduced = p.get_member_cost(1, db)
    print(f"Reduced Cost: {cost_reduced}")
    assert cost_reduced == 3, f"Expected 3, got {cost_reduced}"

    print("Verification Passed!")


if __name__ == "__main__":
    test_get_member_cost()
