---
name: rust_engine
description: Use when changing Rust engine code, tests, build scripts, or cargo workflows.
---
# Rust Engine
## Do
- Build the affected crate first.
- Run the smallest useful test, then widen only if needed.
- Keep failing output and logs reproducible.
## Do not
- Do not assume one passing test covers the change.
- Do not chase warnings before the build is green.
## Verify
- Rerun the same cargo command and confirm the error is gone.