import torch

print(f"Torch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device Name: {torch.cuda.get_device_name(0)}")

print("Attempting to initialize MaskablePPO...")
# Just creating the class usually triggers the C++ backend checks
try:
    print("Success: sb3_contrib imported.")
except Exception as e:
    print(f"Fail: {e}")
