---
name: card_id_auditor
description: Use when auditing card IDs, bit-packed encodings, or ID ranges.
---
# Card ID Auditor
## Do
- Validate the numeric range and encoding bits.
- Check for duplicate or conflicting IDs.
- Track manual exceptions explicitly.
## Do not
- Do not assume a value is safe because it loads.
- Do not hide mismatches behind naming aliases.
## Verify
- Compare the ID against the canonical data source.