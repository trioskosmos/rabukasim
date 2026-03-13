from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import engine_rust
from backend.server import describe_action_for_state
from alphazero.training.overnight_vanilla import (
    VanillaPolicyModel,
    _apply_deterministic_setup,
    _load_checkpoint_into_model,
    load_tournament_decks,
    load_vanilla_database_json,
)
from alphazero.training.vanilla_action_codec import build_legal_policy_mask, build_policy_engine_mapping
from alphazero.training.vanilla_observation import build_card_feature_lookup, build_vanilla_observation
from alphazero.vanilla_net import VanillaTransformerConfig

PHASE_MAIN = 4
PHASE_LIVE_SET = 5


def planner_turn_sequence(state: engine_rust.PyGameState, rust_db: engine_rust.PyCardDatabase) -> list[int] | None:
    phase = int(state.phase)
    try:
        if phase == PHASE_MAIN and hasattr(state, "plan_full_turn"):
            _score, planner_actions, _nodes, _breakdown = state.plan_full_turn(rust_db)
            sequence = [int(action_id) for action_id in planner_actions]
            if not sequence:
                return None

            sim_state = engine_rust.PyGameState(rust_db)
            sim_state.apply_state_json(state.to_json())
            for action_id in sequence:
                legal_ids = set(int(legal_action) for legal_action in sim_state.get_legal_action_ids())
                if int(action_id) not in legal_ids:
                    return None
                sim_state.step(int(action_id))

            if int(sim_state.phase) == PHASE_LIVE_SET and hasattr(sim_state, "find_best_liveset_selection"):
                liveset_actions, _nodes, _score = sim_state.find_best_liveset_selection(rust_db)
                sequence.extend(int(action_id) for action_id in liveset_actions)
            return sequence

        if phase == PHASE_LIVE_SET and hasattr(state, "find_best_liveset_selection"):
            planner_actions, _nodes, _score = state.find_best_liveset_selection(rust_db)
            return [int(action_id) for action_id in planner_actions]
    except Exception as exc:
        print(f"Planner failed: {exc}")
        return None

    return None


def describe_sequence(
    state_json_str: str,
    sequence: list[int],
    rust_db: engine_rust.PyCardDatabase,
    lang: str,
) -> list[str]:
    sim_state = engine_rust.PyGameState(rust_db)
    sim_state.apply_state_json(state_json_str)
    descriptions: list[str] = []
    for index, action_id in enumerate(sequence, start=1):
        descriptions.append(f"{index}. {describe_action_for_state(sim_state, int(action_id), lang)} [{int(action_id)}]")
        sim_state.step(int(action_id))
    return descriptions


def main() -> None:
    parser = argparse.ArgumentParser(description="Trace compact checkpoint decisions against planner sequences")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=str(ROOT_DIR / "alphazero" / "training" / "vanilla_checkpoints_compact" / "latest.pt"),
    )
    parser.add_argument("--db-path", type=str, default=str(ROOT_DIR / "data" / "cards_compiled.json"))
    parser.add_argument("--deck-dir", type=str, default=str(ROOT_DIR / "ai" / "decks"))
    parser.add_argument("--deck-a", type=int, default=0)
    parser.add_argument("--deck-b", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--max-decisions", type=int, default=8)
    parser.add_argument("--lang", type=str, default="en")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    model_config = VanillaTransformerConfig(**checkpoint["model_config"])
    model = VanillaPolicyModel(model_config).to(device)
    _load_checkpoint_into_model(model, checkpoint)
    model.eval()

    full_db, db_json = load_vanilla_database_json(args.db_path)
    card_lookup = build_card_feature_lookup(full_db)
    rust_db = engine_rust.PyCardDatabase(db_json)
    decks = load_tournament_decks(full_db, args.deck_dir)
    deck_a = decks[args.deck_a % len(decks)]
    deck_b = decks[args.deck_b % len(decks)]

    state = engine_rust.PyGameState(rust_db)
    state.initialize_game_with_seed(
        deck_a["initial_deck"],
        deck_b["initial_deck"],
        deck_a["energy"],
        deck_b["energy"],
        [],
        [],
        args.seed,
    )
    state.silent = True
    state.debug_mode = False
    _apply_deterministic_setup(state, rust_db)

    disagreements = 0
    decision_count = 0

    while not state.is_terminal() and decision_count < args.max_decisions:
        legal_ids = [int(action_id) for action_id in state.get_legal_action_ids()]
        if not legal_ids:
            break

        state_json_str = state.to_json()
        state_json = json.loads(state_json_str)
        current_player = int(state.current_player)
        phase = int(state_json.get("phase", -4))
        initial_deck = deck_a["initial_deck"] if current_player == 0 else deck_b["initial_deck"]
        player_json = state_json["players"][current_player]

        mask = build_legal_policy_mask(state, current_player, initial_deck, phase, legal_ids)
        mapping = build_policy_engine_mapping(player_json, legal_ids, initial_deck, phase)
        if not mapping:
            state.step(int(legal_ids[0]))
            state.auto_step(rust_db)
            continue

        obs = build_vanilla_observation(state_json, current_player, initial_deck, card_lookup)
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
        mask_t = torch.as_tensor(mask, dtype=torch.bool, device=device).unsqueeze(0)
        with torch.inference_mode():
            logits, _values = model(obs_t, mask_t)
            policy = torch.softmax(logits, dim=1)[0].detach().cpu().numpy().astype(np.float32)

        policy_ids = np.asarray(list(mapping.keys()), dtype=np.int64)
        legal_policy = policy[policy_ids]
        order = np.argsort(-legal_policy)
        top_policy_ids = policy_ids[order[: min(5, len(order))]]
        planner_sequence = planner_turn_sequence(state, rust_db)

        print(f"\n=== Decision {decision_count + 1} | Turn {int(state.turn)} | Player {current_player} | Phase {phase} ===")
        print("Model top actions:")
        for rank, policy_id in enumerate(top_policy_ids, start=1):
            action_id = int(mapping[int(policy_id)])
            desc = describe_action_for_state(state, action_id, args.lang)
            print(f"  {rank}. {desc} [{action_id}] p={float(policy[int(policy_id)]):.4f}")

        if planner_sequence:
            planner_desc = describe_sequence(state_json_str, planner_sequence, rust_db, args.lang)
            print("Planner sequence:")
            for line in planner_desc:
                print(f"  {line}")

            model_top_action = int(mapping[int(top_policy_ids[0])])
            if model_top_action != int(planner_sequence[0]):
                disagreements += 1
                print("Issue: model top-1 disagrees with planner first action")

            for action_id in planner_sequence:
                legal_now = set(int(legal_action) for legal_action in state.get_legal_action_ids())
                if int(action_id) not in legal_now:
                    print(f"Issue: planner action became illegal mid-sequence [{int(action_id)}]")
                    break
                state.step(int(action_id))
                state.auto_step(rust_db)
                if state.is_terminal():
                    break
        else:
            chosen_action = int(mapping[int(top_policy_ids[0])])
            print(f"Planner unavailable, executing model top action [{chosen_action}]")
            state.step(chosen_action)
            state.auto_step(rust_db)

        decision_count += 1

    print("\n=== Summary ===")
    print(f"Decisions traced: {decision_count}")
    print(f"Top-1 planner disagreements: {disagreements}")
    print(f"Terminal: {bool(state.is_terminal())}")
    print(f"Winner: {int(state.get_winner())}")


if __name__ == "__main__":
    main()