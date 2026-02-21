"""
Neural Network for AlphaZero-style training.

This module provides a simple neural network architecture for policy and value
prediction. For a production system, you would use a more sophisticated
architecture (e.g., ResNet with attention) and train on GPU with PyTorch/TensorFlow.
"""

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class NetworkConfig:
    """Configuration for AlphaZero Network"""

    input_size: int = 800  # Feature-based encoding (32 floats per card slot)
    # Size of observation vector (Matches GameState.get_observation)
    hidden_size: int = 256
    num_hidden_layers: int = 3
    action_size: int = 1000  # Size of action space (Matches GameState.get_legal_actions)
    learning_rate: float = 0.001
    l2_reg: float = 0.0001


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))


def relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0, x)


def softmax(x: np.ndarray) -> np.ndarray:
    exp_x = np.exp(x - np.max(x))
    return exp_x / exp_x.sum()


def tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(x)


class SimpleNetwork:
    """
    Simple feedforward neural network for policy and value prediction.

    Architecture:
    - Input layer (observation)
    - Hidden layers with ReLU
    - Policy head (softmax over actions)
    - Value head (tanh for [-1, 1])
    """

    def __init__(self, config: NetworkConfig = None):
        self.config = config or NetworkConfig()
        self._init_weights()

    def _init_weights(self) -> None:
        """Initialize weights using He initialization"""
        config = self.config

        # Shared layers
        self.hidden_weights = []
        self.hidden_biases = []

        in_size = config.input_size
        for _ in range(config.num_hidden_layers):
            std = np.sqrt(2.0 / in_size)
            w = np.random.randn(in_size, config.hidden_size) * std
            b = np.zeros(config.hidden_size)
            self.hidden_weights.append(w)
            self.hidden_biases.append(b)
            in_size = config.hidden_size

        # Policy head
        std = np.sqrt(2.0 / config.hidden_size)
        self.policy_weight = np.random.randn(config.hidden_size, config.action_size) * std
        self.policy_bias = np.zeros(config.action_size)

        # Value head
        self.value_weight = np.random.randn(config.hidden_size, 1) * std
        self.value_bias = np.zeros(1)

    def forward(self, observation: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Forward pass.

        Args:
            observation: Input features

        Returns:
            (policy probabilities, value)
        """
        # Store activations for backward pass
        self.activations = [observation]

        x = observation
        for w, b in zip(self.hidden_weights, self.hidden_biases, strict=False):
            x = relu(x @ w + b)
            self.activations.append(x)

        # Policy head
        policy_logits = x @ self.policy_weight + self.policy_bias
        policy = softmax(policy_logits)

        # Value head
        value = tanh(x @ self.value_weight + self.value_bias)[0]

        self.last_policy_logits = policy_logits
        self.last_value = value

        return policy, value

    def predict(self, state) -> Tuple[np.ndarray, float]:
        """Get policy and value for a game state"""
        obs = state.get_observation()
        policy, value = self.forward(obs)

        # Mask illegal actions
        legal = state.get_legal_actions()
        masked_policy = policy * legal
        if masked_policy.sum() > 0:
            masked_policy /= masked_policy.sum()
        else:
            # Fall back to uniform over legal
            masked_policy = legal.astype(np.float32)
            masked_policy /= masked_policy.sum()

        return masked_policy, value

    def predict_batch(self, states) -> list:
        """Get policy and value for a batch of game states"""
        if not states:
            return []

        obs = np.array([s.get_observation() for s in states])
        policies, values = self.forward(obs)

        results = []
        for i, (policy, value) in enumerate(zip(policies, values)):
            legal = states[i].get_legal_actions()
            masked_policy = policy * legal
            if masked_policy.sum() > 0:
                masked_policy /= masked_policy.sum()
            else:
                # Fall back to uniform over legal
                masked_policy = legal.astype(np.float32)
                masked_policy /= masked_policy.sum()
            results.append((masked_policy, value))

        return results

    def train_step(
        self, observations: np.ndarray, target_policies: np.ndarray, target_values: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        One training step (Vectorized).

        Args:
            observations: Batch of observations (batch_size, input_size)
            target_policies: Target policy distributions (batch_size, action_size)
            target_values: Target values (batch_size,)

        Returns:
            (total_loss, policy_loss, value_loss)
        """
        batch_size = len(observations)
        config = self.config

        # 1. Forward Pass (Batch)
        pred_policy, pred_value = self.forward(observations)
        # pred_policy: (B, action_size)
        # pred_value: (B,)

        # 2. Loss Calculation
        # Policy loss: Cross-entropy
        # Mean over batch
        policy_loss = -np.mean(np.sum(target_policies * np.log(pred_policy + 1e-8), axis=1))

        # Value loss: MSE
        value_loss = np.mean((pred_value - target_values) ** 2)

        total_loss = policy_loss + value_loss

        # 3. Backward Pass (Gradients)
        # d_policy = (pred - target) / batch_size  (Gradient of Mean Cross Entropy)
        # However, we treat the sum of gradients and then average manually update,
        # so let's stick to the convention: dL/dLogits = (pred - target) / B
        d_policy_logits = (pred_policy - target_policies) / batch_size

        # d_value = 2 * (pred - target) * tanh'(pre_tanh) /  batch_size
        # tanh' = 1 - tanh^2 = 1 - pred_value^2
        d_value_out = 2 * (pred_value - target_values) / batch_size
        d_value_pre_tanh = d_value_out * (1 - pred_value**2)

        # Gradients for heads
        # hidden_out: (B, hidden_size)  (Last activation)
        hidden_out = self.activations[-1]

        # d_Weights = Input.T @ Error
        # Policy: (H, B) @ (B, A) -> (H, A)
        grad_policy_w = hidden_out.T @ d_policy_logits
        grad_policy_b = np.sum(d_policy_logits, axis=0)

        # Value: (H, B) @ (B, 1) -> (H, 1)
        # d_value_pre_tanh needs shape (B, 1)
        d_value_pre_tanh = d_value_pre_tanh.reshape(-1, 1)
        grad_value_w = hidden_out.T @ d_value_pre_tanh
        grad_value_b = np.sum(d_value_pre_tanh, axis=0)

        # Backprop through hidden layers
        # d_hidden_last = d_policy @ W_p.T + d_value @ W_v.T
        # (B, A) @ (A, H) + (B, 1) @ (1, H) -> (B, H)
        d_hidden = d_policy_logits @ self.policy_weight.T + d_value_pre_tanh @ self.value_weight.T

        # Store grads to apply later
        grads_w = []
        grads_b = []

        # Iterate backwards through hidden layers
        for layer_idx in range(len(self.hidden_weights) - 1, -1, -1):
            # ReLU derivative: mask where activation > 0
            # self.activations has inputs at [0], layer 1 out at [1], etc.
            # layer_idx maps to weights[layer_idx], which produces activations[layer_idx+1]
            mask = (self.activations[layer_idx + 1] > 0).astype(np.float32)
            d_hidden = d_hidden * mask

            prev_activation = self.activations[layer_idx]

            # Gradients for this layer
            # (In, B) @ (B, Out) -> (In, Out)
            g_w = prev_activation.T @ d_hidden
            g_b = np.sum(d_hidden, axis=0)

            grads_w.insert(0, g_w)
            grads_b.insert(0, g_b)

            if layer_idx > 0:
                # Propagate to previous layer
                d_hidden = d_hidden @ self.hidden_weights[layer_idx].T

        # 4. Apply Gradients (SGD + L2)
        for i in range(len(self.hidden_weights)):
            # L2: w = w - lr * (grad + l2 * w)
            self.hidden_weights[i] -= config.learning_rate * (grads_w[i] + config.l2_reg * self.hidden_weights[i])
            self.hidden_biases[i] -= config.learning_rate * grads_b[i]

        self.policy_weight -= config.learning_rate * (grad_policy_w + config.l2_reg * self.policy_weight)
        self.policy_bias -= config.learning_rate * grad_policy_b

        self.value_weight -= config.learning_rate * (grad_value_w + config.l2_reg * self.value_weight)
        self.value_bias -= config.learning_rate * grad_value_b

        return total_loss, policy_loss, value_loss

    def save(self, filepath: str) -> None:
        """Save network weights to file"""
        # Use allow_pickle and object-array conversion to handle inhomogeneous layer shapes
        np.savez(
            filepath,
            hidden_weights=np.array(self.hidden_weights, dtype=object),
            hidden_biases=np.array(self.hidden_biases, dtype=object),
            policy_weight=self.policy_weight,
            policy_bias=self.policy_bias,
            value_weight=self.value_weight,
            value_bias=self.value_bias,
        )

    def load(self, filepath: str) -> None:
        """Load network weights from file"""
        data = np.load(filepath, allow_pickle=True)
        # Convert object arrays back to lists of arrays
        self.hidden_weights = list(data["hidden_weights"])
        self.hidden_biases = list(data["hidden_biases"])
        self.policy_weight = data["policy_weight"]
        self.policy_bias = data["policy_bias"]
        self.value_weight = data["value_weight"]
        self.value_bias = data["value_bias"]


class NeuralMCTS:
    """MCTS that uses a neural network for policy and value with parallel search"""

    def __init__(
        self, network: SimpleNetwork, num_simulations: int = 100, batch_size: int = 8, virtual_loss: float = 3.0
    ):
        self.network = network
        self.num_simulations = num_simulations
        self.batch_size = batch_size
        self.c_puct = 1.4
        self.virtual_loss = virtual_loss
        self.root = None

    def get_policy_value(self, state) -> Tuple[np.ndarray, float]:
        """Get policy and value from neural network"""
        return self.network.predict(state)

    def search(self, state) -> np.ndarray:
        """Run MCTS with neural network guidance (Parallel)"""
        from ai.mcts import MCTSNode

        # Initial root expansion (always blocking)
        policy, _ = self.get_policy_value(state)
        self.root = MCTSNode()
        self.root.expand(state, policy)

        # We can't batch perfectly if simulations not divisible, but approx is fine
        num_batches = (self.num_simulations + self.batch_size - 1) // self.batch_size

        for _ in range(num_batches):
            self._simulate_batch(state, self.batch_size)

        # Return visit count distribution
        # Note: visits length must match action_size from network config or game state
        # MCTSNode children keys are actions.
        # We need a fixed size array for the policy target.
        action_size = len(state.get_legal_actions())
        visits = np.zeros(action_size, dtype=np.float32)

        for action, child in self.root.children.items():
            visits[action] = child.visit_count

        if visits.sum() > 0:
            visits /= visits.sum()

        return visits

    def _simulate_batch(self, root_state, batch_size) -> None:
        """Run a batch of MCTS simulations parallelized via Virtual Loss"""
        paths = []
        leaf_nodes = []
        request_states = []

        # 1. Selection Phase for K threads
        for _ in range(batch_size):
            node = self.root
            state = root_state.copy()
            path = [node]

            # Selection
            while node.is_expanded() and not state.is_terminal():
                action, child = node.select_child(self.c_puct)

                # Apply Virtual Loss immediately so subsequent selections in this batch diverge
                child.virtual_loss += self.virtual_loss

                state = state.step(action)
                node = child
                path.append(node)

            paths.append((path, state))
            leaf_nodes.append(node)

            if not state.is_terminal():
                request_states.append(state)

        # 2. Evaluation Phase (Batched)
        responses = []
        if request_states:
            if hasattr(self.network, "predict_batch"):
                responses = self.network.predict_batch(request_states)
            else:
                responses = [self.network.predict(s) for s in request_states]

        # 3. Expansion & Backpropagation Phase
        resp_idx = 0
        for i in range(batch_size):
            path, state = paths[i]
            leaf = leaf_nodes[i]

            value = 0.0

            if state.is_terminal():
                value = state.get_reward(root_state.current_player)
            else:
                # Retrieve prediction
                policy, v = responses[resp_idx]
                resp_idx += 1
                value = v

                # Expand
                leaf.expand(state, policy)

            # Backpropagate
            for node in reversed(path):
                node.visit_count += 1
                node.value_sum += value

                # Remove Virtual Loss (except from root which we didn't add to?
                # Wait, select_child returns child, and we added to child.
                # Root is path[0]. path[1] is first child.
                # So we should only subtract from path[1:] if we logic matches.
                # But wait, did we add to root? No.
                # So check: if node != self.root: node.virtual_loss -= ...
                if node != self.root:
                    node.virtual_loss -= self.virtual_loss

                value = -value


def train_network(network: SimpleNetwork, training_data: list, epochs: int = 10, batch_size: int = 32) -> None:
    """
    Train network on self-play data.

    Args:
        network: Network to train
        training_data: List of (states, policies, winner) tuples
        epochs: Number of training epochs
        batch_size: Batch size for training
    """
    print(f"Training on {len(training_data)} games...")

    # Flatten data with rewards
    all_states = []
    all_policies = []
    all_values = []

    for states, policies, winner, r0, r1 in training_data:
        for i, (s, p) in enumerate(zip(states, policies, strict=False)):
            all_states.append(s)
            all_policies.append(p)

            # Value from perspective of player who made the move
            player_idx = i % 2

            # Use actual calculated reward (with score shaping)
            if player_idx == 0:
                all_values.append(r0)
            else:
                all_values.append(r1)

    all_states = np.array(all_states)
    all_policies = np.array(all_policies)
    all_values = np.array(all_values)

    n_samples = len(all_states)

    for epoch in range(epochs):
        # Shuffle data
        indices = np.random.permutation(n_samples)
        total_loss = 0.0

        for i in range(0, n_samples, batch_size):
            batch_idx = indices[i : i + batch_size]
            loss, p_loss, v_loss = network.train_step(
                all_states[batch_idx], all_policies[batch_idx], all_values[batch_idx]
            )
            total_loss += loss

        num_batches = (n_samples + batch_size - 1) // batch_size
        print(f"Epoch {epoch + 1}/{epochs}, Loss: {total_loss / num_batches:.4f}")


if __name__ == "__main__":
    # Test network
    from engine.game.game_state import initialize_game

    print("Testing neural network...")
    config = NetworkConfig()
    network = SimpleNetwork(config)

    # Test forward pass
    state = initialize_game()
    policy, value = network.predict(state)

    print(f"Policy shape: {policy.shape}")
    print(f"Policy sum: {policy.sum():.4f}")
    print(f"Value: {value:.4f}")

    # Test training step
    obs = state.get_observation()
    target_p = np.zeros(config.action_size)
    target_p[0] = 0.8
    target_p[1] = 0.2
    target_v = 0.5

    loss, p_loss, v_loss = network.train_step(obs.reshape(1, -1), target_p.reshape(1, -1), np.array([target_v]))
    print(f"Training loss: {loss:.4f} (policy: {p_loss:.4f}, value: {v_loss:.4f})")
