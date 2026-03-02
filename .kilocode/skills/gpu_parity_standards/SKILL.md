# GPU Parity Standards Skill

This skill defines the technical standards and workflows for maintaining bit-level parity between the **Rust Game Engine** and the **WGSL GPU Shader**.

## 1. Memory Layout Parity
The GPU and CPU must have identical struct layouts.

### Rules:
- **`#[repr(C)]`**: All Rust structs transferred to GPU must use `#[repr(C)]`.
- **Power of Two / 16-byte Alignment**: Buffers in WGSL/wgpu prefer 16-byte alignment.
- **Type Mapping**:
  - Rust `u32` -> WGSL `u32`
  - Rust `i32` -> WGSL `i32`
  - Rust `f32` -> WGSL `f32`
  - Rust `[u32; N]` -> WGSL `array<u32, N>`
- **Padding**: Explicitly add `_pad` fields to ensure structs are multiples of 16 bytes.

### Reference Files:
- [gpu_state.rs](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/core/gpu_state.rs) (Rust)
- [shader_types.wgsl](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/core/shader_types.wgsl) (WGSL)

## 2. Opcode & Condition Sync
Opcodes and conditions are the "vocabulary" shared between the compiler, engine, and GPU.

### Workflow:
1.  Update `data/metadata.json`.
2.  Run `uv run python tools/sync_metadata.py`.
3.  The script generates [shader_constants.wgsl](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/core/logic/shader_constants.wgsl).
4.  Verify the generated `// IMPLEMENTED` comments match actual logic in `shader_rules.wgsl`.

## 3. The "CPU Mirror" Testing Pattern
To verify parity, we use "Parity Tests" that compare the execution of a single action on both the CPU and GPU.

### Implementation:
- **Snapshot**: Use `GameState::to_gpu()` to create a bit-exact copy of the current state.
- **Forced Action**: Set `gpu_input.forced_action = action_id`.
- **Eager Resumption**: The GPU shader executes multiple steps or resolves choices automatically where possible. The CPU test must match this behavior (e.g., by looping `step(CHOICE_0)` until the interaction stack is empty).
- **Parity Check**: Assert that `hand_len`, `deck_len`, `scores`, and `flags` match exactly.

### Primary Tool:
- `engine_rust_src/src/bin/test_gpu_parity_suite.rs`

## 4. Porting a CPU Test to GPU
1.  Locate an interesting CPU unit test (e.g., in `opcode_tests.rs`).
2.  Copy the setup logic to a new scenario in `test_gpu_parity_suite.rs`.
3.  Run the parity check function `run_parity_check`.
4.  If it fails, debug `shader_rules.wgsl` vs `interpreter.rs`.

## 5. Performance Monitoring
- **Bandwidth**: Avoid reading back the full 1280-byte state if only a score is needed.
- **Stack Size**: Naga compilation on Windows often requires `32MB` stack. Always spawn parity tests in a custom thread.
