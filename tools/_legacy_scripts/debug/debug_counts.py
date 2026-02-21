from engine.game.game_state import initialize_game


def _find_id(game, cno):
    for k, v in game.member_db.items():
        if v.card_no == cno:
            return k
    return None


game = initialize_game(deck_type="training")

cards = [
    "PL!-PR-007-PR",
    "PL!-PR-009-PR",
    "PL!N-bp3-017-N",
    "PL!N-bp4-004-R",
    "PL!N-bp4-004-SEC",
    "PL!N-bp4-005-P",
    "PL!N-bp4-005-R",
    "PL!S-bp3-012-N",
    "PL!S-bp3-017-N",
    "PL!-bp3-002-P",
    "PL!-bp3-002-R",
    "PL!N-bp3-023-N",
    "PL!N-bp4-004-P",
    "PL!N-bp4-004-P＋",
    "PL!N-bp4-004-R＋",
    "PL!N-bp4-001-R＋",
]

for cno in cards:
    cid = _find_id(game, cno)
    if cid:
        card = game.member_db[cid]
        print(f"{cno}: Ability0 Conditions={len(card.abilities[0].conditions)}")
        if len(card.abilities) > 1:
            print(f"{cno}: Ability1 Conditions={len(card.abilities[1].conditions)}")
    else:
        print(f"{cno}: NOT FOUND")
