---
name: alphazero_training
description: Use when changing self-play, training loops, evaluation, or checkpoints.
---
# AlphaZero Training
## Do
- Keep data generation, training, and evaluation in sync.
- Update reward or label logic with the pipeline that consumes it.
- Prefer small smoke runs before long jobs.
## Do not
- Do not tune hyperparameters before the data path is stable.
- Do not mix experimental and baseline runs.
## Verify
- Run a short training or evaluation pass and check the output.