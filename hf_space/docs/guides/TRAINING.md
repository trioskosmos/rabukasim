# Love Live AI Training Guide

This guide explains how to train the AI model and how to resume training from a saved checkpoint.

## Prerequisites
- NVIDIA GPU with CUDA installed.
- Python environment with requirements installed (`pip install -r requirements_rl.txt`).

## Starting Training
To start a fresh training session, run:
```powershell
.\run_training_gpu.bat
```
This will:
1. Start TensorBoard on port 6007.
2. Initialize 4 parallel environment workers.
3. Start the PPO training loop.
4. Save checkpoints to the `./checkpoints/` directory.

## Continuing from a Save
To continue training from a previous checkpoint, you have two options:

### Option 1: Interactive Prompt (Recommended)
Simply run:
```powershell
.\run_training_gpu.bat
```
If checkpoints are found in the `checkpoints/` directory, the script will show the latest one and ask:
`Do you want to resume from the latest checkpoint? (y/n, default: n):`
Press **y** and then **Enter** to resume.

### Option 2: Manual Configuration
1. Locate your checkpoint file (e.g., `checkpoints/best_win_rate_model.zip`).
2. Set the `LOAD_MODEL` environment variable before running the script, or edit `run_training_gpu.bat` to set it permanently.

> [!TIP]
> The training script automatically detects the `LOAD_MODEL` environment variable and will resume from that state if the file exists.

## Performance Tuning
You can adjust the following variables in `run_training_gpu.bat`:
- `TRAIN_CPUS`: Number of parallel workers (default 4).
- `TRAIN_USAGE`: CPU throttle per worker (0.5 = 50% usage).
- `TRAIN_GPU_USAGE`: Fraction of GPU memory to allocate (0.7 = 70%).
- `TRAIN_BATCH_SIZE`: Batch size for PPO.
- `TRAIN_EPOCHS`: Number of epochs per update.

## Advanced Configuration

For a complete list of environment variables and configuration options (including Scenario Mode and Pretraining), see **[docs/CONFIGURATION.md](CONFIGURATION.md)**.
