# Rust Development Skill

This skill provides a unified workflow for developing, compiling, testing, and managing the Rust engine and its Python extensions.

## 🛠️ Core Capabilities

### 1. Compilation & Error Analysis
Use `cargo check` for fast verification. Always redirect output to a file for stable reading.
- **Command**: `cargo check > build_errors.txt 2>&1`
- **Triage**: Focus on the **first** error in the log. Rust errors often cascade.

### 2. Test Discovery & Execution
Discover and run specialized tests within the `engine_rust_src` project.
- **List All Tests**: `cargo test -- --list`
- **Run Specific Test**: `cargo test -- <test_name>`
- **Capture Debug Output**: `cargo test -- <test_name> --nocapture 2>&1 | Out-File -FilePath ../reports/test_output.txt -Encoding utf8`

### 3. Python Extension Management
Best practices for building and troubleshooting the `engine_rust` Python extension.
- **Clean Build Workflow**:
  ```powershell
  uv pip uninstall engine_rust
  Get-ChildItem -Filter *.pyd -Recurse | Remove-Item -Force
  uv pip install -v -e ./engine_rust_src
  ```
- **Numpy ABI Trap**: Ensure `numpy==1.26.4` is installed. Rebuild extension if numpy version changes.

## 📋 Common Debugging Recipes

### Borrow Checker Issues
- Reorder operations to end borrows early.
- Clone data if cheap to avoid holding references.
- Use explicit scopes `{ ... }` to limit lifetimes.

### Stale Binary Symptoms
If you correctly added an enum variant but Python throws `ValueError`, perform the **Clean Build Workflow**.

### Interaction Cycles (Level 3 Testing)
1. **Verify Suspension**: Assert `state.phase == Phase::Response` and `state.interaction_stack.len() > 0`.
2. **Action Generation**: Ensure correct action IDs are available.
3. **Resume**: Call `state.step(db, action_id)` and verify final state.
