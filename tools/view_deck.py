"""
Deck Viewer Script - Visualize parsed deck information.

This script provides a rich visualization of deck data including:
- ASCII art deck layout
- Card type distribution
- Cost distribution chart
- Color-coded card categories

Usage:
    python tools/view_deck.py <deck_file>
    python tools/view_deck.py --html <html_file>
    python tools/view_deck.py --url <deck_url>
"""

import argparse
import json
import os
import sys
from collections import Counter

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from rich.columns import Columns
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better visualization: pip install rich")


def load_deck_from_file(file_path: str) -> dict:
    """Load deck from JSON or parse from HTML."""
    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif file_path.endswith(".txt") or file_path.endswith(".html"):
        from tools.deck_parser import DeckParser

        parser = DeckParser()
        deck = parser.parse_file(file_path)
        return deck.to_dict()
    else:
        raise ValueError(f"Unsupported file format: {file_path}")


def get_card_type(code: str) -> str:
    """Determine card type from code."""
    code_upper = code.upper()
    if "-E-" in code_upper or code_upper.startswith("LL-E-"):
        return "energy"
    elif "-SD" in code_upper:
        return "starter"
    elif "-PR" in code_upper:
        return "promo"
    elif "-BP" in code_upper:
        return "booster"
    elif "-RM" in code_upper:
        return "rare"
    elif "-L" in code_upper and "-L" == code_upper[-2:]:
        return "live"
    elif "-P" in code_upper and ("-P" == code_upper[-2:] or "-P+" in code_upper):
        return "member_p"
    elif "-R" in code_upper and ("-R" == code_upper[-2:] or "-R+" in code_upper):
        return "member_r"
    elif "-N" in code_upper and "-N" == code_upper[-2:]:
        return "member_n"
    else:
        return "other"


def get_card_color(code: str) -> str:
    """Determine card color from code."""
    if "PL!HS" in code:
        return "hasu"
    elif "PL!S" in code:
        return "sunshine"
    elif "PL!N" in code:
        return "nijigasaki"
    elif "PL!M" in code or "PL!-" in code:
        return "muse"
    elif "PL!L" in code:
        return "liella"
    elif "LL-" in code:
        return "general"
    else:
        return "unknown"


def create_cost_chart(costs: list[int], max_cost: int = 5) -> str:
    """Create ASCII bar chart for cost distribution."""
    cost_counts = Counter(costs)
    lines = []

    for cost in range(max_cost + 1):
        count = cost_counts.get(cost, 0)
        bar = "█" * count + "░" * (max(10, max(cost_counts.values()) if cost_counts else 10) - count)
        lines.append(f"Cost {cost}: {bar} ({count})")

    return "\n".join(lines)


def view_deck_basic(deck: dict):
    """Basic text-based deck viewer (no rich library required)."""
    print("\n" + "=" * 70)
    print(f"  DECK: {deck.get('deck_name', 'Unknown')}")
    print(f"  CODE: {deck.get('deck_code', 'N/A')}")
    print(f"  RULE: {deck.get('build_rule', 'Standard')}")
    print("=" * 70)

    # Statistics
    stats = deck.get("stats", {})
    if stats:
        print("\n[STATISTICS]")
        print("-" * 40)
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

    # Main Deck
    main_deck = deck.get("main_deck", [])
    if main_deck:
        print("\n[MAIN DECK]")
        print("-" * 40)

        # Group by type
        by_type = {}
        costs = []
        for card in main_deck:
            card_type = get_card_type(card["code"])
            if card_type not in by_type:
                by_type[card_type] = []
            by_type[card_type].append(card)

            # Get cost from internal ID info if available
            # For now, just count cards

        total = 0
        for card in main_deck:
            id_str = f" [ID:{card['internal_id']}]" if card.get("internal_id") else ""
            print(f"  {card['code']}: {card['name']} x{card['quantity']}{id_str}")
            total += card["quantity"]
        print(f"\n  Total: {total} cards")

    # Energy Deck
    energy_deck = deck.get("energy_deck", [])
    if energy_deck:
        print("\n[ENERGY DECK]")
        print("-" * 40)
        total = 0
        for card in energy_deck:
            id_str = f" [ID:{card['internal_id']}]" if card.get("internal_id") else ""
            print(f"  {card['code']}: {card['name']} x{card['quantity']}{id_str}")
            total += card["quantity"]
        print(f"\n  Total: {total} cards")

    # IDs for game engine
    main_ids = deck.get("main_deck_ids", [])
    energy_ids = deck.get("energy_deck_ids", [])

    print("\n[GAME ENGINE IDS]")
    print("-" * 40)
    print(f"  Main Deck IDs ({len(main_ids)}): {main_ids[:10]}{'...' if len(main_ids) > 10 else ''}")
    print(f"  Energy Deck IDs ({len(energy_ids)}): {energy_ids}")

    print("\n" + "=" * 70)


def view_deck_rich(deck: dict):
    """Rich-based deck viewer with colors and tables."""
    console = Console()

    # Header
    header = Panel(
        f"[bold cyan]{deck.get('deck_name', 'Unknown Deck')}[/bold cyan]\n"
        f"Code: [yellow]{deck.get('deck_code', 'N/A')}[/yellow] | "
        f"Rule: [green]{deck.get('build_rule', 'Standard')}[/green]",
        title="Deck Viewer",
        border_style="blue",
    )
    console.print(header)

    # Statistics Panel
    stats = deck.get("stats", {})
    if stats:
        stats_table = Table(title="Statistics", show_header=False)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="yellow", justify="right")
        for key, value in stats.items():
            stats_table.add_row(key.replace("_", " ").title(), str(value))
        console.print(stats_table)

    # Main Deck Table
    main_deck = deck.get("main_deck", [])
    if main_deck:
        main_table = Table(title="Main Deck")
        main_table.add_column("Code", style="cyan", width=20)
        main_table.add_column("Name", style="white", width=30)
        main_table.add_column("Qty", style="yellow", justify="center", width=4)
        main_table.add_column("ID", style="dim", width=6)
        main_table.add_column("Type", style="green", width=8)

        total = 0
        for card in main_deck:
            card_type = get_card_type(card["code"])
            id_str = str(card["internal_id"]) if card.get("internal_id") else "-"
            main_table.add_row(card["code"], card["name"][:30], str(card["quantity"]), id_str, card_type)
            total += card["quantity"]

        main_table.add_section()
        main_table.add_row("", "TOTAL", str(total), "", "", style="bold")
        console.print(main_table)

    # Energy Deck Table
    energy_deck = deck.get("energy_deck", [])
    if energy_deck:
        energy_table = Table(title="Energy Deck")
        energy_table.add_column("Code", style="cyan", width=20)
        energy_table.add_column("Name", style="white", width=30)
        energy_table.add_column("Qty", style="yellow", justify="center", width=4)
        energy_table.add_column("ID", style="dim", width=6)

        total = 0
        for card in energy_deck:
            id_str = str(card["internal_id"]) if card.get("internal_id") else "-"
            energy_table.add_row(card["code"], card["name"][:30], str(card["quantity"]), id_str)
            total += card["quantity"]

        energy_table.add_section()
        energy_table.add_row("", "TOTAL", str(total), "", style="bold")
        console.print(energy_table)

    # Card Distribution
    if main_deck:
        dist_table = Table(title="Card Distribution")
        dist_table.add_column("Category", style="cyan")
        dist_table.add_column("Count", style="yellow", justify="right")
        dist_table.add_column("Bar", style="green")

        type_counts = Counter(get_card_type(c["code"]) for c in main_deck for _ in range(c["quantity"]))
        max_count = max(type_counts.values()) if type_counts else 1

        for card_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            bar = "█" * count + "░" * (max_count - count)
            dist_table.add_row(card_type, str(count), bar)

        console.print(dist_table)

    # Game Engine IDs
    main_ids = deck.get("main_deck_ids", [])
    energy_ids = deck.get("energy_deck_ids", [])

    ids_panel = Panel(
        f"[bold]Main Deck IDs ({len(main_ids)}):[/bold]\n"
        f"{main_ids[:20]}{'...' if len(main_ids) > 20 else ''}\n\n"
        f"[bold]Energy Deck IDs ({len(energy_ids)}):[/bold]\n"
        f"{energy_ids}",
        title="Game Engine IDs",
        border_style="yellow",
    )
    console.print(ids_panel)


def main():
    parser = argparse.ArgumentParser(
        description="Visualize Love Live TCG deck information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tools/view_deck.py deck.json
    python tools/view_deck.py tests/decktest.txt
    python tools/view_deck.py --url https://decklog.bushiroad.com/view/XXXXX
        """,
    )
    parser.add_argument("file", nargs="?", help="Deck file (JSON or HTML)")
    parser.add_argument("--url", help="DECK LOG URL to fetch and view")
    parser.add_argument("--html", help="Parse HTML file and view")
    parser.add_argument("--save-json", help="Save parsed deck as JSON")
    parser.add_argument("--simple", action="store_true", help="Use simple text output (no colors)")

    args = parser.parse_args()

    deck = None

    if args.url:
        from tools.deck_parser import DeckParser

        deck_parser = DeckParser()
        parsed = deck_parser.parse_url(args.url)
        deck = parsed.to_dict()
    elif args.html:
        from tools.deck_parser import DeckParser

        deck_parser = DeckParser()
        parsed = deck_parser.parse_file(args.html)
        deck = parsed.to_dict()
    elif args.file:
        deck = load_deck_from_file(args.file)
    else:
        parser.print_help()
        return

    # Save if requested
    if args.save_json:
        with open(args.save_json, "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=2)
        print(f"Saved deck to {args.save_json}")

    # View deck
    if args.simple or not RICH_AVAILABLE:
        view_deck_basic(deck)
    else:
        view_deck_rich(deck)


if __name__ == "__main__":
    main()
