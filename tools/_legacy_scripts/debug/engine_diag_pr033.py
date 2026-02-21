import time

from engine.game.game_state import initialize_game

print("Initializing game...")
start = time.time()
state = initialize_game(use_real_data=True)
print(f"Game initialized in {time.time() - start:.2f} seconds.")

print("Running manual PR-033 test logic...")
p0 = state.players[0]
p0.main_deck = [100, 101, 102, 103, 104]
card_id = 473  # PL!S-PR-033-PR
member = state.member_db[card_id]
ability = member.abilities[0]

# Trigger On Play
state.triggered_abilities.append((0, ability, {"card_id": card_id}))
state._process_rule_checks()

print(f"Looked cards: {state.looked_cards}")
assert state.looked_cards == [100, 101, 102]
assert len(state.pending_choices) > 0
choice_type, params = state.pending_choices[0]
print(f"Pending choice: {choice_type} ({params['reason']})")
assert choice_type == "SELECT_FROM_LIST"
assert params["reason"] == "look_and_reorder"

# Select 100
state._handle_choice(600)
# Select 102
state._handle_choice(601)
# Pass
state._handle_choice(0)

print(f"Discard after pass: {p0.discard}")
assert 101 in p0.discard

print(f"Choice after pass: {state.pending_choices[0][0]}")
assert state.pending_choices[0][0] == "SELECT_ORDER"

# Select order: 102, 100
state._handle_choice(701)
state._handle_choice(700)

print(f"Final deck: {p0.main_deck[:5]}")
assert p0.main_deck == [102, 100, 103, 104]

print("MANUAL PR-033 VERIFICATION SUCCESSFUL!")
