import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

# Assuming GameState interface from existing code
# We import the actual GameState to be safe
from engine.game.game_state import GameState


@dataclass
class HeuristicMCTSConfig:
    num_simulations: int = 100
    c_puct: float = 1.4
    depth_limit: int = 50


class HeuristicNode:
    def __init__(self, parent=None, prior=1.0):
        self.parent = parent
        self.children: Dict[int, "HeuristicNode"] = {}
        self.visit_count = 0
        self.value_sum = 0.0
        self.prior = prior
        self.untried_actions: List[int] = []
        self.player_just_moved = -1

    @property
    def value(self):
        if self.visit_count == 0:
            return 0
        return self.value_sum / self.visit_count

    def ucb_score(self, c_puct):
        # Standard UCB1
        if self.visit_count == 0:
            return float("inf")

        # UCB = Q + c * sqrt(ln(N_parent) / N_child)
        # Note: AlphaZero uses a slightly different variant with Priors.
        # Since we don't have a policy network, we assume uniform priors or just use standard UCB.
        # Let's use standard UCB for "MCTS without training"

        parent_visits = self.parent.visit_count if self.parent else 1
        exploitation = self.value
        exploration = c_puct * math.sqrt(math.log(parent_visits) / self.visit_count)
        return exploitation + exploration


class HeuristicMCTS:
    """
    MCTS that uses random rollouts and heuristics instead of a Neural Network.
    This works 'without training' because it relies on the game rules (simulation)
    and hard-coded domain knowledge (rollout policy / terminal evaluation).
    """

    def __init__(self, config: HeuristicMCTSConfig):
        self.config = config
        self.root = None

    def search(self, state: GameState) -> int:
        self.root = HeuristicNode(prior=1.0)
        # We need to copy state for the root? Actually search loop copies it.
        # But we need to know legal actions.
        legal = state.get_legal_actions()
        self.root.untried_actions = [i for i, x in enumerate(legal) if x]
        self.root.player_just_moved = 1 - state.current_player  # Parent moved previously

        for _ in range(self.config.num_simulations):
            node = self.root
            sim_state = state.copy()

            # 1. Selection
            path = [node]
            while node.children and not node.untried_actions:
                action, node = self._select_best_step(node)
                sim_state = sim_state.step(action)
                path.append(node)

            # 2. Expansion
            if node.untried_actions:
                action = node.untried_actions.pop()
                sim_state = sim_state.step(action)
                child = HeuristicNode(parent=node, prior=1.0)
                child.player_just_moved = 1 - sim_state.current_player  # The player who took 'action'
                node.children[action] = child
                node = child
                path.append(node)

            # 3. Simulation (Rollout)
            # Run until terminal or depth limit
            depth = 0
            while not sim_state.is_terminal() and depth < self.config.depth_limit:
                legal = sim_state.get_legal_actions()
                legal_indices = [i for i, x in enumerate(legal) if x]
                if not legal_indices:
                    break
                # Random Policy (No training required)
                action = np.random.choice(legal_indices)
                sim_state = sim_state.step(action)
                depth += 1

            # 4. Backpropagation
            # If terminal, get reward. If cutoff, use heuristic.
            if sim_state.is_terminal():
                # reward is relative to current_player
                # We need reward from perspective of root player?
                # Usually standard MCTS backprops values flipping each layer
                reward = sim_state.get_reward(state.current_player)  # 1.0 if root wins
            else:
                reward = self._heuristic_eval(sim_state, state.current_player)

            for i, n in enumerate(reversed(path)):
                n.visit_count += 1
                # If n.player_just_moved == root_player, this node represents a state AFTER root moved.
                # So its value should be positive if root won.
                # Standard: if player_just_moved won, +1.

                # Simpler view: All values tracked relative to Root Player.
                n.value_sum += reward

        # Select best move (robust child)
        if not self.root.children:
            return 0  # Fallback

        best_action = max(self.root.children.items(), key=lambda item: item[1].visit_count)[0]
        return best_action

    def _select_best_step(self, node: HeuristicNode) -> Tuple[int, HeuristicNode]:
        # Standard UCB
        best_score = -float("inf")
        best_item = None

        for action, child in node.children.items():
            score = child.ucb_score(self.config.c_puct)
            if score > best_score:
                best_score = score
                best_item = (action, child)

        return best_item

    def _heuristic_eval(self, state: GameState, root_player: int) -> float:
        """
        Evaluate state without a neural network.
        Logic: More blades/hearts/lives = Better.
        """
        p = state.players[root_player]
        opp = state.players[1 - root_player]

        # Score = (My Lives - Opp Lives) + 0.1 * (My Power - Opp Power)
        score = 0.0
        score += (len(p.success_lives) - len(opp.success_lives)) * 0.5

        my_power = p.get_total_blades(state.member_db)
        opp_power = opp.get_total_blades(state.member_db)
        score += (my_power - opp_power) * 0.05

        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, score))


if __name__ == "__main__":
    pass
