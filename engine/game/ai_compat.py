"""
AI Compatibility Layer
Handles optional dependencies like Numba and Torch gracefully.
"""

import importlib
import sys


def check_available(module_name: str) -> bool:
    """Check if a module is available without importing it fully."""
    try:
        if module_name in sys.modules:
            return True
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError):
        return False


# 1. Numba Availability
JIT_AVAILABLE = check_available("numba")

if JIT_AVAILABLE:
    from numba import njit, prange
else:
    # No-op decorator fallback
    def njit(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return args[0]  # Used as @njit

        def decorator(func):
            return func  # Used as @njit(cache=True)

        return decorator

    prange = range

# 2. Torch Availability
TORCH_AVAILABLE = check_available("torch")

# 3. Execution Flags
# If this is True, the engine will attempt to use JIT/Batching
GLOBAL_AI_ENABLED = JIT_AVAILABLE


def report_ai_status():
    """Print current AI acceleration status."""
    status = "ENABLED" if GLOBAL_AI_ENABLED else "DISABLED (Legacy Mode)"
    print(f"--- AI Acceleration: {status} ---")
    if not JIT_AVAILABLE:
        print("  [Note] Numba not found. Install with 'pip install numba' for 200x speedup.")
    if not TORCH_AVAILABLE:
        print("  [Note] Torch not found. AI training will be unavailable.")
    print("---------------------------------")
