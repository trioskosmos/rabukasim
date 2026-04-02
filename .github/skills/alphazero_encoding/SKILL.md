---
name: alphazero_encoding
description: Use when changing AlphaZero input encoding, feature layout, or state representation.
---
# AlphaZero Encoding
## Do
- Keep feature order and tensor shape documented.
- Update training and inference code together.
- Check encoding parity on a known board state.
## Do not
- Do not change semantics without a matching test.
- Do not mix old and new feature layouts.
## Verify
- Encode one reference state and inspect size and values.