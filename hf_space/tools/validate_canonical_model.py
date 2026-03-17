from __future__ import annotations

import json
import sys
from pathlib import Path

from compiler.canonical_validator import validate_canonical_model_payload


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_canonical_model.py <path-to-json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    report = validate_canonical_model_payload(data)

    if report.ok:
        print(f"OK: {path}")
        return 0

    print(f"INVALID: {path}")
    for issue in report.issues:
        prefix = f"{issue.path}: " if issue.path else ""
        print(f"- {issue.code}: {prefix}{issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
