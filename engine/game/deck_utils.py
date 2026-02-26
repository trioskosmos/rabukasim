import os
import re
import json
from collections import Counter
from typing import List, Dict, Tuple, Optional


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
        # Pre-normalize DB keys if they are Card Nos
        self.normalized_db = {}
        for k, v in self.card_db.items():
            self.normalized_db[self.normalize_code(k)] = v

    @staticmethod
    def normalize_code(code: str) -> str:
        """Normalizes card codes for consistent matching."""
        if not code:
            return ""
        # Convert full-width '+', '-', ' ' to half-width equivalent if needed, 
        # or just handle the most common character: full-width PLUS '＋'
        code = code.replace("＋", "+").replace("ー", "-").strip()
        return code

    def resolve_card(self, code_or_id: str) -> Dict:
        """Finds card data by Card No or Internal ID."""
        norm_code = self.normalize_code(code_or_id)
        
        # 1. Try direct match in normalized DB
        if norm_code in self.normalized_db:
            return self.normalized_db[norm_code]
            
        # 2. Try as internal ID (integer string)
        try:
            int_id = int(code_or_id)
            for card_data in self.card_db.values():
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
        deck_sections = re.split(r'デッキ名「([^」]+)」のデッキ', content)
        
        decks = []
        if len(deck_sections) > 1:
            # First part is usually meta or empty
            for i in range(1, len(deck_sections), 2):
                name = deck_sections[i]
                body = deck_sections[i+1]
                deck_info = self._parse_single_deck(body)
                deck_info['name'] = name
                decks.append(deck_info)
        else:
            # Single deck or unknown format
            deck_info = self._parse_single_deck(content)
            deck_info['name'] = "Default Deck"
            decks.append(deck_info)
            
        return decks

    def _parse_single_deck(self, content: str) -> Dict:
        """Parses a single deck section."""
        main_deck = []
        energy_deck = []
        errors = []
        
        # 1. Try HTML Structure findall
        # title="PL!xxx-yyy-zzz : NAME" ... <span class="num">N</span>
        pattern_html = r'title="([^"]+?) :[^"]*"[^>]*>.*?class="num">(\d+)</span>'
        matches = re.findall(pattern_html, content, re.DOTALL)

        if not matches:
            # Fallback 1: Text format "QTY x ID"
            text_pattern_1 = r"(\d+)\s*[xX]\s*([A-Za-z0-9!+\-＋]+)"
            matches_1 = re.findall(text_pattern_1, content)
            if matches_1:
                matches = [(m[1], m[0]) for m in matches_1]
            else:
                # Fallback 2: Text format "ID x QTY"
                text_pattern_2 = r"([A-Za-z0-9!+\-＋]+)\s*[xX]\s*(\d+)"
                matches_2 = re.findall(text_pattern_2, content)
                if matches_2:
                    matches = matches_2
                else:
                    # Fallback 3: Simple list of IDs
                    id_pattern = r"([PL!|LL\-E][A-Za-z0-9!+\-＋]+-[A-Za-z0-9!+\-＋]+-[A-Za-z0-9!+\-＋]+[A-Za-z0-9!+\-＋]*)"
                    matches_3 = re.findall(id_pattern, content)
                    if matches_3:
                        counts = Counter(matches_3)
                        matches = [(cid, str(cnt)) for cid, cnt in counts.items()]

        type_counts = {"Member": 0, "Live": 0, "Energy": 0, "Unknown": 0}

        for card_id, qty_str in matches:
            try:
                qty = int(qty_str)
            except ValueError:
                continue

            card_id = card_id.strip()
            cdata = self.resolve_card(card_id)
            ctype = cdata.get("type", "")

            # Determine storage location and type counts
            if "メンバー" in ctype or "Member" in ctype:
                type_counts["Member"] += qty
                for _ in range(qty): main_deck.append(card_id)
            elif "ライブ" in ctype or "Live" in ctype:
                type_counts["Live"] += qty
                for _ in range(qty): main_deck.append(card_id)
            elif "エネルギー" in ctype or "Energy" in ctype or card_id.startswith("LL-E"):
                type_counts["Energy"] += qty
                for _ in range(qty): energy_deck.append(card_id)
            else:
                type_counts["Unknown"] += qty
                for _ in range(qty): main_deck.append(card_id)

        return {
            "main": main_deck,
            "energy": energy_deck,
            "type_counts": type_counts,
            "errors": errors
        }


def extract_deck_data(content: str, card_db: dict):
    """Legacy wrapper for backward compatibility."""
    parser = UnifiedDeckParser(card_db)
    results = parser.extract_from_content(content)
    if not results:
        return [], [], {}, ["No deck found"]
    
    # Return first deck for compatibility
    d = results[0]
    return d['main'], d['energy'], d['type_counts'], d['errors']


def load_deck_from_file(file_path: str, card_db: dict):
    """Helper to read a file and parse it."""
    if not os.path.exists(file_path):
        return None, None, {}, [f"File {file_path} not found."]

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return extract_deck_data(content, card_db)
