# Rust Engine Skill

Unified workflow for development, compilation, testing, and extension management for the LovecaSim engine.

## 🛠️ Development Workflow

### 1. Compilation & Error Analysis
Prefer `cargo check` for verification. **ALWAYS** redirect output to a file.
```powershell
cargo check > build_errors.txt 2>&1
```
- **Triage**: Focus on the **first** error; others are usually cascades.

### 2. Test Management
- **List All**: `cargo test -- --list`
- **Run Module**: `cargo test -- <module_name>::`
- **Debug Output**: `cargo test -- <test_name> --nocapture`

### 3. GPU Parity Standards
Maintain parity between Rust and WGSL Shader logic.
- **Rules**: Use `#[repr(C)]`, 16-byte alignment, and padding.
- **Harness**: Use `GpuParityHarness` in tests to verify state diffs automatically.

## ⚙️ System Operations

### Python Extension Management (`engine_rust`)
The extension is a compiled binary (`.pyd`). Modifying Rust does NOT update Python automatically.
- **Clean Build (Mandatory)**:
  ```powershell
  uv pip uninstall engine_rust
  Get-ChildItem -Filter *.pyd -Recurse | Remove-Item -Force
  uv pip install -v -e ./engine_rust_src
  ```
- **Numpy ABI Trap**: Ensure `numpy==1.26.4`. Rebuild if numpy version changes.

### CPU Optimization
- Use `cargo flamegraph` or `samply` for profiling.
- Optimize hot paths in `filter.rs` and `interpreter.rs`.

## 📋 Common Debugging
- **Borrow Checker**: Reorder ops, clone cheap data, or use explicit scopes `{ ... }`.
- **Stack Size**: Naga/Wgpu on Windows requires `32MB` stack. Run tests in spawned threads if needed.
- **Stale Binaries**: If enums don't match after sync, perform a **Clean Build**.
