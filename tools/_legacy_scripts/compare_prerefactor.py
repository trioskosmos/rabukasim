import os


def check_missing_files(prerefactor_dir, current_repo_dir):
    missing_files = []
    for root, dirs, files in os.walk(prerefactor_dir):
        # Calculate the relative path from the prerefactor root
        rel_path = os.path.relpath(root, prerefactor_dir)

        # Determine the equivalent path in the current repo
        # Note: In the current repo, we might have moved things (e.g. into frontend/web_ui)
        # but let's first check for exact matches.

        for file in files:
            file_rel_path = os.path.join(rel_path, file)
            current_path = os.path.join(current_repo_dir, file_rel_path)

            # Special case: frontend files might have moved to frontend/web_ui
            if file_rel_path.startswith("frontend") and not os.path.exists(current_path):
                # Try frontend/web_ui
                alt_rel_path = file_rel_path.replace("frontend", "frontend/web_ui", 1)
                current_path = os.path.join(current_repo_dir, alt_rel_path)

            if not os.path.exists(current_path):
                missing_files.append(file_rel_path)

    return missing_files


prerefactor = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\prerefactor\lovecasim-main"
current_repo = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy"

missing = check_missing_files(prerefactor, current_repo)
if missing:
    print("Missing files (not in their original or expected new locations):")
    for f in missing:
        print(f)
else:
    print("No missing files found (all accounted for in original or expected new locations).")
