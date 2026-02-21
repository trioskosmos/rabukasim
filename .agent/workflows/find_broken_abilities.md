---
description: Find broken card abilities and AI/User visibility gaps
---

This workflow runs the `ability_validator.py` tool to detect:
1. **Missing Actions**: Abilities that should be activated but aren't available.
2. **Parity Gaps**: Discrepancies between what the AI sees and what the User sees in the UI.
3. **Crashes/Hangs**: Abilities that break the engine or cause infinite loops.

### Steps

1. **Run the full validation suite**
// turbo
```bash
uv run python tools/ability_validator.py
```

2. **Run on a specific card subset** (optional)
```bash
uv run python tools/ability_validator.py --filter "BP01"
```

3. **Check the report**
The script will output a report to `reports/ability_validation_YYYYMMDD_HHMMSS.json`.
Look for `parity_gaps` to find issues where the user cannot see actions that the AI can.
