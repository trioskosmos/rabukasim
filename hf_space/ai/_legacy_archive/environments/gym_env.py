import os
import time

import gymnasium as gym
import numpy as np
from ai.vector_env import VectorGameState
from gymnasium import spaces

# from sb3_contrib import MaskablePPO # Moved to internal use to avoid worker OOM
from engine.game.game_state import initialize_game


class LoveLiveCardGameEnv(gym.Env):
    """
    Love Live Card Game Gymnasium Wrapper
    Default: Plays as Player 0 against a Random or Self-Play Opponent (Player 1)
    """

    metadata = {"render.modes": ["human"]}

    def __init__(self, target_cpu_usage=1.0, deck_type="normal", opponent_type="random"):
        super(LoveLiveCardGameEnv, self).__init__()

        # Init Game
        pid = os.getpid()
        self.deck_type = deck_type
        self.opponent_type = opponent_type
        self.game = initialize_game(deck_type=deck_type)
        self.game.suppress_logs = True  # Holistic speedup: disable rule logging
        self.game.enable_loop_detection = False  # Holistic speedup: disable state hashing
        self.game.fast_mode = True  # Use JIT bytecode for abilities
        self.agent_player_id = 0  # Agent controls player 0

        # Init Opponent
        self.opponent_model = None
        self.opponent_model_path = os.path.join(os.getcwd(), "checkpoints", "self_play_opponent.zip")
        self.last_load_time = 0

        if self.opponent_type == "self_play":
            # Optimization: Restrict torch threads in worker process
            import torch

            torch.set_num_threads(1)
            self._load_opponent()

        # Action Space: 1000
        ACTION_SIZE = 1000
        self.action_space = spaces.Discrete(ACTION_SIZE)

        # Observation Space: STANDARD (2304)
        OBS_SIZE = 2304
        self.observation_space = spaces.Box(low=0, high=1, shape=(OBS_SIZE,), dtype=np.float32)

        # Helper Vector State for Encoding (Reuses the robust logic from VectorEnv)
        self.v_state = VectorGameState(1)

        # CPU Throttling
        self.target_cpu_usage = target_cpu_usage
        self.last_step_time = time.time()

        # Stats tracking
        self.win_count = 0
        self.game_count = 0
        self.last_win_rate = 0.0
        self.total_steps = 0
        self.episode_reward = 0.0
        self.last_score = 0
        self.last_turn = 1
        self.pid = pid

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        # Track stats before reset
        if hasattr(self, "game") and self.game.game_over:
            self.game_count += 1
            if self.game.winner == self.agent_player_id:
                self.win_count += 1
            self.last_win_rate = (self.win_count / self.game_count) * 100

        # Reset Game
        self.game = initialize_game(deck_type=self.deck_type)
        self.game.suppress_logs = True
        self.game.enable_loop_detection = False
        self.game.fast_mode = True

        self.total_steps = 0
        self.episode_reward = 0.0
        self.last_score = 0
        self.last_turn = 1

        # If it's not our turn at the start, we'll need a trick.
        # Gym reset MUST return (obs, info). It can't return a "needs_opponent" signal easily
        # because the VecEnv reset doesn't expect it in the same way 'step' does.
        # HOWEVER, the Vectorized environment calls reset and then step.
        # Let's ensure initialize_game always starts on agent turn or we loop here.

        # For now, we use the legacy behavior if it's the opponent's turn,
        # BUT we'll just return the observation and let the next 'step' handle it if possible.
        # Actually, let's just make it do one random opponent move if it's not our turn yet,
        # or better: initialize_game should be player 0's turn.

        observation = self._get_fast_observation()
        info = {"win_rate": self.last_win_rate}

        # If it's opponent turn, we add a flag to info so the BatchedEnv knows it needs to
        # run an opponent move BEFORE the first agent step.
        if not self.game.is_terminal() and self.game.current_player != self.agent_player_id:
            info["needs_opponent"] = True
            info["opp_obs"] = self._get_fast_observation(self.game.current_player)
            info["opp_masks"] = self.game.get_legal_actions().astype(bool)

        return observation, info

    def step(self, action):
        """
        Execute action for Agent.
        If it's no longer the agent's turn, return 'needs_opponent' signal for batched inference.
        """
        start_time = time.time()
        start_engine = time.perf_counter()
        # 1. Agent's Move
        self.game = self.game.step(action, check_legality=False, in_place=True)
        engine_time = time.perf_counter() - start_engine

        # 2. Check turn
        if not self.game.is_terminal() and self.game.current_player != self.agent_player_id:
            # Need Opponent Move
            obs, reward, terminated, truncated, info = self._signal_opponent_move(start_time)
            info["time_engine"] = engine_time
            # Correct `time_obs` injection is in _finalize_step or _signal_opponent_move
            return obs, reward, terminated, truncated, info

        # 3. Finalize (rewards, terminal check)
        return self._finalize_step(start_time, engine_time_=engine_time)

    def step_opponent(self, action):
        """Executes a move decided by the central batched inference."""
        start_time = time.time()
        self.game = self.game.step(action, check_legality=False, in_place=True)

        # After one opponent move, it might still be their turn
        if not self.game.is_terminal() and self.game.current_player != self.agent_player_id:
            return self._signal_opponent_move(start_time)

        res = self._finalize_step(start_time)

        # CRITICAL: If game ended on opponent move, we MUST trigger auto-reset here
        # so the next agent 'step' doesn't call 'step' on a terminal state.
        if res[2]:  # terminated
            obs, info = self.reset()
            # Wrap terminal info into the result for the agent to see
            res[4]["terminal_observation"] = res[0]
            # Replace observation with the new reset observation
            res = (obs, res[1], res[2], res[3], res[4])

        return res

    def _shape_reward(self, reward: float) -> float:
        """Apply Gym-level reward shaping (Turn penalties, Live bonuses)."""

    def _shape_reward(self, reward: float) -> float:
        """Apply Gym-level reward shaping (Turn penalties, Live bonuses)."""
        # 1. Base State: Ignore Win/Loss, penalize Illegal heavily.
        # We focus purely on "How many lives did I get?" and "How fast?".
        if self.game.winner == -2:
            # Illegal Move / Technical Loss
            reward = -100.0
        else:
            # Neutralize Win/Loss and Heuristic
            reward = 0.0

        # 2. Shaping: Turn Penalty (Major increase to force speed)
        # We penalize -3.0 per turn.
        current_turn = self.game.turn_number
        if current_turn > self.last_turn:
            reward -= 3.0
            self.last_turn = current_turn

        # 3. Shaping: Live Capture Bonus (Primary Objective)
        # +50.0 per live.
        # Win (3 lives) = 150 points. Loss (0 lives) = 0 points.
        current_score = len(self.game.players[self.agent_player_id].success_lives)
        delta = current_score - self.last_score
        if delta > 0:
            reward += delta * 50.0
        self.last_score = current_score
        return reward

    def _signal_opponent_move(self, start_time):
        """Returns the signal needed for BatchedSubprocVecEnv."""
        start_obs = time.perf_counter()
        observation = self._get_fast_observation()
        obs_time = time.perf_counter() - start_obs

        reward = self.game.get_reward(self.agent_player_id)
        reward = self._shape_reward(reward)

        # Get data for opponent's move
        opp_obs = self._get_fast_observation(self.game.current_player)
        opp_masks = self.game.get_legal_actions().astype(bool)

        info = {
            "needs_opponent": True,
            "opp_obs": opp_obs,
            "opp_masks": opp_masks,
            "time_obs": obs_time,  # Inject obs time here too
        }
        return observation, reward, False, False, info

    def _finalize_step(self, start_time, engine_time_=0.0):
        """Standard cleanup and reward calculation."""
        start_obs = time.perf_counter()
        observation = self._get_fast_observation()
        obs_time = time.perf_counter() - start_obs

        reward = self.game.get_reward(self.agent_player_id)
        reward = self._shape_reward(reward)
        terminated = self.game.is_terminal()
        truncated = False

        # Stability
        if not np.isfinite(observation).all():
            observation = np.nan_to_num(observation, 0.0)
        if not np.isfinite(reward):
            reward = 0.0

        self.total_steps += 1
        self.episode_reward += reward

        info = {}
        if terminated:
            info["episode"] = {
                "r": self.episode_reward,
                "l": self.total_steps,
                "win": self.game.winner == self.agent_player_id,
                "phase": self.game.phase.name if hasattr(self.game.phase, "name") else str(self.game.phase),
                "turn": self.game.turn_number,
                "t": round(time.time() - start_time, 6),
            }
        return observation, reward, terminated, False, info

    def _load_opponent(self):
        """Legacy - will be unused in batched mode.
        Only loads if actually requested (e.g. legacy/direct testing)."""
        if self.opponent_type == "self_play" and self.opponent_model is None:
            from sb3_contrib import MaskablePPO

            if os.path.exists(self.opponent_model_path):
                self.opponent_model = MaskablePPO.load(self.opponent_model_path, device="cpu")

    def get_current_info(self):
        """Helper for BatchedSubprocVecEnv to pull info after reset."""
        terminated = self.game.is_terminal()
        if not self.game.is_terminal() and self.game.current_player != self.agent_player_id:
            return self._signal_opponent_move(time.time())[4]

        # Standard info
        info = {}
        if terminated:
            # Reconstruct minimal episode info if needed, but usually this is for reset
            pass
        return info

    def action_masks(self):
        """
        Return mask of legal actions for MaskablePPO
        """
        masks = self.game.get_legal_actions()
        return masks.astype(bool)

    def render(self, mode="human"):
        if mode == "human":
            print(f"Turn: {self.game.turn_number}, Phase: {self.game.phase}, Player: {self.game.current_player}")

    def _get_fast_observation(self, player_idx: int = None) -> np.ndarray:
        """
        Use the JIT-compiled vectorized encoder via VectorGameState Helper.
        Reflects current state into 1-element batches.
        """
        if player_idx is None:
            player_idx = self.agent_player_id

        p = self.game.players[player_idx]
        opp_idx = 1 - player_idx
        opp = self.game.players[opp_idx]

        # Populate v_state buffers (Batch Size=1)
        # 1. Hand
        self.v_state.batch_hand.fill(0)
        for j, c in enumerate(p.hand):
            if j < 60:
                if hasattr(c, "card_id"):
                    self.v_state.batch_hand[0, j] = c.card_id
                elif isinstance(c, (int, np.integer)):
                    self.v_state.batch_hand[0, j] = int(c)

        # 2. Stage
        self.v_state.batch_stage.fill(-1)
        self.v_state.batch_tapped.fill(0)
        self.v_state.batch_energy_count.fill(0)
        for s in range(3):
            self.v_state.batch_stage[0, s] = p.stage[s] if p.stage[s] >= 0 else -1
            self.v_state.batch_tapped[0, s] = 1 if p.tapped_members[s] else 0
            self.v_state.batch_energy_count[0, s] = p.stage_energy_count[s]

        # 3. Opp Stage
        self.v_state.opp_stage.fill(-1)
        self.v_state.opp_tapped.fill(0)
        for s in range(3):
            self.v_state.opp_stage[0, s] = opp.stage[s] if opp.stage[s] >= 0 else -1
            self.v_state.opp_tapped[0, s] = 1 if opp.tapped_members[s] else 0

        # 4. Scores/Lives
        self.v_state.batch_scores[0] = len(p.success_lives)
        self.v_state.opp_scores[0] = len(opp.success_lives)

        # 5. Live Zone (Sync from game state)
        self.v_state.batch_live.fill(0)
        lz = getattr(self.game, "live_zone", [])
        for k, l_card in enumerate(lz):
            if k < 50:
                if hasattr(l_card, "card_id"):
                    self.v_state.batch_live[0, k] = l_card.card_id
                elif isinstance(l_card, (int, np.integer)):
                    self.v_state.batch_live[0, k] = int(l_card)

        # 6. Global Context (Phase, Turn, Deck Counts)
        self.v_state.turn = self.game.turn_number
        self.v_state.batch_global_ctx.fill(0)
        # Map Phase key to Int
        # Phase Enum: START=0, DRAW=1, MAIN=2, PERFORMANCE=3, CLEAR_CHECK=4, TURN_END=5
        # Assuming game.phase is Enum or Int. If Enum, get value.
        p_val = self.game.phase.value if hasattr(self.game.phase, "value") else int(self.game.phase)
        self.v_state.batch_global_ctx[0, 8] = p_val  # Move Phase to index 8
        self.v_state.batch_global_ctx[0, 6] = len(p.main_deck)
        self.v_state.batch_global_ctx[0, 7] = len(opp.main_deck)

        # 6.5 Deck Density (Hearts/Blades)
        d_hearts = 0
        d_blades = 0
        m_db = getattr(self.game, "member_db", {})
        for c_obj in p.main_deck:
            cid = c_obj.card_id if hasattr(c_obj, "card_id") else c_obj
            if cid in m_db:
                card = m_db[cid]
                d_blades += card.blades
                d_hearts += sum(card.hearts)
        self.v_state.batch_global_ctx[0, 8] = d_blades
        self.v_state.batch_global_ctx[0, 9] = d_hearts

        # 7. Opponent History (Trash / Discard Pile)
        self.v_state.batch_opp_history.fill(0)
        # Assuming `opp.discard_pile` is a list of Card objects
        # We want the TOP 12 (Most Recent First).
        if hasattr(opp, "discard_pile"):
            d_pile = opp.discard_pile
            limit = min(len(d_pile), 12)
            for k in range(limit):
                # LIFO: Index 0 = Top (-1), Index 1 = -2
                c = d_pile[-(k + 1)]
                val = 0
                if hasattr(c, "card_id"):
                    val = c.card_id
                elif isinstance(c, (int, np.integer)):
                    val = int(c)

                if val > 0:
                    self.v_state.batch_opp_history[0, k] = val

        # Encode
        batch_obs = self.v_state.get_observations()
        return batch_obs[0]


if __name__ == "__main__":
    # Test Code
    try:
        env = LoveLiveCardGameEnv()
        obs, info = env.reset()
        print("Env Created. Obs shape:", obs.shape)

        terminated = False
        steps = 0
        while not terminated and steps < 20:
            masks = env.action_masks()
            # Random legal action
            legal_indices = np.where(masks)[0]
            if len(legal_indices) == 0:
                print("No legal actions (Game Over?)")
                break

            action = np.random.choice(legal_indices)
            print(f"Agent Action: {action}")
            obs, reward, terminated, truncated, info = env.step(action)
            env.render()
            print(f"Step {steps}: Reward {reward}, Terminated {terminated}")
            steps += 1

        print("Test Complete.")
    except ImportError:
        print("Please install requirements: pip install -r requirements_rl.txt")
    except Exception as e:
        print(f"Test Failed: {e}")
