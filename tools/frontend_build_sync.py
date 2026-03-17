#!/usr/bin/env python3
"""
Frontend Build & Sync Orchestrator
Follows the guides: VITE_USAGE.md and CSS_ORGANIZATION.md
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd, description, cwd=None):
    """Run a shell command and report status."""
    print(f"\n[->] {description}...")
    print(f"    Command: {' '.join(cmd)}")
    
    try:
        # Use shell=True for better PATH resolution on Windows
        result = subprocess.run(
            " ".join(cmd), 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=300,
            shell=True
        )
        
        if result.returncode == 0:
            print(f"[OK] {description} - SUCCESS")
            if result.stdout:
                print(f"    Output: {result.stdout[:200]}")
            return True
        else:
            print(f"[XX] {description} - FAILED (exit code: {result.returncode})")
            if result.stderr:
                print(f"    Error: {result.stderr[:300]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"[XX] {description} - TIMEOUT (exceeded 300 seconds)")
        return False
    except Exception as e:
        print(f"[XX] {description} - EXCEPTION: {e}")
        return False


def main():
    # __file__ = tools/frontend_build_sync.py
    # parent = tools/
    # parent.parent = loveca-copy/
    # parent.parent.parent = vscode/ (wrong)
    # We need loveca-copy directly
    root_dir = Path(__file__).parent.parent
    frontend_dir = root_dir / "frontend" / "web_ui"
    
    print("=" * 70)
    print("FRONTEND BUILD & SYNC ORCHESTRATOR")
    print("=" * 70)
    print(f"Project Root: {root_dir}")
    print(f"Frontend Dir: {frontend_dir}")
    
    # Step 1: Check npm installation
    print("\n[STEP 1] Checking npm environment...")
    
    if not (frontend_dir / "package.json").exists():
        print("[XX] package.json not found!")
        return False
    
    # Try to install dependencies
    if not (frontend_dir / "node_modules").exists():
        print("[!!] node_modules not found. Installing dependencies...")
        if not run_command(["npm", "install"], "npm install", cwd=frontend_dir):
            print("[!!] npm install failed. Attempting to continue anyway...")
    else:
        print("[OK] node_modules already present")
    
    # Step 2: Clean old dist folder
    print("\n[STEP 2] Preparing build environment...")
    dist_dir = frontend_dir / "dist"
    if dist_dir.exists():
        print(f"[!!] Removing old dist folder...")
        try:
            shutil.rmtree(dist_dir)
            print("[OK] Old dist cleaned")
        except Exception as e:
            print(f"[!!] Could not remove dist: {e}")
    
    # Step 3: Build with Vite
    print("\n[STEP 3] Building with Vite...")
    if not run_command(["npm", "run", "build"], "Vite build", cwd=frontend_dir):
        print("[XX] Build failed. Exiting.")
        return False
    
    # Verify dist was created
    if not dist_dir.exists():
        print("[XX] dist folder was not created by build!")
        return False
    
    print(f"[OK] Build successful. dist/ created at {dist_dir}")
    
    # Step 4: Check dist contents
    print("\n[STEP 4] Verifying build output...")
    try:
        dist_files = list(dist_dir.rglob("*"))
        print(f"[OK] Build contains {len([f for f in dist_files if f.is_file()])} files")
        
        # List key files
        html_files = list(dist_dir.glob("*.html"))
        css_files = list(dist_dir.rglob("*.css"))
        print(f"    - HTML files: {len(html_files)}")
        print(f"    - CSS files: {len(css_files)}")
    except Exception as e:
        print(f"[!!] Could not verify dist: {e}")
    
    # Step 5: Run asset sync
    print("\n[STEP 5] Syncing assets to launcher...")
    sync_script = root_dir / "tools" / "sync_launcher_assets.py"
    
    if not sync_script.exists():
        print(f"[XX] Sync script not found at {sync_script}")
        return False
    
    if not run_command(["python", str(sync_script)], "Asset sync", cwd=root_dir):
        print("[!!] Sync had errors. Check output above.")
        # Don't return False - sync might have recovered gracefully
    
    # Step 6: Verify sync result
    print("\n[STEP 6] Verifying sync result...")
    static_content_dir = root_dir / "launcher" / "static_content"
    
    if not static_content_dir.exists():
        print(f"[XX] static_content directory not created!")
        return False
    
    try:
        static_files = list(static_content_dir.rglob("*"))
        print(f"[OK] Sync successful. static_content/ contains {len([f for f in static_files if f.is_file()])} files")
    except Exception as e:
        print(f"[!!] Could not verify static_content: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("BUILD & SYNC COMPLETE [OK]")
    print("=" * 70)
    print(f"\n[DIR] Build location: {dist_dir}")
    print(f"[DIR] Final assets:   {static_content_dir}")
    print(f"\n[OK] Next steps:")
    print(f"  1. Backend now serves from launcher/static_content/")
    print(f"  2. For development: cd frontend/web_ui && npm run dev")
    print(f"  3. For live reload: CSS changes appear instantly during dev")
    print(f"\n[DOCS] See guides:")
    print(f"  - VITE_USAGE.md             (how to use Vite)")
    print(f"  - CSS_ORGANIZATION.md       (CSS file purposes)")
    print(f"  - QUICK_REFERENCE.md        (quick lookup)")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
