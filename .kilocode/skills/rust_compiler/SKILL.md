---
name: rust_compiler
description: Use when compiling Rust tooling, chasing build errors, or validating cargo-driven code generation.
---
# Rust Compiler
## Do
- Reproduce with cargo check or cargo build first.
- Fix the first real error before moving on.
- Keep generated outputs aligned with source changes.
## Do not
- Do not chase warnings before the build is green.
- Do not ignore codegen artifacts if the build uses them.
## Verify
- Rerun the same command and confirm the error is gone.