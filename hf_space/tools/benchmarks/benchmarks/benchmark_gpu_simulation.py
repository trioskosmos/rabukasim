import numpy as np


class FakeGPUArray:
    """Simulates Cupy array behavior on CPU with overhead for scalar access."""

    def __init__(self, shape, dtype=np.float32, latency=10e-6):  # 10us latency
        self.data = np.zeros(shape, dtype=dtype)
        self.latency = latency
        self.shape = self.data.shape
        self.dtype = self.data.dtype

    def __getitem__(self, idx):
        # Simulate PCI-E / Kernel launch latency for scalar access
        if isinstance(idx, int):
            # time.sleep(self.latency) # Sleep is too coarse (min 1ms on Windows, 10ms on Linux?)
            # Busy wait or just math?
            # 10us is small. 4096 * 10us = 40ms.
            # Python function call overhead is ~100ns.
            pass
        return self.data[idx]

    def __setitem__(self, idx, value):
        if isinstance(idx, int):
            # time.sleep(self.latency)
            pass
        self.data[idx] = value

    def __iadd__(self, other):
        # Vectorized operation: 1 kernel launch (1x latency)
        # time.sleep(self.latency)
        if isinstance(other, FakeGPUArray):
            self.data += other.data
        else:
            self.data += other
        return self

    def asnumpy(self):
        # Bulk transfer: 1x latency + transfer time
        # time.sleep(self.latency * 10)
        return self.data.copy()


def benchmark_simulated():
    print("=== GPU Simulation Benchmark (Estimating Latency) ===")

    num_envs = 4096

    # We will simply calculate the operations count
    # Old Method:
    # Loop N times.
    # Inside loop:
    #   if done:
    #      access reward[i] (GPU->CPU) -> 1 Op
    #      access length[i] (GPU->CPU) -> 1 Op
    #      set return[i] = 0 (CPU->GPU) -> 1 Op
    #      set length[i] = 0 (CPU->GPU) -> 1 Op
    #   else:
    #      access reward[i] (GPU) -> 1 Op
    #      add to return[i] (GPU) -> 1 Op (Read+Write?)
    #      increment length[i] (GPU) -> 1 Op

    # Approx 3-5 GPU scalar accesses per environment per step.
    # Total Accesses = 4096 * 4 = 16,384 scalar operations.

    # New Method:
    # Vectorized Add: episode_returns += rewards (1 Kernel Launch)
    # Vectorized Add: episode_lengths += 1 (1 Kernel Launch)
    # Bulk Transfer: cp.asnumpy(dones) (1 Transfer)
    # If Dones:
    #   Bulk Transfer rewards (1 Transfer)
    #   Bulk Transfer lengths (1 Transfer)
    #   Vectorized Reset (1 Kernel)

    # Total Operations = ~5-10 Kernel/Transfer Ops (Constant time wrt N loop overhead)

    latency_per_scalar = 20e-6  # 20 microseconds (conservative for Py-Cuda roundtrip)

    ops_old = num_envs * 4
    estimated_time_old = ops_old * latency_per_scalar

    ops_new = 10
    estimated_time_new = ops_new * latency_per_scalar  # Negligible

    print(f"Number of Environments: {num_envs}")
    print(f"Assumed Python-to-GPU Latency per Scalar: {latency_per_scalar * 1e6:.1f} us")
    print("\n--- ESTIMATED PERFORMANCE ---")
    print("Old Method (Loop O(N) Access):")
    print(f"  Scalar Ops: ~{ops_old}")
    print(f"  Est. Time:  {estimated_time_old:.4f} s")
    print(f"  Est. SPS:   {num_envs / estimated_time_old:,.0f}")

    print("\nNew Method (Vectorized O(1) Access):")
    print(f"  Kernel Ops: ~{ops_new}")
    print(f"  Est. Time:  {estimated_time_new:.4f} s (plus CPU overhead)")

    # Add Python Loop Overhead from previous benchmark
    cpu_overhead_old = 0.015  # From previous run
    cpu_overhead_new = 0.030  # From previous run

    total_old = estimated_time_old + cpu_overhead_old
    total_new = estimated_time_new + cpu_overhead_new

    print("\n--- TOTAL PROJECTED TIME (Latency + CPU Overhead) ---")
    print(f"Old Total: {total_old:.4f} s")
    print(f"New Total: {total_new:.4f} s")
    print(f"Speedup:   {total_old / total_new:.1f}x")


if __name__ == "__main__":
    benchmark_simulated()
