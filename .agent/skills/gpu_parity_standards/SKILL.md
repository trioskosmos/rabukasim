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

## 4. Automated Parity Bridge (The Harness)
To avoid manual duplication of tests, use the `GpuParityHarness` in `test_helpers.rs`. This allows any CPU integration test to trigger a GPU parity check with one line.

### Workflow:
1.  **Initialize**: `let harness = GpuParityHarness::new(&db).unwrap();`
2.  **Assert**: After running CPU logic, call `harness.assert_bytecode_parity(&state, &bytecode, &ctx);`
3.  **Automatic Diff**: Mismatches will panic with a detailed comparison of all state fields.

## 5. Porting a CPU Test to GPU
1.  Locate an interesting CPU unit test (e.g., in `opcode_tests.rs`).
2.  Wrap the test logic in a `harness.assert_...` call.
3.  Ensure the test runs with `--features gpu`.
4.  If it fails, debug `shader_rules.wgsl` vs `interpreter.rs`.

## 6. Performance & Stack Size
- **Bandwidth**: Avoid reading back the full state in production; only use for verification.
- **Stack Size**: Naga compilation on Windows often requires `32MB` stack. `GpuParityHarness` handles this by spawning tests in a custom thread or setting the environment variable.

## 7. WGSL Opcode Audit Procedure
To prevent logic gaps, regularly audit the WGSL shader against CPU semantic tests.

### Steps:
1.  **Grep for Cases**: List all `case O_...` in `shader_rules.wgsl`.
2.  **Cross-Reference**: Check against [semantic_assertions.rs](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/semantic_assertions.rs) or `opcode_tests.rs`.
3.  **Identify Stubs**: Look for opcodes that are present in the switch but have empty bodies or `// TODO` comments (e.g., `O_INCREASE_COST`).
4.  **Verify State Availability**: Ensure all fields required by the CPU logic (like `cost_reduction` or `granted_abilities`) are replicated in `GpuPlayerState`.

## 7. Common Parity Pitfalls
- **Missing State Fields**: CPU engine often adds "transient" buffs (like cost modifiers) that aren't in the base `Member` struct. These must be added to `GpuPlayerState`.
- **Choice Index Propagation**: CPU engine uses `interaction_stack`. GPU parity tests must pass the correct `choice_idx` through `forced_action` or `ctx.choice_index`.
- **Recursion Limits**: WGSL does not support recursion. Nested effects (e.g., card plays card) MUST be handled via the `trigger_queue` system or iterative bytecode resolution.
