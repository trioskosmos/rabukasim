---
name: system_operations
description: Use for workspace maintenance, sync, build, deployment, and training helpers.
---
# System Operations
## Do
- Use the provided scripts and entry points.
- Keep sync and build steps explicit.
- Note when a task changes generated artifacts.
## Do not
- Do not edit generated delivery folders directly.
- Do not bypass the published command when it exists.
## Verify
- Run the named command and check the output artifact.