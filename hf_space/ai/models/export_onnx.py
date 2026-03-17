import argparse
import os
import sys

import torch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.models.training_config import INPUT_SIZE, POLICY_SIZE
from ai.training.train import AlphaNet


def export_model(model_path, output_path):
    device = torch.device("cpu")  # ONNX export usually done on CPU to be safe

    print(f"Loading checkpoint from {model_path}...")
    checkpoint = torch.load(model_path, map_location=device)

    # Handle dictionary checkpoint
    if isinstance(checkpoint, dict) and "model_state" in checkpoint:
        state_dict = checkpoint["model_state"]
    else:
        state_dict = checkpoint

    # Detect policy size from weights to support different versions
    if "policy_head_fc.bias" in state_dict:
        detected_size = state_dict["policy_head_fc.bias"].shape[0]
        print(f"Detected Policy Size: {detected_size}")
    else:
        detected_size = POLICY_SIZE
        print(f"Using Default Policy Size: {detected_size}")

    model = AlphaNet(policy_size=detected_size).to(device)
    model.load_state_dict(state_dict)
    model.eval()

    dummy_input = torch.randn(1, INPUT_SIZE, device=device)

    print(f"Exporting to {output_path}...")
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=17,  # Use modern opset for better compatibility
        do_constant_folding=True,
        input_names=["input"],
        output_names=["policy", "value"],
        dynamic_axes={"input": {0: "batch_size"}, "policy": {0: "batch_size"}, "value": {0: "batch_size"}},
    )
    print("Export complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True, help="Path to .pt checkpoint")
    parser.add_argument("--output", type=str, required=True, help="Path to .onnx output")
    args = parser.parse_args()

    export_model(args.model, args.output)
