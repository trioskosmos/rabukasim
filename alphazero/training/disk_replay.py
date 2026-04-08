from __future__ import annotations

import atexit
import json
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True, slots=True)
class DiskReplaySample:
    obs: np.ndarray
    state_context: np.ndarray
    candidate_features: np.ndarray
    candidate_mask: np.ndarray
    policy_target: np.ndarray
    move_utility_target: np.ndarray
    action_index: np.ndarray
    value_target: np.ndarray
    clearability_target: np.ndarray
    utility_target: np.ndarray


class DiskReplayBuffer:
    def __init__(
        self,
        buffer_dir: str | Path,
        *,
        capacity: int,
        obs_dim: int,
        state_context_dim: int,
        candidate_dim: int,
        max_candidates: int = 128,
    ) -> None:
        self.buffer_dir = Path(buffer_dir)
        self.buffer_dir.mkdir(parents=True, exist_ok=True)
        self.lock_dir = self.buffer_dir / ".replay_lock"
        self.lock_owner_path = self.lock_dir / "owner.json"
        self._lock_acquired = False

        self.capacity = max(1, int(capacity))
        self.obs_dim = int(obs_dim)
        self.state_context_dim = int(state_context_dim)
        self.candidate_dim = int(candidate_dim)
        self.max_candidates = max(1, int(max_candidates))

        self._acquire_lock()
        atexit.register(self.close)

        self.obs = self._init_mmap("obs.npy", (self.capacity, self.obs_dim), np.float16)
        self.state_context = self._init_mmap("state_context.npy", (self.capacity, self.state_context_dim), np.float16)
        self.candidate_features = self._init_mmap(
            "candidate_features.npy",
            (self.capacity, self.max_candidates, self.candidate_dim),
            np.float16,
        )
        self.candidate_mask = self._init_mmap("candidate_mask.npy", (self.capacity, self.max_candidates), np.uint8)
        self.policy_target = self._init_mmap("policy_target.npy", (self.capacity, self.max_candidates), np.float16)
        self.move_utility_target = self._init_mmap("move_utility_target.npy", (self.capacity, self.max_candidates), np.float16)
        self.action_index = self._init_mmap("action_index.npy", (self.capacity,), np.uint16)
        self.value_target = self._init_mmap("value_target.npy", (self.capacity,), np.float32)
        self.clearability_target = self._init_mmap("clearability_target.npy", (self.capacity,), np.float32)
        self.utility_target = self._init_mmap("utility_target.npy", (self.capacity,), np.float32)
        self.meta_path = self.buffer_dir / "meta.json"
        self.ptr = 0
        self.count = 0
        self._load_meta()

    def __len__(self) -> int:
        return int(self.count)

    def _pid_is_alive(self, pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    def _read_lock_owner(self) -> dict[str, object]:
        if not self.lock_owner_path.exists():
            return {}
        try:
            return json.loads(self.lock_owner_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _acquire_lock(self) -> None:
        owner_payload = {
            "pid": os.getpid(),
            "buffer_dir": str(self.buffer_dir),
            "acquired_at_unix": time.time(),
        }
        while True:
            try:
                self.lock_dir.mkdir(parents=False, exist_ok=False)
                self.lock_owner_path.write_text(json.dumps(owner_payload, indent=2), encoding="utf-8")
                self._lock_acquired = True
                return
            except FileExistsError:
                existing_owner = self._read_lock_owner()
                existing_pid = int(existing_owner.get("pid", -1)) if existing_owner else -1
                if existing_pid == os.getpid():
                    self._lock_acquired = True
                    return
                if not self._pid_is_alive(existing_pid):
                    shutil.rmtree(self.lock_dir, ignore_errors=True)
                    continue
                raise RuntimeError(
                    f"Disk replay buffer at {self.buffer_dir} is already in use by PID {existing_pid}."
                )

    def _init_mmap(self, filename: str, shape: tuple[int, ...], dtype: Any):
        path = self.buffer_dir / filename
        if path.exists():
            expected_bytes = int(np.prod(shape)) * np.dtype(dtype).itemsize
            if path.stat().st_size != expected_bytes:
                path.unlink()
        mode = "r+" if path.exists() else "w+"
        return np.memmap(path, dtype=dtype, mode=mode, shape=shape)

    def _save_meta(self) -> None:
        with self.meta_path.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "ptr": int(self.ptr),
                    "count": int(self.count),
                    "capacity": int(self.capacity),
                    "max_candidates": int(self.max_candidates),
                    "obs_dim": int(self.obs_dim),
                    "state_context_dim": int(self.state_context_dim),
                    "candidate_dim": int(self.candidate_dim),
                },
                handle,
            )

    def _load_meta(self) -> None:
        if not self.meta_path.exists():
            return
        try:
            payload = json.loads(self.meta_path.read_text(encoding="utf-8"))
        except Exception:
            return
        self.ptr = max(0, min(int(payload.get("ptr", 0)), self.capacity - 1))
        self.count = max(0, min(int(payload.get("count", 0)), self.capacity))

    def add(
        self,
        *,
        obs: np.ndarray,
        state_context: np.ndarray,
        candidate_features: np.ndarray,
        candidate_mask: np.ndarray,
        policy_target: np.ndarray,
        move_utility_target: np.ndarray,
        action_index: int,
        value_target: float,
        clearability_target: float,
        utility_target: float,
    ) -> None:
        idx = int(self.ptr)
        self.obs[idx] = 0
        self.obs[idx] = np.asarray(obs, dtype=np.float16)
        self.state_context[idx] = 0
        self.state_context[idx] = np.asarray(state_context, dtype=np.float16)

        cand = np.asarray(candidate_features, dtype=np.float16)
        if cand.ndim == 1:
            cand = cand.reshape(1, -1)
        limit = min(cand.shape[0], self.max_candidates)
        self.candidate_features[idx] = 0
        if limit > 0:
            self.candidate_features[idx, :limit, : cand.shape[1]] = cand[:limit, : self.candidate_dim]

        mask = np.asarray(candidate_mask, dtype=np.uint8).reshape(-1)
        mask_limit = min(mask.shape[0], self.max_candidates)
        self.candidate_mask[idx] = 0
        if mask_limit > 0:
            self.candidate_mask[idx, :mask_limit] = mask[:mask_limit]

        policy = np.asarray(policy_target, dtype=np.float16).reshape(-1)
        self.policy_target[idx] = 0
        if limit > 0:
            self.policy_target[idx, :limit] = policy[:limit]

        move_target = np.asarray(move_utility_target, dtype=np.float16).reshape(-1)
        self.move_utility_target[idx] = 0
        if limit > 0:
            self.move_utility_target[idx, :limit] = move_target[:limit]

        stored_action_index = max(0, min(int(action_index), max(0, limit - 1)))
        self.action_index[idx] = np.uint16(stored_action_index)
        self.value_target[idx] = np.float32(value_target)
        self.clearability_target[idx] = np.float32(clearability_target)
        self.utility_target[idx] = np.float32(utility_target)

        self.ptr = (self.ptr + 1) % self.capacity
        self.count = min(self.count + 1, self.capacity)
        if self.ptr % 1000 == 0:
            self._save_meta()

    def sample(self, batch_size: int) -> DiskReplaySample | None:
        if self.count <= 0:
            return None
        batch_size = max(1, int(batch_size))
        indices = np.random.choice(self.count, batch_size, replace=True)
        indices.sort()
        return DiskReplaySample(
            obs=self.obs[indices].astype(np.float32),
            state_context=self.state_context[indices].astype(np.float32),
            candidate_features=self.candidate_features[indices].astype(np.float32),
            candidate_mask=self.candidate_mask[indices].astype(np.bool_),
            policy_target=self.policy_target[indices].astype(np.float32),
            move_utility_target=self.move_utility_target[indices].astype(np.float32),
            action_index=self.action_index[indices].astype(np.int64),
            value_target=self.value_target[indices].astype(np.float32),
            clearability_target=self.clearability_target[indices].astype(np.float32),
            utility_target=self.utility_target[indices].astype(np.float32),
        )

    def flush(self) -> None:
        self.obs.flush()
        self.state_context.flush()
        self.candidate_features.flush()
        self.candidate_mask.flush()
        self.policy_target.flush()
        self.move_utility_target.flush()
        self.action_index.flush()
        self.value_target.flush()
        self.clearability_target.flush()
        self.utility_target.flush()
        self._save_meta()

    def close(self) -> None:
        arrays = (
            "obs",
            "state_context",
            "candidate_features",
            "candidate_mask",
            "policy_target",
            "move_utility_target",
            "action_index",
            "value_target",
            "clearability_target",
            "utility_target",
        )
        if any(getattr(self, attr, None) is not None for attr in arrays):
            try:
                self._save_meta()
            except Exception:
                pass
        for attr in arrays:
            arr = getattr(self, attr, None)
            if arr is not None:
                try:
                    arr.flush()
                except Exception:
                    pass
                mmap_obj = getattr(arr, "_mmap", None)
                if mmap_obj is not None:
                    try:
                        mmap_obj.close()
                    except Exception:
                        pass
            setattr(self, attr, None)
        if getattr(self, "_lock_acquired", False):
            try:
                if self.lock_owner_path.exists():
                    self.lock_owner_path.unlink()
            except Exception:
                pass
            try:
                self.lock_dir.rmdir()
            except Exception:
                pass
            self._lock_acquired = False
