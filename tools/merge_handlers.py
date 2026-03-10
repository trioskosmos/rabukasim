import os
import re

handlers_dir = "engine_rust_src/src/core/logic/interpreter/handlers"
output_file = "engine_rust_src/src/core/logic/interpreter/handlers.rs"

# Get all rust files
mod_file = os.path.join(handlers_dir, "mod.rs")
sub_files = [f for f in os.listdir(handlers_dir) if f.endswith(".rs") and f != "mod.rs"]

with open(mod_file, "r", encoding="utf-8") as f:
    mod_content = f.read()

# Remove 'pub mod' lines
mod_content = re.sub(r"pub mod [a_z_]+;\n", "", mod_content)
# Remove prefix from dispatch calls like draw_hand::handle_draw -> handle_draw
for sub in [f.replace(".rs", "") for f in sub_files]:
    mod_content = mod_content.replace(f"{sub}::", "")

# We need to collect ALL imports from subfiles and put them at the top.
all_imports = set()
all_code = []

for sub in sub_files:
    with open(os.path.join(handlers_dir, sub), "r", encoding="utf-8") as f:
        lines = f.readlines()

    code_lines = []
    for line in lines:
        if line.startswith("use "):
            if not line.startswith("use super::"):  # ignore internal relative imports
                all_imports.add(line.strip())
        else:
            code_lines.append(line)

    all_code.append("".join(code_lines))

final_content = []
final_content.append("// --- Merged Handlers ---")
for imp in all_imports:
    final_content.append(imp)

final_content.append(mod_content)
final_content.append("\n".join(all_code))

with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(final_content))

print("Successfully merged handlers!")
