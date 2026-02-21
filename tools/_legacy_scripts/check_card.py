from engine.game.game_state import initialize_game

g = initialize_game(deck_type="training")
c = [c for k, c in g.member_db.items() if c.card_no == "PL!N-bp3-013-N"][0]
print("RAW TEXT:")
print(c.abilities[0].raw_text)
print()
print("EFFECTS:")
for e in c.abilities[0].effects:
    print(f"  {e.effect_type.name}: value={e.value}")
