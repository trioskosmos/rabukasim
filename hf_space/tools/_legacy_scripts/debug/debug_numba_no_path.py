import os
import time

# Strip CUDA from PATH
path = os.environ.get("PATH", "")
new_path = ";".join([p for p in path.split(";") if "CUDA" not in p and "NVIDIA" not in p])
os.environ["PATH"] = new_path

os.environ["NUMBA_DISABLE_CUDA"] = "1"
os.environ["NUMBA_DISABLE_JIT"] = "1"

print(f"NEW PATH: {os.environ['PATH'][:100]}...")


def monitored_import(name):
    print(f"IMPORTING: {name}...")
    start = time.time()
    try:
        mod = __import__(name)
        print(f"SUCCESS: {name} imported in {time.time() - start:.2f}s")
        return mod
    except Exception as e:
        print(f"FAILED: {name} import: {e}")
        return None


monitored_import("numpy")
monitored_import("numba.core.config")
monitored_import("numba")

print("FINISHED DIAGNOSTIC")
