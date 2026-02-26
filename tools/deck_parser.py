"""
Improved Deck Parser for Love Live TCG Deck Log HTML pages.

Refactored to use engine.game.deck_utils.UnifiedDeckParser.
"""

import os
import sys
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from pathlib import Path

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.game.deck_utils import UnifiedDeckParser


@dataclass
class CardEntry:
    """Represents a single card entry with code, name, and quantity."""
    code: str
    name: str
    quantity: int
    internal_id: Optional[int] = None


@dataclass
class DeckInfo:
    """Represents a complete deck with all metadata."""
    deck_name: str = ""
    deck_code: str = ""
    build_rule: str = ""
    main_deck: List[CardEntry] = field(default_factory=list)
    energy_deck: List[CardEntry] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    main_deck_ids: List[int] = field(default_factory=list)
    energy_deck_ids: List[int] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "deck_name": self.deck_name,
            "deck_code": self.deck_code,
            "build_rule": self.build_rule,
            "main_deck": [asdict(c) for c in self.main_deck],
            "energy_deck": [asdict(c) for c in self.energy_deck],
            "stats": self.stats,
            "main_deck_ids": self.main_deck_ids,
            "energy_deck_ids": self.energy_deck_ids,
        }


class DeckParser:
    """Parser for Bushiroad DECK LOG HTML pages using UnifiedDeckParser."""
    
    def __init__(self, use_compiled_data: bool = True):
        self.card_db = self._load_card_db()
        self.unified_parser = UnifiedDeckParser(self.card_db)
        
    def _load_card_db(self) -> Dict:
        """Load card database."""
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "cards.json")
        if not os.path.exists(db_path):
            return {}
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def parse_html(self, html_content: str) -> DeckInfo:
        """Parse HTML content and extract deck information."""
        # Use unified parser to get the raw data
        results = self.unified_parser.extract_from_content(html_content)
        if not results:
            return DeckInfo()
            
        raw_deck = results[0]
        deck = DeckInfo()
        deck.deck_name = raw_deck.get('name', 'Unknown Deck')
        
        # Extract metadata specifically if present (since UnifiedDeckParser is more generic)
        deck.deck_code = self._extract_regex(html_content, r'デッキコード[：:]\s*([A-Za-z0-9]+)')
        deck.build_rule = self._extract_regex(html_content, r'構築ルール[：:]\s*<span>([^<]+)</span>')
        
        # Stats
        deck.stats = raw_deck.get('type_counts', {})
        
        # Map to CardEntry objects for main deck
        main_counts = Counter(raw_deck['main'])
        for code, qty in main_counts.items():
            card_data = self.unified_parser.resolve_card(code)
            deck.main_deck.append(CardEntry(
                code=code,
                name=card_data.get('name', 'Unknown'),
                quantity=qty,
                internal_id=card_data.get('card_id')
            ))
            if card_data.get('card_id'):
                deck.main_deck_ids.extend([card_data['card_id']] * qty)

        # Map to CardEntry objects for energy deck
        energy_counts = Counter(raw_deck['energy'])
        for code, qty in energy_counts.items():
            card_data = self.unified_parser.resolve_card(code)
            deck.energy_deck.append(CardEntry(
                code=code,
                name=card_data.get('name', 'Unknown'),
                quantity=qty,
                internal_id=card_data.get('card_id')
            ))
            if card_data.get('card_id'):
                deck.energy_deck_ids.extend([card_data['card_id']] * qty)
                
        return deck

    def _extract_regex(self, content: str, pattern: str) -> str:
        match = re.search(pattern, content)
        return match.group(1) if match else ""

    def parse_file(self, file_path: str) -> DeckInfo:
        """Parse deck from HTML file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.parse_html(content)
    
    def parse_url(self, url: str) -> DeckInfo:
        """Parse deck from URL."""
        try:
            import requests
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return self.parse_html(response.text)
        except ImportError:
            raise RuntimeError("requests library required for URL parsing")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch URL: {e}")


def format_output(deck: DeckInfo, format_type: str = "text") -> str:
    """Format deck information for output."""
    if format_type == "json":
        return json.dumps(deck.to_dict(), ensure_ascii=False, indent=2)
    
    elif format_type == "deck":
        lines = [f"# Deck: {deck.deck_name}", f"# Code: {deck.deck_code}", ""]
        lines.append("# Main Deck")
        for card in deck.main_deck:
            lines.append(f"{card.code} x{card.quantity}")
        lines.append("\n# Energy Deck")
        for card in deck.energy_deck:
            lines.append(f"{card.code} x{card.quantity}")
        return "\n".join(lines)
    
    else:  # text format
        lines = ["=" * 60, f"Deck Name: {deck.deck_name}", f"Deck Code: {deck.deck_code}", f"Build Rule: {deck.build_rule}", "=" * 60]
        lines.append(f"\n[Statistics]\n  {deck.stats}")
        lines.append("\n[Main Deck]")
        for card in sorted(deck.main_deck, key=lambda x: x.code):
            id_str = f" [ID:{card.internal_id}]" if card.internal_id else ""
            lines.append(f"  {card.code}: {card.name} x{card.quantity}{id_str}")
        lines.append("\n[Energy Deck]")
        for card in sorted(deck.energy_deck, key=lambda x: x.code):
            id_str = f" [ID:{card.internal_id}]" if card.internal_id else ""
            lines.append(f"  {card.code}: {card.name} x{card.quantity}{id_str}")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Parse Love Live TCG deck from DECK LOG HTML")
    parser.add_argument("file", nargs="?", help="HTML file to parse")
    parser.add_argument("--url", help="DECK LOG URL to fetch and parse")
    parser.add_argument("--output", "-o", choices=["text", "json", "deck"], default="text")
    parser.add_argument("--save", "-s", help="Save output to file")
    
    args = parser.parse_args()
    deck_parser = DeckParser()
    
    if args.url:
        deck = deck_parser.parse_url(args.url)
    elif args.file:
        deck = deck_parser.parse_file(args.file)
    else:
        parser.print_help()
        return
    
    output = format_output(deck, args.output)
    print(output)
    
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            if args.save.endswith(".json"):
                json.dump(deck.to_dict(), f, ensure_ascii=False, indent=2)
            else:
                f.write(output)
        print(f"\nSaved to {args.save}")


if __name__ == "__main__":
    main()
