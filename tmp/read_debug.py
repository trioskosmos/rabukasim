import sys
import re

failed_tests = ['test_q53_deck_refresh_with_empty_deck', 'test_card_579_ability_1_heart_filter', 'test_q160_play_count_trigger']
capturing = False
current_test = None
output = []

try:
    with open('reports/full_rust_test_run.txt', 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    
    # First find where the individual test failures are reported
    for i, line in enumerate(lines):
        if '---- ' in line and ' stdout ----' in line:
            test_name = line.replace('---- ', '').replace(' stdout ----', '').strip()
            if any(ft in test_name for ft in failed_tests):
                capturing = True
                current_test = test_name
                output.append(f"\nFailure for {test_name}:")
                continue
        
        if capturing:
            if '---- ' in line and ' stdout ----' in line:
                capturing = False
            elif 'failures:' in line and i > 100: # end of stdout section
                capturing = False
            else:
                output.append(line.strip())
                
    if not output:
        print("No detailed failure messages found. Printing last 100 lines for context:")
        for line in lines[-100:]:
            print(line.strip())
    else:
        for line in output:
            print(line)

except Exception as e:
    print(f"Error: {e}")
