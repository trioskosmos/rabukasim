import os
import re

RUST_SRC_DIR = r"engine_rust_src/src"
LOGIC_RS = os.path.join(RUST_SRC_DIR, "core/logic.rs")
ENUMS_RS = os.path.join(RUST_SRC_DIR, "core/enums.rs")


def get_opcodes():
    opcodes = set()
    with open(LOGIC_RS, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r"pub const (O_[A-Z0-9_]+):", line)
            if match:
                opcodes.add(match.group(1))
            match_cond = re.search(r"pub const (C_[A-Z0-9_]+):", line)
            if match_cond:
                opcodes.add(match_cond.group(1))
    return opcodes


def get_triggers():
    triggers = set()
    with open(ENUMS_RS, "r", encoding="utf-8") as f:
        in_trigger_enum = False
        for line in f:
            if "pub enum TriggerType" in line:
                in_trigger_enum = True
                continue
            if in_trigger_enum and "}" in line:
                break
            if in_trigger_enum:
                match = re.search(r"^\s+([A-Z][a-zA-Z0-9_]+)\s*=", line)
                if match and match.group(1) != "None":
                    triggers.add(match.group(1))
    return triggers


def check_coverage():
    opcodes = get_opcodes()
    triggers = get_triggers()

    covered_opcodes = set()
    covered_triggers = set()

    for root, dirs, files in os.walk(RUST_SRC_DIR):
        for file in files:
            if file.endswith("_tests.rs") or file == "tests.rs":
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for op in opcodes:
                        if op in content:
                            covered_opcodes.add(op)
                    for trig in triggers:
                        # Check for TriggerType::Variant or just Variant
                        if f"TriggerType::{trig}" in content or f"TriggerType::{trig}" in content:
                            covered_triggers.add(trig)

    missing_opcodes = opcodes - covered_opcodes
    missing_triggers = triggers - covered_triggers

    print(f"Total Opcodes: {len(opcodes)}")
    print(f"Covered Opcodes: {len(covered_opcodes)}")
    print(f"Missing Opcodes: {len(missing_opcodes)}")
    for op in sorted(missing_opcodes):
        print(f" - {op}")

    print("\n" + "=" * 20 + "\n")

    print(f"Total Triggers: {len(triggers)}")
    print(f"Covered Triggers: {len(covered_triggers)}")
    print(f"Missing Triggers: {len(missing_triggers)}")
    for t in sorted(missing_triggers):
        print(f" - {t}")


if __name__ == "__main__":
    check_coverage()
