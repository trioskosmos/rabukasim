import torch

# Mock dimensions based on LoveLiveCardGameEnv
OBS_DIM = 320  # approx
ACT_DIM = 1913  # approx


def test_batch_size(batch_size):
    print(f"Testing Batch Size: {batch_size}...", end=" ")
    try:
        if not torch.cuda.is_available():
            print("Skipping (No CUDA)")
            return False

        device = torch.device("cuda")

        # 1. Allocate Mock Data
        # PPO requires: Obs, Actions, Values, LogProbs, Advantages
        # Float32 = 4 bytes

        # Observation Buffer
        obs = torch.randn((batch_size, OBS_DIM), device=device)

        # Forward Pass Memory (Simulated)
        # A simple MLP Policy (64, 64) isn't huge, but the gradients are what kill VRAM.
        # Let's try to simulate a full backward pass allocation

        model = torch.nn.Sequential(
            torch.nn.Linear(OBS_DIM, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, ACT_DIM),
        ).to(device)

        out = model(obs)
        loss = out.sum()
        loss.backward()

        # If we got here, we survived one training step allocation
        print("OK")

        # Cleanup
        del obs, model, out, loss
        torch.cuda.empty_cache()
        return True

    except RuntimeError as e:
        if "out of memory" in str(e):
            print("OOM!")
        else:
            print(f"Error: {e}")
        torch.cuda.empty_cache()
        return False


def main():
    print("=" * 40)
    print(" GPU BATCH SIZE LIMIT TESTER")
    print("=" * 40)

    # Powers of 2
    sizes = [2048, 4096, 8192, 16384, 32768, 65536]
    max_safe = 0

    for sz in sizes:
        success = test_batch_size(sz)
        if success:
            max_safe = sz
        else:
            print(f"\nLimit Reached around {sz}")
            break

    print("-" * 40)
    print(f"Recommended MAX BATCH SIZE: {max_safe}")
    print("Note: In practice, use slightly less (e.g. 75% of max) to leave room for other apps.")
    print("=" * 40)

    # Save to file
    with open("max_batch_result.txt", "w") as f:
        f.write(str(max_safe))


if __name__ == "__main__":
    main()
