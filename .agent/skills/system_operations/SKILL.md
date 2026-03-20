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
- **HF Upload**: `uv run python tools/hf_upload_staged.py` (uploads current repo state to HF via API).
- **Git Push (HF)**: `cd hf_space && git push origin main` (manual Git push to HF).
- **Build Dist**: `uv run python tools/build_dist_optimized.py`.

### 🚀 Hugging Face (HF) Spaces Protocol
HF has strict limits (10MB for Git blobs, 0-tolerance for raw binaries in history).

1. **Repository Separation**:
   - The `hf_space/` directory is an independent Git repository for deployment.
   - It MUST be ignored by the main project via root `.gitignore` to prevent tracking interference.
   - Files are synced to it before pushing.

2. **Large Assets & Git LFS**:
   - Binaries (`.png`, `.webp`, `.exe`, `.bin`) and large data files (`*.json`) MUST be tracked by Git LFS in the `hf_space` repo.
   - *Check*: `git lfs ls-files` inside `hf_space/`.
   - *Add*: `git lfs track "*.json" "*.bin"` if not present.

3. **History Scrubbing**:
   - If HF rejects a push for "binary files", you must rewrite history to move historical blobs to LFS.
   - *Command*: `git lfs migrate import --everything --include="*.exe,*.vsix,data/*.txt,*.pdf,*.png,*.json,*.bin"`.
   - *Final Push*: `git push origin main --force`.

4. **Dockerfile Compliance**:
   - The `hf_space/Dockerfile` MUST compile the Rust engine and launcher during the build.
   - **Binary Name**: The launcher binary is `rabuka_launcher` (check `launcher/Cargo.toml`).
   - Re-runs `python -m compiler.main` to ensure card data is fresh.
   - Must use `EXPOSE 7860` for Spaces.
