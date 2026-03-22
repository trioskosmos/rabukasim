import sys

def replace_in_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. resolve_semantic_frames check_condition_opcode
    old1 = """            if state.debug.debug_mode {
                println!(
                    "[DEBUG] CALLING check_condition_opcode: op={}, a={:x}",
                    real_op, a
                );
            }"""
    new1 = """            if state.debug.debug_mode {
                if !state.ui.silent {
                    println!(
                        "[DEBUG] CALLING check_condition_opcode: op={}, a={:x}",
                        real_op, a
                    );
                }
            }"""
    
    # 2. resolve_semantic_frames result_line
    old2 = """                println!("[DEBUG] {}", result_line);"""
    new2 = """                if !state.ui.silent {
                    println!("[DEBUG] {}", result_line);
                }"""
    
    # 3. resolve_bytecode log_line
    old3 = """            let log_line = format!("BC_STEP: [depth={}] [card={}] ip={:<3} {}", stack_depth, card_name, ip, desc);
            println!("[DEBUG] {}", log_line);"""
    new3 = """            let log_line = format!("BC_STEP: [depth={}] [card={}] ip={:<3} {}", stack_depth, card_name, ip, desc);
            if !state.ui.silent {
                println!("[DEBUG] {}", log_line);
            }"""
            
    # 4. resolve_bytecode check_condition_opcode
    old4 = """            if state.debug.debug_mode {
                println!(
                    "[DEBUG] CALLING check_condition_opcode: op={}, a={:x}",
                    real_op, a
                );
            }"""
    new4 = """            if state.debug.debug_mode {
                if !state.ui.silent {
                    println!(
                        "[DEBUG] CALLING check_condition_opcode: op={}, a={:x}",
                        real_op, a
                    );
                }
            }"""

    # 5. resolve_bytecode result_line
    old5 = """                println!("[DEBUG] {}", result_line);"""
    new5 = """                if !state.ui.silent {
                    println!("[DEBUG] {}", result_line);
                }"""

    # 6. resolve_bytecode cond_desc
    old6 = """                println!("      | [COND] {}", cond_desc);"""
    new6 = """                if !state.ui.silent {
                    println!("      | [COND] {}", cond_desc);
                }"""

    # Apply replacements
    # Use replace with a count to avoid accidental double-nesting if some are already done
    # But wait, I'll check if already done first.
    
    for old, new in [(old1, new1), (old2, new2), (old3, new3), (old4, new4), (old5, new5), (old6, new6)]:
        if old in content:
            content = content.replace(old, new)
            print(f"Replaced one instance")
        else:
            print(f"Could not find target content")

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    replace_in_file(sys.argv[1])
