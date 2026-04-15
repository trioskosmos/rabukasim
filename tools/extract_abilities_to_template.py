#!/usr/bin/env python3


from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SEMANTIC_PLACEHOLDERS = {
    # Numbers and quantities
    "number": "⟦N⟧",
    "count": "⟦CNT⟧",
    "cost": "⟦COST⟧",
    "amount": "⟦AMT⟧",
    # Game entities
    "card_type": "⟦CTYPE⟧",
    "zone": "⟦ZONE⟧",
    "area": "⟦AREA⟧",
    "resource": "⟦RES⟧",
    "group": "⟦GRP⟧",
    "character": "⟦CHAR⟧",
    # Actions and effects
    "action": "⟦ACT⟧",
    "effect": "⟦EFF⟧",
    "condition": "⟦COND⟧",
    "trigger": "⟦TRIG⟧",
    # Locations and targets
    "source": "⟦SRC⟧",
    "destination": "⟦DST⟧",
    "target": "⟦TGT⟧",
    "location": "⟦LOC⟧",

}

# Legacy support
PLACEHOLDER = "⟦X⟧"
SENTINEL = "__PLACEHOLDER_SENTINEL__"

ICON_TOKEN_RE = re.compile(r"\{\{[^{}]+\}\}")
QUOTE_RE = re.compile(r"『([^』]+)』|「([^」]+)」")
TOKEN_RE = re.compile(r"[一-龥ぁ-ゔァ-ヴーA-Za-z0-9・ー]{2,}")
NUMBER_RE = re.compile(
    r"(?:\bN\b|(?<!⟦)\bX\b(?!⟧)|[0-9０-９]+|[一二三四五六七八九十百千万]+)"
    r"(?:枚|人|つ|個|回|色|コスト|以上|以下|未満|まで|以下ある|以上ある)?"
)





def nfkc(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


# Empty pattern lists (to be filled with new patterns)
ABILITY_LEVEL_PATTERNS = []
DSL_PATTERNS = []


def parse_trigger_effect(clause: str) -> list[tuple[str, str]]:
    """Parse a clause into (trigger, effect) pairs.
    Handles slash-separated triggers like {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}.
    Returns list of (trigger, effect) tuples."""
    # Pattern to match trigger icons: {{icon.png|trigger_name}}
    trigger_pattern = re.compile(r'\{\{([^|]+)\|([^}]+)\}\}')
    
    # Find all triggers in the clause
    triggers = []
    for match in trigger_pattern.finditer(clause):
        icon_file = match.group(1)
        trigger_name = match.group(2)
        triggers.append((icon_file, trigger_name, match.start(), match.end()))
    
    if not triggers:
        # No trigger found, return empty effect
        return [("", clause)]
    
    # Check if triggers are slash-separated
    # Look for / between trigger icons
    for i in range(len(triggers) - 1):
        if triggers[i][3] + 1 < len(clause) and clause[triggers[i][3]] == '/':
            # Slash-separated triggers - split into separate trigger-effect pairs
            # Each trigger has the same effect (the text after the last trigger)
            last_trigger_end = triggers[-1][3]
            effect = clause[last_trigger_end:].lstrip('：')
            pairs = []
            for icon_file, trigger_name, _, _ in triggers:
                pairs.append((trigger_name, effect))
            return pairs
    
    # Single trigger or multiple separate clauses
    # Split by trigger boundaries
    pairs = []
    for i, (icon_file, trigger_name, start, end) in enumerate(triggers):
        # Get the effect text after this trigger
        if i < len(triggers) - 1:
            next_trigger_start = triggers[i + 1][2]
            effect = clause[end:next_trigger_start].lstrip('：')
        else:
            effect = clause[end:].lstrip('：')
        pairs.append((trigger_name, effect))
    
    return pairs




DSL_PATTERNS = [
       
        # NOTE: No catchall patterns - coverage should show actual unmatched clauses
        # This allows us to identify gaps in pattern matching and add specific patterns

    ]


def match_dsl_patterns(clauses: list[dict[str, Any]], term_mapping: dict[str, str]) -> dict[str, Any]:
    # Use module-level ability level patterns
    ability_level_patterns = ABILITY_LEVEL_PATTERNS
    dsl_patterns = DSL_PATTERNS
    
    # Load abilities_from_cards.json for ability-level matching
    try:
        abilities_data = json.load(open('data/abilities_from_cards.json', encoding='utf-8'))
        abilities = abilities_data['abilities']
    except:
        abilities = []
    
    matched_clauses = []
    unmatched_clauses = []
    pattern_counts = Counter()
    pattern_variables = {}
    
    # Ability-level matching (preserves full structure)
    matched_abilities = []
    unmatched_abilities = []
    ability_pattern_counts = Counter()
    ability_pattern_variables = {}
    
    for ability in abilities:
        for source in ability['source_ability_texts']:
            jp_text = source['jp']
            ability_matched = False
            
            for pattern in ability_level_patterns:
                match = re.search(pattern["regex"], jp_text, re.MULTILINE | re.DOTALL)
                if match:
                    variables = list(match.groups())
                    # Extract options if present
                    options = []
                    if len(variables) > 0 and '・' in str(variables[-1]):
                        option_text = variables[-1]
                        options = [opt.strip()[1:].strip() for opt in option_text.split('\n') if opt.strip().startswith('・')]
                    
                    matched_abilities.append({
                        "original": jp_text,
                        "pattern_name": pattern["name"],
                        "structure": pattern["structure"],
                        "template": pattern["template"],
                        "matched_text": match.group(0),
                        "variables": variables,
                        "options": options,
                        "trigger": ability.get('trigger', 'UNKNOWN'),
                    })
                    ability_pattern_counts[pattern["name"]] += 1
                    
                    if pattern["name"] not in ability_pattern_variables:
                        ability_pattern_variables[pattern["name"]] = []
                    ability_pattern_variables[pattern["name"]].append(variables)
                    
                    ability_matched = True
                    break
            
            if not ability_matched:
                # Generic ability: represent as trigger + clause pattern sequence
                # Extract trigger from jp_text
                trigger_match = re.search(r'^(\{\{[^}]+\}\})', jp_text)
                if trigger_match:
                    trigger_icon = trigger_match.group(1)
                    effect_text = jp_text[trigger_match.end():].lstrip('：')
                    
                    # Match effect text against clause-level patterns
                    matched_clauses_for_effect = []
                    for clause_pattern in dsl_patterns:
                        clause_match = re.search(clause_pattern["regex"], effect_text)
                        if clause_match:
                            matched_clauses_for_effect.append({
                                "pattern_name": clause_pattern["name"],
                                "template": clause_pattern["template"],
                                "matched_text": clause_match.group(0),
                                "variables": list(clause_match.groups()),
                            })
                    
                    if matched_clauses_for_effect:
                        matched_abilities.append({
                            "original": jp_text,
                            "pattern_name": "trigger_clause_sequence",
                            "structure": "Ability - Trigger + clause pattern sequence",
                            "template": f"{trigger_icon} + " + " + ".join([c["template"] for c in matched_clauses_for_effect]),
                            "matched_text": jp_text,
                            "variables": [trigger_icon] + [v for c in matched_clauses_for_effect for v in c["variables"]],
                            "trigger": ability.get('trigger', 'UNKNOWN'),
                            "clause_patterns": matched_clauses_for_effect,
                        })
                        ability_pattern_counts["trigger_clause_sequence"] += 1
                        if "trigger_clause_sequence" not in ability_pattern_variables:
                            ability_pattern_variables["trigger_clause_sequence"] = []
                        ability_pattern_variables["trigger_clause_sequence"].append([trigger_icon] + [c["pattern_name"] for c in matched_clauses_for_effect])
                    else:
                        unmatched_abilities.append(jp_text)
                else:
                    unmatched_abilities.append(jp_text)
    
    for clause_data in clauses:
        clause = clause_data["clause"]
        # Don't strip icons - they contain semantic information
        matched = False
        
        for pattern in dsl_patterns:
            match = re.search(pattern["regex"], clause)
            if match:
                variables = list(match.groups())
                matched_clauses.append({
                    "original": clause,
                    "pattern_name": pattern["name"],
                    "structure": pattern["structure"],
                    "template": pattern["template"],
                    "matched_text": match.group(0),
                    "variables": variables,
                })
                pattern_counts[pattern["name"]] += 1
                
                if pattern["name"] not in pattern_variables:
                    pattern_variables[pattern["name"]] = []
                pattern_variables[pattern["name"]].append(variables)
                
                matched = True
                break
        
        if not matched:
            unmatched_clauses.append(clause)
    
    return {
        "total_clauses": len(clauses),
        "matched_clauses": len(matched_clauses),
        "unmatched_clauses": len(unmatched_clauses),
        "unique_patterns": len(pattern_counts),
        "pattern_counts": dict(pattern_counts),
        "pattern_variables": pattern_variables,
        "compression_ratio": len(matched_clauses) / len(clauses) if clauses else 0,
        "matched_sample": matched_clauses[:20],
        "unmatched_sample": unmatched_clauses[:20],
        # Ability-level matching results
        "total_abilities": len(abilities) if abilities else 0,
        "matched_abilities": len(matched_abilities),
        "unmatched_abilities": len(unmatched_abilities),
        "unique_ability_patterns": len(ability_pattern_counts),
        "ability_pattern_counts": dict(ability_pattern_counts),
        "ability_pattern_variables": ability_pattern_variables,
        "ability_compression_ratio": len(matched_abilities) / len(abilities) if abilities else 0,
        "matched_ability_sample": matched_abilities[:20],
        "unmatched_ability_sample": unmatched_abilities[:20],
    }


def analyze_simple_terms(clauses: list[dict[str, Any]], term_mapping: dict[str, str]) -> dict[str, Any]:
    """
    Analyze clauses by simple game mechanic terms to identify DSL structures.
    
    DSL APPROACH: Card game ability text is a domain-specific language for game mechanics.
    We identify the "tokens" and "keywords" of this language to understand its syntax.
    
    INFORMATION THEORY GOAL: Represent abilities in as few patterns as possible without losing meaning.
    - Identify which tokens are "variables" (replaceable) vs "operators" (structural)
    - Variables: numbers, card types, groups, zones (high entropy, should be parameters)
    - Operators: actions, conditions, comparisons (low entropy, should be in template)
    - Goal: Maximize pattern reuse while preserving all game mechanics and meaning
    
    Bottom-up approach: Start with simple terms (keywords) to understand the language's
    vocabulary, then identify the grammatical structures (syntax) that combine them.
    
    Returns term frequencies, clause samples for each term, and compressibility analysis.
    """
    
    # Simple game mechanic terms from rules and common ability text
    simple_terms = [
        "スコア",
        "ブレード",
        "ハート",
        "エール",
        "エネルギー",
        "カード",
        "手札",
        "控え室",
        "デッキ",
        "ステージ",
        "ライブ",
        "メンバー",
        "引く",
        "置く",
        "得る",
        "アクティブ",
        "ウェイト",
        "登場",
        "移動",
        "見る",
        "選ぶ",
        "公開",
        "加える",
        "コスト",
        "必要ハート",
    ]
    
    term_clauses = {}
    term_counts = Counter()
    
    for clause_data in clauses:
        clause = clause_data["clause"]
        clause_no_icons = ICON_TOKEN_RE.sub("", clause)
        
        for term in simple_terms:
            if term in clause_no_icons:
                if term not in term_clauses:
                    term_clauses[term] = []
                term_clauses[term].append(clause)
                term_counts[term] += 1
    
    # Analyze placeholder percentage for each term's clauses
    term_placeholder_analysis = {}
    for term, clauses_with_term in term_clauses.items():
        total_chars = 0
        replaced_chars = 0
        
        for clause in clauses_with_term[:50]:  # Sample first 50
            clause_no_icons = ICON_TOKEN_RE.sub("", clause)
            original_len = len(clause_no_icons)
            total_chars += original_len
            
            # Calculate what would become placeholder
            normalized = clause_no_icons
            for en_name, jp_name in term_mapping.items():
                if jp_name in normalized:
                    replaced_chars += len(jp_name)
                    normalized = normalized.replace(jp_name, PLACEHOLDER)
            
            # Count numbers replaced
            number_matches = NUMBER_RE.findall(normalized)
            for num in number_matches:
                replaced_chars += len(num)
            normalized = NUMBER_RE.sub(PLACEHOLDER, normalized)
        
        if total_chars > 0:
            placeholder_pct = replaced_chars / total_chars
        else:
            placeholder_pct = 0
        
        term_placeholder_analysis[term] = {
            "count": len(clauses_with_term),
            "sample_clauses": clauses_with_term[:10],
            "placeholder_percentage": placeholder_pct,
        }
    
    return {
        "total_clauses": len(clauses),
        "terms_analyzed": len(simple_terms),
        "term_counts": dict(term_counts.most_common(30)),
        "term_placeholder_analysis": term_placeholder_analysis,
    }


def extract_effects_from_clauses(clauses: list[dict[str, Any]], term_mapping: dict[str, str]) -> dict[str, Any]:
    """Extract and normalize effects from clauses, separating them from triggers."""
    effects = []
    triggers = []
    
    for clause_data in clauses:
        clause = clause_data["clause"]
        pairs = parse_trigger_effect(clause)
        
        for trigger, effect in pairs:
            # Normalize the effect using the term mapping
            normalized_effect = effect
            for en_name, jp_name in term_mapping.items():
                normalized_effect = normalized_effect.replace(jp_name, PLACEHOLDER)
            
            # Also replace numbers
            normalized_effect = NUMBER_RE.sub(PLACEHOLDER, normalized_effect)
            
            # Also replace icons in the effect
            normalized_effect = ICON_TOKEN_RE.sub(PLACEHOLDER, normalized_effect)
            
            effects.append({
                "trigger": trigger,
                "effect": effect,
                "normalized_effect": normalized_effect,
            })
            triggers.append(trigger)
    
    # Count unique normalized effects
    unique_effects = {}
    for effect_data in effects:
        norm = effect_data["normalized_effect"]
        if norm not in unique_effects:
            unique_effects[norm] = {
                "count": 0,
                "triggers": set(),
                "original_effects": [],
            }
        unique_effects[norm]["count"] += 1
        unique_effects[norm]["triggers"].add(effect_data["trigger"])
        unique_effects[norm]["original_effects"].append(effect_data["effect"])
    
    # Convert sets to lists for JSON serialization
    for norm in unique_effects:
        unique_effects[norm]["triggers"] = list(unique_effects[norm]["triggers"])
    
    # Count triggers
    trigger_counts = Counter(triggers)
    
    return {
        "total_effects": len(effects),
        "unique_effects": len(unique_effects),
        "unique_effects_data": unique_effects,
        "trigger_counts": dict(trigger_counts.most_common(20)),
        "effects_sample": effects[:20],
    }


def load_cards(cards_file: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(cards_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("cards.json must be a top-level object keyed by card id")
    return data


def load_rules(rules_file: Path) -> str:
    return rules_file.read_text(encoding="utf-8")


def group_abilities(cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for card_id, card in cards.items():
        ability_text = card.get("ability")
        if not isinstance(ability_text, str) or not ability_text.strip():
            continue
        entry = grouped.setdefault(
            ability_text,
            {
                "jp": ability_text,
                "ability_index": 0,
                "card_examples": [],
            },
        )
        entry["card_examples"].append(f"{card_id} | {card.get('name', '')} (ab#0)")

    abilities = list(grouped.values())
    abilities.sort(key=lambda item: item["jp"])
    for item in abilities:
        item["card_examples"].sort()
    return abilities


def split_clauses(text: str) -> list[str]:
    current = text.strip()
    clauses: list[str] = []
    buffer: list[str] = []
    paren_depth = 0
    quote_depth = 0

    for ch in current:
        if ch in "（(":
            paren_depth += 1
            buffer.append(ch)
            continue
        if ch in "）)":
            if paren_depth:
                paren_depth -= 1
            buffer.append(ch)
            continue
        if ch in "「『《":
            quote_depth += 1
            buffer.append(ch)
            continue
        if ch in "」』》":
            if quote_depth:
                quote_depth -= 1
            buffer.append(ch)
            continue
        if ch in "。\n" and paren_depth == 0 and quote_depth == 0:
            clause = "".join(buffer).strip()
            if clause:
                clauses.append(clause)
            buffer = []
            continue
        buffer.append(ch)

    tail = "".join(buffer).strip()
    if tail:
        clauses.append(tail)
    return clauses


def all_ability_clauses(cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    clauses: list[dict[str, Any]] = []
    for card_id, card in cards.items():
        ability = card.get("ability")
        if not isinstance(ability, str) or not ability.strip():
            continue
        for clause in split_clauses(ability):
            clauses.append({"card_id": card_id, "clause": clause, "ability": ability})
    return clauses


def token_counter(text: str) -> Counter[str]:
    return Counter(TOKEN_RE.findall(nfkc(text)))


def build_known_terms(cards: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    known: dict[str, set[str]] = {
        "names": set(),
        "units": set(),
        "series": set(),
        "products": set(),
    }
    for card in cards.values():
        for key, bucket in [
            ("name", "names"),
            ("unit", "units"),
            ("series", "series"),
            ("product", "products"),
        ]:
            value = card.get(key)
            if isinstance(value, str) and value.strip():
                known[bucket].add(value.strip())
    return known


def extract_quotes(text: str) -> list[str]:
    spans: list[str] = []
    for match in QUOTE_RE.finditer(text):
        value = match.group(1) or match.group(2)
        if value:
            spans.append(value)
    return spans


def build_candidate_terms(
    clauses: list[dict[str, Any]],
    rules_text: str,
    known: dict[str, set[str]],
    term_data: dict[str, Any],
) -> tuple[dict[str, list[str]], dict[str, Counter[str]]]:
    rules_counts = token_counter(rules_text)
    clause_counts = Counter()
    clause_seen: dict[str, set[int]] = defaultdict(set)
    for idx, row in enumerate(clauses):
        raw = nfkc(row["clause"])
        for token in TOKEN_RE.findall(raw):
            clause_counts[token] += 1
            clause_seen[token].add(idx)

    quoted_counts: Counter[str] = Counter()
    quoted_seen: dict[str, set[int]] = defaultdict(set)
    for idx, row in enumerate(clauses):
        for span in extract_quotes(nfkc(row["clause"])):
            quoted_counts[span] += 1
            quoted_seen[span].add(idx)

    # Use Japanese terms from the mapping (values) instead of hardcoded lists
    term_mapping = term_data["mapping"]
    manual_terms = set(term_mapping.values())
    
    # Also include quoted terms and known terms
    quoted_terms = set(quoted_counts)
    exact_terms = set().union(*known.values())

    all_terms = {
        "exact_terms": sorted(exact_terms, key=len, reverse=True),
        "discovered_terms": sorted(manual_terms, key=len, reverse=True),
        "term_mapping": term_mapping,
        "term_counts": term_data.get("counts", {}),
        "quoted_terms_discovered": term_data.get("quoted_terms", {}),
    }
    counters = {
        "rules_counts": rules_counts,
        "clause_counts": clause_counts,
        "quoted_counts": quoted_counts,
        "clause_seen": clause_seen,
        "quoted_seen": quoted_seen,
        "quoted_terms": quoted_terms,
    }
    return all_terms, counters


def replace_exact_terms(text: str, terms: list[str], counts: Counter[str], seen: dict[str, set[int]], clause_idx: int) -> str:
    result = text
    for term in terms:
        if not term or term not in result:
            continue
        occurrences = result.count(term)
        if occurrences:
            counts[term] += occurrences
            seen[term].add(clause_idx)
            result = result.replace(term, PLACEHOLDER)
    return result


def normalize_clause(
    clause: str,
    clause_idx: int,
    exact_terms: list[str],
    discovered_terms: list[str],
    stats: dict[str, Any],
) -> str:
    text = nfkc(clause)
    raw_text = text

    # Count and replace full icon tokens, not just the inner label.
    for token in ICON_TOKEN_RE.findall(raw_text):
        stats["icons"][token] += 1
        stats["icon_seen"][token].add(clause_idx)
    text = ICON_TOKEN_RE.sub(PLACEHOLDER, text)

    # Capture quoted spans before they are flattened.
    for span in extract_quotes(raw_text):
        stats["quotes"][span] += 1
        stats["quote_seen"][span].add(clause_idx)
    text = QUOTE_RE.sub(PLACEHOLDER, text)

    text = text.replace(PLACEHOLDER, SENTINEL)
    text = replace_exact_terms(text, exact_terms, stats["exact_terms"], stats["exact_seen"], clause_idx)
    text = replace_exact_terms(text, discovered_terms, stats["discovered_terms"], stats["discovered_seen"], clause_idx)

    # Numbers, counts, and icon labels that survived the previous steps.
    number_hits = NUMBER_RE.findall(text)
    for hit in number_hits:
        stats["numbers"][hit] += 1
        stats["number_seen"][hit].add(clause_idx)
    text = NUMBER_RE.sub(PLACEHOLDER, text)

    # Protect the placeholder from any later cleanup.
    text = re.sub(r"[（）()]", "", text)
    text = re.sub(r"\s+", "", text)
    text = text.replace(SENTINEL, PLACEHOLDER)
    text = re.sub(rf"(?:{re.escape(PLACEHOLDER)})+", PLACEHOLDER, text)
    return text


def blank_stats() -> dict[str, Any]:
    return {
        "icons": Counter(),
        "icon_seen": defaultdict(set),
        "quotes": Counter(),
        "quote_seen": defaultdict(set),
        "exact_terms": Counter(),
        "exact_seen": defaultdict(set),
        "discovered_terms": Counter(),
        "discovered_seen": defaultdict(set),
        "numbers": Counter(),
        "number_seen": defaultdict(set),
    }


def count_unique_clauses(clauses: list[dict[str, Any]]) -> int:
    """Count unique raw clauses."""
    return len({nfkc(c["clause"]) for c in clauses})


def normalize_clause_partial(
    clause: str,
    clause_idx: int,
    replace_icons: bool = False,
    replace_quotes: bool = False,
    replace_numbers: bool = False,
    replace_terms: bool = False,
    terms: list[str] = None,
    stats: dict[str, Any] = None,
) -> str:
    """Normalize clause with selective replacement for comparison."""
    if stats is None:
        stats = blank_stats()
    text = nfkc(clause)
    raw_text = text

    if replace_icons:
        for token in ICON_TOKEN_RE.findall(raw_text):
            stats["icons"][token] += 1
            stats["icon_seen"][token].add(clause_idx)
        text = ICON_TOKEN_RE.sub(PLACEHOLDER, text)

    if replace_quotes:
        for span in extract_quotes(raw_text):
            stats["quotes"][span] += 1
            stats["quote_seen"][span].add(clause_idx)
        text = QUOTE_RE.sub(PLACEHOLDER, text)

    text = text.replace(PLACEHOLDER, SENTINEL)

    if replace_terms and terms:
        text = replace_exact_terms(text, terms, stats["exact_terms"], stats["exact_seen"], clause_idx)

    if replace_numbers:
        number_hits = NUMBER_RE.findall(text)
        for hit in number_hits:
            stats["numbers"][hit] += 1
            stats["number_seen"][hit].add(clause_idx)
        text = NUMBER_RE.sub(PLACEHOLDER, text)

    text = re.sub(r"[（）()]", "", text)
    text = re.sub(r"\s+", "", text)
    text = text.replace(SENTINEL, PLACEHOLDER)
    text = re.sub(rf"(?:{re.escape(PLACEHOLDER)})+", PLACEHOLDER, text)
    return text


def compare_clause_variations(
    clauses: list[dict[str, Any]],
    exact_terms: list[str],
    discovered_terms: list[str],
    term_mapping: dict[str, str],
) -> dict[str, Any]:
    """Compare unique clause counts with manual variable replacement."""
    raw_unique = count_unique_clauses(clauses)
    
    stats = blank_stats()
    all_terms = exact_terms + discovered_terms

    # Normalize with all replacements
    normalized_clauses = []
    for idx, row in enumerate(clauses):
        normalized = normalize_clause_partial(
            row["clause"], idx, replace_icons=True, replace_quotes=True,
            replace_numbers=True, replace_terms=True, terms=all_terms, stats=stats
        )
        normalized_clauses.append(normalized)
    
    final_unique = len(set(normalized_clauses))
    total_reduction = raw_unique - final_unique

    # Show what was replaced
    top_replaced_terms = [
        {"term": term, "count": count, "clause_count": len(stats["exact_seen"].get(term, set()))}
        for term, count in stats["exact_terms"].most_common(30)
    ]

    return {
        "raw_unique": raw_unique,
        "final_unique": final_unique,
        "total_reduction": total_reduction,
        "manual_terms_count": len(discovered_terms),
        "manual_terms_sample": discovered_terms[:30],
        "top_replaced_terms": top_replaced_terms,
        "term_mapping": term_mapping,
    }


def residual_candidates(skeletons: list[str], rules_text: str) -> list[dict[str, Any]]:
    rules_counts = token_counter(rules_text)
    counts = Counter()
    seen: dict[str, set[int]] = defaultdict(set)

    for idx, skeleton in enumerate(skeletons):
        for token in TOKEN_RE.findall(nfkc(skeleton)):
            if token == PLACEHOLDER:
                continue
            counts[token] += 1
            seen[token].add(idx)

    candidates = []
    for token, count in counts.items():
        if count < 3:
            continue
        candidates.append(
            {
                "token": token,
                "count": count,
                "clause_count": len(seen[token]),
                "rules_count": rules_counts.get(token, 0),
                "rules_supported": token in rules_counts,
            }
        )

    candidates.sort(key=lambda row: (-row["count"], -row["clause_count"], row["token"]))
    return candidates[:200]


def group_by_structure(
    clauses: list[dict[str, Any]],
    abilities: list[dict[str, Any]],
    exact_terms: list[str],
    discovered_terms: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    stats = blank_stats()
    all_skeletons: list[str] = []
    for idx, row in enumerate(clauses):
        all_skeletons.append(normalize_clause(row["clause"], idx, exact_terms, discovered_terms, stats))

    grouped: dict[str, dict[str, Any]] = {}
    for ability in abilities:
        skeletons = [
            normalize_clause(clause, -1, exact_terms, discovered_terms, blank_stats())
            for clause in split_clauses(ability["jp"])
        ]
        combined = " / ".join(skeletons)
        entry = grouped.setdefault(
            combined,
            {
                "skeleton": combined,
                "count": 0,
                "jp_examples": [],
                "card_examples": [],
            },
        )
        entry["count"] += 1
        if len(entry["jp_examples"]) < 5:
            entry["jp_examples"].append(ability["jp"])
        entry["card_examples"].extend(ability["card_examples"])

    structure_list = sorted(grouped.values(), key=lambda item: (-item["count"], item["skeleton"]))
    for item in structure_list:
        item["card_examples"] = sorted(set(item["card_examples"]))[:10]

    analysis = {
        "replacement_totals": {
            "icons": int(sum(stats["icons"].values())),
            "quotes": int(sum(stats["quotes"].values())),
            "exact_terms": int(sum(stats["exact_terms"].values())),
            "discovered_terms": int(sum(stats["discovered_terms"].values())),
            "numbers": int(sum(stats["numbers"].values())),
        },
        "top_icons": top_rows(stats["icons"], stats["icon_seen"]),
        "top_quotes": top_rows(stats["quotes"], stats["quote_seen"]),
        "top_exact_terms": top_rows(stats["exact_terms"], stats["exact_seen"]),
        "top_discovered_terms": top_rows(stats["discovered_terms"], stats["discovered_seen"]),
        "top_numbers": top_rows(stats["numbers"], stats["number_seen"]),
    }

    return structure_list, analysis, all_skeletons


def top_rows(counter: Counter[str], seen: dict[str, set[int]], limit: int = 100) -> list[dict[str, Any]]:
    rows = [
        {
            "token": token,
            "count": count,
            "clause_count": len(seen.get(token, set())),
        }
        for token, count in counter.items()
    ]
    rows.sort(key=lambda row: (-row["count"], -row["clause_count"], row["token"]))
    return rows[:limit]


def group_patterns_by_system(structures: list[dict[str, Any]]) -> dict[str, Any]:
    """Group ability patterns by game mechanic system for hierarchical organization."""
    systems = {
        "resource_systems": {"score": [], "hearts": [], "blades": [], "energy": []},
        "zone_operations": {"deck": [], "hand": [], "discard": [], "stage": [], "energy_zone": []},
        "conditions": {"threshold": [], "presence": [], "comparison": [], "count": []},
        "state_management": {"wait": [], "active": [], "move": []},
        "draw_search": {"look": [], "reveal": [], "select": [], "add": []},
        "special_mechanics": {"choice": [], "ability_grant": [], "cost_reduction": [], "duration": []},
        "atomic": [],
        "compound": [],
        "complex": [],
        "fallback": [],
    }
    
    for item in structures:
        skeleton = item.get("skeleton", "")
        structure_type = item.get("structure", "")
        
        # Classify by structure description
        if "Score" in structure_type or "スコア" in skeleton:
            systems["resource_systems"]["score"].append(item)
        elif "Heart" in structure_type or "ハート" in skeleton:
            systems["resource_systems"]["hearts"].append(item)
        elif "Blade" in structure_type or "ブレード" in skeleton:
            systems["resource_systems"]["blades"].append(item)
        elif "Energy" in structure_type or "エネルギー" in skeleton:
            systems["resource_systems"]["energy"].append(item)
        elif "deck" in structure_type.lower() or "デッキ" in skeleton:
            systems["zone_operations"]["deck"].append(item)
        elif "hand" in structure_type.lower() or "手札" in skeleton:
            systems["zone_operations"]["hand"].append(item)
        elif "discard" in structure_type.lower() or "控え室" in skeleton:
            systems["zone_operations"]["discard"].append(item)
        elif "stage" in structure_type.lower() or "ステージ" in skeleton:
            systems["zone_operations"]["stage"].append(item)
        elif "Conditional" in structure_type:
            if "threshold" in structure_type.lower() or "以上" in skeleton or "以下" in skeleton:
                systems["conditions"]["threshold"].append(item)
            elif "presence" in structure_type.lower() or "がいる" in skeleton:
                systems["conditions"]["presence"].append(item)
            elif "comparison" in structure_type.lower() or "より" in skeleton:
                systems["conditions"]["comparison"].append(item)
            else:
                systems["conditions"]["count"].append(item)
        elif "State Change" in structure_type:
            if "wait" in structure_type.lower() or "ウェイト" in skeleton:
                systems["state_management"]["wait"].append(item)
            elif "active" in structure_type.lower() or "アクティブ" in skeleton:
                systems["state_management"]["active"].append(item)
            elif "move" in structure_type.lower() or "移動" in skeleton:
                systems["state_management"]["move"].append(item)
        elif "Look" in structure_type or "見る" in skeleton:
            systems["draw_search"]["look"].append(item)
        elif "Reveal" in structure_type or "公開" in skeleton:
            systems["draw_search"]["reveal"].append(item)
        elif "Select" in structure_type or "選ぶ" in skeleton:
            systems["draw_search"]["select"].append(item)
        elif "Add" in structure_type or "加える" in skeleton:
            systems["draw_search"]["add"].append(item)
        elif "Choice" in structure_type or "選ぶ" in skeleton:
            systems["special_mechanics"]["choice"].append(item)
        elif "Ability Grant" in structure_type or "能力" in skeleton:
            systems["special_mechanics"]["ability_grant"].append(item)
        elif "Cost" in structure_type and "Reduction" in structure_type:
            systems["special_mechanics"]["cost_reduction"].append(item)
        elif "Duration" in structure_type or "まで" in skeleton:
            systems["special_mechanics"]["duration"].append(item)
        elif "Atomic" in structure_type:
            systems["atomic"].append(item)
        elif "Multi-Step" in structure_type or "Cost-Effect" in structure_type:
            systems["compound"].append(item)
        elif "Ability -" in structure_type:
            systems["complex"].append(item)
        elif "Catch-all" in structure_type or "Fragment" in structure_type:
            systems["fallback"].append(item)
        else:
            # Default to atomic
            systems["atomic"].append(item)
    
    return systems


def build_pattern_composition_metadata(dsl_patterns: list[dict[str, Any]]) -> dict[str, Any]:
    """Build metadata showing how patterns compose from atomic elements."""
    atomic_actions = [
        p for p in dsl_patterns 
        if "draw" in p["name"] or "discard" in p["name"] or "place" in p["name"]
        or "reveal" in p["name"] or "select" in p["name"] or "gain" in p["name"]
        or "activate" in p["name"] or "wait" in p["name"] or "move" in p["name"]
        or "look" in p["name"] or "add" in p["name"] or "shuffle" in p["name"]
    ]
    
    atomic_conditions = [
        p for p in dsl_patterns
        if "conditional" in p["name"] and "threshold" not in p["name"] and "presence" not in p["name"]
    ]
    
    compound_patterns = [
        p for p in dsl_patterns
        if "Multi-Step" in p["structure"] or "Cost-Effect" in p["structure"]
        or "conditional" in p["name"] and any(a["name"] in p["template"] for a in atomic_actions)
    ]
    
    complex_patterns = [
        p for p in dsl_patterns
        if "Ability -" in p["structure"] or "Choice" in p["structure"]
        or "Duration" in p["structure"] and "Ability Grant" in p["structure"]
    ]
    
    return {
        "atomic": {
            "actions": [{"name": p["name"], "template": p["template"], "structure": p["structure"]} 
                       for p in atomic_actions[:20]],
            "conditions": [{"name": p["name"], "template": p["template"], "structure": p["structure"]}
                          for p in atomic_conditions[:15]],
            "count": len(atomic_actions) + len(atomic_conditions),
        },
        "compound": {
            "patterns": [{"name": p["name"], "template": p["template"], 
                         "composes_from": _infer_composition(p, atomic_actions, atomic_conditions)}
                        for p in compound_patterns[:20]],
            "count": len(compound_patterns),
        },
        "complex": {
            "patterns": [{"name": p["name"], "template": p["template"], "structure": p["structure"]}
                        for p in complex_patterns[:10]],
            "count": len(complex_patterns),
        },
        "composition_rules": [
            "condition + action = conditional_action",
            "action + action = sequential_action", 
            "cost + effect = cost_effect",
            "modifier + duration = duration_effect",
            "trigger + effect = triggered_ability"
        ]
    }


def _infer_composition(pattern: dict[str, Any], atomic_actions: list[dict], 
                       atomic_conditions: list[dict]) -> list[str]:
    """Infer which atomic patterns compose into this compound pattern."""
    template = pattern.get("template", "")
    composition = []
    
    # Check for condition indicators
    if "場合" in template or "COND" in template:
        composition.append("condition")
    
    # Check for action indicators  
    for action in atomic_actions:
        if action["name"] in pattern["name"]:
            composition.append(f"action.{action['name']}")
    
    # Check for cost-effect pattern
    if "：" in pattern.get("regex", "") or "COST" in template:
        composition.append("cost-effect-connector")
    
    return composition if composition else ["unknown"]


def export_dsl_grammar(dsl_patterns: list[dict[str, Any]], 
                       term_mapping: dict[str, str]) -> dict[str, Any]:
    """Export the discovered DSL grammar for external system consumption."""
    composition = build_pattern_composition_metadata(dsl_patterns)
    
    # Build example expansions
    example_expansions = {}
    for p in dsl_patterns[:30]:
        if "template" in p and p["template"]:
            # Create a concrete example from template
            example = p["template"]
            example = example.replace("⟦SRC⟧", "自分のデッキ")
            example = example.replace("⟦DST⟧", "手札")
            example = example.replace("⟦CTYPE⟧", "メンバー")
            example = example.replace("⟦CNT⟧", "1")
            example = example.replace("⟦N⟧", "3")
            example = example.replace("⟦ZONE⟧", "控え室")
            example = example.replace("⟦GRP⟧", "μ's")
            example = example.replace("⟦RES⟧", "スコア")
            example = example.replace("⟦COND⟧", "自分のエネルギーが3枚以上")
            example = example.replace("⟦EFF⟧", "カードを1枚引く")
            example = example.replace("⟦TEXT⟧", "...")
            
            example_expansions[p["name"]] = {
                "pattern_template": p["template"],
                "concrete_example": example,
                "structure": p.get("structure", ""),
            }
    
    return {
        "version": "1.0",
        "description": "LoveCA Card Game Ability DSL Grammar",
        "atomics": composition["atomic"],
        "compound_rules": composition["composition_rules"],
        "example_expansions": example_expansions,
        "placeholder_definitions": SEMANTIC_PLACEHOLDERS,
        "term_mapping": term_mapping,
    }


def extract_abilities(cards_file: Path, rules_file: Path, output_file: Path, metadata_file: Path) -> dict[str, Any]:
    cards = load_cards(cards_file)
    rules_text = load_rules(rules_file)
    clauses = all_ability_clauses(cards)
    abilities = group_abilities(cards)

    known = build_known_terms(cards)
    
    # Placeholder for term data (discover_japanese_equivalents was deleted)
    term_data = {"mapping": {}, "counts": {}}
    
    all_terms, counters = build_candidate_terms(clauses, rules_text, known, term_data)

    # Extract and normalize effects separately from triggers
    effects_analysis = extract_effects_from_clauses(clauses, term_data["mapping"])

    # Match clauses using DSL pattern matching (language structure approach)
    dsl_pattern_analysis = match_dsl_patterns(clauses, term_data["mapping"])

    # Analyze simple terms to understand clause structure (bottom-up approach)
    simple_term_analysis = analyze_simple_terms(clauses, term_data["mapping"])

    # Compare unique clauses with different replacement strategies
    clause_comparison = compare_clause_variations(
        clauses,
        all_terms["exact_terms"],
        all_terms["discovered_terms"],
        term_data["mapping"],
    )

    structures, analysis, skeletons = group_by_structure(
        clauses,
        abilities,
        all_terms["exact_terms"],
        all_terms["discovered_terms"],
    )
    analysis["residual_candidates"] = residual_candidates(skeletons, rules_text)
    analysis["rules_token_support"] = [
        {"token": token, "count": count}
        for token, count in counters["rules_counts"].most_common(100)
    ]
    analysis["clause_comparison"] = clause_comparison
    analysis["term_mapping"] = term_data["mapping"]
    analysis["term_counts"] = term_data["counts"]
    analysis["effects_analysis"] = effects_analysis
    analysis["dsl_pattern_analysis"] = dsl_pattern_analysis
    analysis["simple_term_analysis"] = simple_term_analysis

    # NEW: Group structures by game mechanic system
    patterns_by_system = group_patterns_by_system(structures)
    
    # NEW: Build pattern composition metadata
    composition_metadata = build_pattern_composition_metadata(DSL_PATTERNS)
    
    # NEW: Export DSL grammar
    dsl_grammar = export_dsl_grammar(DSL_PATTERNS, term_data["mapping"])

    # Calculate coverage and compression metrics
    total_abilities = dsl_pattern_analysis.get("total_abilities", 0)
    matched_abilities = dsl_pattern_analysis.get("matched_abilities", 0)
    coverage = matched_abilities / total_abilities if total_abilities else 0
    
    total_clauses = dsl_pattern_analysis.get("total_clauses", 0)
    matched_clauses = dsl_pattern_analysis.get("matched_clauses", 0)
    clause_compression = matched_clauses / total_clauses if total_clauses else 0
    
    # Build pattern match summary for verification
    pattern_counts = dsl_pattern_analysis.get("pattern_counts", {})
    top_patterns = sorted(pattern_counts.items(), key=lambda x: -x[1])[:20]
    
    # Analyze atomic phrase quality - which patterns are truly atomic?
    def analyze_atomic_quality(template: str) -> dict:
        """Analyze if a template is truly atomic (only placeholders and particles) or has long phrases."""
        # Remove placeholders
        text_only = re.sub(r'⟦[^⟧]+⟧', '', template)
        # Remove common particles/structure words
        particles = re.sub(r'[をのにがはでとから、：\/\(\)「」『』\s]', '', text_only)
        # Count remaining characters (should be 0-3 for truly atomic)
        remaining_len = len(particles)
        return {
            "is_atomic": remaining_len <= 3,
            "remaining_text": particles,
            "remaining_len": remaining_len,
            "template": template
        }
    
    # Categorize all matched patterns by atomic quality
    atomic_patterns = []  # Truly atomic: only placeholders + particles
    semi_atomic_patterns = []  # Has some structure but short phrases
    needs_breakdown_patterns = []  # Long phrases that need decomposition
    
    for pattern_name, count in pattern_counts.items():
        # Find template for this pattern
        template = ""
        for p in DSL_PATTERNS:
            if p.get("name") == pattern_name:
                template = p.get("template", "")
                break
        
        if template:
            quality = analyze_atomic_quality(template)
            entry = {
                "name": pattern_name,
                "count": count,
                "template": template,
                "quality": quality
            }
            
            if quality["is_atomic"]:
                atomic_patterns.append(entry)
            elif quality["remaining_len"] <= 10:
                semi_atomic_patterns.append(entry)
            else:
                needs_breakdown_patterns.append(entry)
    
    # Sort by count
    atomic_patterns.sort(key=lambda x: -x["count"])
    semi_atomic_patterns.sort(key=lambda x: -x["count"])
    needs_breakdown_patterns.sort(key=lambda x: -x["count"])
    
    # Categorize patterns by type for decomposition analysis
    atomic_patterns_matched = [p for p in top_patterns if p[0].startswith(('atomic_', 'action_'))]
    compound_patterns_matched = [p for p in top_patterns if p[0].startswith('compound_')]
    conditional_patterns_matched = [p for p in top_patterns if p[0].startswith('conditional_')]
    trigger_patterns_matched = [p for p in top_patterns if p[0].startswith('trigger_')]
    
    # Decomposition examples - show how complex abilities break down
    decomposition_examples = []
    matched_sample = dsl_pattern_analysis.get("matched_ability_sample", [])
    for ability in matched_sample[:5]:
        clause_patterns = ability.get("clause_patterns", [])
        if len(clause_patterns) > 1:  # Multi-clause = decomposable
            decomposition_examples.append({
                "original": ability.get("original", "")[:60] + "...",
                "trigger": ability.get("trigger", "UNKNOWN"),
                "decomposed_into": [cp.get("pattern_name", "unknown") for cp in clause_patterns],
                "composition_type": "sequential" if len(clause_patterns) == 2 else "complex"
            })
    
    verification = {
        "script_version": "2.0-atomic-analysis",
        "coverage_metrics": {
            "ability_coverage": round(coverage, 3),
            "clause_coverage": round(clause_compression, 3),
            "atomic_coverage": round(atomic_coverage, 3),
            "note": "Atomic coverage = % of matched text using truly atomic patterns (only placeholders)"
        },
        "pattern_counts": {
            "total_dsl_defined": len(DSL_PATTERNS),
            "actually_matched": len([p for p, c in pattern_counts.items() if c > 0]),
            "truly_atomic": len(atomic_patterns),
            "semi_atomic": len(semi_atomic_patterns),
            "needs_breakdown": len(needs_breakdown_patterns)
        },
        "atomic_quality_analysis": {
            "truly_atomic_patterns": [
                {"name": p["name"], "template": p["template"], "matches": p["count"]}
                for p in atomic_patterns[:15]
            ],
            "needs_breakdown_patterns": [
                {"name": p["name"], "template": p["template"], "remaining_text": p["quality"]["remaining_text"], "matches": p["count"]}
                for p in needs_breakdown_patterns[:10]
            ],
            "goal": "All patterns should be atomic: only placeholders + particles (を、の、に、が etc.)"
        },
        "decomposition": {
            "examples": decomposition_examples,
            "principle": "Complex abilities decompose into atomic actions + conditions + triggers",
            "composition_rules": [
                "atomic_action + atomic_action = sequential",
                "condition + atomic_action = conditional_effect",
                "trigger + effect = triggered_ability"
            ]
        },
        "consolidation_proof": {
            "before_estimated": 190,
            "after": len(DSL_PATTERNS),
            "reduction_percent": round((1 - len(DSL_PATTERNS) / 190) * 100, 1),
            "note": "Patterns consolidated by merging duplicates into generic regexes"
        }
    }
    
    payload = {
        "schema": "ability_skeletons.v7",
        "verification": verification,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "source": str(cards_file),
            "rules_source": str(rules_file),
            "metadata_source": str(metadata_file),
            "placeholder_system": SEMANTIC_PLACEHOLDERS,
        },
        "statistics": {
            "total_clauses": total_clauses,
            "total_abilities": total_abilities,
            "unique_patterns": len(structures),
            "coverage": round(coverage, 3),
            "clause_compression_ratio": round(clause_compression, 3),
            "ability_compression_ratio": round(dsl_pattern_analysis.get("ability_compression_ratio", 0), 3),
            "pattern_breakdown": {
                "atomic": len(patterns_by_system.get("atomic", [])),
                "compound": len(patterns_by_system.get("compound", [])),
                "complex": len(patterns_by_system.get("complex", [])),
                "fallback": len(patterns_by_system.get("fallback", [])),
            }
        },
        "patterns": {
            "by_system": patterns_by_system,
            "by_type": {
                "atomic": composition_metadata["atomic"],
                "compound": composition_metadata["compound"],
                "complex": composition_metadata["complex"],
            },
            "all_patterns": [{"name": s.get("skeleton", ""), "count": s.get("count", 0), 
                            "examples": s.get("jp_examples", [])[:3]} 
                           for s in structures[:100]],
        },
        "composition": {
            "rules": composition_metadata["composition_rules"],
            "atomic_count": composition_metadata["atomic"]["count"],
            "compound_count": composition_metadata["compound"]["count"],
            "complex_count": composition_metadata["complex"]["count"],
        },
        "dsl_grammar": dsl_grammar,
        "abilities": {
            "matched": dsl_pattern_analysis.get("matched_ability_sample", [])[:50],
            "unmatched": {
                "count": len(dsl_pattern_analysis.get("unmatched_ability_sample", [])),
                "by_reason": {
                    "no_pattern": dsl_pattern_analysis.get("unmatched_ability_sample", [])[:20],
                }
            }
        },
        "legacy_analysis": analysis,  # Keep old structure for backwards compatibility
        "structures": structures,  # Keep for backwards compatibility
    }
    output_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def generate_structured_dsl_output(dsl_analysis: dict[str, Any], abilities_data: dict[str, Any], patterns: list[dict[str, Any]], output_file: Path) -> None:
    """
    Generate structured JSON output for DSL pattern analysis.
    Follows the structure of ability_frame_source.json for system consumption.
    """
    from datetime import datetime
    
    ability_level = dsl_analysis.get('dsl_pattern_analysis', {})
    pattern_counts = ability_level.get('ability_pattern_counts', {})
    pattern_variables = ability_level.get('ability_pattern_variables', {})
    matched_abilities = ability_level.get('matched_ability_sample', [])
    
    # Load abilities from cards to get card references
    abilities_from_cards = abilities_data.get('abilities', [])
    
    # Build pattern entries with matched abilities and card references
    patterns_output = []
    
    # Add patterns from ABILITY_LEVEL_PATTERNS
    for pattern_name in [p["name"] for p in patterns]:
        if pattern_name == "ability_catchall":
            continue  # Skip catchall in structured output
        
        pattern_info = next((p for p in patterns if p["name"] == pattern_name), None)
        if not pattern_info:
            continue
        
        match_count = pattern_counts.get(pattern_name, 0)
        variables_list = pattern_variables.get(pattern_name, [])
        
        # Find matched abilities for this pattern
        pattern_matched = [a for a in matched_abilities if a['pattern_name'] == pattern_name]
        
        matched_abilities_data = []
        for i, matched in enumerate(pattern_matched):
            # Find card references for this ability
            cards = []
            for ability in abilities_from_cards:
                for source in ability['source_ability_texts']:
                    if source['jp'] == matched['original']:
                        cards = source.get('cards', [])
                        break
                if cards:
                    break
            
            matched_abilities_data.append({
                "ability_text": matched['original'],
                "variables": matched.get('variables', []),
                "trigger": matched.get('trigger', 'UNKNOWN'),
                "card_refs": cards[:5]  # Limit to first 5 cards
            })
        
        patterns_output.append({
            "pattern_name": pattern_name,
            "regex": pattern_info["regex"],
            "template": pattern_info["template"],
            "structure": pattern_info["structure"],
            "match_count": match_count,
            "matched_abilities": matched_abilities_data
        })
    
    # Add dynamically generated trigger_clause_sequence pattern
    if "trigger_clause_sequence" in pattern_counts:
        match_count = pattern_counts["trigger_clause_sequence"]
        pattern_matched = [a for a in matched_abilities if a['pattern_name'] == 'trigger_clause_sequence']
        
        matched_abilities_data = []
        for matched in pattern_matched[:10]:  # Limit to 10 samples
            cards = []
            for ability in abilities_from_cards:
                for source in ability['source_ability_texts']:
                    if source['jp'] == matched['original']:
                        cards = source.get('cards', [])
                        break
                if cards:
                    break
            
            matched_abilities_data.append({
                "ability_text": matched['original'],
                "variables": matched.get('variables', []),
                "trigger": matched.get('trigger', 'UNKNOWN'),
                "clause_patterns": matched.get('clause_patterns', []),
                "card_refs": cards[:5]
            })
        
        patterns_output.append({
            "pattern_name": "trigger_clause_sequence",
            "regex": "DYNAMIC - trigger + clause patterns",
            "template": "⟦TRIGGER⟧ + [⟦CLAUSE_PATTERN_1⟧, ⟦CLAUSE_PATTERN_2⟧, ...]",
            "structure": "Ability - Trigger + clause pattern sequence (generic)",
            "match_count": match_count,
            "matched_abilities": matched_abilities_data
        })
    
    # Sort by match count (descending)
    patterns_output.sort(key=lambda p: -p['match_count'])
    
    output = {
        "schema": "dsl_analysis_structured.v1",
        "_comment": "DSL pattern analysis results - structured for system consumption. Generated by tools/extract_abilities_to_template.py",
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_patterns": len(patterns_output),
            "total_abilities_analyzed": ability_level.get('total_abilities', 0),
            "compression_ratio": ability_level.get('ability_compression_ratio', 0)
        },
        "patterns": patterns_output
    }
    
    output_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize ability text into clause skeletons")
    parser.add_argument("--cards", type=Path, default=Path("data/cards.json"), help="Path to cards.json")
    parser.add_argument("--rules", type=Path, default=Path("data/rules.txt"), help="Path to rules.txt")
    parser.add_argument("--metadata", type=Path, default=Path("data/metadata.json"), help="Path to metadata.json")
    parser.add_argument("--output", type=Path, default=Path("data/abilities_extracted.json"), help="Output JSON path")
    args = parser.parse_args()
    payload = extract_abilities(args.cards, args.rules, args.output, args.metadata)
    
    # Generate structured DSL output
    try:
        abilities_data = json.load(open('data/abilities_from_cards.json', encoding='utf-8'))
        dsl_output_file = Path("data/dsl_analysis_structured.json")
        generate_structured_dsl_output(payload['legacy_analysis'], abilities_data, ABILITY_LEVEL_PATTERNS, dsl_output_file)
        print(f"Structured DSL output written to {dsl_output_file}")
    except Exception as e:
        print(f"Warning: Could not generate structured DSL output: {e}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
