from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Sequence

import numpy as np
import torch

from alphazero.training.vanilla_action_codec import (
    ACTION_SPACE,
    OBS_DIM,
    VanillaActionSpaceSpec,
    assign_hand_positions,
    build_legal_policy_mask,
    build_policy_engine_mapping,
    dense_to_sparse,
    engine_action_to_policy_id as map_engine_to_vanilla,
    policy_id_to_engine_action as action_256_to_engine_action,
    sparse_policy_from_engine_visits,
)
from alphazero.vanilla_net import HighFidelityAlphaNet

engine_action_to_action_256 = map_engine_to_vanilla
engine_action_to_action_248 = map_engine_to_vanilla
action_248_to_engine_action = action_256_to_engine_action
build_action_mask_248 = build_legal_policy_mask
build_action_mask_256 = build_legal_policy_mask
ACTION_SPEC = VanillaActionSpaceSpec()


class NeuralMCTS:
    def __init__(self, model, device, initial_deck: Sequence[int] | None = None, sims: int = 64, batch_size: int = 64):
        import engine_rust

        self.model = model
        self.device = device
        self.initial_deck = list(initial_deck or [])
        self.num_sims = sims
        self.batch_size = batch_size
        self.temperature = 1.0
        self.evaluator = engine_rust.PyAlphaZeroEvaluator(model, engine_rust.AlphaZeroTensorType.Vanilla)

    def select_action(self, state, player_idx: int, current_phase: int):
        player_json = json.loads(state.to_json())["players"][player_idx]
        legal_ids = state.get_legal_action_ids()
        mask = build_legal_policy_mask(state, player_idx, self.initial_deck, current_phase, legal_ids)
        mapping = build_policy_engine_mapping(player_json, legal_ids, self.initial_deck, current_phase)

        if not mapping:
            fallback = legal_ids[0] if legal_ids else 0
            uniform = np.zeros(ACTION_SPACE, dtype=np.float32)
            if legal_ids:
                vids = [map_engine_to_vanilla(player_json, aid, self.initial_deck, current_phase) for aid in legal_ids]
                vids = [vid for vid in vids if 0 <= vid < ACTION_SPACE]
                if vids:
                    uniform[vids] = 1.0 / len(vids)
            return uniform, fallback, 0.5

        suggestions = []
        if hasattr(state, "search_mcts_alphazero"):
            suggestions = state.search_mcts_alphazero(self.num_sims, self.evaluator, self.batch_size)
        elif hasattr(state, "get_mcts_suggestions"):
            suggestions = state.get_mcts_suggestions(self.num_sims)

        dense_policy = sparse_policy_from_engine_visits(player_json, suggestions, self.initial_deck, current_phase)
        if dense_policy.sum() <= 0:
            dense_policy = mask.astype(np.float32)
            dense_policy /= dense_policy.sum()

        if self.temperature > 0.01:
            sample_dist = dense_policy ** (1.0 / self.temperature)
            sample_dist /= sample_dist.sum()
            action_id = int(np.random.choice(np.arange(ACTION_SPACE), p=sample_dist))
        else:
            action_id = int(np.argmax(dense_policy))

        return dense_policy, mapping.get(action_id, legal_ids[0]), 0.5


def run_benchmark(model_path=None, sims: int = 32, model=None, db=None):
    import engine_rust
    from engine.game.deck_utils import UnifiedDeckParser

    root_dir = Path(__file__).resolve().parent.parent.parent
    db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as handle:
        full_db = json.load(handle)

    stripped = json.loads(json.dumps(full_db))
    for category in ["member_db", "live_db"]:
        for data in stripped.get(category, {}).values():
            data["abilities"] = []
            data["ability_flags"] = 0
            if "synergy_flags" in data:
                data["synergy_flags"] &= 1

    db = db or engine_rust.PyCardDatabase(json.dumps(stripped))
    parser = UnifiedDeckParser(full_db)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if model is None:
        model = HighFidelityAlphaNet().to(device)
        if model_path:
            checkpoint = torch.load(model_path, map_location=device, weights_only=True)
            state_dict = checkpoint["model"] if isinstance(checkpoint, dict) and "model" in checkpoint else checkpoint
            model.load_state_dict(state_dict)
    model.eval()

    decks = []
    for deck_file in (root_dir / "ai" / "decks").glob("*.txt"):
        extracted = parser.extract_from_content(deck_file.read_text(encoding="utf-8"))
        if not extracted:
            continue
        members, lives = [], []
        for card_no in extracted[0]["main"]:
            resolved = parser.resolve_card(card_no)
            if not resolved:
                continue
            if resolved.get("type") == "Member":
                members.append(resolved["card_id"])
            elif resolved.get("type") == "Live":
                lives.append(resolved["card_id"])
        if members and lives:
            decks.append({"name": deck_file.stem, "main": (members * 5)[:48] + (lives * 5)[:12], "energy": [38] * 12})

    results = []
    for deck in decks[: min(6, len(decks))]:
        state = engine_rust.PyGameState(db)
        state.initialize_game(deck["main"], deck["main"], deck["energy"], deck["energy"], [], [])
        state.silent = True

        initial_decks = [deck["main"], deck["main"]]
        mcts = NeuralMCTS(model, device, initial_decks[0], sims=sims)
        while not state.is_terminal() and state.turn < 12:
            legal = state.get_legal_action_ids()
            if not legal:
                state.auto_step(db)
                continue
            phase = json.loads(state.to_json()).get("phase", -4)
            if phase in (-4,):
                action = 0
            elif phase in (-3, -2):
                action = random.choice(legal)
            else:
                _policy, action, _value = mcts.select_action(state, state.current_player, phase)
            state.step(action)
            state.auto_step(db)

        results.append({"deck": deck["name"], "winner": state.get_winner(), "turns": state.turn})

    avg_turns = float(np.mean([entry["turns"] for entry in results])) if results else 0.0
    avg_score = float(np.mean([1.0 if entry["winner"] in (0, 1) else 0.0 for entry in results])) if results else 0.0
    return avg_turns, avg_score
