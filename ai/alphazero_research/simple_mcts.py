import math
import random


class MCTSNode:
    def __init__(self, state, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children = []
        self.visits = 0
        self.value = 0.0
        self.untried_actions = state.get_legal_action_ids()

    def uct_select_child(self, exploration_weight=1.41):
        return max(
            self.children,
            key=lambda c: (c.value / c.visits) + exploration_weight * math.sqrt(math.log(self.visits) / c.visits),
        )

    def add_child(self, action, state):
        child = MCTSNode(state, parent=self, action=action)
        self.untried_actions.remove(action)
        self.children.append(child)
        return child

    def update(self, result):
        self.visits += 1
        self.value += result


class SimpleMCTS:
    """
    A readable, pure-Python MCTS implementation for research and debugging.
    """

    def __init__(self, simulation_limit=100, horizon=20):
        self.simulation_limit = simulation_limit
        self.horizon = horizon

    def search(self, initial_state):
        root = MCTSNode(initial_state)

        for _ in range(self.simulation_limit):
            node = root
            state = initial_state.clone()

            # 1. Select
            while not node.untried_actions and node.children:
                node = node.uct_select_child()
                state = state.step(node.action, check_legality=False, in_place=True)

            # 2. Expand
            if node.untried_actions:
                action = random.choice(node.untried_actions)
                state = state.step(action, check_legality=False, in_place=True)
                node = node.add_child(action, state)

            # 3. Rollout (Simulation)
            depth = 0
            while not state.is_terminal() and depth < self.horizon:
                legal_actions = state.get_legal_action_ids()
                if not legal_actions:
                    break
                action = random.choice(legal_actions)
                state = state.step(action, check_legality=False, in_place=True)
                depth += 1

            # 4. Backpropagate
            # Simple reward: 1 for win, 0 for loss/draw
            # Assuming player 0 is the agent we are optimizing for
            result = 1.0 if state.winner == 0 else 0.0
            while node:
                node.update(result)
                node = node.parent

        return sorted(root.children, key=lambda c: c.visits, reverse=True)[0].action


if __name__ == "__main__":
    # Example usage (requires engine setup)
    print("SimpleMCTS Research Script Loaded.")
