import os
import re
import unicodedata
from collections import Counter
from typing import Dict, List, Optional


class UnifiedDeckParser:
    """
    Deck parser that resolves card codes and internal IDs.
    """

    def __init__(self, card_db: Optional[Dict] = None):
        self.card_db = card_db or {}
        self.normalized_db = {}
        for db_name, sub_db in self.card_db.items():
            if not isinstance(sub_db, dict):
                continue
            inferred_type = (
                "Member"
                if "member" in db_name
                else "Live"
                if "live" in db_name
                else "Energy"
                if "energy" in db_name
                else "Unknown"
            )
            for value in sub_db.values():
                if isinstance(value, dict) and "card_no" in value:
                    card = value.copy()
                    card["type"] = inferred_type
                    self.normalized_db[self.normalize_code(card["card_no"])] = card

    @staticmethod
    def normalize_code(code: str) -> str:
        """Normalize card codes for matching."""
        if not code:
            return ""

        normalized = unicodedata.normalize("NFKC", str(code)).strip()
        translation = str.maketrans(
            {
                "\u2212": "-",
                "\u2010": "-",
                "\u2011": "-",
                "\u2012": "-",
                "\u2013": "-",
                "\u2014": "-",
                "\uff0b": "+",
                "\ufe62": "+",
                "\u207a": "+",
                "\u3000": "",
                " ": "",
            }
        )
        return normalized.translate(translation).upper()

    def resolve_card(self, code_or_id: str) -> Dict:
        """Find card data by card number or internal ID."""
        norm_code = self.normalize_code(code_or_id)
        if norm_code in self.normalized_db:
            return self.normalized_db[norm_code]

        try:
            int_id = int(code_or_id)
        except (TypeError, ValueError):
            return {}

        for card_data in self.normalized_db.values():
            if card_data.get("card_id") == int_id:
                return card_data

        return {}

    def extract_from_content(self, content: str) -> List[Dict]:
        """Parse content into a single normalized deck payload."""
        deck = self._parse_single_deck(content)
        deck["name"] = "Default Deck"
        return [deck]

    def _parse_card_matches_from_content(self, content: str):
        """Extract (card_id, qty_str) pairs from HTML or free text."""
        pattern_html = r'title="([^"]+?)\s*:\s*[^"]*"[\s\S]*?class="num"[^>]*>(\d+)</span>'
        matches = re.findall(pattern_html, content, re.DOTALL)
        if matches:
            return matches

        code = r"[A-Za-z0-9!+\-]+"
        text_pattern_1 = rf"(\d+)\s*[xX]\s*({code})"
        matches_1 = re.findall(text_pattern_1, content)
        if matches_1:
            return [(card_no, qty) for qty, card_no in matches_1]

        text_pattern_2 = rf"({code})\s*[xX]\s*(\d+)"
        matches_2 = re.findall(text_pattern_2, content)
        if matches_2:
            return matches_2

        id_pattern = rf"\b({code})\b"
        matches_3 = re.findall(id_pattern, content)
        if matches_3:
            counts = Counter(matches_3)
            return [(cid, str(cnt)) for cid, cnt in counts.items()]

        return []

    def _parse_single_deck(self, content: str) -> Dict:
        main_deck = []
        energy_deck = []
        errors = []
        type_counts = {"Member": 0, "Live": 0, "Energy": 0, "Unknown": 0}

        matches = self._parse_card_matches_from_content(content)
        for card_id, qty_str in matches:
            try:
                qty = int(qty_str)
            except ValueError:
                continue

            card_id = str(card_id).strip()
            cdata = self.resolve_card(card_id)
            ctype = cdata.get("type", "")
            normalized = self.normalize_code(card_id)
            is_energy = (
                "Energy" in ctype
                or normalized.startswith("LL-E")
                or normalized.endswith("-PE")
                or normalized.endswith("-PE+")
            )

            if is_energy:
                type_counts["Energy"] += qty
                energy_deck.extend([card_id] * qty)
            elif "Member" in ctype:
                type_counts["Member"] += qty
                main_deck.extend([card_id] * qty)
            elif "Live" in ctype:
                type_counts["Live"] += qty
                main_deck.extend([card_id] * qty)
            else:
                type_counts["Unknown"] += qty
                main_deck.extend([card_id] * qty)

        return {"main": main_deck, "energy": energy_deck, "type_counts": type_counts, "errors": errors}


def extract_deck_data(content: str, card_db: dict):
    """Legacy wrapper for backward compatibility."""
    parser = UnifiedDeckParser(card_db)
    results = parser.extract_from_content(content)
    if not results:
        return [], [], {}, ["No deck found"]

    deck = results[0]
    return deck["main"], deck["energy"], deck["type_counts"], deck["errors"]


def load_deck_from_file(file_path: str, card_db: dict):
    """Helper to read a file and parse it."""
    if not os.path.exists(file_path):
        return None, None, {}, [f"File {file_path} not found."]

    with open(file_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    return extract_deck_data(content, card_db)
