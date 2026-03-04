import torch
from alphazero.alphanet import AlphaNet
import sys

def test_hierarchical_forward():
    print("Initializing AlphaNet...")
    model = AlphaNet(num_action_types=17, max_sub_index=100)
    
    # 20500 = 100 (Global) + 120 * 170 (Cards)
    x = torch.randn(2, 20500)
    
    print("Running forward pass...")
    try:
        p, v = model(x)
        print(f"Policy shape: {p.shape}")
        print(f"Value shape: {v.shape}")
        
        assert p.shape == (2, 16384), f"Expected 16384 policy dims, got {p.shape[1]}"
        assert v.shape == (2, 1), f"Expected value shape (2, 1), got {v.shape}"
        
        # Check for NaNs
        assert not torch.isnan(p).any(), "NaNs found in policy"
        assert not torch.isnan(v).any(), "NaNs found in value"
        
        print("SMOKE TEST SUCCESS")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_hierarchical_forward()
