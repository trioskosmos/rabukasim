import time

from numba import njit

ITERATIONS = 10_000_000


@njit()
def pure_arithmetic(n):
    a = 10
    b = 0
    for _ in range(n):
        if a > 0:
            a -= 2
            b += 2
        else:
            a = 10
    return b


def benchmark():
    # Warmup
    pure_arithmetic(100)

    print(f"Running pure arithmetic benchmark ({ITERATIONS:,} iterations)...")
    start = time.perf_counter()
    pure_arithmetic(ITERATIONS)
    dur = time.perf_counter() - start
    print(f"Time: {dur:.6f}s | Speed: {ITERATIONS / dur:,.0f} ops/sec")


if __name__ == "__main__":
    benchmark()
