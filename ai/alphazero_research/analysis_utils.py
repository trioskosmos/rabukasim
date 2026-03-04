import torch
import numpy as np

def analyze_policy_output(policy_logits, action_mask=None):
    """
    Analyzes policy logits and returns the top-N predicted actions.
    """
    if action_mask is not None:
        policy_logits = policy_logits.masked_fill(~action_mask, -1e9)
    
    probs = torch.softmax(policy_logits, dim=-1)
    top_probs, top_indices = torch.topk(probs, k=5)
    
    return top_probs.tolist(), top_indices.tolist()

def compare_with_heuristic(neural_eval, heuristic_eval):
    """
    Compares neural network value prediction with heuristic win probability.
    """
    diff = abs(neural_eval - heuristic_eval)
    return {
        "neural": neural_eval,
        "heuristic": heuristic_eval,
        "delta": diff,
        "congruent": diff < 0.2
    }

if __name__ == "__main__":
    print("AI Analysis Utils Loaded.")
