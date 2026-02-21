import argparse
import os
import random
import sys

import numpy as np

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.data_loader import CardDataLoader
from game.game_state import GameState, initialize_game
from headless_runner import RandomAgent, create_easy_cards


def print_separator():
    print("\n" + "=" * 60)


def print_header(title):
    print(f"\n--- {title} ---")


def get_color_name(idx):
    colors = ["Red", "Blue", "Green", "Yellow", "Purple", "Pink", "Any"]
    if 0 <= idx < len(colors):
        return colors[idx]
    return "Unknown"


def print_state(state: GameState, user_pid: int):
    # Always show from perspective of user
    user = state.players[user_pid]
    ai = state.players[1 - user_pid]

    print_separator()
    print(f" TURN: {state.turn_number} | PHASE: {state.phase.name} | ACTIVE: P{state.current_player}")
    print(f" SCORE: YOU (P{user_pid}): {len(user.success_lives)} | AI (P{1 - user_pid}): {len(ai.success_lives)}")
    print_separator()

    # AI STAGE
    print(f" AI (P{ai.player_id}) | Hand: {len(ai.hand)} | Deck: {len(ai.main_deck)} | Energy: {len(ai.energy_zone)}")
    print(" STAGE:")
    for i in reversed(range(3)):
        cid = ai.stage[i]
        status = "[WAIT]" if ai.tapped_members[i] else "[ACT]"
        if cid >= 0:
            m = GameState.member_db[cid]
            print(f"   Area {i}: {m.name} {status} (Cost:{m.cost}, H:{m.hearts})")
        else:
            print(f"   Area {i}: [EMPTY]")

    print("-" * 60)

    # USER STAGE
    print(f" YOU (P{user.player_id})")
    print(" STAGE:")
    for i in range(3):
        cid = user.stage[i]
        status = "[WAIT]" if user.tapped_members[i] else "[ACT]"
        if cid >= 0:
            m = GameState.member_db[cid]
            print(f"   Area {i}: {m.name} {status} (Cost:{m.cost}, H:{m.hearts})")
        else:
            print(f"   Area {i}: [EMPTY]")

    print(f"\n ENERGY: {user.count_untapped_energy()}/{len(user.energy_zone)} Untapped")

    # LIVES
    if user.live_zone:
        print("\n YOUR PENDING LIVES:")
        for lid in user.live_zone:
            l = GameState.live_db[lid]
            print(f"   - {l.name} (Score: {l.score}, Need: {l.required_hearts})")

    # HAND
    print(f"\n YOUR HAND ({len(user.hand)} cards):")
    for i, cid in enumerate(user.hand):
        if cid in GameState.member_db:
            m = GameState.member_db[cid]
            print(f"   [{i}] {m.name} (Cost: {m.cost}, Hearts: {m.hearts})")
        elif cid in GameState.live_db:
            l = GameState.live_db[cid]
            print(f"   [{i}] [LIVE] {l.name} (Score: {l.score}, Need: {l.required_hearts})")
        else:
            print(f"   [{i}] Card ID: {cid}")

    if state.pending_choices:
        choice_type, params = state.pending_choices[0]
        print(f"\n >>> PENDING CHOICE: {choice_type} ({params})")


def get_action_desc(state: GameState, a: int):
    p = state.active_player
    if a == 0:
        return "Pass / Next Phase"

    if 1 <= a <= 180:
        idx = (a - 1) // 3
        area = (a - 1) % 3
        if idx < len(p.hand):
            cid = p.hand[idx]
            if cid in GameState.member_db:
                name = GameState.member_db[cid].name
                return f"Play {name} to Area {area}"
            elif cid in GameState.live_db:
                name = GameState.live_db[cid].name
                return f"Set Live Card: {name}"

    if 181 <= a <= 200:
        idx = a - 181
        return f"Select choice targeted at Hand[{idx}]"

    if 201 <= a <= 260:
        # Activated ability
        area = (a - 201) // 20
        ability_idx = (a - 201) % 20
        cid = p.stage[area]
        if cid >= 0:
            m = GameState.member_db[cid]
            return f"Activate Ability {ability_idx} of {m.name} at Area {area}"

    if 270 <= a <= 279:
        return f"Modal Choice Option {a - 270}"

    if 280 <= a <= 285:
        colors = ["Red", "Blue", "Green", "Yellow", "Purple", "Pink"]
        return f"Select Color: {colors[a - 280]}"

    return f"Action {a}"


def run_battle():
    parser = argparse.ArgumentParser()
    parser.add_argument("--easy", action="store_true", help="Use easy mode cards")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)
        np.random.seed(args.seed)

    # 1. Setup Data
    loader = CardDataLoader("data/cards.json")
    m_db, l_db = loader.load()

    if args.easy:
        easy_m, easy_l = create_easy_cards()
        m_db[easy_m.card_id] = easy_m
        l_db[easy_l.card_id] = easy_l
        GameState.member_db = m_db
        GameState.live_db = l_db

        state = initialize_game(use_real_data=False)  # Skip reload
        # Override decks with easy stuff
        for p in state.players:
            m_list = [888] * 48
            l_list = [999] * 12
            p.main_deck = m_list + l_list
            random.shuffle(p.main_deck)
            p.hand = []
            for _ in range(5):
                if p.main_deck:
                    p.hand.append(p.main_deck.pop())
            p.energy_deck = [200] * 12
            p.energy_zone = []
            for _ in range(3):
                if p.energy_deck:
                    p.energy_zone.append(p.energy_deck.pop(0))
    else:
        GameState.member_db = m_db
        GameState.live_db = l_db
        state = initialize_game(use_real_data=True)

    user_pid = 0  # You are P0
    ai_agent = RandomAgent()

    print_header("WELCOME TO LOVE LIVE! OCG - BATTLE MODE")
    print("You are P0. AI is P1.")
    print("Wait for your turn to make moves!")

    while not state.is_terminal():
        curr_pid = state.current_player

        if curr_pid == user_pid:
            # USER TURN
            print_state(state, user_pid)
            mask = state.get_legal_actions()
            actions = [i for i, val in enumerate(mask) if val]

            print("\nLEGAL ACTIONS:")
            for a in actions:
                print(f"  [{a}] {get_action_desc(state, a)}")

            try:
                cmd = input("\nYour Move (ID or 'q') > ").strip().lower()
                if cmd == "q":
                    break
                aid = int(cmd)
                if mask[aid]:
                    state = state.step(aid)
                else:
                    print("Invalid Move!")
            except ValueError:
                print("Please enter a number.")
        else:
            # AI TURN
            print(f"\nAI (P{curr_pid}) is thinking...")
            aid = ai_agent.choose_action(state, curr_pid)
            desc = get_action_desc(state, aid)
            print(f"AI chooses: [{aid}] {desc}")
            state = state.step(aid)
            # Add small delay or just wait for input to continue?
            # input("Press Enter for next step...")

    print_separator()
    print("GAME OVER")
    winner = state.get_winner()
    if winner == user_pid:
        print("CONGRATULATIONS! YOU WON!")
    elif winner == 1 - user_pid:
        print("THE AI DEFEATED YOU. BETTER LUCK NEXT TIME!")
    else:
        print("IT'S A DRAW!")

    p0_score = len(state.players[0].success_lives)
    p1_score = len(state.players[1].success_lives)
    print(f"Final Score - YOU: {p0_score} | AI: {p1_score}")


if __name__ == "__main__":
    run_battle()
