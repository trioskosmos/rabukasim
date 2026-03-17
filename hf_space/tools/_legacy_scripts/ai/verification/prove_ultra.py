import time

import numpy as np

# Ultra-minimal Numba benchmark
# No imports from engine to avoid side effects
from numba import njit

# Raw Integer constants (no Enums)
OP_DRAW = 10
OP_ENERGY_CHARGE = 23
OP_ADD_BLADES = 11
OP_CHECK_LIFE_LEAD = 207
OP_BOOST_SCORE = 16
OP_JUMP_IF_FALSE = 3
OP_RETURN = 1

G_P_HAND_SIZE = 3
G_P_DECK_SIZE = 6
G_P_ENERGY_SIZE = 5
G_P_SCORE = 0
G_O_SCORE = 1


@njit(cache=True)
def ultra_fast_vm(bytecode, global_ctx, flat_ctx, p_cont_vec):
    ip = 0
    curr_ptr = 0
    total_bonus = 0
    last_cond = True

    while ip < len(bytecode):
        op = bytecode[ip, 0]
        val = bytecode[ip, 1]
        attr = bytecode[ip, 2]
        slot = bytecode[ip, 3]

        if op == OP_RETURN:
            break
        elif op == OP_JUMP_IF_FALSE:
            if not last_cond:
                ip += val
                continue
        elif op == OP_CHECK_LIFE_LEAD:
            last_cond = global_ctx[G_P_SCORE] > global_ctx[G_O_SCORE]
        elif op == OP_DRAW:
            if last_cond:
                global_ctx[G_P_DECK_SIZE] -= val
                global_ctx[G_P_HAND_SIZE] += val
        elif op == OP_ENERGY_CHARGE:
            if last_cond:
                global_ctx[G_P_DECK_SIZE] -= val
                global_ctx[G_P_ENERGY_SIZE] += val
        elif op == OP_ADD_BLADES:
            if last_cond:
                p_cont_vec[curr_ptr, 0] = 1
                curr_ptr += 1
        elif op == OP_BOOST_SCORE:
            if last_cond:
                total_bonus += val

        ip += 1
    return total_bonus


@njit(cache=True)
def run_ultra_batch(iters, bytecode, global_ctx, flat_ctx, p_cont_vec):
    results = 0
    for _ in range(iters):
        # Reset state
        global_ctx[G_P_DECK_SIZE] = 50
        global_ctx[G_P_HAND_SIZE] = 0
        global_ctx[G_P_ENERGY_SIZE] = 0
        global_ctx[G_P_SCORE] = 10
        global_ctx[G_O_SCORE] = 5

        results += ultra_fast_vm(bytecode, global_ctx, flat_ctx, p_cont_vec)
    return results


def prove_limit():
    iters = 5_000_000
    bytecode = np.array(
        [
            [OP_DRAW, 2, 0, 0],
            [OP_ENERGY_CHARGE, 2, 0, 0],
            [OP_ADD_BLADES, 1, 0, 0],
            [OP_CHECK_LIFE_LEAD, 0, 0, 0],
            [OP_JUMP_IF_FALSE, 2, 0, 0],
            [OP_BOOST_SCORE, 1, 0, 0],
            [OP_RETURN, 0, 0, 0],
        ],
        dtype=np.int32,
    )

    global_ctx = np.zeros(128, dtype=np.int32)
    flat_ctx = np.zeros(64, dtype=np.int32)
    p_cont_vec = np.zeros((32, 10), dtype=np.int32)

    # Warmup
    run_ultra_batch(100, bytecode, global_ctx, flat_ctx, p_cont_vec)

    print(f"Running Ultra-Optimized Numba Proof ({iters:,} iterations)...")
    start = time.perf_counter()
    run_ultra_batch(iters, bytecode, global_ctx, flat_ctx, p_cont_vec)
    dur = time.perf_counter() - start

    ops_sec = iters / dur
    print(f"Time: {dur:.4f}s | Speed: {ops_sec:,.0f} turns/sec")

    # Python comparison (hardcoded from prev batch)
    py_speed = 777_181
    print(f"Vs Python (777k): {ops_sec / py_speed:.2f}x Speedup")


if __name__ == "__main__":
    prove_limit()
