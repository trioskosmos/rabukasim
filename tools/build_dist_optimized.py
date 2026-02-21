import os
import shutil
import subprocess
import sys

# Paths
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
TEMP_STAGING = os.path.join(ROOT, "build_staging")

IMAGES_SRC = os.path.join(ROOT, "frontend", "img")
WEB_UI_SRC = os.path.join(ROOT, "frontend", "web_ui")
SERVER_PY = os.path.join(ROOT, "backend", "server.py")


def clean():
    print(f"[1/4] Cleaning {DIST} and {TEMP_STAGING}...")
    for p in [DIST, TEMP_STAGING]:
        if os.path.exists(p):
            shutil.rmtree(p)
        os.makedirs(p, exist_ok=True)


def prepare_minimal_assets():
    print("[2/4] Preparing Minimal Assets (WebP only)...")

    # 1. Frontend
    fe_dest = os.path.join(TEMP_STAGING, "frontend", "web_ui")
    shutil.copytree(WEB_UI_SRC, fe_dest, dirs_exist_ok=True)

    # 2. Images (Filter WebP)
    img_dest = os.path.join(TEMP_STAGING, "frontend", "img")
    os.makedirs(img_dest, exist_ok=True)

    total_size = 0
    count = 0
    for root, dirs, files in os.walk(IMAGES_SRC):
        rel_path = os.path.relpath(root, IMAGES_SRC)
        target_dir = os.path.join(img_dest, rel_path)
        os.makedirs(target_dir, exist_ok=True)

        is_card_dir = "cards" in rel_path.lower()

        for f in files:
            ext = f.lower()
            src_file = os.path.join(root, f)

            should_copy = False
            if ext.endswith((".webp", ".json", ".txt")):
                should_copy = True
            elif ext.endswith(".png"):
                # Essential icons in root or subdirs, BUT skip card PNGs
                if not is_card_dir:
                    should_copy = True
                elif "ui" in root.lower() or "texticon" in root.lower():
                    should_copy = True

            if should_copy:
                shutil.copy2(src_file, os.path.join(target_dir, f))
                total_size += os.path.getsize(src_file)
                count += 1

    print(f"   Collected {count} files ({total_size / 1024 / 1024:.1f} MB)")

    # 3. Data
    data_dest = os.path.join(TEMP_STAGING, "data")
    os.makedirs(data_dest, exist_ok=True)
    shutil.copy2(os.path.join(ROOT, "data", "cards_compiled.json"), os.path.join(data_dest, "cards_compiled.json"))


def run_rust_build():
    print("[3/4] Building Rust Launcher (Standalone EXE)...")

    # 1. Sync assets to launcher/static_content
    # We call the script via subprocess to ensure clean environment and path handling
    try:
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sync_launcher_assets.py")], check=True)
    except Exception as e:
        print(f"Asset sync failed: {e}")
        raise

    # 2. Build Rust binary
    launcher_dir = os.path.join(ROOT, "launcher")
    try:
        subprocess.run(["cargo", "build", "--release"], cwd=launcher_dir, check=True)
    except Exception as e:
        print(f"Rust build failed: {e}")
        raise

    # 3. Copy binary to dist
    ext = ".exe" if sys.platform == "win32" else ""
    src_bin = os.path.join(launcher_dir, "target", "release", f"loveca_launcher{ext}")
    dest_bin = os.path.join(DIST, f"LovecaSim{ext}")

    if os.path.exists(src_bin):
        shutil.copy2(src_bin, dest_bin)
        print(f"   Created {dest_bin} ({os.path.getsize(dest_bin) / 1024 / 1024:.1f} MB)")
    else:
        raise FileNotFoundError(f"Could not find build binary at {src_bin}")


def create_source_archive():
    print("[4/5] Creating Source Code Archive...")
    archive_name = os.path.join(DIST, "Source_Code")
    # Exclude build artifacts and envs if possible, or just zip the root minus some folders
    # Shutil make_archive is simple but zips everything.
    # Better to use a specific patterns or just zip the main folders.

    # We'll use a temporary folder for source selection to keep it clean
    src_staging = os.path.join(ROOT, "source_staging")
    if os.path.exists(src_staging):
        shutil.rmtree(src_staging)
    os.makedirs(src_staging)

    dirs_to_include = [
        "backend",
        "engine",
        "frontend",
        "ai",
        "tools",
        "compiler",
        "data",
        "engine_rust_src",
        "launcher",
    ]
    files_to_include = ["pyproject.toml", "README.md", "GEMINI.md", "start_server.bat", "build_engine.bat"]

    for d in dirs_to_include:
        src_d = os.path.join(ROOT, d)
        if os.path.exists(src_d):
            shutil.copytree(
                src_d,
                os.path.join(src_staging, d),
                ignore=shutil.ignore_patterns("__pycache__", "target", "build", "node_modules", ".venv"),
            )

    for f in files_to_include:
        src_f = os.path.join(ROOT, f)
        if os.path.exists(src_f):
            shutil.copy2(src_f, os.path.join(src_staging, f))

    shutil.make_archive(archive_name, "zip", src_staging)
    shutil.rmtree(src_staging)
    print(f"   Created {archive_name}.zip")


def main():
    try:
        clean()
        run_rust_build()
        create_source_archive()
        print(f"\n[5/5] Success! Release artifacts are in {DIST}/")
    except Exception as e:
        print(f"Error during build: {e}")
        sys.exit(1)
    finally:
        # Cleanup staging
        if os.path.exists(TEMP_STAGING):
            shutil.rmtree(TEMP_STAGING)


if __name__ == "__main__":
    main()
