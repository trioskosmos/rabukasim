import json

SUPPORTED_OPCODES = {
    1,
    2,
    3,
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
    81,
    82,
    99,
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
}


def find_missing():
    try:
        with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            data = json.load(f)

    cards = []
    if "member_db" in data:
        cards.extend(data["member_db"].values())
    if "live_db" in data:
        cards.extend(data["live_db"].values())

    missing = {}
    for card in cards:
        for ab in card.get("abilities", []):
            bc = ab.get("bytecode", [])
            for k in range(0, len(bc), 4):
                op = bc[k]
                if op not in SUPPORTED_OPCODES:
                    missing[op] = missing.get(op, 0) + 1

    print("MISSING OPCODES REPORT")
    print("----------------------")
    for op in sorted(missing.keys()):
        base = op - 1000 if op >= 1000 else op
        print(f"Opcode {op} (Base: {base}): {missing[op]} instances")


if __name__ == "__main__":
    find_missing()
