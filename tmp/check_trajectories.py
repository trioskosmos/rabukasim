import numpy as np
import torch

data = np.load("trajectories.npz")
obs = data["obs"]
policy = data["policy"]
value = data["value"]

print(f"Obs NaN: {np.isnan(obs).any()}")
print(f"Policy NaN: {np.isnan(policy).any()}")
print(f"Value NaN: {np.isnan(value).any()}")

print(f"Obs Inf: {np.isinf(obs).any()}")
print(f"Policy Inf: {np.isinf(policy).any()}")
print(f"Value Inf: {np.isinf(value).any()}")

print(f"Obs min/max: {obs.min()} / {obs.max()}")
