import re

# Since we don't have the cards json, we will infer from the opcodes.py and fast_logic.py
# But we can try to look for the file in other locations or just assume a standard set based on opcodes.

# Let's check which opcodes are implemented in fast_logic.py
FAST_LOGIC_PATH = "engine/game/fast_logic.py"
OPCODES_PATH = "engine/models/opcodes.py"


def analyze_gap():
    # 1. Get All Opcodes
    all_opcodes = {}
    with open(OPCODES_PATH, "r") as f:
        lines = f.readlines()
        for line in lines:
            m = re.match(r"\s+([A-Z_]+)\s*=\s*(\d+)", line)
            if m:
                name, val = m.groups()
                all_opcodes[name] = int(val)

    # 2. Get Implemented Opcodes
    implemented = set()
    with open(FAST_LOGIC_PATH, "r") as f:
        content = f.read()
        # Look for "opcode == Opcode.NAME"
        matches = re.findall(r"opcode == Opcode\.([A-Z_]+)", content)
        implemented.update(matches)

    # 3. Report
    print(f"Total Opcodes Defined: {len(all_opcodes)}")
    print(f"Implemented in VM:   {len(implemented)}")
    print("-" * 30)

    missing = [name for name in all_opcodes.keys() if name not in implemented and name != "NOP"]
    print("MISSING OPCODES:")
    for m in missing[:20]:  # Show top 20
        print(f" - {m}")
    if len(missing) > 20:
        print(f"... and {len(missing) - 20} more.")

    # 4. Impact Assessment
    # Common missing ones usually involved in logic:
    critical_missing = ["SELECT_MODE", "SET_TARGET_MEMBER_SELECT", "TRIGGER_REMOTE", "CHECK_HAS_KEYWORD"]
    print("-" * 30)
    print("CRITICAL MISSING (Estimation):")
    for c in critical_missing:
        status = "MISSING" if c in missing else "OK"
        print(f" {c}: {status}")


if __name__ == "__main__":
    analyze_gap()
