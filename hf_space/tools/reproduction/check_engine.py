import engine_rust


def check():
    gs = engine_rust.PyGameState(engine_rust.PyCardDatabase('{"members":{},"lives":{},"effects":{},"conditions":{}}'))
    print(f"Ping: {gs.ping()}")

    # Check PyPlayerState
    p = gs.get_player(0)
    print(f"Player has revealed_cards: {hasattr(p, 'revealed_cards')}")


if __name__ == "__main__":
    check()
