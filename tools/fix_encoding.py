import os
import re

def fix(path, pattern, replace):
    print(f"Fixing {path}...")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = bool(re.search(pattern, content))
    if new_content:
        content = re.sub(pattern, replace, content)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {path}")
    else:
        print(f"No match in {path}")

fix("engine_rust_src/src/core/logic/interpreter/handlers.rs", r"(?<!pub )fn handle_", r"pub fn handle_")
fix("engine_rust_src/src/qa_verification_tests.rs", r"interpreter::handlers::[a-z_]+::handle_", r"interpreter::handlers::handle_")
fix("engine_rust_src/src/debug_q203.rs", r"interpreter::handlers::[a-z_]+::handle_", r"interpreter::handlers::handle_")
