---
description: Unified card lookup and report generator using tools/cf.py.
---

Use this workflow to quickly analyze card data, bytecode, and related tests.

### Usage
Run the following command to see card details, decoded bytecode, and coverage:
```powershell
python tools/cf.py [card_no_or_id]
```

### Options
- `-i`: Interactive mode
- `--json`: Output raw JSON
- `-o [file]`: Generate a markdown report
- `--member [name]`: Filter by member name
- `--group [name]`: Filter by group name

// turbo
1. python tools/cf.py --help
