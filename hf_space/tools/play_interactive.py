import os
import random
import sys
import traceback

import numpy as np

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.data_loader import CardDataLoader
from game.game_state import GameState


def generate_random_decks(member_ids, live_ids):
    """Generate two random decks: 48 members, 12 lives each"""
    m_pool = list(member_ids)
    l_pool = list(live_ids)

    deck1_m = [random.choice(m_pool) for _ in range(48)]
    deck1_l = [random.choice(l_pool) for _ in range(12)]

    deck2_m = [random.choice(m_pool) for _ in range(48)]
    deck2_l = [random.choice(l_pool) for _ in range(12)]

    return (deck1_m, deck1_l), (deck2_m, deck2_l)


def print_separator():
    print("\n" + "=" * 60)


def print_header(title):
    print(f"\n--- {title} ---")


def print_state(state: GameState):
    p = state.active_player
    opp = state.inactive_player

    print_separator()
    print(f" TURN: {state.turn_number} | PHASE: {state.phase.name} | ACTIVE: P{p.player_id}")
    print(f" SCORE: P0: {len(state.players[0].success_lives)} | P1: {len(state.players[1].success_lives)}")
    print_separator()

    # OPPONENT STAGE (Visible but simplified)
    print(
        f" OPPONENT (P{opp.player_id}) | Hand: {len(opp.hand)} | Deck: {len(opp.main_deck)} | Energy: {len(opp.energy_zone)}"
    )
    print(" STAGE (Mirrored):")
    for i in reversed(range(3)):
        cid = opp.stage[i]
        status = "[WAIT]" if opp.tapped_members[i] else "[ACT]"
        if cid >= 0:
            m = GameState.member_db[cid]
            print(f"   Area {i}: {m.name} {status} (Cost:{m.cost}, Power:{np.sum(m.hearts)})")
        else:
            print(f"   Area {i}: [EMPTY]")

    print("-" * 60)

    # PLAYER STAGE
    print(f" PLAYER (P{p.player_id})")
    print(" STAGE:")
    for i in range(3):
        cid = p.stage[i]
        status = "[WAIT]" if p.tapped_members[i] else "[ACT]"
        if cid >= 0:
            m = GameState.member_db[cid]
            print(f"   Area {i}: {m.name} {status} (Cost:{m.cost}, Power:{np.sum(m.hearts)})")
        else:
            print(f"   Area {i}: [EMPTY]")

    print(f"\n ENERGY: {p.count_untapped_energy()}/{len(p.energy_zone)} Untapped")

    # HAND
    print(f"\n HAND ({len(p.hand)} cards):")
    for i, cid in enumerate(p.hand):
        if cid in GameState.member_db:
            m = GameState.member_db[cid]
            print(f"   [{i}] {m.name} (Cost: {m.cost}, H: {m.hearts})")
        else:
            print(f"   [{i}] Card ID: {cid}")

    if state.pending_choices:
        choice_type, params = state.pending_choices[0]
        print(f"\n >>> PENDING CHOICE: {choice_type} ({params})")


def get_legal_actions_desc(state: GameState):
    mask = state.get_legal_actions()
    actions = [i for i, val in enumerate(mask) if val]
    descs = []

    for a in actions:
        desc = ""
        if a == 0:
            desc = "Pass / Next Phase"
        elif 1 <= a <= 180:
            # Play Member
            idx = (a - 1) // 3
            area = (a - 1) % 3
            if idx < len(state.active_player.hand):
                cid = state.active_player.hand[idx]
                name = GameState.member_db[cid].name
                desc = f"Play {name} to Area {area}"
            else:
                desc = f"Play Hand[{idx}] to Area {area} (Invalid Index?)"
        elif 181 <= a <= 200:
            idx = a - 181
            desc = f"Auto-Play/Effect Target Hand[{idx}]"
        elif 201 <= a <= 260:
            idx = a - 201
            desc = "Activated Ability of Member at Area ?"  # TODO decoding
        elif 270 <= a <= 279:
            desc = f"Modal Choice Option {a - 270}"
        elif 280 <= a <= 285:
            colors = ["Red", "Blue", "Green", "Yellow", "Purple", "Pink"]
            desc = f"Select Color: {colors[a - 280]}"
        else:
            desc = f"Action ID {a}"

        descs.append((a, desc))
    return descs


def run_cli():
    # Load data
    loader = CardDataLoader("data/cards.json")
    m_db, l_db = loader.load()
    GameState.member_db = m_db
    GameState.live_db = l_db
    print(f"Loaded {len(m_db)} members and {len(l_db)} lives.")

    # Init
    (d1_m, d1_l), (d2_m, d2_l) = generate_random_decks(m_db.keys(), l_db.keys())
    state = GameState()
    state.players[0].main_deck = d1_m
    state.players[0].live_deck = d1_l
    state.players[1].main_deck = d2_m
    state.players[1].live_deck = d2_l

    # Initial Draw
    for _ in range(5):
        state.players[0].hand.append(state.players[0].main_deck.pop())
        state.players[1].hand.append(state.players[1].main_deck.pop())

    # Game Loop
    while True:
        try:
            print_state(state)

            # Show options
            legal = get_legal_actions_desc(state)
            print("\nLegal Actions:")
            for aid, desc in legal:
                print(f"  [{aid}] {desc}")

            print("\nOptions: [ID] to act, 'r' to force-run specific ID, 'exec <code>' for god mode, 'q' to quit")
            cmd = input("\nCommand > ").strip()

            if not cmd:
                continue

            if cmd.lower() == "q":
                break

            elif cmd.lower().startswith("exec "):
                # GOD MODE: Execute arbitrary python
                code = cmd[5:]
                try:
                    # Provide 'state' and 'p' (active player) to the context
                    exec(code, {"state": state, "p": state.active_player, "np": np, "m_db": m_db}, locals())
                    print("Executed.")
                except Exception as e:
                    print(f"Exec Error: {e}")
                    traceback.print_exc()

            elif cmd.lower().startswith("r "):
                # forceful run
                try:
                    aid = int(cmd.split()[1])
                    state = state.step(aid)
                except Exception as e:
                    print(f"Force Run Error: {e}")

            else:
                # Normal move
                try:
                    aid = int(cmd)
                    if any(a[0] == aid for a in legal):
                        state = state.step(aid)
                    else:
                        print("Illegal action! Use 'r <id>' to force it if you really want to.")
                except ValueError:
                    print("Invalid input.")

        except Exception as e:
            print(f"Loop Error: {e}")
            traceback.print_exc()
            break


if __name__ == "__main__":
    run_cli()
