---
name: rust_extension_management
description: Use when dealing with Rust-backed VS Code extensions, stale binaries, or extension rebuilds.
---
# Rust Extension Management
## Do
- Rebuild after changing native code.
- Replace stale binaries when symptoms point to old output.
- Confirm the editor loads the new build.
## Do not
- Do not trust an old binary when behavior looks stale.
- Do not skip restart checks after native changes.
## Verify
- Restart the extension host or editor and check the new behavior.