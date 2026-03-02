import numpy as np
data = np.load("trajectories.npz")
obs = data["obs"]
print("Global (0-25):", obs[:, :25].min(), obs[:, :25].max())
print("Cards (25-3865):", obs[:, 25:3865].min(), obs[:, 25:3865].max())
print("Hist (3865-3910):", obs[:, 3865:].min(), obs[:, 3865:].max())
# Find where the huge values are
huge_indices = np.where(obs > 1000)
if len(huge_indices[0]) > 0:
    print("Found huge values at indices:", huge_indices[1][:10])
    print("Values:", obs[huge_indices[0][0], huge_indices[1][0]])
