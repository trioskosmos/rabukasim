from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
import shutil
import time

import numpy as np


class PersistentBuffer:
    def __init__(
        self,
        buffer_dir,
        max_size,
        obs_dim,
        num_actions,
        sparse_limit=256,
        value_dim=4,
        index_dtype=np.uint16,
    ):
        self.buffer_dir = Path(buffer_dir)
        self.buffer_dir.mkdir(parents=True, exist_ok=True)
        self.lock_dir = self.buffer_dir / ".buffer_lock"
        self.lock_owner_path = self.lock_dir / "owner.json"
        self._lock_acquired = False
        self.max_size = int(max_size)
        self.obs_dim = int(obs_dim)
        self.num_actions = int(num_actions)
        self.sparse_limit = int(sparse_limit)
        self.value_dim = int(value_dim)
        self.mask_bytes = (self.num_actions + 7) // 8
        self.index_dtype = index_dtype

        self._acquire_lock()
        atexit.register(self.close)

        self.obs = self._init_mmap("obs.npy", (self.max_size, self.obs_dim), np.float16)
        self.p_idx = self._init_mmap("p_idx.npy", (self.max_size, self.sparse_limit), self.index_dtype)
        self.p_val = self._init_mmap("p_val.npy", (self.max_size, self.sparse_limit), np.float16)
        self.values = self._init_mmap("values.npy", (self.max_size, self.value_dim), np.float32)
        self.masks = self._init_mmap("masks.npy", (self.max_size, self.mask_bytes), np.uint8)
        self.meta_path = self.buffer_dir / "meta.json"
        self.ptr = 0
        self.count = 0
        self._load_meta()

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
                    f"Persistent buffer at {self.buffer_dir} is already in use by PID {existing_pid}. "
                    "Stop the existing trainer or wait for it to exit."
                )

    def _close_memmap(self, array) -> None:
        if array is None:
            return
        try:
            array.flush()
        except Exception:
            pass
        mmap_obj = getattr(array, "_mmap", None)
        if mmap_obj is not None:
            try:
                mmap_obj.close()
            except Exception:
                pass

    def _init_mmap(self, filename, shape, dtype):
        path = self.buffer_dir / filename
        if path.exists():
            expected_bytes = int(np.prod(shape)) * np.dtype(dtype).itemsize
            actual_bytes = path.stat().st_size
            if actual_bytes != expected_bytes:
                path.unlink()
        mode = "r+" if path.exists() else "w+"
        return np.memmap(path, dtype=dtype, mode=mode, shape=shape)

    def _load_meta(self):
        if not self.meta_path.exists():
            return
        with open(self.meta_path, "r", encoding="utf-8") as handle:
            meta = json.load(handle)
        loaded_ptr = int(meta.get("ptr", 0))
        loaded_count = int(meta.get("count", 0))
        if loaded_ptr >= self.max_size or loaded_count > self.max_size:
            return
        self.ptr = loaded_ptr
        self.count = loaded_count

    def _save_meta(self):
        with open(self.meta_path, "w", encoding="utf-8") as handle:
            json.dump({"ptr": self.ptr, "count": self.count, "value_dim": self.value_dim}, handle)

    def add(self, obs, sparse_policy, targets, mask):
        idx = self.ptr
        self.obs[idx] = np.clip(obs, -65504.0, 65504.0).astype(np.float16)

        p_indices, p_values = sparse_policy
        if len(p_indices) == 0:
            p_indices = np.array([0], dtype=np.uint16)
            p_values = np.array([0.0], dtype=np.float16)

        limit = min(len(p_indices), self.sparse_limit)
        self.p_idx[idx, :limit] = p_indices[:limit]
        self.p_val[idx, :limit] = p_values[:limit]
        if limit < self.sparse_limit:
            self.p_idx[idx, limit:] = 0
            self.p_val[idx, limit:] = 0

        self.values[idx] = np.asarray(targets, dtype=np.float32)
        bits = np.zeros(self.num_actions, dtype=np.uint8)
        valid_indices = np.asarray(mask, dtype=np.int32)
        valid_indices = valid_indices[(0 <= valid_indices) & (valid_indices < self.num_actions)]
        bits[valid_indices] = 1
        self.masks[idx] = np.packbits(bits, bitorder="little")

        self.ptr = (self.ptr + 1) % self.max_size
        self.count = min(self.count + 1, self.max_size)
        if self.ptr % 1000 == 0:
            self._save_meta()

    def sample(self, batch_size):
        if self.count == 0:
            return None

        batch_size = int(batch_size)
        indices = np.random.choice(self.count, batch_size, replace=True)
        indices.sort()
        batch_obs = self.obs[indices].astype(np.float32)
        batch_values = self.values[indices].astype(np.float32)
        batch_p_idx = self.p_idx[indices].astype(np.int32)
        batch_p_val = self.p_val[indices].astype(np.float32)

        row_v = np.repeat(np.arange(batch_size, dtype=np.int32), self.sparse_limit)
        col_v = batch_p_idx.ravel()
        val_v = batch_p_val.ravel()
        nz = val_v > 0
        sparse_policy = (row_v[nz], col_v[nz], val_v[nz])

        batch_masks_raw = self.masks[indices]
        mask_np = np.unpackbits(batch_masks_raw, axis=1, bitorder="little")[:, : self.num_actions].astype(np.bool_)
        return batch_obs, sparse_policy, mask_np, batch_values

    def flush(self):
        self.obs.flush()
        self.p_idx.flush()
        self.p_val.flush()
        self.values.flush()
        self.masks.flush()
        self._save_meta()

    def close(self):
        obs = getattr(self, "obs", None)
        p_idx = getattr(self, "p_idx", None)
        p_val = getattr(self, "p_val", None)
        values = getattr(self, "values", None)
        masks = getattr(self, "masks", None)
        if any(item is not None for item in (obs, p_idx, p_val, values, masks)):
            try:
                self._save_meta()
            except Exception:
                pass
        for attr in ("obs", "p_idx", "p_val", "values", "masks"):
            self._close_memmap(getattr(self, attr, None))
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
