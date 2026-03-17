import os

import numpy as np
from gymnasium import spaces
from stable_baselines3.common.vec_env import VecEnv

# RUST Engine Toggle
USE_RUST_ENGINE = os.getenv("USE_RUST_ENGINE", "0") == "1"

if USE_RUST_ENGINE:
    print(" [VecEnvAdapter] RUST Engine ENABLED (USE_RUST_ENGINE=1)")
    from ai.vec_env_rust import RustVectorEnv

    # Wrapper to inject MCTS_SIMS from env
    class VectorEnvAdapter(RustVectorEnv):
        def __init__(self, num_envs, action_space=None, opp_mode=0, force_start_order=-1):
            mcts_sims = int(os.getenv("MCTS_SIMS", "50"))
            super().__init__(num_envs, action_space, opp_mode, force_start_order, mcts_sims)
else:
    # GPU Environment Toggle
    USE_GPU_ENV = os.getenv("USE_GPU_ENV", "0") == "1" or os.getenv("GPU_ENV", "0") == "1"

    if USE_GPU_ENV:
        try:
            from ai.vector_env_gpu import HAS_CUDA, VectorEnvGPU

            if HAS_CUDA:
                print(" [VecEnvAdapter] GPU Environment ENABLED (USE_GPU_ENV=1)")
            else:
                print(" [VecEnvAdapter] Warning: USE_GPU_ENV=1 but CUDA not available. Falling back to CPU.")
                USE_GPU_ENV = False
        except ImportError as e:
            print(f" [VecEnvAdapter] Warning: Failed to import GPU env: {e}. Falling back to CPU.")
            USE_GPU_ENV = False

    if not USE_GPU_ENV:
        from ai.environments.vector_env import VectorGameState

    class VectorEnvAdapter(VecEnv):
        """
        Wraps the Numba-accelerated VectorGameState to be compatible with Stable-Baselines3.

        When USE_GPU_ENV=1 is set, uses VectorEnvGPU for GPU-resident environments
        with zero-copy observation transfer to PyTorch.
        """

        metadata = {"render_modes": ["rgb_array"]}

        def __init__(self, num_envs, action_space=None, opp_mode=0, force_start_order=-1):
            self.num_envs = num_envs
            self.use_gpu = USE_GPU_ENV

            # For Legacy Adapter: Read MCTS_SIMS env var or default
            mcts_sims = int(os.getenv("MCTS_SIMS", "50"))

            if self.use_gpu:
                # GPU Env doesn't support MCTS yet, pass legacy args
                self.game_state = VectorEnvGPU(num_envs, opp_mode=opp_mode, force_start_order=force_start_order)
            else:
                self.game_state = VectorGameState(num_envs, opp_mode=opp_mode, force_start_order=force_start_order)

            # Use Dynamic Dimension from Engine (IMAX 8k, Standard 2k, or Compressed 512)
            obs_dim = self.game_state.obs_dim
            self.observation_space = spaces.Box(low=0, high=1, shape=(obs_dim,), dtype=np.float32)
            if action_space is None:
                # Check if game_state has defined action_space_dim (default 2000)
                if hasattr(self.game_state, "action_space_dim"):
                    action_dim = self.game_state.action_space_dim
                else:
                    # Fallback: The Engine always produces 2000-dim masks (Action IDs 0-1999)
                    action_dim = 2000

                action_space = spaces.Discrete(action_dim)

            # Manually initialize VecEnv fields to bypass render_modes crash
            self.action_space = action_space
            self.actions = None
            self.render_mode = None

            # Track previous scores for delta-based rewards
            self.prev_scores = np.zeros(num_envs, dtype=np.int32)
            self.prev_turns = np.zeros(num_envs, dtype=np.int32)
            # Pre-allocate empty infos list (reused when no envs done)
            self._empty_infos = [{} for _ in range(num_envs)]

        def reset(self):
            """
            Reset all environments.
            """
            self.game_state.reset()
            self.prev_scores.fill(0)  # Reset score tracking
            self.prev_turns.fill(0)  # Reset turn tracking

            obs = self.game_state.get_observations()
            # Convert CuPy to NumPy if using GPU (SB3 expects numpy)
            if self.use_gpu:
                try:
                    import cupy as cp

                    if isinstance(obs, cp.ndarray):
                        obs = cp.asnumpy(obs)
                except:
                    pass
            return obs

        def step_async(self, actions):
            """
            Tell the generic VecEnv wrapper to hold these actions.
            """
            self.actions = actions

        def step_wait(self):
            """
            Execute the actions on the Numba engine.
            """
            # Ensure actions are int32 for Numba (avoid copy if already correct type)
            if self.actions.dtype != np.int32:
                actions_int32 = self.actions.astype(np.int32)
            else:
                actions_int32 = self.actions

            # Step the engine
            obs, rewards, dones, infos = self.game_state.step(actions_int32)

            # Convert CuPy arrays to NumPy if using GPU (SB3 expects numpy)
            if self.use_gpu:
                try:
                    import cupy as cp

                    if isinstance(obs, cp.ndarray):
                        obs = cp.asnumpy(obs)
                    if isinstance(rewards, cp.ndarray):
                        rewards = cp.asnumpy(rewards)
                    if isinstance(dones, cp.ndarray):
                        dones = cp.asnumpy(dones)
                except:
                    pass

            return obs, rewards, dones, infos

        def close(self):
            pass

        def get_attr(self, attr_name, indices=None):
            """
            Return attribute from vectorized environments.
            """
            if attr_name == "action_masks":
                # Return function reference or result? SB3 usually looks for method
                pass
            return [None] * self.num_envs

        def set_attr(self, attr_name, value, indices=None):
            pass

        def env_method(self, method_name, *method_args, **method_kwargs):
            """
            Call instance methods of vectorized environments.
            """
            if method_name == "action_masks":
                # Return list of masks for all envs
                masks = self.game_state.get_action_masks()
                if self.use_gpu:
                    try:
                        import cupy as cp

                        if isinstance(masks, cp.ndarray):
                            masks = cp.asnumpy(masks)
                    except:
                        pass
                return [masks[i] for i in range(self.num_envs)]

            return [None] * self.num_envs

        def env_is_wrapped(self, wrapper_class, indices=None):
            return [False] * self.num_envs

        def action_masks(self):
            """
            Required for MaskablePPO. Returns (num_envs, action_space.n) boolean array.
            """
            masks = self.game_state.get_action_masks()
            if self.use_gpu:
                try:
                    import cupy as cp

                    if isinstance(masks, cp.ndarray):
                        masks = cp.asnumpy(masks)
                except:
                    pass
            return masks
