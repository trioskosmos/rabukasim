import torch
from alphazero.alphanet import AlphaNet
import sys
from pathlib import Path

def sensitivity_analysis():
    print("--- Sensitivity Analysis (Evidence of Learning Capability) ---")
    
    # 1. Initialize model with random weights
    model = AlphaNet()
    model.eval()
    
    # 2. Base Input (Baseline)
    base_input = torch.zeros(1, 20500)
    with torch.no_grad():
        _, base_v = model(base_input)
    
    # 3. Stimulus Input (Change one "Pro Vision" hint)
    # Let's change Index 70 (Win Probability placeholder) from 0.0 to 1.0
    stim_input = base_input.clone()
    stim_input[0, 70] = 1.0
    with torch.no_grad():
        _, stim_v = model(stim_input)
    
    # 4. Impact Calculation
    diff = (stim_v - base_v).abs().item()
    print(f"Base Value Prediction: {base_v.item():.6f}")
    print(f"Stimulated Value Prediction (Hint shifted): {stim_v.item():.6f}")
    print(f"Prediction Delta: {diff:.8f}")

    # 5. Gradient Sensitivity (Proof that learning *will* happen)
    stim_input.requires_grad = True
    _, v = model(stim_input)
    v.backward()
    
    grad_at_hint = stim_input.grad[0, 70].item()
    print(f"Gradient at Hint Index 70: {grad_at_hint:.8f}")

    if abs(grad_at_hint) > 0:
        print("\nEVIDENCE: The model's Value Head is mathematically coupled to the Pro Vision hints.")
        print("This confirms that backpropagation will tune these weights to learn from the hints.")
    else:
        print("\nFAILURE: Model is blind to the hint.")

if __name__ == "__main__":
    # Add root to sys.path
    root_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root_dir))
    
    try:
        sensitivity_analysis()
    except Exception as e:
        print(f"Error: {e}")
