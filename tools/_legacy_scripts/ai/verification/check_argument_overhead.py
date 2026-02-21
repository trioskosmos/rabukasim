import time

import numpy as np
from numba import njit


@njit(nopython=True)
def callee_many(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14):
    return a1[0] + a14[0]


@njit(nopython=True)
def callee_few(a1, a2):
    return a1[0] + a2[0]


@njit(nopython=True)
def loop_many(iters, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14):
    s = 0
    for _ in range(iters):
        s += callee_many(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14)
    return s


@njit(nopython=True)
def loop_few(iters, a1, a14):
    s = 0
    for _ in range(iters):
        s += callee_few(a1, a14)
    return s


def bench():
    iters = 10_000_000
    arr = np.zeros(1, dtype=np.int32)

    # Warmup
    loop_many(10, arr, arr, arr, arr, arr, arr, arr, arr, arr, arr, arr, arr, arr, arr)
    loop_few(10, arr, arr)

    print(f"Running argument overhead benchmark ({iters:,} calls)...")

    start = time.perf_counter()
    loop_many(iters, arr, arr, arr, arr, arr, arr, arr, arr, arr, arr, arr, arr, arr, arr)
    dur_many = time.perf_counter() - start
    print(f"Many Args (14): {dur_many:.4f}s | {iters / dur_many:,.0f} calls/sec")

    start = time.perf_counter()
    loop_few(iters, arr, arr)
    dur_few = time.perf_counter() - start
    print(f"Few Args (2):   {dur_few:.4f}s | {iters / dur_few:,.0f} calls/sec")

    print(f"Overhead Ratio: {dur_many / dur_few:.2f}x")


if __name__ == "__main__":
    bench()
