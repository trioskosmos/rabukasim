from engine.game.game_state import GameState


class Agent:
    def choose_action(self, state: GameState, player_id: int) -> int:
        raise NotImplementedError
