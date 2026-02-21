# LovecaSim Deployment Guide

This guide covers the two primary ways to deploy LovecaSim to the web.

## 1. Hugging Face Spaces (Primary Hosted Version)
This is the recommended way to host the full game with a Python backend and Rust engine.

### Prerequisites
- A Hugging Face account.
- A **WRITE** access token from [Settings > Tokens](https://huggingface.co/settings/tokens).

### Deployment Steps
1. **Create a Space**: Go to Hugging Face, click "New Space", name it `LovecaSim`, and select **Docker** as the SDK.
2. **Push Code**: Use the `tools/hf_upload_staged.py` script to upload the project.
   - Update the `REPO` and `TOKEN` variables in the script.
   - Run: `uv run python tools/hf_upload_staged.py`
3. **Monitor Build**: Watch the logs in the Hugging Face UI. It will automatically build the container and start the server.
4. **Access**: Your game will be live at `https://huggingface.co/spaces/YOUR_USERNAME/LovecaSim`.

---

## 2. GitHub Pages (Static/WASM Version)
This version runs entirely in the browser using WebAssembly. It is great for static hosting but does not support "Online Mode" (multiplayer).

### Prerequisites
- `wasm-pack` installed locally.
- A GitHub repository with Pages enabled.

### Deployment Steps
1. **Build WASM**: Run `wasm-pack build engine_rust_src --target web --out-dir ../frontend/web_ui/wasm`.
2. **Sync Assets**: Ensure `frontend/web_ui/js/wasm_adapter.js` is correctly pointing to the WASM files.
3. **Deploy**:
   - Push your code to the `main` branch.
   - Ensure the `.github/workflows/deploy.yml` exists to automate the build.
   - Settings > Pages > Source should be "GitHub Actions".
4. **Access**: Your game will be live at `https://YOUR_USERNAME.github.io/LovecaSim/frontend/web_ui/`.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'ai'" (Hugging Face)
Ensure the `ai/` and `models/` directories are included in your upload script. If you use `hf_upload_staged.py`, check the `dirs` list.

### "404 Not Found" for WASM files (GitHub Pages)
Check that the `.wasm` extension is allowed by your server. On GitHub Pages, this is handled automatically via the deployment workflow. Ensure paths in `wasm_adapter.js` use `getAppBaseUrl()`.

### Stalling Push
If `git push` stalls, it's likely due to large image files in history. Use the "Lean Push" method (orphaned branch) or the `huggingface_hub` Python API for more reliable uploads.
