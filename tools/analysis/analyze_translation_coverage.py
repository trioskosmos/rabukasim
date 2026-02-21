import json

# Supported opcodes derived from ability_translator.js (Translations.en.opcodes)
SUPPORTED_OPCODES = {
    # Flow
    1,
    2,
    3,
    # Effects
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50,
    51,
    52,
    53,
    57,
    58,
    60,
    61,
    62,
    63,
    64,
    65,
    66,
    67,
    68,
    69,
    70,
    71,
    72,
    73,
    74,
    75,
    76,
    77,
    80,
    81,
    82,
    83,
    90,
    99,
    # Conditions
    200,
    201,
    202,
    203,
    204,
    205,
    206,
    207,
    208,
    209,
    210,
    211,
    212,
    213,
    214,
    215,
    216,
    217,
    218,
    219,
    220,
    221,
    222,
    223,
    224,
    225,
    226,
    227,
    228,
    229,
    230,
    231,
    232,
    233,
    234,
}

# Values from EffectType in logic.rs/opcodes.py that map to the standard set.
# ability_translator.js uses a custom mapping in EffectType const.
# Let's use the strings from the JS file to match against raw text if needed,
# but for bytecode we need to match integer values.

# Re-mapping JS EffectType to Integers used in bytecode (which usually match opcodes.py)
# Based on ability_translator.js:
# DRAW: 0, ADD_BLADES: 1, ...
# These match opcodes.py generally.
# Missing from JS list but likely in bytecode:
# GRANT_ABILITY = 60 (Not in JS)
# INCREASE_COST = 70 (Not in JS)
# ...


def load_cards():
    try:
        # Check compiled data for bytecode analysis
        path = "engine/data/cards_compiled.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {path} not found.")
        return []


def analyze_coverage():
    data = load_cards()
    if not data:
        return

    # cards_compiled.json has 'member_db' and 'live_db'
    cards = []
    if "member_db" in data:
        cards.extend(data["member_db"].values())
    if "live_db" in data:
        cards.extend(data["live_db"].values())

    total_cards = len(cards)
    cards_with_abilities = 0
    fully_covered_friendly = 0
    partially_covered = 0
    unsupported_opcodes = {}

    print(f"Total Cards in DB (Member + Live): {total_cards}")

    for card in cards:
        current_abilities = card.get("abilities", [])

        # In compiled data, abilities should be a list of objects with 'bytecode' and 'raw_text'
        if current_abilities:
            cards_with_abilities += 1
            all_ops_supported = True

            for ab in current_abilities:
                if "bytecode" in ab and ab["bytecode"]:
                    bc = ab["bytecode"]
                    i = 0
                    while i + 3 < len(bc):
                        op = bc[i]
                        base_op = op - 1000 if op >= 1000 else op
                        if base_op not in SUPPORTED_OPCODES:
                            all_ops_supported = False
                            unsupported_opcodes[op] = unsupported_opcodes.get(op, 0) + 1
                        i += 4

            if all_ops_supported:
                fully_covered_friendly += 1
            else:
                partially_covered += 1

    print(f"Cards with Compiled Abilities: {cards_with_abilities}")
    if cards_with_abilities > 0:
        print(
            f"Fully Covered by Friendly Text: {fully_covered_friendly} ({fully_covered_friendly / cards_with_abilities * 100:.1f}%)"
        )
        print(f"Partially Covered: {partially_covered}")

    print("\nMost Common Unsupported Opcodes:")
    sorted_unsupported = sorted(unsupported_opcodes.items(), key=lambda x: x[1], reverse=True)
    for op, count in sorted_unsupported[:10]:
        print(f"Opcode {op}: {count} cards")


if __name__ == "__main__":
    analyze_coverage()
