# Distribution Guide

This guide explains how to package the game for distribution and what to tell your users.

## 1. Prerequisites (For Developer)

Ensure you have the Rust toolchain installed.
```bash
rustup target add wasm32-unknown-unknown
cargo install wasm-pack
```

## 2. Build the Package

Run the build script from the repository root:
```bash
./scripts/build_dist.sh
```

This will create a `dist/` folder containing:
*   `loveca_launcher` (The executable)
*   `www/` (Game files)
*   `pkg/` (WASM engine)
*   `data/` (Card database)

## 3. Package for Users

1.  **Locate** the `dist` folder.
2.  **Rename** it to something user-friendly, e.g., `LovecaSolo_Offline`.
3.  **Zip** the folder. (Right-click -> Send to -> Compressed (zipped) folder).
    *   Result: `LovecaSolo_Offline.zip`

## 4. Instructions for Users (Copy-Paste)

You can send the following instructions to your less technically inclined users:

---

### **How to Play Loveca Solo (Offline)**

Hi! Here is the offline version of the game.

1.  **Download** the attached zip file.
2.  **Unzip/Extract** the folder to your Desktop or Documents.
    *   *Important*: Do not run the file directly from inside the zip! Extract it first.
3.  Open the folder and double-click **`loveca_launcher`** (or `loveca_launcher.exe`).
4.  The game will open in your web browser automatically.

**No installation is required.** Have fun!
---
