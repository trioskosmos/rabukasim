import numpy as np
import torch
from alphanet import AlphaNet

data_path = "trajectories.npz"
data = np.load(data_path)

obs = torch.from_numpy(data["obs"][0:2])
policy = torch.from_numpy(data["policy"][0:2])
mask = torch.from_numpy(data["mask"][0:2])
value = torch.from_numpy(data["value"][0:2]).unsqueeze(1)

model = AlphaNet()

print("Any initial NaN in obs?", torch.isnan(obs).any().item())

policy_preds, value_preds = model(obs, mask=mask)

print("Any NaN in policy_preds from model?", torch.isnan(policy_preds).any().item())

log_probs = torch.log_softmax(policy_preds, dim=1)
print("Any NaN in log_probs?", torch.isnan(log_probs).any().item())
if torch.isnan(log_probs).any().item():
    print("Finding why log_probs is NaN...")
    print("policy_preds max per row:", policy_preds.max(dim=1).values)

# Mask
log_probs_masked = log_probs.masked_fill(~mask, 0.0)
print("Any NaN in log_probs_masked?", torch.isnan(log_probs_masked).any().item())

# Cross entropy
product = policy * log_probs_masked
print("Any NaN in policy * log_probs_masked?", torch.isnan(product).any().item())

summed = product.sum(dim=1)
print("Any NaN in summed?", torch.isnan(summed).any().item())
print("summed values:", summed)

loss = -summed.mean()
print("Final policy loss:", loss.item())
