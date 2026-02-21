import numpy as np

data = np.load("ai/data/test_yield.npz")
print(f"Samples: {len(data['states'])}")
