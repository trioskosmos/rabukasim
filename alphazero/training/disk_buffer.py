import os
import numpy as np
import torch
from pathlib import Path

class PersistentBuffer:
    """
    Experimental experience replay buffer that stores large datasets on disk
    using numpy.memmap to bypass system RAM limitations.
    
    Layout (for 20,500 obs and 22,000 actions):
    - obs: float16 (2 bytes per element)
    - policy_indices: uint16 (sparse non-zero indices, max 128+ sims)
    - policy_values: float16 (non-zero values)
    - values: float32 (3 targets: win_prob, momentum, efficiency)
    - masks: uint8 (bitpacked 22,000 bits)
    """
    def __init__(self, buffer_dir, max_size, obs_dim, num_actions, sparse_limit=256):
        self.buffer_dir = Path(buffer_dir)
        self.buffer_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_size = max_size
        self.obs_dim = obs_dim
        self.num_actions = num_actions
        self.sparse_limit = sparse_limit
        self.mask_bytes = (num_actions + 7) // 8
        
        # Initialize memory-mapped files
        self.obs = self._init_mmap("obs.npy", (max_size, obs_dim), np.float16)
        self.p_idx = self._init_mmap("p_idx.npy", (max_size, sparse_limit), np.uint16)
        self.p_val = self._init_mmap("p_val.npy", (max_size, sparse_limit), np.float16)
        self.values = self._init_mmap("values.npy", (max_size, 3), np.float32)
        self.masks = self._init_mmap("masks.npy", (max_size, self.mask_bytes), np.uint8)
        
        # Metadata
        self.meta_path = self.buffer_dir / "meta.json"
        self.ptr = 0
        self.count = 0
        self._load_meta()

    def _init_mmap(self, filename, shape, dtype):
        path = self.buffer_dir / filename
        mode = 'r+' if path.exists() else 'w+'
        return np.memmap(path, dtype=dtype, mode=mode, shape=shape)

    def _load_meta(self):
        import json
        if self.meta_path.exists():
            with open(self.meta_path, "r") as f:
                meta = json.load(f)
                self.ptr = meta.get("ptr", 0)
                self.count = meta.get("count", 0)

    def _save_meta(self):
        import json
        with open(self.meta_path, "w") as f:
            json.dump({"ptr": self.ptr, "count": self.count}, f)

    def add(self, obs, sparse_policy, targets, mask):
        """
        obs: np.array (float32)
        sparse_policy: (indices, values)
        targets: np.array (float32, 3)
        mask: np.array (uint32/int32 indices)
        """
        # Store metadata
        idx = self.ptr
        
        # Clip to float16 range before cast — raw engine values (card IDs, counts) can exceed ±65504
        obs_clipped = np.clip(obs, -65504.0, 65504.0)
        self.obs[idx] = obs_clipped.astype(np.float16)
        
        # 2. Sparse Policy
        p_indices, p_values = sparse_policy
        limit = min(len(p_indices), self.sparse_limit)
        self.p_idx[idx, :limit] = p_indices[:limit]
        self.p_val[idx, :limit] = p_values[:limit]
        if limit < self.sparse_limit:
            self.p_idx[idx, limit:] = 0
            self.p_val[idx, limit:] = 0
            
        # 3. Targets
        self.values[idx] = targets
        
        # 4. Mask (bitpacking) — fully vectorised via np.packbits
        bits = np.zeros(self.num_actions, dtype=np.uint8)
        valid_indices = mask[mask < self.num_actions]
        bits[valid_indices] = 1
        packed = np.packbits(bits, bitorder='little')
        self.masks[idx] = packed
        
        # Advance pointer
        self.ptr = (self.ptr + 1) % self.max_size
        self.count = min(self.count + 1, self.max_size)
        
        # Periodically flush meta (every 1000 samples)
        if self.ptr % 1000 == 0:
            self._save_meta()

    def sample(self, batch_size):
        if self.count == 0: return None
        
        indices = np.random.choice(self.count, batch_size, replace=True)
        # Sort indices to improve memmap access locality (sequential-ish disk reads)
        indices.sort()
        
        # --- Observations: single batched memmap read ---
        batch_obs = self.obs[indices].astype(np.float32)
        batch_val = self.values[indices]
        
        # --- Policy: Sparse pieces for GPU scatter ---
        batch_p_idx = self.p_idx[indices].astype(np.int32)    # (B, sparse_limit)
        batch_p_val = self.p_val[indices].astype(np.float32)  # (B, sparse_limit)
        
        row_v = np.repeat(np.arange(batch_size, dtype=np.int32), self.sparse_limit)
        col_v = batch_p_idx.ravel()
        val_v = batch_p_val.ravel()
        nz = val_v > 0
        
        sparse_pol = (row_v[nz], col_v[nz], val_v[nz])
        
        # --- Mask: single np.unpackbits call over the full batch ---
        batch_masks_raw = self.masks[indices]  # (B, mask_bytes)
        msk_np = np.unpackbits(
            batch_masks_raw, axis=1, bitorder='little'
        )[:, :self.num_actions].astype(np.bool_)
        
        return batch_obs, sparse_pol, msk_np, batch_val

    def flush(self):
        self.obs.flush()
        self.p_idx.flush()
        self.p_val.flush()
        self.values.flush()
        self.masks.flush()
        self._save_meta()
