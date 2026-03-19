import os
import shutil


def sync_assets():
    # Paths relative to project root
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FE_BASE = os.path.join(ROOT, "frontend", "web_ui")
    
    # Prefer Vite build output if it exists
    VITE_DIST = os.path.join(FE_BASE, "dist")
    if os.path.exists(VITE_DIST):
        FE_SRC = VITE_DIST
        print(f"Using Vite build output: {FE_SRC}")
    else:
        FE_SRC = FE_BASE
        print(f"Vite build not found at {VITE_DIST}; using raw source fallback: {FE_SRC}")
        
    IMG_SRC = os.path.join(ROOT, "frontend", "img")
    LAUNCH_DEST_FINAL = os.path.join(ROOT, "launcher", "static_content")
    LAUNCH_DEST = os.path.join(ROOT, "launcher", ".static_content_staging")
    
    if os.path.exists(LAUNCH_DEST):
        shutil.rmtree(LAUNCH_DEST)
    os.makedirs(LAUNCH_DEST)

    print("--- Syncing Assets to Launcher ---")

    # 1. Sync Frontend Web UI (HTML/JS/CSS)
    print(f"Syncing Web UI -> {LAUNCH_DEST}")
    if os.path.exists(FE_SRC):
        # We use a custom copy tree to avoid stomping on the img folder inside static_content if it exists
        for item in os.listdir(FE_SRC):
            s = os.path.join(FE_SRC, item)
            d = os.path.join(LAUNCH_DEST, item)
            if item in ["img", "dist", "node_modules", "package.json", "package-lock.json", "vite.config.js"]:
                continue  # Handled separately or ignored
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

    # 1b. Sync Compiled Data
    print("Syncing Compiled Data...")
    DATA_DEST = os.path.join(LAUNCH_DEST, "data")
    if not os.path.exists(DATA_DEST):
        os.makedirs(DATA_DEST)

    COMPILED_SRC = os.path.join(ROOT, "data", "cards_compiled.json")
    if os.path.exists(COMPILED_SRC):
        shutil.copy2(COMPILED_SRC, os.path.join(DATA_DEST, "cards_compiled.json"))
        print(f"Synced cards_compiled.json to {DATA_DEST}")
    else:
        print(f"WARNING: {COMPILED_SRC} not found!")

    # 2. Smart Sync Images
    IMG_DEST = os.path.join(LAUNCH_DEST, "img")
    print(f"Syncing Images -> {IMG_DEST} (Filtering for WebP/Icons)")

    if not os.path.exists(IMG_DEST):
        os.makedirs(IMG_DEST)

    # Clean up existing cards to ensure no stale PNGs
    CARDS_DEST = os.path.join(IMG_DEST, "cards")
    if os.path.exists(CARDS_DEST):
        shutil.rmtree(CARDS_DEST)

    count = 0
    for root, dirs, files in os.walk(IMG_SRC):
        rel_path = os.path.relpath(root, IMG_SRC)
        target_dir = os.path.join(IMG_DEST, rel_path)

        # Determine if this is a card directory
        is_legacy_cards = rel_path.startswith("cards") and not rel_path.startswith("cards_webp")
        is_webp_cards = rel_path.startswith("cards_webp")

        for f in files:
            ext = f.lower()
            src_file = os.path.join(root, f)
            dest_file = os.path.join(target_dir, f)

            # Inclusion Logic:
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
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                shutil.copy2(src_file, dest_file)
                count += 1

    print(f"Done! Synced {count} image/data files.")


    # 3. Atomic Flip (Windows-Safe)
    print(f"--- Atomic Flip: {LAUNCH_DEST} -> {LAUNCH_DEST_FINAL} ---")
    
    # Use shutil.move() which is more robust on Windows for in-use directories
    # First, remove the old destination if it exists (handles in-use directory)
    if os.path.exists(LAUNCH_DEST_FINAL):
        try:
            # Try to remove the old destination and replace it with staging
            if os.path.exists(LAUNCH_DEST_FINAL):
                shutil.rmtree(LAUNCH_DEST_FINAL)
            shutil.move(LAUNCH_DEST, LAUNCH_DEST_FINAL)
        except (OSError, PermissionError) as e:
            # If the target is in use (common on Windows with dev servers), 
            # copy the new content directly into the existing directory
            print(f"[!] Note: {LAUNCH_DEST_FINAL} is in use (likely dev server). Copying content instead of replacing.")
            for item in os.listdir(LAUNCH_DEST):
                src = os.path.join(LAUNCH_DEST, item)
                dst = os.path.join(LAUNCH_DEST_FINAL, item)
                try:
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                except Exception as inner_e:
                    print(f"[!] Warning: Could not sync {item}: {inner_e}")
            # Clean up staging dir
            try:
                shutil.rmtree(LAUNCH_DEST)
            except Exception as cleanup_e:
                print(f"[!] Warning: Could not clean up staging directory: {cleanup_e}")
    else:
        # Normal case: just rename the staging directory
        shutil.move(LAUNCH_DEST, LAUNCH_DEST_FINAL)

    print("Sync Complete!")


if __name__ == "__main__":
    sync_assets()
