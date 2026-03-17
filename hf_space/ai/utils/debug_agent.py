import os
import sys

import numpy as np
import torch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.models.training_config import POLICY_SIZE
from ai.training.train import AlphaNet


def debug_model(model_path, data_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(model_path, map_location=device)

    if isinstance(checkpoint, dict) and "model_state" in checkpoint:
        state_dict = checkpoint["model_state"]
    else:
        state_dict = checkpoint

    model = AlphaNet(policy_size=POLICY_SIZE).to(device)
    model.load_state_dict(state_dict)
    model.eval()

    print(f"Loading data from {data_path}...")
    data = np.load(data_path)
    states = data["states"][:5]
    true_policies = data["policies"][:5]

    for i in range(len(states)):
        state = torch.FloatTensor(states[i]).unsqueeze(0).to(device)
        with torch.no_grad():
            p_logits, v = model(state)
            p_probs = torch.softmax(p_logits, dim=1)

        print(f"\nSample {i}:")
        print(f"Value prediction: {v.item():.4f}")

        # Check Top-5 predicted actions
        top_probs, top_actions = torch.topk(p_probs, 5)
        print("Top 5 Predictions:")
        for j in range(5):
            print(f"  Action {top_actions[0][j].item()}: {top_probs[0][j].item():.1%}")

        # Check ground truth Top-1
        gt_action = np.argmax(true_policies[i])
        gt_prob = true_policies[i][gt_action]
        print(f"Ground Truth Action {gt_action} with weight {gt_prob:.1%}")


if __name__ == "__main__":
    debug_model("ai/models/alphanet_best.pt", "ai/data/data_batch_0.npz")
