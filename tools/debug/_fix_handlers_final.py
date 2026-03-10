def process_alphazero():
    path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\core\alphazero_evaluator.rs"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if "use crate::core::alphazero_encoding::AlphaZeroEncoding;" not in content:
        content = content.replace(
            "use crate::core::logic::{CardDatabase, GameState};",
            "use crate::core::logic::{CardDatabase, GameState};\nuse crate::core::alphazero_encoding::AlphaZeroEncoding;",
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            print("Fixed alphazero_evaluator.rs")


def process_handlers():
    path = (
        r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\core\logic\interpreter\handlers.rs"
    )
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Simple string replacements
    replacements = {
        '"ORDER_DECK"': "crate::core::enums::ChoiceType::OrderDeck",
        '"SELECT_HAND_PLAY"': "crate::core::enums::ChoiceType::SelectHandPlay",
        '"TAP_M_SELECT"': "crate::core::enums::ChoiceType::TapMSelect",
        '"MOVE_MEMBER_DEST"': "crate::core::enums::ChoiceType::MoveMemberDest",
        '"UNKNOWN"': "crate::core::enums::ChoiceType::None",
        '"RECOV_L"': "crate::core::enums::ChoiceType::RecovL",
        '"RECOV_M"': "crate::core::enums::ChoiceType::RecovM",
    }

    for k, v in replacements.items():
        content = content.replace(k, v)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        print("Fixed handlers.rs strings")


def main():
    process_alphazero()
    process_handlers()


if __name__ == "__main__":
    main()
