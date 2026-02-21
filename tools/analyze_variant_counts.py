import json
from collections import defaultdict

def analyze_variants():
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Map Logic ID -> List of (Card No, Rarity, Variant Index)
    logic_groups = defaultdict(list)
    
    # Helper to process DB
    def process_db(db):
        for packed_id_str, card in db.items():
            packed_id = int(packed_id_str)
            logic_id = packed_id & 0x07FF # 11 bits
            variant_idx = packed_id >> 11 # 5 bits
            
            logic_groups[logic_id].append({
                "card_no": card["card_no"],
                "name": card["name"],
                "rare": card.get("rare", "N/A"),
                "variant_idx": variant_idx
            })

    process_db(data.get("member_db", {}))
    process_db(data.get("live_db", {}))
    
    # Sort by variant count (descending)
    sorted_groups = sorted(logic_groups.items(), key=lambda x: len(x[1]), reverse=True)
    
    print(f"{'Count':<5} | {'Logic ID':<8} | {'Name (Sample)':<30} | {'Max Index':<10}")
    print("-" * 70)
    
    for logic_id, variants in sorted_groups:
        if len(variants) < 2: continue # Skip singletons to reduce noise
        
        name = variants[0]["name"]
        max_idx = max(v["variant_idx"] for v in variants)
        count = len(variants)
        
        print(f"{count:<5} | {logic_id:<8} | {name:<30} | {max_idx:<10}")
        
        # Breakdown for high variance cards
        if count >= 10:
            print("  Variants:")
            for v in sorted(variants, key=lambda x: x["variant_idx"]):
                 print(f"    [{v['variant_idx']:>2}] {v['card_no']:<20} ({v['rare']})")
            print("-" * 30)

if __name__ == "__main__":
    analyze_variants()
