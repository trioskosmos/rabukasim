---
name: rust_compiler
description: Standard workflow for compiling Rust code, capturing errors, and resolving them.
---

# Rust Compilation & Debugging Skill

Use this skill when you need to compile Rust code (`cargo build`) or check for errors (`cargo check`), especially when dealing with complex or multiple errors.

## 1. Compilation Strategy

Always prefer `cargo check` for verifying code correctness as it is faster than `cargo build`.

### Command Pattern
> [!IMPORTANT]
> **ALWAYS** redirect output to a file and read the file using `view_file`. Standard output/stderr via `run_command` is often truncated or mangled in the terminal view.

**NEVER** rely on terminal output for more than a quick status check.

```powershell
# Windows PowerShell
cargo check > build_errors.txt 2>&1
```

```bash
# Bash
cargo check > build_errors.txt 2>&1
```

## 2. Error Analysis

1.  **Read the Log**: Use `view_file` to read `build_errors.txt`.
2.  **Identify First Error**: Rust compilers often cascade errors. Focus on the **first** reported error first.
3.  **Locate Source**: Note the file path, line number, and error message.
4.  **Context**: Use `view_file` to examine the code around the error.

## 3. Common Issues & Fixes

### A. Borrow Checker (Ownership/Borrowing)
- **Error**: `cannot borrow *self as mutable more than once`
- **Fix**: 
    - Reorder operations to end the first borrow before the second starts.
    - Clone data if needed/cheap to avoid holding a reference.
    - Use scopes `{ ... }` to limit the lifetime of a borrow.

### B. Type Mismatches
- **Error**: `expected type X, found type Y`
- **Fix**: Check trait implementations (`Into`, `From`, `AsRef`). Use explicit casts (`as u16`) if safe.

### C. Missing Imports
- **Error**: `cannot find type/function X in this scope`
- **Fix**: Add `use` statements. Check if the crate is in `Cargo.toml`.

### D. Macro Expansion
- **Error**: Errors pointing to macro usage (e.g., `lazy_static!`, `json!`).
- **Fix**: Check macro syntax.

## 4. Iterative Resolution

1.  **Fix**: Apply code changes to resolve the identified error.
2.  **Verify**: Run `cargo check > build_errors.txt 2>&1` again.
3.  **Repeat**: If errors persist, analyze the new log. If the fixed error is gone, move to the next one.

## 5. Final Verification

Once `cargo check` passes, run `cargo build` (or the specific build script like `build_engine.bat`) to ensure linking works and binaries are generated.
