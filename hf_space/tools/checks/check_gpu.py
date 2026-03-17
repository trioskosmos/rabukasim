import sys

import torch


def check():
    print(f"Python: {sys.version}")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"CUDA Device Count: {torch.cuda.device_count()}")
        print(f"CUDA Device Name: {torch.cuda.get_device_name(0)}")
        try:
            x = torch.tensor([1.0, 2.0], device="cuda")
            print(f"Tensor on CUDA: {x}")
        except Exception as e:
            print(f"Failed to create tensor on CUDA: {e}")
    else:
        print("CUDA is NOT available. Training will force CPU.")


if __name__ == "__main__":
    check()
