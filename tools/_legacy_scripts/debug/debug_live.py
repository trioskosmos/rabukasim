"""Debug script to trace live card ability resolution."""

from engine.game.enums import Phase
from engine.game.game_state import initialize_game


def test():
    gs = initialize_game(use_real_data=True)
    p1 = gs.players[0]

    target_id = 1001  # PL!-bp3-019-L
    second_muse = 1025  # PL!-sd1-020-SD

    p1.live_zone = [target_id, second_muse]
    p1.live_zone_revealed = [True, True]

    gs.phase = Phase.PERFORMANCE_P1
    gs.current_player = 0
    gs.first_player = 0

    print(f"Before: p1.live_score_bonus = {p1.live_score_bonus}")
    print(f"gs.fast_mode = {getattr(gs, 'fast_mode', 'NOT SET')}")

    gs.step(0)  # Performance

    print(f"After step: triggered_abilities = {len(gs.triggered_abilities)}")
    print(f"After step: pending_effects = {len(gs.pending_effects)}")
    print(f"After step: pending_choices = {len(gs.pending_choices)}")

    while gs.triggered_abilities or gs.pending_effects:
        if gs.triggered_abilities:
            pid, ab, ctx = gs.triggered_abilities.pop(0)
            print(f"Processing ability for player {pid}: {ab.raw_text[:50]}")
            print(f"  Conditions: {[c.type for c in ab.conditions]}")
            print(f"  Effects: {[(e.effect_type, e.value) for e in ab.effects]}")
            print(f"  Effect count: {len(ab.effects)}")
            gs._play_automatic_ability(pid, ab, ctx)
            print(f"  After: p1.live_score_bonus = {p1.live_score_bonus}")
        elif gs.pending_effects:
            top = gs.pending_effects[0]
            print(f"Resolving effect: {type(top)} = {top}")
            gs._resolve_pending_effect(0)
            print(f"  After: p1.live_score_bonus = {p1.live_score_bonus}")

    print(f"Final: p1.live_score_bonus = {p1.live_score_bonus}")
    assert p1.live_score_bonus > 0, f"FAIL: bonus = {p1.live_score_bonus}"
    print("PASS")


if __name__ == "__main__":
    test()
