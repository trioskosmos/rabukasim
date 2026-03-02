import os
import re

exclude = ["game.rs", "interpreter.rs", "py_bindings.rs", "test_helpers.rs", "action_gen.rs", "rules.rs", "performance.rs", "lib.rs"]
target_dirs = [
    r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src",
    r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\tests"
]

modified_files = []
for target_dir in target_dirs:
    for root, _, files in os.walk(target_dir):
        for fn in files:
            if fn.endswith(".rs") and fn not in exclude:
                path = os.path.join(root, fn)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # 1. replace resolve_bytecode_ref -> resolve_bytecode_cref (typo fix)
                    content = content.replace(".resolve_bytecode_ref(", ".resolve_bytecode_cref(")
                    
                    # 2. replace state.resolve_bytecode(&db, &bc, &ctx) -> state.resolve_bytecode_cref(&db, &bc, &ctx)
                    content = re.sub(r'(\w+)\.resolve_bytecode\(&(\w+), &(\w+), &(\w+)\)', 
                                    r'\1.resolve_bytecode_cref(&\2, &\3, &\4)', 
                                    content)
                    
                    # 3. handle free function calls: resolve_bytecode(&mut state, &db, bytecode, &ctx)
                    content = re.sub(r'resolve_bytecode\(&mut (\w+), &(\w+), (\w+), &(\w+)\)', 
                                    r'resolve_bytecode(&mut \1, &\2, std::sync::Arc::new(\3.clone()), &\4)', 
                                    content)
                    
                    # 4. fix process_rule_checks() -> process_rule_checks(&db)
                    if "state.process_rule_checks()" in content:
                        if "let db =" not in content and "let mut db =" not in content:
                            # Insert dummy db
                            content = content.replace("let mut state = GameState::default();", 
                                                    "let mut state = GameState::default();\n    let db = CardDatabase::default();")
                            content = content.replace("state.process_rule_checks()", "state.process_rule_checks(&db)")
                        else:
                            content = content.replace("state.process_rule_checks()", "state.process_rule_checks(&db)")

                    if content != original_content:
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(content)
                        modified_files.append(fn)
                except Exception as e:
                    print(f"Error processing {path}: {e}")

print(f"Modified {len(modified_files)} files: {', '.join(modified_files)}")
