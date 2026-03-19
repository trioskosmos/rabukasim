import json
import re
from collections import defaultdict
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from compiler.aliases import (
    CONDITION_SEMANTIC_SPECIAL_CASES,
    CONDITION_TRUE_ALIASES,
    EFFECT_GRAMMAR_CONVENIENCES,
    EFFECT_SEMANTIC_SPECIAL_CASES,
    EFFECT_TRUE_ALIASES,
    IGNORED_CONDITIONS,
    KEYWORD_CONDITIONS,
    TRIGGER_ALIASES,
)


def analyze():
    # Load metadata
    with open("data/metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    parser_trigger_aliases = set(TRIGGER_ALIASES)
    parser_effect_aliases = set(EFFECT_TRUE_ALIASES) | set(EFFECT_GRAMMAR_CONVENIENCES) | set(EFFECT_SEMANTIC_SPECIAL_CASES)
    parser_condition_aliases = (
        set(CONDITION_TRUE_ALIASES)
        | set(CONDITION_SEMANTIC_SPECIAL_CASES)
        | set(KEYWORD_CONDITIONS)
        | set(IGNORED_CONDITIONS)
    )
    parser_ignored_conds = set(IGNORED_CONDITIONS)

    # Load consolidated abilities
    with open("data/consolidated_abilities.json", "r", encoding="utf-8") as f:
        consolidated = json.load(f)

    # Load cards compiled to get counts
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        compiled = json.load(f)

    all_members = compiled.get("member_db", {})

    # Map pseudocode to card count
    pseudo_to_count = defaultdict(int)
    pseudo_to_cards = defaultdict(list)

    for mid, mdata in all_members.items():
        for ability in mdata.get("abilities", []):
            p = ability.get("pseudocode", "")
            if p:
                pseudo_to_count[p] += 1
                pseudo_to_cards[p].append(mdata.get("card_no", mid))

    # Extract keywords from pseudocode
    effects = defaultdict(int)
    conditions = defaultdict(int)
    triggers = defaultdict(int)
    costs = defaultdict(int)
    targets = defaultdict(int)

    keyword_usage_cards = {
        "EFFECT": defaultdict(set),
        "CONDITION": defaultdict(set),
        "TRIGGER": defaultdict(set),
        "COST": defaultdict(set),
        "TARGET": defaultdict(set),
    }

    for pseudo, count in pseudo_to_count.items():
        cards = pseudo_to_cards[pseudo]
        lines = pseudo.split("\n")
        for line in lines:
            line = line.strip()

            # Extract Effects
            if "EFFECT:" in line:
                match = re.search(r"EFFECT:\s*([\w|]+)", line)
                if match:
                    for e in match.group(1).split("|"):
                        effects[e] += count
                        for c in cards:
                            keyword_usage_cards["EFFECT"][e].add(c)

            # Extract Conditions
            if "CONDITION:" in line:
                match = re.search(r"CONDITION:\s*([\w|]+)", line)
                if match:
                    for c_kw in match.group(1).split("|"):
                        conditions[c_kw] += count
                        for c in cards:
                            keyword_usage_cards["CONDITION"][c_kw].add(c)

            # Extract Triggers
            if "TRIGGER:" in line:
                match = re.search(r"TRIGGER:\s*([\w|]+)", line)
                if match:
                    for t in match.group(1).split("|"):
                        triggers[t] += count
                        for c in cards:
                            keyword_usage_cards["TRIGGER"][t].add(c)

            # Extract Costs
            if "COST:" in line:
                match = re.search(r"COST:\s*([\w|]+)", line)
                if match:
                    for cost_kw in match.group(1).split("|"):
                        costs[cost_kw] += count
                        for c in cards:
                            keyword_usage_cards["COST"][cost_kw].add(c)

            # Extract Targets (-> KEYWORD)
            targets_match = re.findall(r"->\s*([\w|]+)", line)
            for tm in targets_match:
                for target_kw in tm.split("|"):
                    targets[target_kw] += count
                    for c in cards:
                        keyword_usage_cards["TARGET"][target_kw].add(c)

    # Compare with metadata
    meta_opcodes = set(metadata.get("opcodes", {}).keys())
    meta_conditions = set(metadata.get("conditions", {}).keys())
    meta_triggers = set(metadata.get("triggers", {}).keys())
    meta_costs = set(metadata.get("costs", {}).keys())
    meta_targets = set(metadata.get("targets", {}).keys())

    # Extras that are often handled without opcodes or are meta
    ignored_keywords = {
        "COUNT_VAL",
        "PLAYER",
        "SELF",
        "OPPONENT",
        "VARIABLE",
        "PER_CARD",
        "AND",
        "OR",
        "NOT",
        "TRUE",
        "FALSE",
        "IF",
        "THEN",
        "ELSE",
        "VALUE_GT",
        "VALUE_GE",
        "VALUE_LT",
        "VALUE_LE",
        "VALUE_EQ",
        "VALUE_NE",
    }

    def print_gaps(category, found, meta, parser_aliases, ignore=set()):
        print(f"\n=== {category} GAPS (Not in Metadata AND Not Aliased) ===")
        missing = []
        for kw, count in sorted(found.items(), key=lambda x: -x[1]):
            if kw not in meta and kw not in parser_aliases and kw not in ignore and not kw.isdigit():
                missing.append((kw, count))

        if not missing:
            print("No gaps found.")
        else:
            for kw, count in missing:
                cards = sorted(list(keyword_usage_cards[category][kw]))[:5]
                print(f"{kw:<25} Usage: {count:>3}  Cards: {', '.join(cards)}")

    print_gaps("TRIGGER", triggers, meta_triggers, parser_trigger_aliases)
    print_gaps("EFFECT", effects, meta_opcodes, parser_effect_aliases)
    print_gaps(
        "CONDITION", conditions, meta_conditions, parser_condition_aliases, ignored_keywords.union(parser_ignored_conds)
    )
    print_gaps("COST", costs, meta_costs, set())  # Costs don't have aliases usually
    print_gaps("TARGET", targets, meta_targets, set(), ignored_keywords)


if __name__ == "__main__":
    analyze()
