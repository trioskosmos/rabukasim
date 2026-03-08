import re

with open("alphazero/training/overnight_vanilla.py", "r") as f:
    code = f.read()

# Fix policy_logits handling to match AlphaNet forward output (which returns type_logits, sub_logits, value in forward_heads... wait, forward returns policy, value)
# Let's check alphanet.py forward method
