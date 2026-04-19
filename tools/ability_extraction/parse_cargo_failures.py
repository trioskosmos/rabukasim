"""Parse cargo test output to extract failing test names and card IDs."""

import re
import subprocess
import json
from pathlib import Path

def run_cargo_test():
    """Run cargo test and capture output."""
    result = subprocess.run(
        ["cargo", "test", "--lib"],
        cwd="C:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\engine_rust_src",
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    stdout = result.stdout if result.stdout else ""
    stderr = result.stderr if result.stderr else ""
    return stdout + stderr

def extract_failing_tests(output):
    """Extract failing test names from cargo test output."""
    # Pattern to match test failures
    test_pattern = r"test_suite::\w+::tests::(\w+)"
    
    failing_tests = []
    for match in re.finditer(test_pattern, output):
        test_name = match.group(1)
        failing_tests.append(test_name)
    
    return failing_tests

def extract_card_id_from_test(test_name, qa_data_map):
    """Extract card ID from test name."""
    # Pattern to match card IDs in test names like "test_id_717_..."
    match = re.search(r'test_id_(\d+)_', test_name)
    if match:
        return int(match.group(1))
    
    # Pattern to match QA tests (Q1-Q240)
    # Note: QA tests refer to QA data, not card IDs directly
    # The actual card ID is embedded in the qa_data.json
    match = re.search(r'test_q(\d+)_', test_name)
    if match:
        qa_id = int(match.group(1))
        # For QA tests, we need to extract the actual card ID from the test data
        if qa_id <= 240:
            # Look up the actual card ID from qa_data.json
            qa_key = f"Q{qa_id}"
            if qa_key in qa_data_map:
                related_cards = qa_data_map[qa_key].get("related_cards", [])
                if related_cards and len(related_cards) > 0:
                    card_no = related_cards[0].get("card_no", "")
                    # Extract card ID from card_no
                    # Format: PL!-bp3-012-RM -> need to map to card_id
                    # For now, return the card_no as-is
                    return card_no
            return f"QA_{qa_id}"
        else:
            # Above 240, it's actually a card ID
            return qa_id
    
    # Try to extract card identifier like bp2_001, bp4_001, etc.
    match = re.search(r'(bp\d+_\d+)', test_name)
    if match:
        # This is a card identifier but not the card ID
        # Return the identifier as-is for later mapping
        return match.group(1)
    
    return None

def main():
    print("Running cargo test...")
    output = run_cargo_test()
    
    print("Extracting failing tests...")
    failing_tests = extract_failing_tests(output)
    
    print(f"Found {len(failing_tests)} failing tests")
    
    # Load QA data to map QA IDs to card IDs
    qa_data_path = Path("data/qa_data.json")
    qa_data_map = {}
    if qa_data_path.exists():
        with open(qa_data_path, 'r', encoding='utf-8') as f:
            qa_data_list = json.load(f)
            for entry in qa_data_list:
                qa_data_map[entry["id"]] = entry
        print(f"Loaded {len(qa_data_map)} QA data entries")
    
    # Group by card ID
    cards_to_investigate = {}
    for test_name in failing_tests:
        card_id = extract_card_id_from_test(test_name, qa_data_map)
        if card_id:
            if card_id not in cards_to_investigate:
                cards_to_investigate[card_id] = []
            cards_to_investigate[card_id].append(test_name)
    
    print(f"Found {len(cards_to_investigate)} unique card IDs to investigate")
    
    # Save to JSON
    output_path = Path("tools/ability_extraction/cargo_failures.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "failing_tests": failing_tests,
            "cards_to_investigate": cards_to_investigate
        }, f, indent=2)
    
    print(f"Saved to {output_path}")
    
    # Print summary
    for card_id, test_names in sorted(cards_to_investigate.items(), key=lambda x: (str(x[0]), x[0] if isinstance(x[0], int) else 0)):
        print(f"Card {card_id}: {len(test_names)} failing tests")
        for test_name in test_names[:3]:  # Show first 3
            print(f"  - {test_name}")
        if len(test_names) > 3:
            print(f"  ... and {len(test_names) - 3} more")

if __name__ == "__main__":
    main()
