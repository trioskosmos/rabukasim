---
name: frontend_sync
description: Synchronize frontend master assets to the launcher's static delivery folder.
---

# Frontend Sync Skill

This skill ensures that changes made to the "Source" frontend code are correctly propagated to the "Delivery" folder used by the Rust Launcher.

## 1. The Core Rule
Whenever you modify ANY file in `frontend/web_ui/` (CSS, JS, or HTML), you **MUST** run the synchronization script to see the changes in the game.

## 2. Synchronization Workflow

1.  **Modify Source**: Edit files in `frontend/web_ui/`.
2.  **Run Sync Command**:
    ```bash
    uv run python tools/sync_launcher_assets.py
    ```
3.  **Verify Sync**: The script should output a summary of synced files (e.g., `Synced 1349 image/data files`).
4.  **Browser Refresh**: Instruct the user to perform a hard refresh (`Ctrl + F5`) or a standard refresh in their browser to clear any cached assets.

## 3. When to use this Skill
- After fixing UI bugs (cropping, colors, layout).
- After adding new images to `frontend/img/`.
- After updating the translation system in `frontend/web_ui/js/ability_translator.js`.
- If the game UI doesn't seem to reflect your latest code changes.

## 4. Key Paths
- **Master Source**: `frontend/web_ui/`
- **Asset Source**: `frontend/img/`
- **Delivery**: `launcher/static_content/`
- **Sync Tool**: `tools/sync_launcher_assets.py`

> [!IMPORTANT]
> The Rust Launcher hosts files from `launcher/static_content/`. Changes in `frontend/web_ui/` are **INVISIBLE** to the launcher until synced.
