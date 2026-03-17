# System Operations Skill

Infrastructure, training, and ancillary operations for LovecaSim.

## 🖼️ Frontend Synchronization
Sync master assets from `frontend/web_ui/` to the launcher's delivery folder.
- **Command**: `uv run python tools/sync_launcher_assets.py`.
- **Note**: Never edit `launcher/static_content/` directly; it is overwritten.

## 🧠 AlphaZero Training
Principles for MCTS and neural network optimization.
- **Workflow**: Generate rollouts -> Train model -> Evaluate -> Checkpoint.
- **Tuning**: Adjust `CPCT`, `DIRICHLET_ALPHA`, and `MCTS_ITERATIONS`.

## 📅 Roadmap & Registry
Registry of planned features and deferred optimizations.
- **Reference**: `future_implementations/SKILL.md`.

## 📦 Deployment
- **HF Upload**: `uv run python tools/hf_upload_staged.py`.
- **Build Dist**: `uv run python tools/build_dist_optimized.py`.
