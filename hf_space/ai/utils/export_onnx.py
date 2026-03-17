import os
import sys

import torch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.models.training_config import INPUT_SIZE, POLICY_SIZE
from ai.training.train import AlphaNet


def export_to_onnx(model_path, output_path):
    device = torch.device("cpu")
    checkpoint = torch.load(model_path, map_location=device)
    state_dict = (
        checkpoint["model_state"] if isinstance(checkpoint, dict) and "model_state" in checkpoint else checkpoint
    )

    model = AlphaNet(policy_size=POLICY_SIZE).to(device)
    model.load_state_dict(state_dict)
    model.eval()

    dummy_input = torch.randn(1, INPUT_SIZE)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["policy", "value"],
        dynamic_axes={"input": {0: "batch_size"}, "policy": {0: "batch_size"}, "value": {0: "batch_size"}},
    )
    print(f"Model successfully exported to {output_path}")


if __name__ == "__main__":
    export_to_onnx("ai/models/alphanet_best.pt", "ai/models/alphanet.onnx")
