import os
import sys

import numpy as np

sys.path.append(os.getcwd())

from engine.game.fast_logic import resolve_bytecode


def check_mode():
    bytecode = np.zeros((1, 4), dtype=np.int32)
    flat_ctx = np.zeros(64, dtype=np.int32)
    global_ctx = np.zeros(128, dtype=np.int32)
    p_h = np.zeros(1, dtype=np.int32)
    p_d = np.zeros(1, dtype=np.int32)
    p_s = np.zeros(1, dtype=np.int32)
    p_ev = np.zeros((1, 1), dtype=np.int32)
    p_ec = np.zeros(1, dtype=np.int32)
    p_cv = np.zeros((1, 1), dtype=np.int32)
    p_tap = np.zeros(1, dtype=np.int32)
    p_lr = np.zeros(1, dtype=np.int32)
    o_tap = np.zeros(1, dtype=np.int32)

    # Trigger compilation
    resolve_bytecode(bytecode, flat_ctx, global_ctx, 0, p_h, p_d, p_s, p_ev, p_ec, p_cv, 0, p_tap, p_lr, o_tap)

    print("--- Numba Inspection ---")
    # check for object mode
    # If successful, it should NOT contain 'pyobject' or similar in the nopython section
    resolve_bytecode.inspect_types()


if __name__ == "__main__":
    check_mode()
