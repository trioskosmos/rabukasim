import os
import sys

import torch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.models.training_config import INPUT_SIZE, POLICY_SIZE
from ai.training.train import AlphaNet


def export_to_torchscript(model_path, output_path):
    device = torch.device("cpu")  # Export on CPU for cross-device compatibility
    checkpoint = torch.load(model_path, map_location=device)
    state_dict = (
        checkpoint["model_state"] if isinstance(checkpoint, dict) and "model_state" in checkpoint else checkpoint
    )

    model = AlphaNet(policy_size=POLICY_SIZE).to(device)
    model.load_state_dict(state_dict)
    model.eval()

    # Create dummy input for tracing
    dummy_input = torch.randn(1, INPUT_SIZE)

    # Trace the model
    traced_model = torch.jit.trace(model, dummy_input)
    traced_model.save(output_path)
    print(f"Model successfully exported to {output_path}")


if __name__ == "__main__":
    export_to_torchscript("ai/models/alphanet_best.pt", "ai/models/alphanet_traced.pt")
