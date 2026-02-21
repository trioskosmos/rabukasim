import engine_rust


class RustMCTSAgent:
    def __init__(self, sims=1000):
        self.sims = sims

    def choose_action(self, gs: engine_rust.PyGameState):
        # The Rust engine can run MCTS internally and set the move
        # But we might want to just get the action index.
        # Actually PyGameState has step_opponent_mcts which executes it.
        # We'll use a wrapper that returns the suggested action.
        pass

    def get_best_move_incremental(self, gs: engine_rust.PyGameState, sims_per_step=100):
        # This will be used for the "Live Update" feature
        # We need to expose a way to get MCTS stats from Rust
        # Currently the Rust bindings don't expose the search tree.
        # I might need to update the Rust bindings to return the action values.
        pass
