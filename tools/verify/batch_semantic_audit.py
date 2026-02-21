
import json
import re
import os
import sys

# Force UTF-8 for Windows consoles
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Semantic Audit Tool
# --------------------
# This script iterates through all cards, extracts their intended meaning from JP text,
# and flags discrepancies with existing pseudocode.

def extract_meaning(card_id, raw_text):
    """
    Precision Semantic Extraction.
    Maps JP Keywords to 'Vocabulary of Truth' tags.
    """
    expectations = []
    
    # 1. Cost Extraction
    energy_cost = raw_text.count("icon_energy.png")
    # PRECISION FIX: Distinguish between Member Sacrifice and Hand Discard
    is_sacrifice = "このメンバーをステージから控え室に置く" in raw_text or "このメンバーを控え室に置く" in raw_text
    is_hand_discard = "手札を" in raw_text and "控え室に置く" in raw_text
    
    if energy_cost > 0:
        expectations.append({"tag": "ENERGY_PAID", "value": energy_cost})
    if is_sacrifice:
        expectations.append({"tag": "MEMBER_SACRIFICED", "value": True})
    if is_hand_discard:
        expectations.append({"tag": "HAND_DISCARDED", "value": True})

    # 2. Effect Extraction
    if "手札に加える" in raw_text or "引く" in raw_text:
        expectations.append({"tag": "HAND_DELTA", "value": 1})
    if "スコアを＋" in raw_text or "スコアを+" in raw_text:
        # Attempt to find the number (simple version)
        match = re.search(r'スコアを[＋+]([0-9１２３４５])', raw_text)
        val = 1
        if match:
            v_str = match.group(1)
            # Handle full-width
            v_map = {"１": 1, "２": 2, "３": 3, "４": 4, "５": 5}
            val = int(v_map.get(v_str, v_str))
        expectations.append({"tag": "SCORE_DELTA", "value": val})
        
    return expectations

def run_batch_audit():
    print("🚀 Starting Precision Semantic Audit (Cost & Effect Divergence)...")
    
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)
    
    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        pseudo = json.load(f)
        
    mismatches = []
    total = len(cards)
    count = 0
    
    for cid, data in cards.items():
        count += 1
        text = data.get("ability", "")
        if not text: continue
        
        # 1. Oracle interprets meaning
        meanings = extract_meaning(cid, text)
        
        # 2. Get Implemented Pseudocode
        p_data = pseudo.get(cid, {})
        p_text = p_data.get("pseudocode", "").upper()
        
        # 3. Detect Divergences
        for m in meanings:
            tag = m["tag"]
            val = m["value"] if "value" in m else True
            
            error = None
            if tag == "ENERGY_PAID" and "PAY_ENERGY" not in p_text:
                # SPECIAL CASE: Sometimes energy is in Trigger for non-activated (Live Start E icons)
                if "ENERGY" not in p_text:
                    error = f"MISSING ENERGY COST ({val})"
            elif tag == "MEMBER_SACRIFICED" and "MOVE_TO_DISCARD" not in p_text:
                # Ensure it's not a False Positive against discard
                error = "MISSING SACRIFICE COST"
            elif tag == "HAND_DISCARDED" and "DISCARD_HAND" not in p_text and "DISCARD" not in p_text:
                error = "MISSING HAND DISCARD COST"
            elif tag == "SCORE_DELTA" and "BOOST_SCORE" not in p_text and "SCORE" not in p_text:
                error = f"MISSING SCORE EFFECT (+{val})"
            elif tag == "HAND_DELTA" and all(x not in p_text for x in ["HAND", "DRAW", "RECOVER_LIVE", "RECOVER_MEMBER"]):
                error = "MISSING DRAW/HAND EFFECT"

            if error:
                mismatches.append({
                    "id": cid,
                    "error": error,
                    "text": text,
                    "implemented": p_text
                })

    print(f"\n✅ Audit Complete. Found {len(mismatches)} Precision Mismatches.")
    
    # Save Report
    with open("reports/semantic_audit_report.json", "w", encoding="utf-8") as f:
        json.dump(mismatches, f, indent=2, ensure_ascii=False)
    
    # Print Top 15 Bugs
    print("\n--- 🚩 CRITICAL LOGIC DIVERGENCES FOUND ---")
    for m in mismatches[:15]:
        print(f"[{m['id']}] {m['error']}")
        print(f"   Implemented: {m['implemented']}")
        print("-" * 40)

if __name__ == "__main__":
    run_batch_audit()
