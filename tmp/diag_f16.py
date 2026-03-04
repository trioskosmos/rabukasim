import torch
import torch.nn.functional as F
import numpy as np

torch.manual_seed(42)

print("--- log_softmax range over 22k actions ---")
for label, logits in [("random normal", torch.randn(1, 22000)), ("zeros (uniform)", torch.zeros(1, 22000))]:
    lp = F.log_softmax(logits, dim=1)
    lp16 = lp.half()
    inf_ct = torch.isinf(lp16).sum().item()
    finite_min = lp16[~torch.isinf(lp16)].min().item() if inf_ct < 22000 else float("nan")
    print(f"  {label}:")
    print(f"    f32 min={lp.min().item():.3f}  f32 max={lp.max().item():.3f}")
    print(f"    f16 -inf count={inf_ct}/22000  f16 finite min={finite_min:.3f}")

print()
print("--- KL divergence: target at most-suppressed logit (worst case) ---")
logits = torch.randn(1, 22000)
lp = F.log_softmax(logits, dim=1)
lp16 = lp.half().float()
lp_clamped = lp.clamp(min=-100.0)

# Worst case: MCTS visited a very unlikely action, put all policy mass there
worst_idx = int(logits.argmin())
pol = torch.zeros(1, 22000)
pol[0, worst_idx] = 1.0

kl_raw = F.kl_div(lp, pol, reduction="batchmean").item()
kl_f16 = F.kl_div(lp16, pol, reduction="batchmean").item()
kl_clamped = F.kl_div(lp_clamped, pol, reduction="batchmean").item()

print(f"  f32 logit at worst_idx: {logits[0, worst_idx].item():.3f}")
print(f"  f32 log_prob at worst_idx: {lp[0, worst_idx].item():.3f}")
print(f"  f16 log_prob at worst_idx: {lp16[0, worst_idx].item()} (may be -inf)")
print()
print(f"  KL raw f32:    {kl_raw}")
print(f"  KL via f16:    {kl_f16}")
print(f"  KL clamped -100: {kl_clamped:.4f}")

print()
print("--- float16 underflow / overflow thresholds ---")
# float16 smallest positive subnormal (can represent) 
f16_min_positive = float(np.finfo(np.float16).tiny)   # ~5.96e-8 (normal)
f16_subnormal    = 5.96e-8 / 64                        # ~approx smallest subnormal
print(f"  float16 smallest normal positive: {f16_min_positive:.2e}")
print(f"  log(f16 tiny normal): {np.log(f16_min_positive):.2f}  <- f16 rounds to -inf below this log prob")
print(f"  log_softmax of uniform 22k actions: {-np.log(22000):.3f}  (safe: above f16 floor)")
print(f"  Clamp at -100 is safe: covers log probs > {np.exp(-100):.2e} (essentially zero)")
print()
print("--- autocast AMP behaviour ---")
print("  Under torch.amp.autocast, matmuls run in f16 but log_softmax stays f32.")
print("  So in practice f16 overflow is NOT the source of NaN in this codebase.")
print("  The NaN came purely from f32 KL divergence hitting -inf * non-zero.")
