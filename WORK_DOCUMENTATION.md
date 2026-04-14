# Variable Decomposition Coverage

## Goal
Reach 100% coverage for Japanese ability-text decomposition using the DSL patterns in `tools/extract_abilities_to_template.py`.

## Current Status
- Average coverage: 94.0%
- Abilities with < 50% coverage: 0
- Low-coverage outliers still exist and need pattern-specific fixes

## What Matters
- Keep the clause matcher accurate
- Add or refine real semantic patterns
- Avoid fake wins or placeholder shortcuts
- Verify every change against the data

## Core Files
- `tools/extract_abilities_to_template.py` - Main DSL pattern matcher and extractor
- `data/abilities_extracted_simple.json` - Coverage dataset used by `check_cov.py`
- `low_abilities.txt` - Current low-coverage examples

## Useful Checks
- `python check_cov.py` - Prints the current average coverage
- `python show_coverage_stats.py` - Shows the distribution
- `python get_lowest_abilities.py` - Shows the worst coverage examples
- `python show_below_70.py` - Lists all abilities below 70%

## Working Rule
When coverage is below 100%, the right fix is a real pattern that matches the missing text, not a workaround. Prefer clean, reusable clause patterns over ad hoc special cases unless the text truly needs one.

## Next Steps
1. Run `get_lowest_abilities.py`
2. Inspect the exact unmatched text
3. Add the smallest correct pattern that covers it
4. Re-run `tools/extract_abilities_to_template.py`
5. Re-check coverage with `check_cov.py`
6. Repeat until coverage reaches 100%

