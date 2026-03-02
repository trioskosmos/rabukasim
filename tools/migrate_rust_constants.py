import os
import re

REPLACEMENTS = {
    r"\bO_RECOV_L\b": "O_RECOVER_LIVE",
    r"\bO_RECOV_M\b": "O_RECOVER_MEMBER",
    r"\bO_TAP_O\b": "O_TAP_OPPONENT",
    r"\bO_TAP_M\b": "O_TAP_MEMBER",
    r"\bO_FORMATION\b": "O_FORMATION_CHANGE",
    r"\bO_NEGATE\b": "O_NEGATE_EFFECT",
    r"\bO_CHARGE\b": "O_ENERGY_CHARGE",
    r"\bO_BOOST\b": "O_BOOST_SCORE",
    r"\bO_BUFF\b": "O_BUFF_POWER",
    r"\bO_BLADES\b": "O_ADD_BLADES",
    r"\bO_HEARTS\b": "O_ADD_HEARTS",
    r"\bO_REVEAL\b": "O_REVEAL_CARDS",
    r"\bO_ADD_H\b": "O_ADD_TO_HAND",
    r"\bO_BATON_MOD\b": "O_BATON_TOUCH_MOD",
    r"\bC_TR1\b": "C_TURN_1",
    r"\bC_HAS_MEMBER\b": "C_HAS_MEMBER",  # No change
    r"\bC_CLR\b": "C_HAS_COLOR",
    r"\bC_STG\b": "C_COUNT_STAGE",
    r"\bC_HND\b": "C_COUNT_HAND",
    r"\bC_DSR\b": "C_COUNT_DISCARD",
    r"\bC_CTR\b": "C_IS_CENTER",
    r"\bC_LLD\b": "C_LIFE_LEAD",
    r"\bC_GRP\b": "C_COUNT_GROUP",
    r"\bC_GRP_FLT\b": "C_GROUP_FILTER",
    r"\bC_OPH\b": "C_OPPONENT_HAS",
    r"\bC_SLF_GRP\b": "C_SELF_IS_GROUP",
    r"\bC_ENR\b": "C_COUNT_ENERGY",
    r"\bC_HAS_LIVE\b": "C_HAS_LIVE_CARD",
    r"\bC_COST_CHK\b": "C_COST_CHECK",
    r"\bC_RARITY_CHK\b": "C_RARITY_CHECK",
    r"\bC_HND_NO_LIVE\b": "C_HAND_HAS_NO_LIVE",
    r"\bC_SCS_LIV\b": "C_COUNT_SUCCESS_LIVE",
    r"\bC_OPP_HND_DIF\b": "C_OPPONENT_HAND_DIFF",
    r"\bC_CMP\b": "C_SCORE_COMPARE",
    r"\bC_HRT\b": "C_COUNT_HEARTS",
    r"\bC_BLD\b": "C_COUNT_BLADES",
    r"\bC_OPP_ENR_DIF\b": "C_OPPONENT_ENERGY_DIFF",
    r"\bC_HAS_KWD\b": "C_HAS_KEYWORD",
    r"\bC_DK_REFR\b": "C_DECK_REFRESHED",
    r"\bC_LIV_ZN\b": "C_COUNT_LIVE_ZONE",
    r"\bO_PREVENT_SET_TO_SUCCESS_PILE\b": "O_PREVENT_SET_TO_SUCCESS_PILE",  # Ensure no mangling
}


def migrate():
    root_dir = "engine_rust_src/src"
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".rs"):
                # Skip generated files
                if file == "generated_constants.rs":
                    continue

                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                new_content = content
                for pattern, replacement in REPLACEMENTS.items():
                    new_content = re.sub(pattern, replacement, new_content)

                if new_content != content:
                    print(f"Migrating {path}...")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)


if __name__ == "__main__":
    migrate()
