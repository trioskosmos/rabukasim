import os
import re

# Map of string literals to enum variants
CHOICE_MAP = {
    '"OPTIONAL"': "crate::core::enums::ChoiceType::Optional",
    '"PAY_ENERGY"': "crate::core::enums::ChoiceType::PayEnergy",
    '"REVEAL_HAND"': "crate::core::enums::ChoiceType::RevealHand",
    '"SELECT_DISCARD"': "crate::core::enums::ChoiceType::SelectDiscard",
    '"SELECT_SWAP_SOURCE"': "crate::core::enums::ChoiceType::SelectSwapSource",
    '"SELECT_STAGE"': "crate::core::enums::ChoiceType::SelectStage",
    '"SELECT_STAGE_EMPTY"': "crate::core::enums::ChoiceType::SelectStageEmpty",
    '"SELECT_LIVE_SLOT"': "crate::core::enums::ChoiceType::SelectLiveSlot",
    '"SELECT_SWAP_TARGET"': "crate::core::enums::ChoiceType::SelectSwapTarget",
    '"SELECT_MEMBER"': "crate::core::enums::ChoiceType::SelectMember",
    '"SELECT_DISCARD_PLAY"': "crate::core::enums::ChoiceType::SelectDiscardPlay",
    '"SELECT_HAND_DISCARD"': "crate::core::enums::ChoiceType::SelectHandDiscard",
    '"COLOR_SELECT"': "crate::core::enums::ChoiceType::ColorSelect",
    '"SELECT_MODE"': "crate::core::enums::ChoiceType::SelectMode",
    '"OPPONENT_CHOOSE"': "crate::core::enums::ChoiceType::OpponentChoose",
    '"SELECT_CARDS_ORDER"': "crate::core::enums::ChoiceType::SelectCardsOrder",
    '"TAP_O"': "crate::core::enums::ChoiceType::TapO",
    '"LOOK_AND_CHOOSE"': "crate::core::enums::ChoiceType::LookAndChoose",
    '"SELECT_CARDS"': "crate::core::enums::ChoiceType::SelectCards",
    '"SELECT_PLAYER"': "crate::core::enums::ChoiceType::SelectPlayer",
    '"SELECT_LIVE"': "crate::core::enums::ChoiceType::SelectLive",
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original_content = content

    # Replace straight string matches
    for k, v in CHOICE_MAP.items():
        # Avoid replacing within macros like format! if it expects a string.
        # But for assignment/arguments it's fine.
        # Let's use a regex to replace the string if it's passed as an argument
        # or used in equality.
        
        # equality check
        content = re.sub(r'==\s*' + k, f'== {v}', content)
        content = re.sub(k + r'\s*==', f'{v} ==', content)
        content = re.sub(r'!=\s*' + k, f'!= {v}', content)
        content = re.sub(k + r'\s*!=', f'{v} !=', content)

        # assignments
        content = re.sub(r'choice_type:\s*' + k + r'\.to_string\(\)', f'choice_type: {v}', content)
        content = re.sub(r'choice_type:\s*' + k, f'choice_type: {v}', content)

        # arguments in suspend_interaction
        # it might look like: `\n            "SELECT_MEMBER",\n`
        content = re.sub(r'(suspend_interaction\([^)]*?)' + k + r'([,;)])', r'\1' + v + r'\2', content, flags=re.DOTALL)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

def main():
    directory = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src"
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".rs"):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
