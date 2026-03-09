import os
filepath = "engine_rust_src/src/qa_verification_tests.rs"
with open(filepath, "r") as f:
    text = f.read()

# Let's fix the FLAG_REVEAL_UNTIL_IS_LIVE.
# FLAG_REVEAL_UNTIL_IS_LIVE is u64 from constants, value 33554432 (1<<25).
# Wait, S_STANDARD_IS_REVEAL_UNTIL_LIVE_SHIFT is 25.
# Let's set the s value manually by doing `(1 << 25) | 6`
# `6` goes to `S_STANDARD_TARGET_SLOT_SHIFT` (which is 0).
# So `1 << 25 | 6`. That's it!
text = text.replace(
    "(FLAG_REVEAL_UNTIL_IS_LIVE | (6 << crate::core::S_STANDARD_AREA_IDX_SHIFT) | 6) as i32",
    "(1 << 25) | 6"
)

with open(filepath, "w") as f:
    f.write(text)
