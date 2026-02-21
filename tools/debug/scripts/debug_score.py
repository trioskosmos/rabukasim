from engine.game.player_state import PlayerState

try:
    p = PlayerState(0)
    print(f"Has score attr: {hasattr(p, 'score')}")
    print(f"Score: {p.score}")
except Exception as e:
    print(f"Error: {e}")
