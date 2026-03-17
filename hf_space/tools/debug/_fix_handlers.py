import re

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
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Just replace all occurrences of these exact string literals in handlers.rs with the ChoiceType variant
    # They are only used for choice types anyway.
    for k, v in CHOICE_MAP.items():
        # Only replace if not immediately followed by .to_string() or similar,
        # but honestly we can just replace all of them.
        content = re.sub(r"(?<!\w)" + k + r"(?!\w)", v, content)

    # We also need to find any choice_type.to_string() leftovers, though they might not exist here.
    content = content.replace("choice_type.to_string()", "choice_type")

    # Fix any println! string formatting if choice_type is now an enum
    # We can change {} to {:?} for choice_type printing.
    # We know choice_type is often passed to suspend_interaction as a variable.

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


process_file(
    r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\core\logic\interpreter\handlers.rs"
)
