import json
import random
from pathlib import Path

import numpy as np
import torch

from alphazero.vanilla_net import HighFidelityAlphaNet
from engine.game.deck_utils import UnifiedDeckParser

# Configuration
ACTION_SPACE = 256
OBS_DIM = 800
FIXED_SEEDS = [101, 202, 303]
MULLIGAN_REPLACE_COUNT = 5
MAX_STAGE_SLOTS = 3
MAX_LIVE_SET_CARDS = 3


def analyze_card_costs(db_json, card_id):
    """Analyze a card's costs for mulligan decisions."""
    for cat in ["member_db", "live_db"]:
        if cat in db_json and card_id in db_json[cat]:
            card = db_json[cat][card_id]
            energy = card.get("cost", 0)
            life_req = card.get("life", 0)
            yell = 1 if "YellHeart" in str(card.get("abilities", [])) else 0
            return energy, life_req, yell
    return 0, 0, 0


def calculate_mulligan_strategy(db_json, hand, deck_copy, replace_count=5):
    """Determine which cards to replace during mulligan."""
    if not hand:
        return []
    card_scores = []
    for idx, card_id in enumerate(hand):
        energy, life_req, yell = analyze_card_costs(db_json, card_id)
        score = -1 * (energy * 2 + life_req) + yell * 5
        card_scores.append((idx, score))
    card_scores.sort(key=lambda x: x[1])
    max_replace = min(replace_count, len(hand) - 1)
    return [idx for idx, _ in card_scores[:max_replace]]


def map_engine_to_vanilla(p_data, engine_id, initial_deck, current_phase=None):
    """Maps engine action ID to vanilla 256-dim action space."""
    if engine_id == 0:
        if current_phase in [-1, 0, 5, 8, 10]:
            return 7  # Confirm
        return 0  # Pass
    if 300 <= engine_id <= 305:
        return 1 + (engine_id - 300)
    if engine_id == 11000:
        return 7
    if 1000 <= engine_id < 1600:
        hand_idx = (engine_id - 1000) // 10
        slot = (engine_id - 1000) % 10
        hand = p_data.get("hand", [])
        if hand_idx < len(hand):
            card_id = hand[hand_idx]
            if initial_deck and card_id in initial_deck:
                try:
                    deck_idx = initial_deck.index(card_id)
                    if deck_idx < 60:
                        if 1 <= slot <= 3:
                            return 68 + (slot - 1) * 60 + deck_idx
                        return 8 + deck_idx
                except ValueError:
                    pass
        return -1
    if 400 <= engine_id < 500:
        hand_idx = engine_id - 400
        hand = p_data.get("hand", [])
        if hand_idx < len(hand):
            card_id = hand[hand_idx]
            if initial_deck and card_id in initial_deck:
                try:
                    deck_idx = initial_deck.index(card_id)
                    if deck_idx < 60:
                        return 8 + deck_idx
                except ValueError:
                    pass
        return -1
    if 600 <= engine_id <= 602:
        return 248 + (engine_id - 600)
    if 8200 <= engine_id <= 8204:
        return 251 + (engine_id - 8200)
    if 20000 <= engine_id <= 20002:
        return 240 + (engine_id - 20000)
    if 21000 <= engine_id <= 21002:
        return 240 + (engine_id - 21000)
    return -1


# Aliases for compatibility
engine_action_to_action_256 = map_engine_to_vanilla
engine_action_to_action_248 = map_engine_to_vanilla


def action_256_to_engine_action(state, player_idx, action_idx, phase, initial_deck):
    """Converts 256-dim action index to engine action ID."""
    if action_idx == 0:
        return 0
    if 1 <= action_idx <= 6:
        return 300 + (action_idx - 1)
    if action_idx == 7:
        return 11000 if phase == 4 else 0
    if 248 <= action_idx <= 250:
        return 600 + (action_idx - 248)
    if 251 <= action_idx <= 255:
        return 8200 + (action_idx - 251)
    if 8 <= action_idx < 68:
        deck_idx = action_idx - 8
        if deck_idx < len(initial_deck):
            cid = initial_deck[deck_idx]
            pj = json.loads(state.to_json())
            hand = pj["players"][player_idx].get("hand", [])
            if cid in hand:
                h_idx = hand.index(cid)
                if phase == 4:
                    return 1000 + h_idx * 10 + 1
                if phase == 5:
                    return 400 + h_idx
    if 68 <= action_idx < 248:
        offset = action_idx - 68
        slot_idx = offset // 60
        deck_idx = offset % 60
        if deck_idx < len(initial_deck):
            cid = initial_deck[deck_idx]
            pj = json.loads(state.to_json())
            hand = pj["players"][player_idx].get("hand", [])
            if cid in hand:
                h_idx = hand.index(cid)
                if phase == 4:
                    return 1000 + h_idx * 10 + (slot_idx + 1)
                if phase == 5:
                    return 400 + h_idx
    return None


action_256_to_engine_action = action_256_to_engine_action  # already named this way
action_248_to_engine_action = action_256_to_engine_action


def prioritize_live_set_actions(legal_actions, state, curr_p):
    """Prioritize live set actions."""
    pj = json.loads(state.to_json())
    current_lives = len(pj["players"][curr_p].get("live_zone", []))
    prioritized = []
    for aid in legal_actions:
        is_live_play = 400 <= aid < 500
        priority = 10 if is_live_play and current_lives < MAX_LIVE_SET_CARDS else 0
        prioritized.append((aid, priority))
    prioritized.sort(key=lambda x: x[1], reverse=True)
    return [a[0] for a in prioritized]


def prioritize_field_actions(legal_actions, state, curr_p, db_json=None):
    """Prioritize field placement."""
    pj = json.loads(state.to_json())
    field = pj["players"][curr_p].get("field", [])
    hand = pj["players"][curr_p].get("hand", [])
    field_count = len(field)
    field_costs = []
    if db_json:
        for field_card in field:
            if field_card:
                energy, _, _ = analyze_card_costs(db_json, field_card)
                field_costs.append(energy)
    prioritized = []
    for aid in legal_actions:
        is_member_play = 1000 <= aid < 1600
        priority = 0
        if is_member_play and field_count < MAX_STAGE_SLOTS:
            priority = 20
            hand_idx = (aid - 1000) // 10
            if hand_idx < len(hand):
                card_id = hand[hand_idx]
                if db_json:
                    energy, _, _ = analyze_card_costs(db_json, card_id)
                    if field_costs:
                        bonus = 0
                        for f_energy in field_costs:
                            if energy > f_energy:
                                bonus += 10
                            elif energy == f_energy:
                                bonus += 3
                            else:
                                bonus += 5
                        priority += bonus // len(field_costs)
                    else:
                        priority += 5
        prioritized.append((aid, priority))
    prioritized.sort(key=lambda x: x[1], reverse=True)
    return [a[0] for a in prioritized]


def build_action_mask_248(state, player_idx, initial_deck, phase):
    """Builds 256-dim binary mask of legal actions."""
    legal_engine = state.get_legal_action_ids()
    mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
    if not initial_deck:
        mask[0] = True
        return mask
    pj = json.loads(state.to_json())
    p_data = pj["players"][player_idx]
    for eng_id in legal_engine:
        vid = map_engine_to_vanilla(p_data, eng_id, initial_deck, phase)
        if 0 <= vid < ACTION_SPACE:
            mask[vid] = True
    return mask


class NeuralMCTS:
    """Card-centric + slot-aware neural action selection (256-dim action space)."""

    def __init__(self, model, device, initial_deck=None):
        import engine_rust

        self.model = model
        self.device = device
        self.initial_deck = initial_deck if initial_deck is not None else []
        self.temperature = 1.0
        self.dirichlet_alpha = 0.3
        self.dirichlet_epsilon = 0.25
        self.use_noise = True
        self.evaluator = engine_rust.PyAlphaZeroEvaluator(model, engine_rust.AlphaZeroTensorType.Vanilla)

    def select_action(self, state, player_idx, current_phase):
        mask_248 = build_action_mask_248(state, player_idx, self.initial_deck, current_phase)
        if not mask_248.any():
            legal_actions = state.get_legal_action_ids()
            fallback = legal_actions[0] if legal_actions else 0
            return np.ones(ACTION_SPACE) / ACTION_SPACE, fallback, 0.5

        num_sims = getattr(self, "num_sims", 64)
        batch_size = 128
        sugg = state.search_mcts_alphazero(num_sims, self.evaluator, batch_size)
        policy_248_masked = np.zeros(ACTION_SPACE, dtype=np.float32)
        value = 0.5
        pj = json.loads(state.to_json())
        if sugg:
            total_visits = sum(s[2] for s in sugg)
            if total_visits > 0:
                for engine_id, q, visits in sugg:
                    vid = map_engine_to_vanilla(pj["players"][player_idx], engine_id, self.initial_deck, current_phase)
                    if vid is not None and 0 <= vid < ACTION_SPACE:
                        policy_248_masked[vid] = visits / total_visits
                value = sum(s[1] * s[2] for s in sugg) / total_visits
        if self.temperature > 0.01:
            if self.use_noise and self.dirichlet_epsilon > 0:
                legal_vids = np.where(policy_248_masked > 0)[0]
                if len(legal_vids) > 0:
                    noise = np.random.dirichlet([self.dirichlet_alpha] * len(legal_vids))
                    policy_248_masked[legal_vids] = (1 - self.dirichlet_epsilon) * policy_248_masked[
                        legal_vids
                    ] + self.dirichlet_epsilon * noise
                    policy_248_masked = policy_248_masked / policy_248_masked.sum()
            policy_sample = policy_248_masked ** (1.0 / self.temperature)
            policy_sample = policy_sample / policy_sample.sum()
            action_idx = int(np.random.choice(ACTION_SPACE, p=policy_sample))
        else:
            action_idx = int(np.argmax(policy_248_masked))

        action_engine = action_256_to_engine_action(state, player_idx, action_idx, current_phase, self.initial_deck)
        legal_ids = state.get_legal_action_ids()
        if action_engine not in legal_ids:
            action_engine = legal_ids[0] if legal_ids else 0
        return policy_248_masked, action_engine, value


def run_benchmark(model_path=None, sims=50, model=None, db=None):
    """Standard Vanilla Benchmark."""
    import engine_rust

    print(f"Benchmark Init (Sims: {sims})")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    root_dir = Path(__file__).resolve().parent.parent.parent

    if db is None:
        db_path = root_dir / "data" / "cards_compiled.json"
        with open(db_path, "r", encoding="utf-8") as f:
            full_db = json.load(f)
        stripped = json.loads(json.dumps(full_db))
        for cat in ["member_db", "live_db"]:
            for cid, data in stripped.get(cat, {}).items():
                data["abilities"] = []
                data["ability_flags"] = 0
                if "synergy_flags" in data:
                    data["synergy_flags"] &= 1
        db = engine_rust.PyCardDatabase(json.dumps(stripped))
        parser = UnifiedDeckParser(full_db)
    else:
        parser = UnifiedDeckParser({})

    if model is None:
        model = HighFidelityAlphaNet(input_dim=OBS_DIM, num_actions=ACTION_SPACE).to(device)
        if model_path and Path(model_path).exists():
            ckpt = torch.load(model_path, map_location=device, weights_only=True, mmap=True)
            model.load_state_dict(ckpt["model"] if isinstance(ckpt, dict) and "model" in ckpt else ckpt)

    model.eval()
    decks_dir = root_dir / "ai" / "decks"
    all_decks = []
    for df in list(decks_dir.glob("*.txt")):
        with open(df, "r", encoding="utf-8") as f:
            ext = parser.extract_from_content(f.read())
            if ext:
                m, l = [], []
                for c in ext[0]["main"]:
                    cd = parser.resolve_card(c)
                    if cd and cd.get("type") == "Member":
                        m.append(cd["card_id"])
                    elif cd and cd.get("type") == "Live":
                        l.append(cd["card_id"])
                if m and l:
                    all_decks.append({"name": df.stem, "m": (m * 5)[:48], "l": (l * 5)[:12]})

    results = []
    for deck in all_decks:
        for seed in FIXED_SEEDS:
            state = engine_rust.PyGameState(db)
            state.initialize_game_with_seed(deck["m"], deck["m"], [38] * 12, [38] * 12, deck["l"], deck["l"], seed)
            initial_decks = [state.get_player(0).initial_deck, state.get_player(1).initial_deck]
            moves = 0
            while not state.is_terminal() and state.turn < 25 and moves < 500:
                legal = state.get_legal_action_ids()
                if not legal:
                    state.auto_step(db)
                    legal = state.get_legal_action_ids()
                if not legal:
                    break

                pj = json.loads(state.to_json())
                cp = pj.get("phase", -4)
                curr_p = state.current_player

                if cp == -4:
                    if 0 in legal:
                        state.step(0)
                        state.auto_step(db)
                        moves += 1
                        continue
                if cp in [-3, -2]:
                    state.step(random.choice(legal))
                    state.auto_step(db)
                    moves += 1
                    continue

                action = -1
                if sims > 0 and cp in [4, 5, 0]:
                    sugg = state.search_mcts(
                        sims, 0.0, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Solitaire, None
                    )
                    if sugg:
                        action = sugg[0][0]

                if action == -1:
                    mask = torch.zeros((1, ACTION_SPACE), dtype=torch.bool, device=device)
                    v_to_e = {}
                    for aid in legal:
                        vid = map_engine_to_vanilla(pj["players"][curr_p], aid, initial_decks[curr_p], cp)
                        if 0 <= vid < ACTION_SPACE:
                            mask[0, vid] = True
                            v_to_e[vid] = aid

                    if mask.any():
                        obs = (
                            torch.from_numpy(np.array(state.to_vanilla_tensor(), dtype=np.float32))
                            .unsqueeze(0)
                            .to(device)
                        )
                        with torch.no_grad():
                            lgt, _ = model(obs, mask=mask)
                            action = v_to_e.get(torch.argmax(lgt).item(), legal[0])
                    else:
                        action = legal[0]

                state.step(action)
                state.auto_step(db)
                moves += 1

            p0s = len(state.get_player(0).success_lives)
            p1s = len(state.get_player(1).success_lives)
            results.append({"turns": state.turn, "score": p0s + p1s})

    if results:
        avg_turns = sum(r["turns"] for r in results) / len(results)
        avg_score = sum(r["score"] for r in results) / len(results)
        return avg_turns, avg_score
    return 0.0, 0.0
