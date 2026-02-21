@echo off
echo Starting TensorBoard...
echo Open http://localhost:6006 in your browser.
uv run tensorboard --logdir logs/ppo_tensorboard/
pause
