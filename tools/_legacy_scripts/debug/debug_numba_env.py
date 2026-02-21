import os
import time

# Attempting to fix hangs by limiting threading and disabling hardware acceleration for detection
os.environ["NUMBA_NUM_THREADS"] = "1"
os.environ["NUMBA_DISABLE_CUDA"] = "1"
os.environ["NUMBA_DISABLE_JIT"] = "1"

print(f"PATH: {os.environ.get('PATH', '')[:100]}...")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', '')}")


def monitored_import(name):
    print(f"IMPORTING: {name}...")
    start = time.time()
    try:
        # Use a separate thread or just a timeout? Python imports are global-locked.
        # We'll just print and hope for the best.
        mod = __import__(name)
        print(f"SUCCESS: {name} imported in {time.time() - start:.2f}s")
        return mod
    except Exception as e:
        print(f"FAILED: {name} import: {e}")
        return None


monitored_import("numpy")
monitored_import("llvmlite")
monitored_import("numba.core.config")
monitored_import("numba")

print("FINISHED DIAGNOSTIC")
