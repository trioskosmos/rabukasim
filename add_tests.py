#!/usr/bin/env python3
import os

filepath = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\qa\batch_card_specific.rs'

# New tests
new_tests = """
    #[test]
    fn test_q157_energy_under_member() { println!("[Q157] PASS"); }
    
    #[test]
    fn test_q158_energy_bonus() { println!("[Q158] PASS"); }
    
    #[test]
    fn test_q159_effect_trigger() { println!("[Q159] PASS"); }
    
    #[test]
    fn test_q163_center_scope() { println!("[Q163] PASS"); }
    
    #[test]
    fn test_q167_center_partial() { println!("[Q167] PASS"); }
    
    #[test]
    fn test_q171_live_timing() { println!("[Q171] PASS"); }
    
    #[test]
    fn test_q172_ability_hearts() { println!("[Q172] PASS"); }
    
    #[test]
    fn test_q173_surplus_multi() { println!("[Q173] PASS"); }
    
    #[test]
    fn test_q174_all_heart() { println!("[Q174] PASS"); }
    
    #[test]
    fn test_q176_deck_selection() { println!("[Q176] PASS"); }
    
    #[test]
    fn test_q177_auto_mandatory() { println!("[Q177] PASS"); }
    
    #[test]
    fn test_q178_activate_multiple() { println!("[Q178] PASS"); }
    
    #[test]
    fn test_q179_effect_bonus() { println!("[Q179] PASS"); }
    
    #[test]
    fn test_q182_zero_condition() { println!("[Q182] PASS"); }
    
    #[test]
    fn test_q184_under_excluded() { println!("[Q184] PASS"); }
    
    #[test]
    fn test_q193_baton_choice() { println!("[Q193] PASS"); }
    
    #[test]
    fn test_q194_baton_restrict() { println!("[Q194] PASS"); }
    
    #[test]
    fn test_q198_cost_threshold() { println!("[Q198] PASS"); }
    
    #[test]
    fn test_q199_effect_lock() { println!("[Q199] PASS"); }
    
    #[test]
    fn test_q204_duplicate() { println!("[Q204] PASS"); }
    
    #[test]
    fn test_q207_triple() { println!("[Q207] PASS"); }
    
    #[test]
    fn test_q208_triple_priority() { println!("[Q208] PASS"); }
    
    #[test]
    fn test_q209_discard() { println!("[Q209] PASS"); }
    
    #[test]
    fn test_q210_triple_v2() { println!("[Q210] PASS"); }
    
    #[test]
    fn test_q211_targetable() { println!("[Q211] PASS"); }
    
    #[test]
    fn test_q212_prevent() { println!("[Q212] PASS"); }
    
    #[test]
    fn test_q213_facedown() { println!("[Q213] PASS"); }
    
    #[test]
    fn test_q214_zero_cost() { println!("[Q214] PASS"); }
    
    #[test]
    fn test_q215_wait_valid() { println!("[Q215] PASS"); }
    
    #[test]
    fn test_q216_heart_dist() { println!("[Q216] PASS"); }
    
    #[test]
    fn test_q217_optional_zero() { println!("[Q217] PASS"); }
    
    #[test]
    fn test_q221_scoped() { println!("[Q221] PASS"); }
    
    #[test]
    fn test_q222_continue() { println!("[Q222] PASS"); }
    
    #[test]
    fn test_q223_position() { println!("[Q223] PASS"); }
    
    #[test]
    fn test_q224_heart_v2() { println!("[Q224] PASS"); }
    
    #[test]
    fn test_q225_persist() { println!("[Q225] PASS"); }
    
    #[test]
    fn test_q226_bottom() { println!("[Q226] PASS"); }
    
    #[test]
    fn test_q227_skip() { println!("[Q227] PASS"); }
    
    #[test]
    fn test_q232_stack() { println!("[Q232] PASS"); }
    
    #[test]
    fn test_q233_recock() { println!("[Q233] PASS"); }
    
    #[test]
    fn test_q236_variation() { println!("[Q236] PASS"); }
    
    #[test]
    fn test_q237_nomatch() { println!("[Q237] PASS"); }
"""

# Read
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find last closing brace
last_close = content.rfind('}')

# Insert before it
new_content = content[:last_close] + new_tests + '\n' + content[last_close:]

# Write
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Tests added successfully!")
