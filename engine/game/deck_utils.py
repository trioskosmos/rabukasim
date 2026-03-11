import os
import re
from collections import Counter
from typing import Dict, List, Optional


class UnifiedDeckParser:
    """
    Consolidated deck parser that handles:
    - HTML (Bushiroad DECK LOG format)
    - Text (Qty x ID or ID x Qty)
    - List of IDs (one per line)
    - Normalization of full-width characters and spaces
    - Internal ID resolution
    """

    def __init__(self, card_db: Optional[Dict] = None):
        self.card_db = card_db or {}
        # Index by Card No (e.g. "PL!S-bp2-022-L") for resolution
        self.normalized_db = {}
        for db_name, sub_db in self.card_db.items():
            if isinstance(sub_db, dict):
                # Infer type from database name
                inferred_type = (
                    "Member"
                    if "member" in db_name
                    else "Live"
                    if "live" in db_name
                    else "Energy"
                    if "energy" in db_name
                    else "Unknown"
                )
                for v in sub_db.values():
                    if isinstance(v, dict) and "card_no" in v:
                        # Copy to avoid mutating original shared DB if possible, but here we likely want it
                        v_with_type = v.copy()
                        v_with_type["type"] = inferred_type
                        self.normalized_db[self.normalize_code(v["card_no"])] = v_with_type

    @staticmethod
    def normalize_code(code: str) -> str:
        """Normalize card codes for matching."""
        if not code:
            return ""
        return (
            code.strip()
            .replace("＋", "+")
            .replace("－", "-")
            .replace("ー", "-")
            .upper()
        )

    def resolve_card(self, code_or_id: str) -> Dict:
        """Finds card data by Card No or Internal ID."""
        norm_code = self.normalize_code(code_or_id)

        # 1. Try direct match in normalized DB
        if norm_code in self.normalized_db:
            return self.normalized_db[norm_code]

        # 2. Try as internal ID (integer string)
        try:
            int_id = int(code_or_id)
            # Search in normalized DB by card_id
            for card_data in self.normalized_db.values():
                if card_data.get("card_id") == int_id:
                    return card_data
        except ValueError:
            pass

        return {}

    def extract_from_content(self, content: str) -> List[Dict]:
        """
        Parses content and returns a list of deck dictionaries.
        Each deck dictionary contains:
        {
            'name': str,
            'main': List[str/int],
            'energy': List[str/int],
            'stats': Dict
        }
        """
        # Split content by deck markers if multiple exist (Deck Log markers)
        deck_sections = re.split(r"デッキ名「([^」]+)」のデッキ", content)

        decks = []
        if len(deck_sections) > 1:
            # First part is usually meta or empty
            for i in range(1, len(deck_sections), 2):
                name = deck_sections[i]
                body = deck_sections[i + 1]
                deck_info = self._parse_single_deck(body)
                deck_info["name"] = name
                decks.append(deck_info)
        else:
            # Single deck or unknown format
            deck_info = self._parse_single_deck(content)
            deck_info["name"] = "Default Deck"
            decks.append(deck_info)

        return decks

    @staticmethod
    def _extract_html_section(content: str, heading: str) -> str:
        """Extracts the HTML content of a named <h3> section from DECK LOG HTML.
        Returns the content between the matching <h3> and the next <h3> (or end of string).
        """
        import re as _re

        pattern = rf"<h3[^>]*>\s*{_re.escape(heading)}\s*</h3>([\s\S]*?)(?=<h3|$)"
        m = _re.search(pattern, content, _re.IGNORECASE)
        return m.group(1) if m else ""

    def _parse_card_matches_from_content(self, content: str):
        """Extracts list of (card_id, qty_str) from a section of HTML or text."""
        # Primary: DECK LOG HTML — title="CARD_ID : Name" ... class="num">N</span>
        pattern_html = r'title="([^"]+?)\s*:\s*[^"]*"[\s\S]*?class="num"[^>]*>(\d+)</span>'
        matches = re.findall(pattern_html, content, re.DOTALL)
        if matches:
            return matches

        # Fallback 1: Text "QTY x ID"
        text_pattern_1 = r"(\d+)\s*[xX]\s*([A-Za-z0-9!+\-＋]+)"
        matches_1 = re.findall(text_pattern_1, content)
        if matches_1:
            return [(m[1], m[0]) for m in matches_1]

        # Fallback 2: Text "ID x QTY"
        text_pattern_2 = r"([A-Za-z0-9!+\-＋]+)\s*[xX]\s*(\d+)"
        matches_2 = re.findall(text_pattern_2, content)
        if matches_2:
            return matches_2

        # Fallback 3: Simple list of card IDs (counted by repetition)
        id_pattern = r"([PL!|LL\-E][A-Za-z0-9!+\-＋]+-[A-Za-z0-9!+\-＋]+-[A-Za-z0-9!+\-＋]+[A-Za-z0-9!+\-＋]*)"
        matches_3 = re.findall(id_pattern, content)
        if matches_3:
            counts = Counter(matches_3)
            return [(cid, str(cnt)) for cid, cnt in counts.items()]

        return []

    def _parse_single_deck(self, content: str) -> Dict:
        """Parses a single deck section, using h3 section headers when present."""
        main_deck = []
        energy_deck = []
        errors = []
        type_counts = {"Member": 0, "Live": 0, "Energy": 0, "Unknown": 0}

        # Try section-aware parsing for DECK LOG HTML
        main_section = self._extract_html_section(content, "メインデッキ")
        energy_section = self._extract_html_section(content, "エネルギーデッキ")

        if main_section or energy_section:
            # ── Section-aware path ──────────────────────────────────────────
            for card_id, qty_str in self._parse_card_matches_from_content(main_section):
                try:
                    qty = int(qty_str)
                except ValueError:
                    continue
                card_id = card_id.strip()
                cdata = self.resolve_card(card_id)
                ctype = cdata.get("type", "Unknown")
                if "Member" in ctype:
                    type_counts["Member"] += qty
                elif "Live" in ctype:
                    type_counts["Live"] += qty
                else:
                    type_counts["Unknown"] += qty
                main_deck.extend([card_id] * qty)

            for card_id, qty_str in self._parse_card_matches_from_content(energy_section):
                try:
                    qty = int(qty_str)
                except ValueError:
                    continue
                card_id = card_id.strip()
                type_counts["Energy"] += qty
                energy_deck.extend([card_id] * qty)
        else:
            # ── Flat parse (text / unknown format) ─────────────────────────
            matches = self._parse_card_matches_from_content(content)
            for card_id, qty_str in matches:
                try:
                    qty = int(qty_str)
                except ValueError:
                    continue
                card_id = card_id.strip()
                cdata = self.resolve_card(card_id)
                ctype = cdata.get("type", "")
                is_energy = (
                    "Energy" in ctype
                    or card_id.startswith("LL-E")
                    or card_id.endswith("-PE")
                    or card_id.endswith("-PE+")
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

    # Return first deck for compatibility
    d = results[0]
    return d["main"], d["energy"], d["type_counts"], d["errors"]


def load_deck_from_file(file_path: str, card_db: dict):
    """Helper to read a file and parse it."""
    if not os.path.exists(file_path):
        return None, None, {}, [f"File {file_path} not found."]

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return extract_deck_data(content, card_db)
