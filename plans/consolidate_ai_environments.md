# AI Environments Consolidation Plan

## Summary
Consolidate backup/legacy files in `ai/environments/` and `ai/utils/` that are no longer used.

## Current State Analysis

### ai/environments/
| File | Size | Status | Used By |
|------|------|--------|---------|
| vector_env.py | 51366 | **KEEP** - Current main version | vec_env_adapter.py |
| vector_env_legacy.py | 11107 | DELETE - Unused | None |
| vector_env_backup.py | 48823 | DELETE - Unused | None |
| vector_env_gpu.py | 34354 | KEEP - GPU version | None (opt-in) |
| vec_env_adapter.py | 7405 | **KEEP** - Active | train_vectorized.py, train_gpu_workers.py, train_bc.py |
| vec_env_adapter_legacy.py | 3821 | DELETE - Unused | None |
| rust_env_lite.py | 2469 | KEEP - Rust version | None |

### ai/utils/
| File | Size | Status | Used By |
|------|------|--------|---------|
| obs_adapters.py | 6820 | **KEEP** - Has 8192/2048/320/128 dims | None (available) |
| obs_adapters_backup.py | 6741 | DELETE - Unused (missing 2048 dim) | None |

## Actions to Take

### Phase 1: Delete unused backup files
- [ ] Delete `ai/environments/vector_env_legacy.py`
- [ ] Delete `ai/environments/vector_env_backup.py`
- [ ] Delete `ai/environments/vec_env_adapter_legacy.py`
- [ ] Delete `ai/utils/obs_adapters_backup.py`

### Phase 2: Optional - Archive instead of delete (if you want safety)
- [ ] Create `ai/environments/archive/` directory
- [ ] Move backup files to archive instead of deleting

## Files After Consolidation

### ai/environments/
```
vector_env.py       - Main CPU vector environment
vector_env_gpu.py   - GPU vector environment  
vec_env_adapter.py - SB3-compatible wrapper
rust_env_lite.py   - Rust engine lite version
```

### ai/utils/
```
obs_adapters.py    - Observation encoder (all dimensions)
```

## Notes
- The `ai/environments/vec_env_adapter.py` has a reference to `ai.vec_env_rust` which doesn't exist - this may need investigation
- Some "keep" files are not actively imported but provide alternative functionality that may be needed
