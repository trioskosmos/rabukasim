import os

CHOICE_VARIANTS = [
    "Optional",
    "PayEnergy",
    "RevealHand",
    "SelectDiscard",
    "SelectSwapSource",
    "SelectStage",
    "SelectStageEmpty",
    "SelectLiveSlot",
    "SelectSwapTarget",
    "SelectMember",
    "SelectDiscardPlay",
    "SelectHandDiscard",
    "ColorSelect",
    "SelectMode",
    "OpponentChoose",
    "SelectCardsOrder",
    "TapO",
    "LookAndChoose",
    "SelectCards",
    "SelectPlayer",
    "SelectLive",
    "OrderDeck",
    "SelectHandPlay",
    "TapMSelect",
    "MoveMemberDest",
    "RecovL",
    "RecovM",
]


def to_snake_caps(s):
    res = ""
    for i, c in enumerate(s):
        if c.isupper() and i > 0:
            res += "_"
        res += c.upper()
    return res


CHOICE_MAP = {f'"{to_snake_caps(v)}"': f"ChoiceType::{v}" for v in CHOICE_VARIANTS}
CHOICE_MAP['"NONE"'] = "ChoiceType::None"
CHOICE_MAP['"UNKNOWN"'] = "ChoiceType::None"


def process_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return False

    orig = content

    # 0. Handle Imports
    if (
        "ChoiceType" in content
        and "use crate::core::enums::ChoiceType" not in content
        and "use crate::core::logic::*" not in content
    ):
        # Add import after other crate::core imports
        if "use crate::core::logic::" in content:
            content = content.replace("use crate::core::logic::{", "use crate::core::logic::{ChoiceType, ")
        else:
            content = "use crate::core::enums::ChoiceType;\n" + content

    # 1. Replace string literals with ChoiceType::Variant
    for s_val, enum_val in CHOICE_MAP.items():
        content = content.replace(s_val, enum_val)

    # 2. Fix len() issues
    content = content.replace(".choice_type.len()", ".choice_type.as_str().len()")

    # 3. Fix specific reference issue
    content = content.replace(
        "let choice_type = &state.interaction_stack.last().unwrap().choice_type;",
        "let choice_type = state.interaction_stack.last().unwrap().choice_type;",
    )

    # Handle the specific comparison in opcode_coverage_gap_2.rs:
    # if choice_type == ChoiceType::Optional (when choice_type is &ChoiceType)
    # Actually if I fix the let binding above, I don't need this for many cases.
    # But let's look for `*choice_type` or just make sure choice_type is not a ref.

    # 4. Fix opcode_coverage_gap_2.rs specifically if missed
    if "opcode_coverage_gap_2.rs" in filepath:
        content = content.replace(
            "let choice_type = &state.interaction_stack.last().unwrap().choice_type;",
            "let choice_type = state.interaction_stack.last().unwrap().choice_type;",
        )

    if content != orig:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    src_dir = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src"
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".rs"):
                if process_file(os.path.join(root, file)):
                    print(f"Fixed {file}")


if __name__ == "__main__":
    main()
