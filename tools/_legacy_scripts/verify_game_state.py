import os
import sys

sys.path.append(os.getcwd())
from engine.game.game_state import GameState, initialize_game

# Ensure we have a fresh load
GameState.member_db = {}
GameState.live_db = {}

game = initialize_game(deck_type="training")

cno_target = "PL!-sd1-007-SD"
cid = None
for k, v in game.member_db.items():
    if v.card_no == cno_target:
        cid = k
        break

print(f"Target: {cno_target}")
if cid is not None:
    card = game.member_db[cid]
    print(f"ID: {cid}")
    print(f"Name: {card.name}")
    print(f"Ability Text: {card.ability_text}")
    print(f"Abilities count: {len(card.abilities)}")
    if card.abilities:
        ab = card.abilities[0]
        print(f"  Trigger: {ab.trigger}")
        print(f"  Conditions: {len(ab.conditions)}")
        for i, c in enumerate(ab.conditions):
            print(f"    C{i} type: {c.type}")
        print(f"  Effects: {len(ab.effects)}")
        for i, e in enumerate(ab.effects):
            print(f"    E{i} type: {e.effect_type}")
else:
    print("Card not found!")
