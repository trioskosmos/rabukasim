import os

# Simulation of GameState path logic
current_file = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine\game\game_state.py"
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(current_file))))
data_path = os.path.join(base_dir, "data", "cards.json")

print(f"Computed Base Dir: {base_dir}")
print(f"Computed Data Path: {data_path}")
print(f"Data Path Exists: {os.path.exists(data_path)}")

print("\nActual CWD:", os.getcwd())
print("Files in data/ (manually):", os.listdir(os.path.join(os.getcwd(), "data")) if os.path.exists("data") else "N/A")
