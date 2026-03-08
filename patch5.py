import re

with open("alphazero/training/overnight_vanilla.py", "r") as f:
    code = f.read()

# Replace HighFidelityAlphaNet init
code = re.sub(r'HighFidelityAlphaNet\(input_dim=OBS_DIM, num_actions=ACTION_SPACE\)', 'AlphaNet()', code)

with open("alphazero/training/overnight_vanilla.py", "w") as f:
    f.write(code)
