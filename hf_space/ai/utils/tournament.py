import argparse
import json
import os
import random
import sys

import torch
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import engine_rust

from ai.agents.neural_mcts import HybridMCTSAgent
from ai.models.training_config import POLICY_SIZE
from ai.training.train import AlphaNet
from ai.utils.benchmark_decks import parse_deck


class Agent:
    def get_action(self, game, db):
        pass


class RandomAgent(Agent):
    def get_action(self, game, db):
        actions = game.get_legal_action_ids()
        if not actions:
            return 0
        return random.choice(actions)


class MCTSAgent(Agent):
    def __init__(self, sims=100):
        self.sims = sims

    def get_action(self, game, db):
        suggestions = game.get_mcts_suggestions(self.sims, engine_rust.SearchHorizon.TurnEnd)
        if not suggestions:
            return 0
        return suggestions[0][0]


class ResNetAgent(Agent):
    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        checkpoint = torch.load(model_path, map_location=self.device)

        # Handle new dictionary checkpoint format
        if isinstance(checkpoint, dict) and "model_state" in checkpoint:
            state_dict = checkpoint["model_state"]
        else:
            state_dict = checkpoint

        # Detect policy size from weights
        p_fc_bias = state_dict.get("policy_head_fc.bias")
        detected_policy_size = p_fc_bias.shape[0] if p_fc_bias is not None else POLICY_SIZE
        print(f"ResNetAgent: Detected Policy Size {detected_policy_size}")

        self.model = AlphaNet(policy_size=detected_policy_size).to(self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()
        self.policy_size = detected_policy_size

    def get_action(self, game, db):
        # 1. Encode state
        encoded = game.encode_state(db)
        state_tensor = torch.FloatTensor(encoded).unsqueeze(0).to(self.device)

        # 2. Get policy logits
        with torch.no_grad():
            logits, _ = self.model(state_tensor)

        # 3. Mask illegal actions
        legal_ids = game.get_legal_action_ids()
        mask = torch.full((self.policy_size,), -1e9).to(self.device)
        for aid in legal_ids:
            if aid < self.policy_size:
                mask[int(aid)] = 0.0

        masked_logits = logits.squeeze(0) + mask

        # 4. Argmax
        return int(torch.argmax(masked_logits).item())


def play_match(agent0, agent1, db_content, decks, game_id):
    db = engine_rust.PyCardDatabase(db_content)
    game = engine_rust.PyGameState(db)

    # Select random decks
    p0_deck, p0_lives, p0_energy = random.choice(decks)
    p1_deck, p1_lives, p1_energy = random.choice(decks)

    game.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

    agents = [agent0, agent1]
    step = 0
    while not game.is_terminal() and step < 1000:
        cp = game.current_player
        phase = game.phase

        is_interactive = phase in [-1, 0, 4, 5]

        if is_interactive:
            action = agents[cp].get_action(game, game.db)
            try:
                game.step(action)
            except Exception:
                # print(f"Action {action} failed: {e}")
                # Fallback to random if model fails
                legal = game.get_legal_action_ids()
                if legal:
                    game.step(int(legal[0]))
                else:
                    break
        else:
            game.step(0)
        step += 1

    return game.get_winner(), game.get_player(0).score, game.get_player(1).score, game.turn


def run_tournament(num_games=10):
    with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)

    # Load Decks
    deck_paths = [
        "ai/decks/aqours_cup.txt",
        "ai/decks/hasunosora_cup.txt",
        "ai/decks/liella_cup.txt",
        "ai/decks/muse_cup.txt",
        "ai/decks/nijigaku_cup.txt",
    ]
    decks = []
    for dp in deck_paths:
        if os.path.exists(dp):
            decks.append(parse_deck(dp, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})))

    # Agents
    # Agents
    random_agent = RandomAgent()
    mcts_agent = MCTSAgent(sims=100)
    # resnet_agent = ResNetAgent("ai/models/alphanet_best.pt")

    competitors = {
        "Random": random_agent,
        "MCTS-100": mcts_agent,
        # "ResNet-Standalone": resnet_agent,
        # "Neural-Hybrid (Py)": NeuralHeuristicAgent("ai/models/alphanet_best.pt", sims=100),
        # "Neural-Rust (Full)": NeuralMCTSFullAgent("ai/models/alphanet.onnx", sims=100),
        "Neural-Rust (Hybrid)": HybridMCTSAgent("ai/models/alphanet_best.onnx", sims=100, neural_weight=0.3),
    }

    results = {name: {"wins": 0, "draws": 0, "losses": 0, "total_score": 0, "turns": []} for name in competitors}

    matchups = [("Neural-Rust (Hybrid)", "MCTS-100"), ("Neural-Rust (Hybrid)", "Random")]

    print(f"Starting Tournament: {num_games} rounds per matchup...")
    for p0_name, p1_name in matchups:
        print(f"Matchup: {p0_name} vs {p1_name}")
        for i in tqdm(range(num_games)):
            # Swap sides every game
            if i % 2 == 0:
                winner, s0, s1, t = play_match(competitors[p0_name], competitors[p1_name], db_content, decks, i)
                results[p0_name]["total_score"] += s0
                results[p1_name]["total_score"] += s1
                results[p0_name]["turns"].append(t)
                results[p1_name]["turns"].append(t)
                if winner == 0:
                    results[p0_name]["wins"] += 1
                    results[p1_name]["losses"] += 1
                elif winner == 1:
                    results[p1_name]["wins"] += 1
                    results[p0_name]["losses"] += 1
                else:
                    results[p0_name]["draws"] += 1
                    results[p1_name]["draws"] += 1
            else:
                winner, s1, s0, t = play_match(competitors[p1_name], competitors[p0_name], db_content, decks, i)
                results[p0_name]["total_score"] += s0
                results[p1_name]["total_score"] += s1
                results[p0_name]["turns"].append(t)
                results[p1_name]["turns"].append(t)
                if winner == 0:
                    results[p1_name]["wins"] += 1
                    results[p0_name]["losses"] += 1
                elif winner == 1:
                    results[p0_name]["wins"] += 1
                    results[p1_name]["losses"] += 1
                else:
                    results[p0_name]["draws"] += 1
                    results[p1_name]["draws"] += 1

    print("\nTournament Results:")
    print(f"{'Agent':<18} | {'Wins':<5} | {'Draws':<5} | {'Losses':<5} | {'Avg Score':<10} | {'Avg Turns':<10}")
    print("-" * 75)
    for name, stat in results.items():
        total_games = stat["wins"] + stat["draws"] + stat["losses"]
        avg_score = stat["total_score"] / total_games if total_games > 0 else 0
        avg_turns = sum(stat["turns"]) / len(stat["turns"]) if stat["turns"] else 0
        print(
            f"{name:<18} | {stat['wins']:<5} | {stat['draws']:<5} | {stat['losses']:<5} | {avg_score:<10.2f} | {avg_turns:<10.2f}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=10)
    args = parser.parse_args()

    run_tournament(num_games=args.rounds)
