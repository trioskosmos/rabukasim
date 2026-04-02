---
name: rich_rule_log_guide
description: Use when adding or cleaning up rule logs, trace output, or diagnostic markers.
---
# Rich Rule Log Guide
## Do
- Include turn, phase, player, execution ID, and rule label.
- Keep logs short, structured, and searchable.
- Group related lines together.
## Do not
- Do not dump full state on every step.
- Do not log noise that cannot help debug a failure.
## Verify
- Check one trace for context and brevity.