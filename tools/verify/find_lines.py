targets = [
    "PL!HS-PR-001-PR",
    "PL!HS-PR-002-PR",
    "PL!HS-PR-005-PR",
    "PL!HS-bp2-001-R",
    "PL!N-bp1-012-R＋",
    "PL!SP-bp4-019-N",
]

with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        for t in targets:
            if f'"{t}"' in line:
                print(f"{t}: {i + 1}")
