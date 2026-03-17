import json
import re


def load_translator_keys():
    # Heuristic parsing of JS file to get keys
    path = "frontend/web_ui/js/ability_translator.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract keys from Translations object
    # This is rough but should catch most literal keys string keys
    # We look for "KEY": "Value" or [EffectType.KEY]: "Value"

    # 1. Standard string keys: "DISCARD_HAND":
    string_keys = re.findall(r'"([A-Z_]+)":\s*"', content)

    # 2. EffectType keys: [EffectType.DRAW]:
    effect_type_keys = re.findall(r"\[EffectType\.([A-Z_]+)\]:", content)

    return set(string_keys + effect_type_keys)


def get_used_keywords():
    path = "engine/data/cards_compiled.json"
    keywords = set()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Data file not found")
        return keywords

    cards = []
    if "member_db" in data:
        cards.extend(data["member_db"].values())
    if "live_db" in data:
        cards.extend(data["live_db"].values())

    # Regex to find keywords in COST/EFFECT lines
    # e.g. "REMOVE_SELF", "DRAW(1)", "CHECK_COUNT_STAGE"
    # We want "REMOVE_SELF", "DRAW", "CHECK_COUNT_STAGE"

    # Matches A_B at start of line (after prefix) or after ;
    token_pattern = re.compile(r"(?:^|;\s*|\s+)([A-Z_]{2,})(?:$|[(\s])")

    for card in cards:
        if "abilities" not in card:
            continue
        for ab in card["abilities"]:
            raw = ab.get("raw_text", "")
            for line in raw.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # Remove prefixes
                cleaned = re.sub(r"^(TRIGGER|COST|EFFECT|CONDITION):\s*", "", line)

                # Check tokens
                # We split by ; to handle multiple effects
                parts = cleaned.split(";")
                for part in parts:
                    part = part.strip()
                    # Extract the leading keyword
                    match = re.search(r"^([A-Z_]+)", part)
                    if match:
                        kw = match.group(1)
                        # Filter out common parameter words if they look like keywords?
                        # No, parser keywords are usually distinct.
                        if kw not in ["IF", "ELSE", "THEN", "AND", "OR", "NOT"]:  # Basic exclusions if needed
                            keywords.add(kw)
    return keywords


def main():
    translator_keys = load_translator_keys()
    # Add manual exclusions or implicit keys if any
    translator_keys.add("TRIGGER")
    translator_keys.add("COST")
    translator_keys.add("EFFECT")
    translator_keys.add("CONDITION")

    used_keywords = get_used_keywords()

    missing = used_keywords - translator_keys

    print(f"Found {len(used_keywords)} unique keywords in data.")
    print(f"Found {len(translator_keys)} keys in translator.")

    if missing:
        print("\nMISSING TRANSLATIONS:")
        for k in sorted(missing):
            print(f"- {k}")
    else:
        print("\nAll data keywords appear to be covered.")


if __name__ == "__main__":
    main()
