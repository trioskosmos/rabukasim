# Test Policy

- Prefer the full Rust suite for verification after engine changes.
- Do not stop at single-test smoke checks when the request is to drive failures to zero.
- Use targeted tests only when a full-suite run is impossible or the user explicitly asks for a narrow check.
- Keep the runtime path unified around the frame/instruction model and avoid reintroducing parallel ability systems.

