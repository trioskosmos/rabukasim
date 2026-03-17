"""
MCTS (Monte Carlo Tree Search) implementation for AlphaZero-style self-play.

This module provides a pure MCTS implementation that can work with or without
a neural network. When using a neural network, it uses the network's value
and policy predictions to guide the search.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from engine.game.game_state import GameState


@dataclass
class MCTSConfig:
    """Configuration for MCTS"""

    num_simulations: int = 10  # Number of simulations per move
    c_puct: float = 1.4  # Exploration constant
    dirichlet_alpha: float = 0.3  # For root exploration noise
    dirichlet_epsilon: float = 0.25  # Fraction of noise added to prior
    virtual_loss: float = 3.0  # Virtual loss for parallel search
    temperature: float = 1.0  # Policy temperature


class MCTSNode:
    """A node in the MCTS tree"""

    def __init__(self, prior: float = 1.0):
        self.visit_count = 0
        self.value_sum = 0.0
        self.virtual_loss = 0.0  # Accumulated virtual loss
        self.prior = prior  # Prior probability from policy network
        self.children: Dict[int, "MCTSNode"] = {}
        self.state: Optional[GameState] = None

    @property
    def value(self) -> float:
        """Average value of this node (adjusted for virtual loss)"""
        if self.visit_count == 0:
            return 0.0 - self.virtual_loss
        # Q = (W - VL) / N
        # Standard approach: subtract virtual loss from value sum logic?
        # Or (W / N) - VL?
        # AlphaZero: Q = (W - v_loss) / N
        return (self.value_sum - self.virtual_loss) / (self.visit_count + 1e-8)

    def is_expanded(self) -> bool:
        return len(self.children) > 0

    def select_child(self, c_puct: float) -> Tuple[int, "MCTSNode"]:
        """Select child with highest UCB score"""
        best_score = -float("inf")
        best_action = -1
        best_child = None

        # Virtual loss increases denominator in some implementations,
        # but here we just penalize Q and rely on high N to reduce UCB exploration if visited.
        # But wait, we want to discourage visiting the SAME node.
        # So we penalize Q.

        sqrt_parent_visits = math.sqrt(self.visit_count)

        for action, child in self.children.items():
            # UCB formula: Q + c * P * sqrt(N) / (1 + n)
            # Child value includes its own virtual loss penalty
            ucb = child.value + c_puct * child.prior * sqrt_parent_visits / (1 + child.visit_count)

            if ucb > best_score:
                best_score = ucb
                best_action = action
                best_child = child

        return best_action, best_child

    def expand(self, state: GameState, policy: np.ndarray) -> None:
        """Expand node with children for all legal actions"""
        self.state = state
        legal_actions = state.get_legal_actions()

        for action in range(len(legal_actions)):
            if legal_actions[action]:
                self.children[action] = MCTSNode(prior=policy[action])


class MCTS:
    """Monte Carlo Tree Search with AlphaZero-style neural network guidance"""

    def __init__(self, config: MCTSConfig = None):
        self.config = config or MCTSConfig()
        self.root = None

    def reset(self) -> None:
        """Reset the search tree"""
        self.root = None

    def get_policy_value(self, state: GameState) -> Tuple[np.ndarray, float]:
        """
        Get policy and value from neural network.

        For now, uses uniform policy and random rollout value.
        Replace with actual neural network for full AlphaZero.
        """
        # Uniform policy over legal actions
        legal = state.get_legal_actions()
        policy = legal.astype(np.float32)
        if policy.sum() > 0:
            policy /= policy.sum()

        # Random rollout for value estimation
        value = self._random_rollout(state)

        return policy, value

    def _random_rollout(self, state: GameState, max_steps: int = 50) -> float:
        """Perform random rollout to estimate value"""
        current = state.copy()
        current_player = state.current_player

        for _ in range(max_steps):
            if current.is_terminal():
                return current.get_reward(current_player)

            legal = current.get_legal_actions()
            legal_indices = np.where(legal)[0]

            if len(legal_indices) == 0:
                return 0.0

            action = np.random.choice(legal_indices)
            current = current.step(action)

        # Game didn't finish - use heuristic
        return self._heuristic_value(current, current_player)

    def _heuristic_value(self, state: GameState, player_idx: int) -> float:
        """Simple heuristic value for non-terminal states"""
        p = state.players[player_idx]
        opp = state.players[1 - player_idx]

        # Compare success lives
        my_lives = len(p.success_lives)
        opp_lives = len(opp.success_lives)

        if my_lives > opp_lives:
            return 0.5 + 0.1 * (my_lives - opp_lives)
        elif opp_lives > my_lives:
            return -0.5 - 0.1 * (opp_lives - my_lives)

        # Compare board strength
        my_blades = p.get_total_blades(state.member_db)
        opp_blades = opp.get_total_blades(state.member_db)

        return 0.1 * (my_blades - opp_blades) / 10.0

    def search(self, state: GameState) -> np.ndarray:
        """
        Run MCTS and return action probabilities.

        Args:
            state: Current game state

        Returns:
            Action probabilities based on visit counts
        """
        # Initialize root
        policy, _ = self.get_policy_value(state)
        self.root = MCTSNode()
        self.root.expand(state, policy)

        # Add exploration noise at root
        self._add_exploration_noise(self.root)

        # Run simulations
        for _ in range(self.config.num_simulations):
            self._simulate(state)

        # Return visit count distribution
        visits = np.zeros(len(policy), dtype=np.float32)
        for action, child in self.root.children.items():
            visits[action] = child.visit_count

        # Apply temperature
        if self.config.temperature == 0:
            # Greedy - pick best
            best = np.argmax(visits)
            visits = np.zeros_like(visits)
            visits[best] = 1.0
        else:
            # Softmax with temperature
            visits = np.power(visits, 1.0 / self.config.temperature)

        if visits.sum() > 0:
            visits /= visits.sum()

        return visits

    def _add_exploration_noise(self, node: MCTSNode) -> None:
        """Add Dirichlet noise to root node for exploration"""
        actions = list(node.children.keys())
        if not actions:
            return

        noise = np.random.dirichlet([self.config.dirichlet_alpha] * len(actions))

        for i, action in enumerate(actions):
            child = node.children[action]
            child.prior = (1 - self.config.dirichlet_epsilon) * child.prior + self.config.dirichlet_epsilon * noise[i]

    def _simulate(self, root_state: GameState) -> None:
        """Run one MCTS simulation"""
        node = self.root
        state = root_state.copy()
        search_path = [node]

        # Selection - traverse tree until we reach a leaf
        while node.is_expanded() and not state.is_terminal():
            action, node = node.select_child(self.config.c_puct)
            state = state.step(action)
            search_path.append(node)

        # Get value for this node
        if state.is_terminal():
            value = state.get_reward(root_state.current_player)
        else:
            # Expansion
            policy, value = self.get_policy_value(state)
            node.expand(state, policy)

        # Backpropagation
        for node in reversed(search_path):
            node.visit_count += 1
            node.value_sum += value
            value = -value  # Flip value for opponent's perspective

    def select_action(self, state: GameState, greedy: bool = False) -> int:
        """Select action based on MCTS policy"""
        temp = self.config.temperature
        if greedy:
            self.config.temperature = 0

        action_probs = self.search(state)

        if greedy:
            self.config.temperature = temp
            action = np.argmax(action_probs)
        else:
            action = np.random.choice(len(action_probs), p=action_probs)

        return action


def play_game(mcts1: MCTS, mcts2: MCTS, verbose: bool = True) -> int:
    """
    Play a complete game between two MCTS agents.

    Returns:
        Winner (0 or 1) or 2 for draw
    """
    from engine.game.game_state import initialize_game

    state = initialize_game()
    mcts_players = [mcts1, mcts2]

    move_count = 0
    max_moves = 500

    while not state.is_terminal() and move_count < max_moves:
        current_mcts = mcts_players[state.current_player]
        action = current_mcts.select_action(state)

        if verbose and move_count % 10 == 0:
            print(f"Move {move_count}: Player {state.current_player}, Phase {state.phase.name}, Action {action}")

        state = state.step(action)
        move_count += 1

    if state.is_terminal():
        winner = state.get_winner()
        if verbose:
            print(f"Game over after {move_count} moves. Winner: {winner}")
        return winner
    else:
        if verbose:
            print(f"Game exceeded {max_moves} moves, declaring draw")
        return 2


def self_play(num_games: int = 10, simulations: int = 50) -> List[Tuple[List, List, int]]:
    """
    Run self-play games to generate training data.

    Returns:
        List of (states, policies, winner) tuples for training
    """
    training_data = []
    config = MCTSConfig(num_simulations=simulations)

    for game_idx in range(num_games):
        from game.game_state import initialize_game

        state = initialize_game()
        mcts = MCTS(config)

        game_states = []
        game_policies = []

        move_count = 0
        max_moves = 500

        while not state.is_terminal() and move_count < max_moves:
            # Get MCTS policy
            policy = mcts.search(state)

            # Store state and policy for training
            game_states.append(state.get_observation())
            game_policies.append(policy)

            # Select action
            action = np.random.choice(len(policy), p=policy)
            state = state.step(action)

            # Reset MCTS tree for next move
            mcts.reset()
            move_count += 1

        winner = state.get_winner() if state.is_terminal() else 2
        training_data.append((game_states, game_policies, winner))

        print(f"Game {game_idx + 1}/{num_games} complete. Moves: {move_count}, Winner: {winner}")

    return training_data


if __name__ == "__main__":
    print("Testing MCTS self-play...")

    # Quick test game
    config = MCTSConfig(num_simulations=20)  # Low for testing
    mcts1 = MCTS(config)
    mcts2 = MCTS(config)

    winner = play_game(mcts1, mcts2, verbose=True)
    print(f"Test game complete. Winner: {winner}")
