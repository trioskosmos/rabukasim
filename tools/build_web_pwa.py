import json
import os
import shutil
from pathlib import Path


def build_web_pwa():
    # Paths relative to project root
    ROOT = Path(__file__).parent.parent.absolute()
    FE_SRC = ROOT / "frontend" / "web_ui"
    IMG_SRC = ROOT / "frontend" / "img"
    WASM_SRC = ROOT / "engine_rust_src" / "target" / "wasm32-unknown-unknown" / "release" / "engine_rust.wasm"
    DATA_SRC = ROOT / "data" / "cards_compiled.json"
    DIST_DEST = ROOT / "web_dist"

    print("--- Building LovecaSim Web PWA ---")

    if DIST_DEST.exists():
        print(f"Cleaning existing {DIST_DEST}...")
        shutil.rmtree(DIST_DEST)
    DIST_DEST.mkdir(exist_ok=True)

    # 1. Copy Frontend Web UI (HTML/JS/CSS)
    print("Copying Web UI assets...")
    # Copy everything except the img folder initially
    for item in FE_SRC.iterdir():
        if item.name == "img":
            continue
        if item.is_dir():
            shutil.copytree(item, DIST_DEST / item.name)
        else:
            shutil.copy2(item, DIST_DEST / item.name)

    # 2. Smart Copy Images (WebP Only)
    IMG_DEST = DIST_DEST / "img"
    IMG_DEST.mkdir(exist_ok=True)
    print("Copying optimized images (WebP only)...")

    img_count = 0
    for root, dirs, files in os.walk(IMG_SRC):
        rel_path = os.path.relpath(root, IMG_SRC)
        target_dir = IMG_DEST / rel_path

        # Determine if this is a card directory
        is_legacy_cards = rel_path.startswith("cards") and not rel_path.startswith("cards_webp")
        is_webp_cards = rel_path.startswith("cards_webp")

        for f in files:
            ext = f.lower()
            src_file = os.path.join(root, f)

            should_copy = False
            if is_webp_cards:
                if ext.endswith(".webp"):
                    should_copy = True
            elif is_legacy_cards:
                should_copy = False
            else:
                # General assets
                if ext.endswith((".webp", ".json", ".txt")):
                    should_copy = True
                elif ext.endswith(".png"):
                    if "ui" in root.lower() or "texticon" in root.lower() or rel_path == ".":
                        should_copy = True

            if should_copy:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, target_dir / f)
                img_count += 1

    print(f"Copied {img_count} assets.")

    # 3. Copy Compiled Card Database
    print("Copying card metadata...")
    DATA_DEST = DIST_DEST / "data"
    DATA_DEST.mkdir(exist_ok=True)
    if DATA_SRC.exists():
        shutil.copy2(DATA_SRC, DATA_DEST / "cards_compiled.json")
        # Also copy the raw cards.json for the deck builder and viewer
        RAW_DATA_SRC = DATA_SRC.parent / "cards.json"
        if RAW_DATA_SRC.exists():
            shutil.copy2(RAW_DATA_SRC, DATA_DEST / "cards.json")
    else:
        print(f"WARNING: {DATA_SRC} not found! Run card compiler first.")

    # 3.1 Copy AI Decks
    print("Copying AI decks...")
    DECKS_SRC = ROOT / "ai" / "decks"
    DECKS_DEST = DIST_DEST / "decks"
    DECKS_DEST.mkdir(exist_ok=True)
    if DECKS_SRC.exists():
        deck_names = []
        for f in DECKS_SRC.iterdir():
            if f.suffix == ".txt" and not f.name.startswith("verify"):
                shutil.copy2(f, DECKS_DEST / f.name)
                deck_names.append(f.stem)

        # Create a manifest for the decks
        with open(DECKS_DEST / "list.json", "w", encoding="utf-8") as f_json:
            json.dump({"success": True, "available_decks": deck_names}, f_json)
        print(f"Copied {len(deck_names)} decks.")
    else:
        print(f"WARNING: AI decks directory {DECKS_SRC} not found!")

    # 4. Handle WASM Engine
    PKG_DEST = DIST_DEST / "pkg"
    PKG_DEST.mkdir(exist_ok=True)

    # Check for wasm-pack style pkg folder first (if user ran it)
    ENGINE_PKG_SRC = ROOT / "engine_rust_src" / "pkg"
    if ENGINE_PKG_SRC.exists():
        print("Found wasm-pack 'pkg' folder, copying...")
        for item in ENGINE_PKG_SRC.iterdir():
            shutil.copy2(item, PKG_DEST / item.name)
    else:
        print("Wasm 'pkg' folder not found. Attempting manual WASM copy...")
        if WASM_SRC.exists():
            shutil.copy2(WASM_SRC, PKG_DEST / "engine_rust_bg.wasm")
            print("Copied wasm binary. Note: JS glue (engine_rust.js) may be missing!")
        else:
            print(f"ERROR: WASM binary not found at {WASM_SRC}")

    # 5. Generate PWA Manifest
    print("Generating manifest.json...")
    manifest = {
        "name": "Love Live! School Idol Collection Sim",
        "short_name": "LovecaSim",
        "description": "Love Live! SIC TCG Simulator with AI Support",
        "start_url": "./index.html",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#ff4a9e",
        "icons": [{"src": "img/icon_blade.png", "sizes": "192x192", "type": "image/png"}],
    }
    with open(DIST_DEST / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=4)

    print(f"\nBuild Complete! Files ready in: {DIST_DEST}")
    print("To deploy to GitHub Pages, commit the contents of 'web_dist' to a 'gh-pages' branch or 'docs' folder.")


if __name__ == "__main__":
    build_web_pwa()
