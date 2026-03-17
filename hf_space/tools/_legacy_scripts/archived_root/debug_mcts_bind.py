import inspect
import sys

import engine_rust

print(f"Python executable: {sys.executable}")
print(f"engine_rust file: {getattr(engine_rust, '__file__', 'unknown')}")

try:
    sig = inspect.signature(engine_rust.PyHybridMCTS.__new__)
    print(f"Signature: {sig}")
except Exception as e:
    print(f"Could not get signature: {e}")

try:
    print("\nAttempting 3-arg constructor...")
    # neural_weight is float, skip_rollout is bool
    # args: (model_path, neural_weight, skip_rollout)
    m = engine_rust.PyHybridMCTS("ai/models/alphanet_best.onnx", 0.5, True)
    print("SUCCESS: 3-arg constructor worked")
except TypeError as e:
    print(f"FAILURE: 3-arg constructor failed: {e}")

try:
    print("\nAttempting 2-arg constructor...")
    m = engine_rust.PyHybridMCTS("ai/models/alphanet_best.onnx", 0.5)
    print("SUCCESS: 2-arg constructor worked (Old version?)")
except TypeError as e:
    print(f"FAILURE: 2-arg constructor failed: {e}")
