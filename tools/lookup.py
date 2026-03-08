import json
import os
import sys
import argparse

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Centralized Metadata & Card Lookup Tool for LovecaSim")
    parser.add_argument("query", help="ID, Card No, or Name to look up")
    parser.add_argument("--domain", help="Filter metadata by domain (e.g. opcodes, triggers)")
    parser.add_argument("--cards", action="store_true", help="Search in card data only")
    parser.add_argument("--meta", action="store_true", help="Search in metadata only")
    args = parser.parse_args()

    metadata = load_json("data/metadata.json")
    cards_data = load_json("data/cards.json")
    query = args.query.upper()
    
    # Try numeric lookup
    is_numeric = query.isdigit()
    query_int = int(query) if is_numeric else None

    # Meta Lookup
    if not args.cards:
        meta_results = []
        domains = [args.domain] if args.domain else ["opcodes", "conditions", "costs", "choices", "triggers", "character_ids", "group_ids", "unit_ids", "phases", "action_bases"]
        
        for domain in domains:
            data = metadata.get(domain, {})
            for name, val in data.items():
                if is_numeric:
                    if val == query_int:
                        meta_results.append((domain, name, val))
                else:
                    if query in name.upper():
                        meta_results.append((domain, name, val))
        
        if meta_results:
            print(f"\n--- Metadata Results for '{args.query}' ---")
            print(f"{'Domain':<15} | {'Name':<35} | {'Value':<10}")
            print("-" * 65)
            for domain, name, val in meta_results:
                print(f"{domain:<15} | {name:<35} | {val:<10}")

    # Card Lookup
    if not args.meta:
        card_results = []
        # Search members
        for card in cards_data.get("members", []):
            match = False
            if is_numeric and card.get("id") == query_int: match = True
            elif query in card.get("card_no", "").upper(): match = True
            elif query in card.get("name", "").upper(): match = True
            
            if match:
                card_results.append(("Member", card.get("card_no"), card.get("name"), card.get("id")))

        # Search lives
        for card in cards_data.get("lives", []):
            match = False
            if is_numeric and card.get("id") == query_int: match = True
            elif query in card.get("card_no", "").upper(): match = True
            elif query in card.get("name", "").upper(): match = True
            
            if match:
                card_results.append(("Live", card.get("card_no"), card.get("name"), card.get("id")))

        if card_results:
            print(f"\n--- Card Results for '{args.query}' ---")
            print(f"{'Type':<10} | {'Card No':<20} | {'Name':<30} | {'ID':<10}")
            print("-" * 75)
            for ctype, cno, name, cid in card_results[:20]: # Cap at 20
                print(f"{ctype:<10} | {cno:<20} | {name:<30} | {cid:<10}")
            if len(card_results) > 20:
                print(f"... and {len(card_results)-20} more.")

if __name__ == "__main__":
    main()
