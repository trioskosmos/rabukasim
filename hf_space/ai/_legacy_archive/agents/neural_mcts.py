import os
import sys

import torch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import engine_rust

from ai.models.training_config import POLICY_SIZE
from ai.training.train import AlphaNet


class NeuralHeuristicAgent:
    """
    An agent that uses the ResNet (Intuition) to filter moves,
    and MCTS (Calculation) to verify them.
    """

    def __init__(self, model_path, sims=100):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        checkpoint = torch.load(model_path, map_location=self.device)
        state_dict = (
            checkpoint["model_state"] if isinstance(checkpoint, dict) and "model_state" in checkpoint else checkpoint
        )

        self.model = AlphaNet(policy_size=POLICY_SIZE).to(self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()

        self.sims = sims

    def get_action(self, game, db):
        # 1. Get Logits from ResNet
        encoded = game.encode_state(db)
        state_tensor = torch.FloatTensor(encoded).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits, score_eval = self.model(state_tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        legal_actions = game.get_legal_action_ids()
        if not legal_actions:
            return 0
        if len(legal_actions) == 1:
            return int(legal_actions[0])

        # 2. Run engine's fast MCTS (Random Rollout based)
        # This provides a 'ground truth' sanity check.
        mcts_suggestions = game.get_mcts_suggestions(self.sims, engine_rust.SearchHorizon.TurnEnd)
        mcts_visits = {int(a): v for a, s, v in mcts_suggestions}
        mcts_scores = {int(a): s for a, s, v in mcts_suggestions}

        # 3. Combine Intuition (Probs) and Calculation (MCTS Win Rate)
        # We calculate a combined score for each legal action
        best_action = legal_actions[0]
        max_score = -1e9

        for aid in legal_actions:
            aid = int(aid)
            prior = probs[aid] if aid < len(probs) else 0.0

            # Convert MCTS visits/score to a win probability [0, 1]
            # MCTS score is usually total reward / visits.
            # We'll use visits as a proxy for confidence.
            win_prob = mcts_scores.get(aid, 0.0)
            conf = mcts_visits.get(aid, 0) / (self.sims + 1)

            # Strategy:
            # If MCTS finds a move that is significantly better than PASS (0),
            # we favor it even if ResNet is biased towards 0.

            # Simple weighted sum
            # Prior (0.3) + WinProb (0.7)
            score = 0.3 * prior + 0.7 * win_prob

            # Bonus for MCTS confidence
            score += 0.2 * conf

            if score > max_score:
                max_score = score
                best_action = aid

        return best_action


class NeuralMCTSFullAgent:
    """
    AlphaZero-style agent that uses the Rust-implemented NeuralMCTS.
    This is much faster than the Python hybrid because the entire
    MCTS search and NN evaluation happens inside the Rust core.
    """

    def __init__(self, model_path, sims=100):
        # We assume engine_rust has been compiled with ORT support.
        # This will load the ONNX model once into a background session.
        self.mcts = engine_rust.PyNeuralMCTS(model_path)
        self.sims = sims

    def get_action(self, game, db):
        # suggestions: Vec<(action_id, score, visit_count)>
        suggestions = self.mcts.get_suggestions(game, self.sims)
        if not suggestions:
            # Fallback to random or pass if something is wrong
            return 0

        # NeuralMCTS returns suggestions sorted by visit count descending
        # so [0][0] is the most visited action.
        return int(suggestions[0][0])


class HybridMCTSAgent:
    """
    The ultimate agent. It uses the Rust-implemented HybridMCTS
    which blends Neural intuition with Heuristic calculation.
    Target speed is <0.1s/move at 100 sims.
    """

    def __init__(self, model_path, sims=100, neural_weight=0.3):
        self.mcts = engine_rust.PyHybridMCTS(model_path, neural_weight)
        self.sims = sims

    def get_action(self, game, db):
        suggestions = self.mcts.get_suggestions(game, self.sims)
        if not suggestions:
            return 0
        return int(suggestions[0][0])
