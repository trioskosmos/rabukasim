import json

targets = [
    "PL!N-bp1-003-R＋", "PL!N-bp1-003-P＋", "PL!N-bp1-003-SEC",
    "PL!N-sd1-001-SD", "PL!N-sd1-009-SD",
    "PL!HS-bp1-003-R＋", "PL!HS-bp1-003-P＋", "PL!HS-bp1-003-SEC",
    "PL!N-pb1-003-R", "PL!N-pb1-003-P＋",
    "PL!N-bp1-012-P＋", "PL!N-bp1-012-SEC",
    "PL!N-bp1-018-R＋", "PL!N-bp1-018-P＋",
    "PL!SP-bp1-010-R"
]

with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        for t in targets:
            if f'"{t}"' in line:
                print(f"{t}: {i+1}")
