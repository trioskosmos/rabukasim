import sys
from pathlib import Path

import torch
import torch.onnx

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from alphazero.alphanet import AlphaNet


def export_v8_to_onnx(model_path, output_path):
    device = torch.device("cpu")
    print(f"Loading model from {model_path}...")

    # Initialize model
    model = AlphaNet().to(device)

    # Load state dict
    try:
        # Check if it's a full checkpoint or just state dict
        checkpoint = torch.load(model_path, map_location=device)
        if isinstance(checkpoint, dict) and "model_state" in checkpoint:
            state_dict = checkpoint["model_state"]
        else:
            state_dict = checkpoint

        model.load_state_dict(state_dict, strict=False)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    model.eval()

    # Input: (Batch, 20500)
    dummy_input = torch.randn(1, 20500)

    # Mask: (Batch, 22000)
    dummy_mask = torch.ones(1, 22000, dtype=torch.bool)

    print(f"Exporting to {output_path}...")

    # Export with optional mask input
    torch.onnx.export(
        model,
        (dummy_input, dummy_mask),
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input", "mask"],
        output_names=["policy", "value"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "mask": {0: "batch_size"},
            "policy": {0: "batch_size"},
            "value": {0: "batch_size"},
        },
    )
    print("Done!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        model_path = "alphazero/training/firstrun.pt"

    output_path = model_path.replace(".pt", ".onnx")
    export_v8_to_onnx(model_path, output_path)
