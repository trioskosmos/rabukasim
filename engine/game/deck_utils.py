import os
import re
from collections import Counter


def extract_deck_data(content: str, card_db: dict):
    """
    Parses deck content (HTML or various text formats) to extract card IDs and quantities.
    Returns (main_deck, energy_deck, type_counts, errors)
    """
    # 1. Try HTML Structure (Deck Log)
    # pattern matches: title="PL!xxx-yyy-zzz : NAME" ... <span class="num">N</span>
    pattern_html = r'title="([^"]+?) :[^"]*"[^>]*>.*?class="num">(\d+)</span>'
    matches = re.findall(pattern_html, content, re.DOTALL)

    if not matches:
        # Fallback 1: Text format "QTY x ID" (e.g., "4 x LL-bp3-001-R＋")
        text_pattern_1 = r"(\d+)\s*[xX]\s*([A-Za-z0-9!+\-＋]+)"
        matches_1 = re.findall(text_pattern_1, content)
        if matches_1:
            # Swap to (ID, Qty) format
            matches = [(m[1], m[0]) for m in matches_1]
        else:
            # Fallback 2: Text format "ID x QTY" (e.g., "PL!S-bp2-022-L x 2")
            text_pattern_2 = r"([A-Za-z0-9!+\-＋]+)\s*[xX]\s*(\d+)"
            matches_2 = re.findall(text_pattern_2, content)
            if matches_2:
                matches = matches_2
            else:
                # Fallback 3: Simple list of IDs (one per line)
                # Matches strings like "PL!S-bp1-001-M" but avoids common words
                # This is risky but useful for simple text files.
                # Let's use a more specific regex for ID patterns.
                id_pattern = r"([PL!|LL\-E][A-Za-z0-9!+\-＋]+-[A-Za-z0-9!+\-＋]+-[A-Za-z0-9!+\-＋]+[A-Za-z0-9!+\-＋]*)"
                matches_3 = re.findall(id_pattern, content)
                if matches_3:
                    # Count occurrences
                    counts = Counter(matches_3)
                    matches = [(cid, str(cnt)) for cid, cnt in counts.items()]

    if not matches:
        return [], [], {}, ["No recognizable card data found in content."]

    main_deck = []
    energy_deck = []
    type_counts = {"Member": 0, "Live": 0, "Energy": 0, "Unknown": 0}
    errors = []

    for card_id, qty_str in matches:
        try:
            qty = int(qty_str)
        except ValueError:
            continue

        card_id = card_id.strip()

        # Determine Type from database
        cdata = card_db.get(card_id, {})
        ctype = cdata.get("type", "")

        if "メンバー" in ctype or "Member" in ctype:
            type_counts["Member"] += qty
        elif "ライブ" in ctype or "Live" in ctype:
            type_counts["Live"] += qty
        elif "エネルギー" in ctype or "Energy" in ctype:
            type_counts["Energy"] += qty
        else:
            type_counts["Unknown"] += qty

        for _ in range(qty):
            if "エネルギー" in ctype or "Energy" in ctype or card_id.startswith("LL-E"):
                energy_deck.append(card_id)
            else:
                main_deck.append(card_id)

    # Basic Validation
    all_counts = Counter(main_deck + energy_deck)
    for cid, count in all_counts.items():
        if count > 4 and not cid.startswith("LL-E"):
            # Some formats might have duplicates if listing line-by-line + QTY.
            # We don't block here, just warn.
            errors.append(f"Card limit exceeded: {cid} x{count} (Max 4)")

    return main_deck, energy_deck, type_counts, errors


def load_deck_from_file(file_path: str, card_db: dict):
    """Helper to read a file and parse it."""
    if not os.path.exists(file_path):
        return None, None, {}, [f"File {file_path} not found."]

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return extract_deck_data(content, card_db)
