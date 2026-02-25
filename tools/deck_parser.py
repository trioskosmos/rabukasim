"""
Improved Deck Parser for Love Live TCG Deck Log HTML pages.

Parses deck information from Bushiroad DECK LOG HTML pages and extracts:
- Deck name and code
- Main deck cards with quantities
- Energy deck cards with quantities
- Statistics (member count, live count, blade count)
- Converts card numbers to internal IDs

Usage:
    python tools/deck_parser.py <html_file> [--output json|text|deck]
    python tools/deck_parser.py --url <deck_url> [--output json|text|deck]
"""

import os
import re
import sys
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


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
    main_deck: list = field(default_factory=list)
    energy_deck: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    main_deck_ids: list = field(default_factory=list)
    energy_deck_ids: list = field(default_factory=list)
    
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
    """Parser for Bushiroad DECK LOG HTML pages."""
    
    def __init__(self, use_compiled_data: bool = True):
        self.card_no_to_id: dict[str, int] = {}
        self.card_id_to_info: dict[int, dict] = {}
        if use_compiled_data:
            self._build_card_mappings()
    
    def _build_card_mappings(self):
        """Build card number to internal ID mappings from compiled data."""
        compiled_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "cards_compiled.json"
        )
        
        if not os.path.exists(compiled_path):
            print(f"Warning: Compiled data not found at {compiled_path}")
            return
        
        try:
            with open(compiled_path, "r", encoding="utf-8") as f:
                compiled_data = json.load(f)
            
            count = 0
            for db_name in ["member_db", "live_db", "energy_db"]:
                if db_name in compiled_data:
                    for internal_id, card_data in compiled_data[db_name].items():
                        card_no = card_data.get("card_no", "")
                        if card_no:
                            self.card_no_to_id[card_no] = int(internal_id)
                            self.card_id_to_info[int(internal_id)] = card_data
                            count += 1
            
            print(f"Loaded {count} card mappings from compiled data")
        except Exception as e:
            print(f"Error loading compiled data: {e}")
    
    def parse_html(self, html_content: str) -> DeckInfo:
        """Parse HTML content and extract deck information."""
        deck = DeckInfo()
        
        # Extract deck name
        deck.deck_name = self._extract_deck_name(html_content)
        
        # Extract deck code
        deck.deck_code = self._extract_deck_code(html_content)
        
        # Extract build rule
        deck.build_rule = self._extract_build_rule(html_content)
        
        # Extract statistics
        deck.stats = self._extract_stats(html_content)
        
        # Extract main deck and energy deck sections
        main_section, energy_section = self._split_deck_sections(html_content)
        
        # Parse cards from each section
        deck.main_deck = self._parse_cards_from_section(main_section)
        deck.energy_deck = self._parse_cards_from_section(energy_section)
        
        # Convert to internal IDs
        deck.main_deck_ids = self._convert_to_ids(deck.main_deck)
        deck.energy_deck_ids = self._convert_to_ids(deck.energy_deck)
        
        return deck
    
    def _extract_deck_name(self, html: str) -> str:
        """Extract deck name from HTML."""
        # Pattern: <h2>デッキ名「新蓮ノ空」のデッキ</h2>
        match = re.search(r'デッキ名「([^」]+)」', html)
        if match:
            return match.group(1)
        
        # Alternative pattern from title
        match = re.search(r'<title>([^<]+)\s*｜', html)
        if match:
            return match.group(1).strip()
        
        return "Unknown Deck"
    
    def _extract_deck_code(self, html: str) -> str:
        """Extract deck code from HTML."""
        # Pattern: デッキコード： 158K4
        match = re.search(r'デッキコード[：:]\s*([A-Za-z0-9]+)', html)
        if match:
            return match.group(1)
        return ""
    
    def _extract_build_rule(self, html: str) -> str:
        """Extract build rule from HTML."""
        # Pattern: 構築ルール：\n<span>スタンダード</span>
        match = re.search(r'構築ルール[：:]\s*<span>([^<]+)</span>', html)
        if match:
            return match.group(1)
        return ""
    
    def _extract_stats(self, html: str) -> dict:
        """Extract deck statistics from HTML."""
        stats = {}
        
        # Member count: メンバー</span> ： <span>48</span>
        match = re.search(r'メンバー</span>\s*[：:]\s*<span>(\d+)</span>', html)
        if match:
            stats["member_count"] = int(match.group(1))
        
        # Live count: ライブ</span> ： <span>12</span>
        match = re.search(r'ライブ</span>\s*[：:]\s*<span>(\d+)</span>', html)
        if match:
            stats["live_count"] = int(match.group(1))
        
        # Blade count: ブレード...の数</span> ： <span>94</span>
        match = re.search(r'ブレード[^<]*の数</span>\s*[：:]\s*<span>(\d+)</span>', html)
        if match:
            stats["blade_count"] = int(match.group(1))
        
        # Energy count: エネルギー</span> ： <span>12</span>
        match = re.search(r'エネルギー</span>\s*[：:]\s*<span>(\d+)</span>', html)
        if match:
            stats["energy_count"] = int(match.group(1))
        
        # Total cards: from graph-sum-value
        match = re.search(r'<span class="graph-sum-value">(\d+)</span>', html)
        if match:
            stats["total_cards"] = int(match.group(1))
        
        return stats
    
    def _split_deck_sections(self, html: str) -> tuple[str, str]:
        """Split HTML into main deck and energy deck sections."""
        # Find main deck section
        main_match = re.search(r'<h3>メインデッキ</h3>(.*?)(?:<h3>|<footer|$)', html, re.DOTALL)
        main_section = main_match.group(1) if main_match else ""
        
        # Find energy deck section
        energy_match = re.search(r'<h3>エネルギーデッキ</h3>(.*?)(?:<h3>|<footer|$)', html, re.DOTALL)
        energy_section = energy_match.group(1) if energy_match else ""
        
        return main_section, energy_section
    
    def _parse_cards_from_section(self, section_html: str) -> list[CardEntry]:
        """Parse card entries from a deck section."""
        cards = []
        
        # Split by card-item divs
        items = section_html.split('class="card-item')
        
        for item in items[1:]:  # Skip first empty part
            # Extract card code and name from title attribute
            # Pattern: title="PL!HS-bp1-003-P : 乙宗 梢"
            code_match = re.search(r'title="([^"]+)\s*:\s*([^"]+)"', item)
            if not code_match:
                continue
            
            code = code_match.group(1).strip()
            name = code_match.group(2).strip()
            
            # Extract quantity
            qty_match = re.search(r'<span class="num">(\d+)</span>', item)
            quantity = int(qty_match.group(1)) if qty_match else 1
            
            # Get internal ID if available
            internal_id = self.card_no_to_id.get(code)
            
            cards.append(CardEntry(
                code=code,
                name=name,
                quantity=quantity,
                internal_id=internal_id
            ))
        
        return cards
    
    def _convert_to_ids(self, cards: list[CardEntry]) -> list[int]:
        """Convert card entries to list of internal IDs (with quantities)."""
        ids = []
        for card in cards:
            if card.internal_id is not None:
                ids.extend([card.internal_id] * card.quantity)
            else:
                print(f"Warning: No ID mapping for card {card.code}")
        return ids
    
    def parse_file(self, file_path: str) -> DeckInfo:
        """Parse deck from HTML file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.parse_html(content)
    
    def parse_url(self, url: str) -> DeckInfo:
        """Parse deck from URL (requires requests library)."""
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
        # Simple deck format for game engine
        lines = []
        lines.append(f"# Deck: {deck.deck_name}")
        lines.append(f"# Code: {deck.deck_code}")
        lines.append("")
        lines.append("# Main Deck")
        for card in deck.main_deck:
            lines.append(f"{card.code} x{card.quantity}")
        lines.append("")
        lines.append("# Energy Deck")
        for card in deck.energy_deck:
            lines.append(f"{card.code} x{card.quantity}")
        return "\n".join(lines)
    
    else:  # text format
        lines = []
        lines.append("=" * 60)
        lines.append(f"Deck Name: {deck.deck_name}")
        lines.append(f"Deck Code: {deck.deck_code}")
        lines.append(f"Build Rule: {deck.build_rule}")
        lines.append("=" * 60)
        
        if deck.stats:
            lines.append("\n[Statistics]")
            for key, value in deck.stats.items():
                lines.append(f"  {key}: {value}")
        
        lines.append("\n[Main Deck]")
        total_main = 0
        for card in deck.main_deck:
            id_str = f" [ID:{card.internal_id}]" if card.internal_id else ""
            lines.append(f"  {card.code}: {card.name} x{card.quantity}{id_str}")
            total_main += card.quantity
        lines.append(f"  Total: {total_main} cards")
        
        if deck.energy_deck:
            lines.append("\n[Energy Deck]")
            total_energy = 0
            for card in deck.energy_deck:
                id_str = f" [ID:{card.internal_id}]" if card.internal_id else ""
                lines.append(f"  {card.code}: {card.name} x{card.quantity}{id_str}")
                total_energy += card.quantity
            lines.append(f"  Total: {total_energy} cards")
        
        lines.append("\n" + "=" * 60)
        lines.append(f"Main Deck IDs: {deck.main_deck_ids}")
        lines.append(f"Energy Deck IDs: {deck.energy_deck_ids}")
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Parse Love Live TCG deck from DECK LOG HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tools/deck_parser.py tests/decktest.txt
    python tools/deck_parser.py tests/decktest.txt --output json
    python tools/deck_parser.py tests/decktest.txt --save deck.json
    python tools/deck_parser.py --url https://decklog.bushiroad.com/view/XXXXX
        """
    )
    parser.add_argument("file", nargs="?", help="HTML file to parse")
    parser.add_argument("--url", help="DECK LOG URL to fetch and parse")
    parser.add_argument("--output", "-o", choices=["text", "json", "deck"], 
                        default="text", help="Output format")
    parser.add_argument("--save", "-s", help="Save output to file")
    parser.add_argument("--ids-only", action="store_true",
                        help="Output only internal IDs (for game engine)")
    
    args = parser.parse_args()
    
    deck_parser = DeckParser()
    
    if args.url:
        deck = deck_parser.parse_url(args.url)
    elif args.file:
        deck = deck_parser.parse_file(args.file)
    else:
        parser.print_help()
        return
    
    if args.ids_only:
        print(json.dumps({
            "main": deck.main_deck_ids,
            "energy": deck.energy_deck_ids
        }))
    else:
        output = format_output(deck, args.output)
        print(output)
    
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            if args.save.endswith(".json"):
                json.dump(deck.to_dict(), f, ensure_ascii=False, indent=2)
            else:
                f.write(format_output(deck, args.output))
        print(f"\nSaved to {args.save}")


if __name__ == "__main__":
    main()
