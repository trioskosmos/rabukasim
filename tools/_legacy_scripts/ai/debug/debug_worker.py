import multiprocessing
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.train_optimized import create_env


def worker(rank):
    print(f"Worker {rank} starting pid={os.getpid()}")
    try:
        env = create_env(rank)
        print(f"Worker {rank} env created: {env}")
        env.close()
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Worker {rank} failed: {e}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    print(f"Main process pid={os.getpid()}")

    p = multiprocessing.Process(target=worker, args=(0,))
    p.start()
    p.join()
    print(f"Main process done. Exitcode: {p.exitcode}")
