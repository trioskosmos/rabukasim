import os
import sys

import numpy as np
import torch
import torch.multiprocessing as mp

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecEnv


# Worker function to run in a separate process
def worker_process(remote, parent_remote, num_envs):
    parent_remote.close()

    # Initialize the Numba-optimized vector environment
    env = VectorEnvAdapter(num_envs=num_envs)

    try:
        while True:
            cmd, data = remote.recv()
            if cmd == "step":
                # data is actions
                obs, rewards, dones, infos = env.step(data)
                remote.send((obs, rewards, dones, infos))
            elif cmd == "reset":
                obs = env.reset()
                remote.send(obs)
            elif cmd == "close":
                env.close()
                remote.close()
                break
            elif cmd == "get_attr":
                remote.send(getattr(env, data))
            else:
                raise NotImplementedError(f"Worker received unknown command: {cmd}")
    except KeyboardInterrupt:
        print("Worker interrupt.")
    finally:
        env.close()


class DistributedVectorEnv(VecEnv):
    """
    A distributed Vector Environment that manages multiple worker processes,
    each running a Numba-optimized VectorEnvAdapter.

    Structure:
    Main Process (PPO) -> DistributedVectorEnv
        -> Worker Process 1 -> VectorEnvAdapter (N=1024) -> Numba
        -> Worker Process 2 -> VectorEnvAdapter (N=1024) -> Numba
        ...
    """

    def __init__(self, num_workers: int, envs_per_worker: int):
        self.num_workers = num_workers
        self.envs_per_worker = envs_per_worker
        self.total_envs = num_workers * envs_per_worker

        # Define spaces (assuming consistent across all envs)
        # We create a dummy adapter just to get the spaces
        dummy = VectorEnvAdapter(num_envs=1)
        observation_space = dummy.observation_space
        action_space = dummy.action_space
        dummy.close()
        del dummy

        super().__init__(self.total_envs, observation_space, action_space)

        self.closed = False
        self.waiting = False
        self.remotes, self.work_remotes = zip(*[mp.Pipe() for _ in range(num_workers)])
        self.processes = []

        for work_remote, remote in zip(self.work_remotes, self.remotes):
            p = mp.Process(target=worker_process, args=(work_remote, remote, envs_per_worker))
            p.daemon = True  # Kill if main process dies
            p.start()
            self.processes.append(p)
            work_remote.close()

    def step_async(self, actions):
        # Split actions into chunks for each worker
        chunks = np.array_split(actions, self.num_workers)
        for remote, action_chunk in zip(self.remotes, chunks):
            remote.send(("step", action_chunk))
        self.waiting = True

    def step_wait(self):
        results = [remote.recv() for remote in self.remotes]
        self.waiting = False

        # Aggregate results
        obs_list, rews_list, dones_list, infos_list = zip(*results)

        return (
            np.concatenate(obs_list),
            np.concatenate(rews_list),
            np.concatenate(dones_list),
            # Infos are lists of dicts, so we just add them
            sum(infos_list, []),
        )

    def reset(self):
        for remote in self.remotes:
            remote.send(("reset", None))

        results = [remote.recv() for remote in self.remotes]
        return np.concatenate(results)

    def close(self):
        if self.closed:
            return
        if self.waiting:
            for remote in self.remotes:
                remote.recv()
        for remote in self.remotes:
            remote.send(("close", None))
        for p in self.processes:
            p.join()
        self.closed = True

    def get_attr(self, attr_name, indices=None):
        # Simplified: return from first worker
        self.remotes[0].send(("get_attr", attr_name))
        return self.remotes[0].recv()

    def set_attr(self, attr_name, value, indices=None):
        pass

    def env_method(self, method_name, *method_args, **method_kwargs):
        pass

    def env_is_wrapped(self, wrapper_class, indices=None):
        return [False] * self.total_envs


def run_training():
    print("========================================================")
    print(" LovecaSim - DISTRIBUTED GPU TRAINING (Async Workers)   ")
    print("========================================================")

    # Configuration
    TRAIN_ENVS = int(os.getenv("TRAIN_ENVS", "16384"))  # Increased default
    NUM_WORKERS = int(os.getenv("NUM_WORKERS", "4"))
    ENVS_PER_WORKER = TRAIN_ENVS // NUM_WORKERS

    TRAIN_STEPS = int(os.getenv("TRAIN_STEPS", "100_000_000"))
    BATCH_SIZE = int(os.getenv("TRAIN_BATCH_SIZE", "32768"))  # Increased batch size for GPU

    print(f" [Config] Total Envs: {TRAIN_ENVS}")
    print(f" [Config] Workers: {NUM_WORKERS} (Envs/Worker: {ENVS_PER_WORKER})")
    print(f" [Config] Batch Size: {BATCH_SIZE}")
    print(f" [Config] Architecture: Main(PPO) <-> {NUM_WORKERS} Workers <-> Numba(Vectors)")

    print(f" [Init] Launching {NUM_WORKERS} distributed worker processes...")
    vec_env = DistributedVectorEnv(NUM_WORKERS, ENVS_PER_WORKER)

    print(" [Init] Creating PPO Model...")
    model = PPO(
        "MlpPolicy",
        vec_env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=128,
        batch_size=BATCH_SIZE,
        n_epochs=4,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01,
        tensorboard_log="./logs/gpu_workers_tensorboard/",
        device="cuda" if torch.cuda.is_available() else "cpu",
    )

    print(f" [Init] Model Device: {model.device}")

    try:
        print(" [Train] Starting Distributed Training...")
        model.learn(total_timesteps=TRAIN_STEPS, progress_bar=True)
    except KeyboardInterrupt:
        print("\n [Stop] Interrupted by user.")
    finally:
        print(" [Done] Saving model and closing workers...")
        model.save("./checkpoints/gpu_workers_final")
        vec_env.close()


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    run_training()
