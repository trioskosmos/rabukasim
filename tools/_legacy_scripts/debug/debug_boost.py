"""Minimal debug to test BOOST_SCORE directly."""

from engine.game.game_state import initialize_game
from engine.models.ability import Effect, EffectType, TargetType


def test():
    gs = initialize_game(use_real_data=True)
    p1 = gs.players[0]

    print(f"Before: p1.live_score_bonus = {p1.live_score_bonus}")

    # Create a BOOST_SCORE effect directly
    effect = Effect(EffectType.BOOST_SCORE, 1, TargetType.SELF, {})

    # Push it to pending_effects with context
    from engine.models.ability import ResolvingEffect

    gs.pending_effects.append(ResolvingEffect(effect, 1001, 1, 1))

    print(f"Pending effects: {len(gs.pending_effects)}")
    print(f"Effect type: {gs.pending_effects[0].effect.effect_type}")

    # Set context
    gs.current_player = 0
    ctx = {"source_player_id": 0}

    # Resolve it
    gs._resolve_pending_effect(0, context=ctx)

    print(f"After: p1.live_score_bonus = {p1.live_score_bonus}")
    assert p1.live_score_bonus == 1, f"Expected 1, got {p1.live_score_bonus}"
    print("PASS")


if __name__ == "__main__":
    test()
