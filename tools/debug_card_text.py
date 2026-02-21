import json
import os
import sys

sys.path.append(os.getcwd())

from pydantic import TypeAdapter

from engine.models.card import MemberCard

TARGET_NO = "PL!N-bp3-003-R"


def debug_card():
    with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    adapter = TypeAdapter(MemberCard)

    found = False
    for k, v in data["member_db"].items():
        card = adapter.validate_python(v)
        if card.card_no == TARGET_NO:
            found = True
            print(f"Found {TARGET_NO} (ID: {k})")
            print("--- Abilities ---")
            for ab in card.abilities:
                print(f"Raw: {ab.raw_text}")
                print(f"Reconstructed: {ab.reconstruct_text()}")
                # Also print internal structure to see if conditions exist
                print(f"Conditions: {[c.type.name for c in ab.conditions]}")
                print(f"Effects: {[e.effect_type.name for e in ab.effects]}")
            break

    with open("temp_debug.out", "w", encoding="utf-8") as out:
        sys.stdout = out
        if not found:
            print(f"Card {TARGET_NO} not found in DB.")

        if found:
            print(f"Found {TARGET_NO} (ID: {k})")
            print("--- Abilities ---")
            for ab in card.abilities:
                print(f"Raw: {ab.raw_text}")
                print(f"Reconstructed: {ab.reconstruct_text()}")
                print(f"Conditions: {[c.type.name for c in ab.conditions]}")
                print(f"Effects: {[e.effect_type.name for e in ab.effects]}")
        sys.stdout = sys.__stdout__


if __name__ == "__main__":
    debug_card()
