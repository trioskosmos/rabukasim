---
title: Rabukasim
emoji: 💃
colorFrom: pink
colorTo: purple
sdk: docker
app_port: 7860
---

# Love Live Card Game Engine
# Rabukasim (Love Live! School Idol Collection Simulator)

Rabukasim is a high-performance simulation engine and RL pipeline for the Love Live! School Idol Collection card game.

## Project Structure

- `engine_rust_src/`: Core game engine written in Rust for high performance.
- `ai/`: Reinforcement Learning pipeline and training scripts.
- `compiler/`: Card and ability compilation system.
- `backend/`: Flask-based server for game orchestration.
- `frontend/`: Web-based user interface for game interaction and visualization.
- `docs/`: Project documentation and architecture overviews.
- `reports/`: Diagnostic reports, probe results, and performance metrics.
- `logs/`: Build and execution logs.

## Setup and Usage

Refer to `docs/` for detailed setup instructions and developer guides.
For RL training, see `ai/training/` and the `CLEANUP_ARCHIVE_SUMMARY.md` in `docs/archive/` for context on the recent pipeline consolidation.

## Development

- **Engine**: Rebuild the Rust extension using `maturin`.
- **AI**: Run the main RL loop via `vanilla_loop.py`.
- **Tests**: Use `cargo test` in `engine_rust_src` or the root test suite.
