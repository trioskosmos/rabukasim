import os

files_to_clean = [r"engine/game/player_state.py", r"engine/game/game_state.py"]

for file_path in files_to_clean:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if "DEBUG:" in line and "print(" in line:
                continue
            new_lines.append(line)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"Cleaned {file_path}")
    else:
        print(f"File not found: {file_path}")
