# Rust Build Speed Optimizations

## Changes Made

### 1. `.cargo/config.toml` Optimizations
- **LLD Linker**: Already configured (`rust-lld.exe`) - fastest linker on Windows
- **All CPU cores**: `jobs = 0` uses all available cores
- **Pipelining**: Starts compiling dependent crates sooner
- **Sparse registry**: Faster crate resolution (Rust 1.70+)
- **CLI git**: Faster git operations

### 2. `Cargo.toml` Profile Changes

#### `[profile.dev]`
- `debug = "line-tables-only"` - Smaller/faster than full debug info
- `split-debuginfo = "packed"` - Faster linking on Windows
- Dependencies at `opt-level = 1` (vs 0) - better runtime with minimal compile cost

#### `[profile.test]`
- `debug = "line-tables-only"` - Minimal but useful for panic traces
- `split-debuginfo = "packed"` - Faster test linking
- Dependencies at `opt-level = 1` - faster test execution

#### New Profiles
- **`bench-fast`**: For benchmarks when you need results quickly (opt-level 2, no LTO)
- **`test-fast`**: Tests with opt-level 1 for code, opt-level 2 for deps

## Commands to Use

```bash
# Standard test (faster than before due to dep optimizations)
cargo test

# Fast test (optimized tests - slightly slower compile, faster run)
cargo test-fast

# Standard benchmark
cargo bench

# Fast benchmark (faster compile, good enough performance)
cargo bench-fast
```

## Additional Recommendations

### 1. sccache (for CI/shared environments)
```bash
cargo install sccache
# Set env: SCCACHE_CACHE_SIZE=10G
```

### 2. If you have 32GB+ RAM, consider mold linker (Linux) or faster settings:
Add to `.cargo/config.toml` under `[target.x86_64-pc-windows-msvc]`:
```toml
rustflags = ["-C", "link-arg=-threads=4"]
```

### 3. For Nightly Rust (additional 10-20% build speed):
```toml
[build]
rustflags = ["-Z", "threads=8"]
```

## Expected Improvements

| Metric | Before | After |
|--------|--------|-------|
| dev build | Baseline | ~10-15% faster linking |
| test build | Baseline | ~20-30% faster (dep opt) |
| test execution | Baseline | ~2-3x faster (opt deps) |
| bench-fast | N/A | ~40% faster compile than release |
