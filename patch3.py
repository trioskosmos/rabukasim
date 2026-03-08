import re

with open("alphazero/training/overnight_vanilla.py", "r") as f:
    code = f.read()

# Fix policy value loss mismatch
code = re.sub(r'value_loss = F\.mse_loss\(value_preds\.view_as\(val_t\[:, 0:1\]\), val_t\[:, 0:1\]\)',
              'value_loss = F.mse_loss(value_preds[:, 0:1], val_t[:, 0:1])', code)

with open("alphazero/training/overnight_vanilla.py", "w") as f:
    f.write(code)
