import os
import shutil
import subprocess
import sys

# Paths
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist_rust")
LAUNCHER_DIR = os.path.join(ROOT, "launcher")
STATIC_CONTENT = os.path.join(LAUNCHER_DIR, "static_content")

IMAGES_SRC = os.path.join(ROOT, "frontend", "img")
WEB_UI_SRC = os.path.join(ROOT, "frontend", "web_ui")


def clean():
    print(f"[1/5] Cleaning {DIST} and static_content...")
    if os.path.exists(DIST):
        try:
            shutil.rmtree(DIST)
        except Exception as e:
            print(f"Warning: Could not fully clean {DIST}: {e}")
            print("!!! HINT: Is loveca_launcher.exe still running? Please close it! !!!")

    os.makedirs(DIST, exist_ok=True)

    if os.path.exists(STATIC_CONTENT):
        try:
            shutil.rmtree(STATIC_CONTENT)
        except Exception as e:
            print(f"Warning: Could not fully clean {STATIC_CONTENT}: {e}")

    os.makedirs(STATIC_CONTENT, exist_ok=True)


def build_wasm():
    print("[2/5] Building WASM Engine (Optional)...")
    engine_dir = os.path.join(ROOT, "engine_rust_src")
    pkg_dest = os.path.join(STATIC_CONTENT, "pkg")

    # Check if wasm-pack is available
    wasm_pack = shutil.which("wasm-pack")
    if wasm_pack:
        print("Using wasm-pack...")
        # Build directly to static_content/pkg
        try:
            res = subprocess.run([wasm_pack, "build", "--target", "web", "--out-dir", pkg_dest], cwd=engine_dir)
            if res.returncode != 0:
                print("WASM build failed (non-fatal, Offline Mode via WASM will be disabled).")
        except Exception as e:
            print(f"WASM build error: {e}")
    else:
        print("wasm-pack not found. Skipping WASM build.")
        print("Offline Mode (Client-Side) will not work, but Server Mode (Rust backend) will work fine.")


def prepare_static_content():
    print("[3/5] Preparing Static Content (Frontend + Images + Data)...")

    # 1. Frontend (Root of static_content)
    for item in os.listdir(WEB_UI_SRC):
        if item == "pkg":
            continue  # Skip existing pkg if any
        s = os.path.join(WEB_UI_SRC, item)
        d = os.path.join(STATIC_CONTENT, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    # 2. Images (into static_content/img)
    # 2. Images (into static_content/img) - WEBP ONLY
    img_dest = os.path.join(STATIC_CONTENT, "img")

    if os.path.exists(IMAGES_SRC):
        os.makedirs(img_dest, exist_ok=True)
        print("[3.2/5] Copying only WebP images (skipping PNGs to save space)...")
        for root, dirs, files in os.walk(IMAGES_SRC):
            # Create corresponding subdir in dist
            rel_path = os.path.relpath(root, IMAGES_SRC)
            target_dir = os.path.join(img_dest, rel_path)
            os.makedirs(target_dir, exist_ok=True)

            for f in files:
                if f.lower().endswith(".webp"):
                    shutil.copy2(os.path.join(root, f), os.path.join(target_dir, f))

    # 3. Data (into static_content/data)
    data_dest = os.path.join(STATIC_CONTENT, "data")
    os.makedirs(data_dest, exist_ok=True)
    cards_json = os.path.join(ROOT, "data", "cards.json")
    cards_compiled = os.path.join(ROOT, "data", "cards_compiled.json")

    if os.path.exists(cards_json):
        shutil.copy2(cards_json, os.path.join(data_dest, "cards.json"))
    if os.path.exists(cards_compiled):
        shutil.copy2(cards_compiled, os.path.join(data_dest, "cards_compiled.json"))
    else:
        print(f"Warning: {cards_compiled} not found.")


def build_launcher():
    print("[4/5] Building Rust Launcher (Embedding Assets)...")
    res = subprocess.run(["cargo", "build", "--release"], cwd=LAUNCHER_DIR)
    if res.returncode != 0:
        print("Launcher build failed! Ensure rust-embed and dependencies are correct.")
        sys.exit(1)

    # Copy launcher executable
    exe_name = "loveca_launcher.exe" if os.name == "nt" else "loveca_launcher"
    exe_src = os.path.join(LAUNCHER_DIR, "target", "release", exe_name)

    if os.path.exists(exe_src):
        shutil.copy(exe_src, os.path.join(DIST, exe_name))
        print(f"[5/5] Success! copied {exe_name} to {DIST}")
    else:
        print("Error: Compiled executable not found.")


if __name__ == "__main__":
    clean()
    build_wasm()
    prepare_static_content()
    build_launcher()
    print("\n--------------------------------------------------")
    print(f"Build Complete! Single-file executable is in: {DIST}")
    print("Run loveca_launcher.exe directly. No other files needed.")
    print("--------------------------------------------------")
