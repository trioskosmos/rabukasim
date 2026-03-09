import os
filepath = "engine_rust_src/src/core/logic/interpreter/instruction.rs"
with open(filepath, "r") as f:
    text = f.read()

print(text[:1000])
