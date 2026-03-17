# Archived AI Infrastructure

This directory contains legacy AI code replaced by the new RL training pipeline.

## What Was Archived

- **Old agent implementations**: agents/ (MCTS, neural MCTS, various search agents)
- **Old research code**: alphazero_research/, research/
- **Legacy training infrastructure**: train.py, train_bc.py, train_ppo.py, train_gpu_workers.py
- **Old utilities**: data_generation/, environments/
- **Legacy runners and docs**: headless_runner.py, TRAINING_INTEGRATION_GUIDE.md, OPTIMIZATION_IDEAS.md

## Active Components (Kept)

- `ai/training/vanilla_loop.py` - New CLI entrypoint for RL training
- `ai/data/` - Game data and card metadata
- `ai/decks/`, `ai/decks2/` - Deck definitions
- `ai/models/` - Model architecture code
- `ai/utils/` - Utility functions

## Why We Archived

The legacy AI infrastructure was based on imitation learning and oracle-based proof validation. This has been replaced with a self-play RL pipeline that:
- Generates own training data through self-play
- Uses real model behavior metrics (not oracle comparisons)
- Is simpler and more maintainable

All old code related to that approach was safely archived here.
