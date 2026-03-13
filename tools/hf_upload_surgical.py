import os
import shutil
import tempfile
from pathlib import Path
from huggingface_hub import HfApi

# Configuration
REPO_ID = "trioskosmos/LovecaSim"
TOKEN = os.environ.get("HF_TOKEN")

# Paths
ROOT = Path(__file__).parent.parent.absolute()

def stage_files(staging_dir):
    print(f"Staging files to {staging_dir}...")
    
    # 1. Frontend Web UI
    fe_src = ROOT / "frontend" / "web_ui"
    fe_dest = staging_dir / "frontend" / "web_ui"
    if fe_src.exists():
        shutil.copytree(fe_src, fe_dest, dirs_exist_ok=True)
        print(f"  Synced {fe_src.relative_to(ROOT)}")

    # 2. Frontend Images (Filtered)
    img_src = ROOT / "frontend" / "img"
    img_dest = staging_dir / "frontend" / "img"
    if img_src.exists():
        img_dest.mkdir(parents=True, exist_ok=True)
        # We copy specific folders: cards_webp, texticon, ui
        for folder in ["cards_webp", "texticon", "ui"]:
            src_f = img_src / folder
            if src_f.exists():
                shutil.copytree(src_f, img_dest / folder, dirs_exist_ok=True)
                print(f"  Synced {src_f.relative_to(ROOT)}")
        # And any root images (like icon_blade.png)
        for f in img_src.glob("*"):
            if f.is_file() and f.suffix in [".png", ".webp", ".ico"]:
                shutil.copy2(f, img_dest / f.name)

    # 3. Backend
    backend_src = ROOT / "backend"
    backend_dest = staging_dir / "backend"
    if backend_src.exists():
        shutil.copytree(backend_src, backend_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        print(f"  Synced {backend_src.relative_to(ROOT)}")

    # 4. Data (Compiled Cards)
    data_src = ROOT / "data" / "cards_compiled.json"
    data_dest = staging_dir / "data"
    if data_src.exists():
        data_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(data_src, data_dest / "cards_compiled.json")
        print(f"  Synced {data_src.relative_to(ROOT)}")

    # 5. Launcher (Rust)
    launcher_src = ROOT / "launcher"
    launcher_dest = staging_dir / "launcher"
    if launcher_src.exists():
        shutil.copytree(launcher_src, launcher_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns("target", "build"))
        print(f"  Synced {launcher_src.relative_to(ROOT)}")

    # 6. Engine Rust Src
    engine_src = ROOT / "engine_rust_src"
    engine_dest = staging_dir / "engine_rust_src"
    if engine_src.exists():
        shutil.copytree(engine_src, engine_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns("target", "build"))
        print(f"  Synced {engine_src.relative_to(ROOT)}")

    # 7. Root Build Configs + README
    root_files = ["pyproject.toml", "uv.lock", "Dockerfile", ".dockerignore", "README.md"]
    for rf in root_files:
        src_f = ROOT / rf
        if src_f.exists():
            shutil.copy2(src_f, staging_dir / rf)
            # Touch README.md to ensure it has a fresh timestamp in the commit
            if rf == "README.md":
                (staging_dir / rf).touch()
            print(f"  Synced {rf}")

    # 8. Essential Tools
    tools_dest = staging_dir / "tools"
    tools_dest.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "tools" / "sync_launcher_assets.py", tools_dest / "sync_launcher_assets.py")
    print("  Synced tools/sync_launcher_assets.py")

    # 9. Compiler
    compiler_src = ROOT / "compiler"
    compiler_dest = staging_dir / "compiler"
    if compiler_src.exists():
        shutil.copytree(compiler_src, compiler_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        print(f"  Synced {compiler_src.relative_to(ROOT)}")

def upload_to_hf(staging_dir, dry_run=False):
    if dry_run:
        print("\n--- DRY RUN: Files that would be uploaded ---")
        for p in Path(staging_dir).rglob("*"):
            if p.is_file():
                print(f"  {p.relative_to(staging_dir)}")
        print("--- END DRY RUN ---")
        return

    if not TOKEN:
        print("ERROR: HF_TOKEN environment variable not set.")
        return

    api = HfApi()
    print(f"\nStarting surgical upload to {REPO_ID}...")
    
    # We want to delete old artifacts that are not in our surgical staging
    # This ensures the remote matches our staging exactly for the directories we care about.
    # We use a broad delete pattern for files that might be leftovers from previous "full" uploads.
    delete_patterns = ["TEST_UPLOAD.txt", "archive/*", "logs/*", "*.log"]
    
    try:
        api.upload_folder(
            folder_path=str(staging_dir),
            repo_id=REPO_ID,
            repo_type="space",
            token=TOKEN,
            commit_message="Surgical update of frontend and backend",
            commit_description="Updated via tools/hf_upload_surgical.py - cleaning up stale artifacts.",
            ignore_patterns=["*.pyc", "__pycache__/*"],
            delete_patterns=delete_patterns,
        )
        print("Upload complete!")
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Surgically upload LovecaSim to Hugging Face Spaces.")
    parser.add_argument("--dry-run", action="store_true", help="Lists files to be staged without uploading.")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        staging_dir = Path(tmpdir)
        stage_files(staging_dir)
        upload_to_hf(staging_dir, dry_run=args.dry_run)
