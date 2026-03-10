import os
import numpy as np
import torch
from pathlib import Path
import json


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
    def __init__(self, buffer_dir, max_size, obs_dim, num_actions, sparse_limit=256, index_dtype=np.uint16):
        self.buffer_dir = Path(buffer_dir)
        self.buffer_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_size = max_size
        self.obs_dim = obs_dim
        self.num_actions = num_actions
        self.sparse_limit = sparse_limit
        self.mask_bytes = (num_actions + 7) // 8
        self.index_dtype = index_dtype
        
        # Initialize memory-mapped files
        self.obs = self._init_mmap("obs.npy", (max_size, obs_dim), np.float16)
        self.p_idx = self._init_mmap("p_idx.npy", (max_size, sparse_limit), self.index_dtype)
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
        if path.exists():
            # Validate file size matches expected shape.
            # On Windows, opening with wrong shape can cause a silent hang or OOM.
            expected_bytes = int(np.prod(shape)) * np.dtype(dtype).itemsize
            actual_bytes = path.stat().st_size
            if actual_bytes != expected_bytes:
                print(f"[Buffer] Size mismatch for {filename} "
                      f"(expected {expected_bytes:,}, got {actual_bytes:,}). Recreating.")
                path.unlink()
        mode = 'r+' if path.exists() else 'w+'
        return np.memmap(path, dtype=dtype, mode=mode, shape=shape)


    def _load_meta(self):
        if self.meta_path.exists():
            with open(self.meta_path, "r") as f:
                meta = json.load(f)
                loaded_ptr = meta.get("ptr", 0)
                loaded_count = meta.get("count", 0)
                if loaded_ptr >= self.max_size or loaded_count > self.max_size:
                    print(f"[Buffer] Meta pointer out of bounds (ptr {loaded_ptr}, max {self.max_size}). Resetting.")
                    self.ptr = 0
                    self.count = 0
                else:
                    self.ptr = loaded_ptr
                    self.count = loaded_count

    def _save_meta(self):
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
        if len(p_indices) == 0:
            # Fallback for empty policy (e.g., mapping failure)
            # Store at least one index to avoid potential issues with some consumers
            p_indices = np.array([0], dtype=np.uint16)
            p_values = np.array([0.0], dtype=np.float16)
            
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


class PriorityPersistentBuffer(PersistentBuffer):
    """
    Priority Experience Replay buffer that weights new experiences higher.
    Extends PersistentBuffer with priority-based sampling.
    """
    def __init__(self, buffer_dir, max_size, obs_dim, num_actions, sparse_limit=256, 
                 index_dtype=np.uint16, alpha=0.6, beta_start=0.4, beta_end=1.0):
        super().__init__(buffer_dir, max_size, obs_dim, num_actions, sparse_limit, index_dtype)
        
        self.alpha = alpha  # Priority exponent
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.beta = beta_start
        
        # Priority array (higher = more important = higher sampling probability)
        self.priorities_path = self.buffer_dir / "priorities.npy"
        self.priorities = self._init_mmap("priorities.npy", (max_size,), np.float32)
        
        # Initialize priorities to 1.0
        if self.count == 0:
            self.priorities[:] = 1.0
        
        self.max_priority = 1.0
        
    def _init_mmap(self, filename, shape, dtype):
        path = self.buffer_dir / filename
        mode = 'r+' if path.exists() else 'w+'
        return np.memmap(path, dtype=dtype, mode=mode, shape=shape)
    
    def _load_priorities(self):
        """Load priorities from disk if available"""
        if self.priorities_path.exists():
            try:
                with open(self.priorities_path, 'rb') as f:
                    loaded = np.load(f)
                self.priorities[:len(loaded)] = loaded
                self.max_priority = float(np.max(self.priorities[:self.count])) if self.count > 0 else 1.0
            except Exception as e:
                print(f"Warning: Could not load priorities: {e}")
                self._initialize_priorities()
        else:
            self._initialize_priorities()
    
    def _initialize_priorities(self):
        """Initialize priorities for existing buffer"""
        if self.count > 0:
            self.priorities[:self.count] = 1.0  # Initial uniform priority
            self.max_priority = 1.0
        self._save_priorities()
        self._save_priorities()
    
    def _save_priorities(self):
        """Save priorities to disk"""
        # Use tolist() to avoid pickle issues
        with open(self.priorities_path, 'wb') as f:
            np.save(f, np.array(self.priorities[:self.count], dtype=np.float32))
    
    def add(self, obs, sparse_policy, targets, mask):
        """Add new experience with maximum priority (new experiences have highest priority)"""
        # Store data first
        idx = self.ptr
        
        # Clip to float16 range before cast
        obs_clipped = np.clip(obs, -65504.0, 65504.0)
        self.obs[idx] = obs_clipped.astype(np.float16)
        
        # Sparse Policy
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
            
        # Targets
        self.values[idx] = targets
        
        # Mask (bitpacking)
        bits = np.zeros(self.num_actions, dtype=np.uint8)
        valid_indices = mask[mask < self.num_actions]
        bits[valid_indices] = 1
        packed = np.packbits(bits, bitorder='little')
        self.masks[idx] = packed
        
        # Set priority to max (new experiences have highest priority)
        self.priorities[idx] = self.max_priority
        
        # Advance pointer
        self.ptr = (self.ptr + 1) % self.max_size
        self.count = min(self.count + 1, self.max_size)
        
        # Periodically flush meta
        if self.ptr % 1000 == 0:
            self._save_meta()
            self._save_priorities()
    
    def sample(self, batch_size, beta=None):
        """
        Sample batch with priority-based probabilities.
        
        P(i) = priority[i]^alpha / sum(priority^alpha)
        
        weights = (count * P(i))^-beta / max_weights^-beta
        """
        if self.count == 0: return None
        
        # Update beta (annealing)
        if beta is not None:
            self.beta = beta
        
        # Compute sampling probabilities
        priorities = self.priorities[:self.count]
        probs = priorities ** self.alpha
        probs = probs / probs.sum()
        
        # Sample indices based on priorities
        indices = np.random.choice(self.count, batch_size, replace=True, p=probs)
        indices.sort()
        
        # Compute importance sampling weights
        weights = (self.count * probs[indices]) ** (-self.beta)
        weights = weights / weights.max()  # Normalize
        
        # --- Observations: single batched memmap read ---
        batch_obs = self.obs[indices].astype(np.float32)
        batch_val = self.values[indices]
        
        # --- Policy: Sparse pieces for GPU scatter ---
        batch_p_idx = self.p_idx[indices].astype(np.int32)
        batch_p_val = self.p_val[indices].astype(np.float32)
        
        row_v = np.repeat(np.arange(batch_size, dtype=np.int32), self.sparse_limit)
        col_v = batch_p_idx.ravel()
        val_v = batch_p_val.ravel()
        nz = val_v > 0
        
        sparse_pol = (row_v[nz], col_v[nz], val_v[nz])
        
        # --- Mask: single np.unpackbits call over the full batch ---
        batch_masks_raw = self.masks[indices]
        msk_np = np.unpackbits(
            batch_masks_raw, axis=1, bitorder='little'
        )[:, :self.num_actions].astype(np.bool_)
        
        # Return weights for importance sampling
        weights_np = weights.astype(np.float32)
        
        return batch_obs, sparse_pol, msk_np, batch_val, weights_np
    
    def update_priorities(self, indices, priorities):
        """Update priorities for sampled experiences (after computing TD errors)"""
        for idx, pri in zip(indices, priorities):
            if 0 <= idx < self.count:
                self.priorities[idx] = pri
                self.max_priority = max(self.max_priority, pri)
        
        # Periodically save
        if len(indices) > 0 and indices[0] % 1000 == 0:
            self._save_priorities()
    
    def flush(self):
        super().flush()
        self._save_priorities()
    
    def set_beta(self, beta):
        """Manually set beta for importance sampling"""
        self.beta = beta
    
    def get_beta(self, iteration, total_iterations, beta_start=None, beta_end=None):
        """
        Compute beta with linear annealing.
        beta = beta_start + (beta_end - beta_start) * iteration / total_iterations
        """
        if beta_start is None:
            beta_start = self.beta_start
        if beta_end is None:
            beta_end = self.beta_end
        
        fraction = min(1.0, iteration / max(1, total_iterations))
        return beta_start + (beta_end - beta_start) * fraction
