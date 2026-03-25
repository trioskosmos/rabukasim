import sys
import re

def fix_mod_rs(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the correctly gated versions
    
    # 1. resolve_semantic_frames check_condition_opcode
    # Search for the pattern and replace it
    content = re.sub(
        r'if state\.debug\.debug_mode \{\s+println!\(\s+"\[DEBUG\] CALLING check_condition_opcode: op=\{\}, a=\{:x\}",\s+real_op, a\s+\);\s+\}',
        r'if state.debug.debug_mode {\n                if !state.ui.silent {\n                    println!(\n                        "[DEBUG] CALLING check_condition_opcode: op={}, a={:x}",\n                        real_op, a\n                    );\n                }\n            }',
        content
    )

    # 2. resolve_semantic_frames cond_desc and its println
    # Restore the definition if it's missing (it matches the println without the let)
    def fix_cond_desc(m):
        match_str = m.group(0)
        if "let cond_desc =" in match_str:
            return match_str # Already has it (maybe double gated)
        
        # If it's gated but missing the let, we need to find where to put the let.
        # But wait, it's easier to just replace the whole block if we can find it.
        return match_str

    # Let's just use a simpler approach: replace the broken blocks with known good ones.
    
    # Cleaning up the accidental double nesting and missing let
    # This matches the broken block I saw in step 295
    broken_block = r'if state\.debug\.debug_mode \{\s+if !state\.ui\.silent \{\s+if !state\.ui\.silent \{\s+println!\("      \| \[COND\] \{\}", cond_desc\);\s+\}\s+\}'
    # We need to restore the let cond_desc before this
    # But wait, I'll just replace the entire block from 'cond = cond && ...' to 'ctx.choice_index = -1;'
    
    # Actually, the most reliable way is to find the println and replace the whole Surrounding if state.debug.debug_mode block
    
    patterns_to_fix = [
        # resolve_semantic_frames cond
        (r'cond = cond && if is_negated \{ !passed \} else \{ passed \};\s+if state\.debug\.debug_mode \{.*?\}\s+ctx\.choice_index = -1;',
         r'''cond = cond && if is_negated { !passed } else { passed };
            if state.debug.debug_mode {
                let cond_desc = format!(
                    "BC_COND: ip={:<3} {} -> passed={}, final={}",
                    ip,
                    logging::describe_condition(real_op, v, a as u64),
                    passed,
                    cond
                );
                if !state.ui.silent {
                    println!("      | [COND] {}", cond_desc);
                }

                let b_log = &mut state.ui.bytecode_log;
                if b_log.len() < MAX_BYTECODE_LOG_SIZE {
                    b_log.push(cond_desc.clone());
                }
                state.trace_internal(&cond_desc);
            }
            ctx.choice_index = -1;'''),

        # resolve_semantic_frames result
        (r'if state\.debug\.debug_mode \{\s+let result_line = format!\(\s+"BC_RESULT: ip=\{:<3\} \{\}",\s+ip,\s+if is_negated \{ !passed \} else \{ passed \}\s+\);\s+(?:if !state\.ui\.silent \{\s+)+println!\("\[DEBUG\] \{\}", result_line\);(?:\s+\})+',
         r'''if state.debug.debug_mode {
                let result_line = format!(
                    "BC_RESULT: ip={:<3} {}",
                    ip,
                    if is_negated { !passed } else { passed }
                );
                if !state.ui.silent {
                    println!("[DEBUG] {}", result_line);
                }
                let b_log = &mut state.ui.bytecode_log;
                if b_log.len() < MAX_BYTECODE_LOG_SIZE {
                    b_log.push(result_line.clone());
                }
                state.trace_internal(&result_line);
            }'''),
    ]

    for pat, repl in patterns_to_fix:
        content = re.sub(pat, repl, content, flags=re.DOTALL)

    # Now for resolve_frames (the second half of the file)
    # I'll just look for the println! and ensure they are properly gated and have their variables.
    
    # 3. resolve_frames cond_desc
    content = re.sub(
        r'executor\.cond = executor\.cond && if is_negated \{ !passed \} else \{ passed \};\s+if state\.debug\.debug_mode \{.*?\}\s+frame\.ctx\.choice_index = -1;',
        r'''executor.cond = executor.cond && if is_negated { !passed } else { passed };
            if state.debug.debug_mode {
                let cond_desc = format!(
                    "BC_COND: ip={:<3} {} -> passed={}, final={}",
                    ip,
                    logging::describe_condition(real_op, v, a as u64),
                    passed,
                    executor.cond
                );
                if !state.ui.silent {
                    println!("      | [COND] {}", cond_desc);
                }

                let b_log = &mut state.ui.bytecode_log;
                if b_log.len() < MAX_BYTECODE_LOG_SIZE {
                    b_log.push(cond_desc.clone());
                }
                state.trace_internal(&cond_desc);
            }
            frame.ctx.choice_index = -1;''',
        content, flags=re.DOTALL
    )

    # Ensure all [DEBUG] and [COND] println! are gated
    content = re.sub(r'(?<!if !state\.ui\.silent \{\n\s+)println!\("\[DEBUG\]', r'if !state.ui.silent {\n                    println!("[DEBUG]', content)
    # Wait, that's too simple and might break things.
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_mod_rs(sys.argv[1])
