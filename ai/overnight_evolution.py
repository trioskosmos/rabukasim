import os
import subprocess
import time


def run_step(name, cmd):
    print(f"\n>>> Starting {name}...")
    start = time.time()
    try:
        subprocess.check_call(cmd, shell=True)
        print(f">>> {name} completed in {time.time() - start:.1f}s")
    except subprocess.CalledProcessError as e:
        print(f"!!! Error in {name}: {e}")
        return False
    return True


def main():
    print("=== LOVE-CA ALPHA ZERO OVERNIGHT EVOLUTION ===")

    # 1. Ensure model is exported
    if not os.path.exists("ai/models/alphanet.onnx"):
        run_step("Model Export", "uv run python ai/utils/export_onnx.py")

    generation = 0
    while True:
        print(f"\n--- GENERATION {generation} ---")

        # 1. Generate Data (Self-Play)
        # Using 800 sims for high quality, 1000 games per batch
        if not run_step(
            "Data Generation",
            "uv run python ai/data_generation/generate_data.py --num-games 1000 --sims 800 --output-file ai/data/overnight_batch.npz",
        ):
            break

        # 2. Train Model
        # Training for a few epochs on the new data
        if not run_step(
            "Model Training", "uv run python ai/training/train.py --data-path ai/data/overnight_batch.npz --epochs 5"
        ):
            break

        # 3. Export New Model
        run_step("Model Update", "uv run python ai/utils/export_onnx.py")

        # 4. Evaluation (Optional, simple score)
        print(f"Generation {generation} completed.")

        generation += 1

        # Limit or break? User said overnight, so loop forever until stopped.
        # But maybe sleep a bit to avoid CPU melt
        time.sleep(10)


if __name__ == "__main__":
    main()
