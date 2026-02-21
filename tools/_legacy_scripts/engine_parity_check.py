import os
import re
import sys

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

PYTHON_OPCODES = os.path.join(PROJECT_ROOT, "engine/models/opcodes.py")
RUST_INTERPRETER = os.path.join(PROJECT_ROOT, "engine_rust_src/src/core/interpreter.rs")
RUST_ENUMS = os.path.join(PROJECT_ROOT, "engine_rust_src/src/core/enums.rs")


def get_python_opcodes():
    opcodes = {}
    if not os.path.exists(PYTHON_OPCODES):
        return opcodes
    with open(PYTHON_OPCODES, "r", encoding="utf-8") as f:
        for line in f:
            # Match assignments like DRAW = 0
            match = re.match(r"^([A-Z0-9_]+)\s*=\s*(\d+)", line.strip())
            if match:
                opcodes[match.group(1)] = int(match.group(2))
    return opcodes


def get_rust_implemented():
    implemented = set()
    paths = [RUST_INTERPRETER, os.path.join(PROJECT_ROOT, "engine_rust_src/src/core/logic.rs")]
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            # Look for case matches like "O_DRAW =>" or "C_TR1 =>" or "ConditionType::AreaCheck =>"
            matches = re.findall(r"([OC]_[A-Z0-9_]+)\s*=>", content)
            implemented.update(matches)

            # Also check for ConditionType variants
            cond_matches = re.findall(r"ConditionType::([A-Za-z0-9_]+)\s*=>", content)
            for cm in cond_matches:
                implemented.add(f"CT_{cm}")
    return implemented


def main():
    py_ops = get_python_opcodes()
    rust_impl = get_rust_implemented()

    print("=" * 60)
    print("ENGINE PARITY CHECK (Python -> Rust)")
    print("=" * 60)
    print(f"Found {len(py_ops)} Python opcodes.")
    print(
        f"Found {len([r for r in rust_impl if r.startswith('O_') or r.startswith('C_')])} Rust bytecode implementations."
    )

    gaps = []

    # Common mappings (heuristics for names that don't match exactly)
    ALIASES = {
        "CHECK_TURN_1": "C_TR1",
        "CHECK_COUNT_STAGE": "C_STG",
        "CHECK_COUNT_HAND": "C_HND",
        "CHECK_COUNT_ENERGY": "C_ENR",
        "CHECK_COUNT_SUCCESS_LIVE": "C_SCS_LIV",
        "CHECK_COUNT_DISCARD": "C_DSR",
        "CHECK_IS_CENTER": "C_CTR",
        "CHECK_AREA_CHECK": "C_AREA_CHK",
        "CHECK_LIFE_LEAD": "C_LLD",
        "CHECK_HAS_MEMBER": "C_HAS_MEMBER",
        "CHECK_HAS_COLOR": "C_CLR",
        "CHECK_COUNT_GROUP": "C_GRP",
        "CHECK_COST_CHECK": "C_CMP",  # Often mapped to compare
        "CHECK_GROUP_FILTER": "C_GRP_FLT",
        "CHECK_MODAL_ANSWER": "C_MODAL_ANSWER",
        "CHECK_HAND_HAS_NO_LIVE": "C_HND_NO_LIVE",
        "CHECK_SCORE_COMPARE": "C_CMP",
        "CHECK_COUNT_HEARTS": "C_HRT",
        "CHECK_COUNT_BLADES": "C_BLD",
        "CHECK_TYPE_CHECK": "C_TYPE_CHECK",
        "CHECK_IS_IN_DISCARD": "C_IS_IN_DISCARD",
        "CHECK_AREA_CHECK": "C_AREA_CHK",
        "ADD_BLADES": "O_BLADES",
        "ADD_HEARTS": "O_HEARTS",
        "RECOVER_LIVE": "O_RECOV_L",
        "BOOST_SCORE": "O_BOOST",
        "RECOVER_MEMBER": "O_RECOV_M",
        "ENERGY_CHARGE": "O_CHARGE",
        "FORMATION_CHANGE": "O_FORMATION",
        "NEGATE_EFFECT": "O_NEGATE",
        "TAP_OPPONENT": "O_TAP_O",
        "REVEAL_CARDS": "O_REVEAL",
        "ADD_TO_HAND": "O_ADD_H",
        "BUFF_POWER": "O_BUFF",
        "FLAVOR_ACTION": "O_FLAVOR",
        "BATON_TOUCH_MOD": "O_BATON_MOD",
        "REDUCE_YELL_COUNT": "O_REDUCE_YELL_COUNT",
    }

    for name in py_ops:
        rust_name = ALIASES.get(name)
        if name.startswith("CHECK_"):
            if not rust_name:
                rust_name = f"C_{name.replace('CHECK_', '')}"
            # Check high-level ConditionType as well
            ct_name = f"CT_{name.replace('CHECK_', '').replace('_', '')}"
            # Fuzzy match CT names
            found_ct = any(
                ru.lower().replace("_", "") == ct_name.lower().replace("_", "")
                for ru in rust_impl
                if ru.startswith("CT_")
            )
            if rust_name not in rust_impl and not found_ct:
                gaps.append((name, f"{rust_name} or ConditionType member"))
        else:
            if not rust_name:
                rust_name = f"O_{name}"
            if rust_name not in rust_impl:
                gaps.append((name, rust_name))

    if gaps:
        print(f"\n[WARNING] {len(gaps)} Potential Parity Gaps Found:")
        for py, ru in gaps:
            print(f"  - {py.ljust(25)} -> Expected Rust: {ru}")
        print("\nRecommendation: Audit engine_rust_src/src/core/interpreter.rs for these opcodes.")
    else:
        print("\n[SUCCESS] All Python opcodes appear to have Rust implementations!")


if __name__ == "__main__":
    main()
