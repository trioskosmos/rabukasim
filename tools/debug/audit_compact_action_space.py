from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import engine_rust
from backend.server import describe_action_for_state
from alphazero.training.overnight_vanilla import load_tournament_decks, load_vanilla_database_json
from alphazero.training.vanilla_action_codec import ACTION_SPACE, engine_action_to_policy_id


def audit_random_games(
    deck_dir: str,
    db_path: str,
    games: int,
    max_steps: int,
    seed: int,
) -> dict[str, object]:
    rng = random.Random(seed)
    full_db, db_json = load_vanilla_database_json(db_path)
    rust_db = engine_rust.PyCardDatabase(db_json)
    decks = load_tournament_decks(full_db, deck_dir)

    total_states = 0
    total_legal_actions = 0
    unmapped_actions = 0
    collision_states = 0
    phase_counts: Counter[int] = Counter()
    unmapped_by_phase: Counter[int] = Counter()
    collisions_by_phase: Counter[int] = Counter()
    examples: list[dict[str, object]] = []

    for game_idx in range(games):
        deck_a = decks[rng.randrange(len(decks))]
        deck_b = decks[rng.randrange(len(decks))]
        game_seed = rng.randrange(2**31)

        state = engine_rust.PyGameState(rust_db)
        state.initialize_game_with_seed(
            deck_a["initial_deck"],
            deck_b["initial_deck"],
            deck_a["energy"],
            deck_b["energy"],
            [],
            [],
            game_seed,
        )
        state.silent = True
        state.debug_mode = False

        steps = 0
        while not state.is_terminal() and steps < max_steps:
            legal_ids = [int(action_id) for action_id in state.get_legal_action_ids()]
            if not legal_ids:
                state.auto_step(rust_db)
                steps += 1
                continue

            state_json_str = state.to_json()
            state_json = json.loads(state_json_str)
            current_player = int(getattr(state, "acting_player", state.current_player))
            phase = int(state_json.get("phase", int(state.phase)))
            initial_deck = deck_a["initial_deck"] if current_player == 0 else deck_b["initial_deck"]
            player_json = state_json["players"][current_player]

            total_states += 1
            total_legal_actions += len(legal_ids)
            phase_counts[phase] += 1

            by_policy: dict[int, list[int]] = {}
            state_unmapped: list[int] = []
            for action_id in legal_ids:
                policy_id = engine_action_to_policy_id(player_json, action_id, initial_deck, phase)
                if 0 <= policy_id < ACTION_SPACE:
                    by_policy.setdefault(int(policy_id), []).append(int(action_id))
                else:
                    unmapped_actions += 1
                    unmapped_by_phase[phase] += 1
                    state_unmapped.append(int(action_id))

            state_collisions = {policy_id: actions for policy_id, actions in by_policy.items() if len(actions) > 1}
            if state_collisions:
                collision_states += 1
                collisions_by_phase[phase] += 1

            if (state_unmapped or state_collisions) and len(examples) < 12:
                entry: dict[str, object] = {
                    "game": game_idx,
                    "turn": int(state.turn),
                    "phase": phase,
                    "player": current_player,
                }
                if state_unmapped:
                    entry["unmapped"] = [
                        {
                            "action": action_id,
                            "description": describe_action_for_state(state, action_id, "en"),
                        }
                        for action_id in state_unmapped[:5]
                    ]
                if state_collisions:
                    entry["collisions"] = [
                        {
                            "policy_id": policy_id,
                            "actions": [
                                {
                                    "action": action_id,
                                    "description": describe_action_for_state(state, action_id, "en"),
                                }
                                for action_id in actions[:5]
                            ],
                        }
                        for policy_id, actions in list(state_collisions.items())[:5]
                    ]
                examples.append(entry)

            action = rng.choice(legal_ids)
            state.step(int(action))
            state.auto_step(rust_db)
            steps += 1

    return {
        "games": games,
        "states": total_states,
        "legal_actions": total_legal_actions,
        "unmapped_actions": unmapped_actions,
        "collision_states": collision_states,
        "phase_counts": dict(sorted(phase_counts.items())),
        "unmapped_by_phase": dict(sorted(unmapped_by_phase.items())),
        "collisions_by_phase": dict(sorted(collisions_by_phase.items())),
        "examples": examples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit compact abilityless action coverage against real legal actions")
    parser.add_argument("--db-path", type=str, default=str(ROOT_DIR / "data" / "cards_compiled.json"))
    parser.add_argument("--deck-dir", type=str, default=str(ROOT_DIR / "ai" / "decks"))
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    report = audit_random_games(
        deck_dir=args.deck_dir,
        db_path=args.db_path,
        games=args.games,
        max_steps=args.max_steps,
        seed=args.seed,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()