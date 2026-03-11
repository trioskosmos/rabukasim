
import json
import os

PROJECT_ROOT = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy'

def normalize_code(code):
    if not code: return ""
    return code.strip().replace('＋', "+").replace('－', "-").replace('ー', "-").upper()

def load_named_deck(content, db_members, db_lives, db_energy):
    main = []
    energy = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'): continue
        
        current_code = ""
        current_count = 1
        line_lower = line.lower()
        if " x " in line_lower:
            idx = line_lower.find(" x ")
            part1 = line[:idx].strip()
            part2 = line[idx+3:].strip()
            
            try:
                current_count = int(part1)
                current_code = part2
            except:
                try:
                    current_count = int(part2)
                    current_code = part1
                except:
                    current_code = line
        else:
            current_code = line
            
        if not current_code: continue
        
        if current_code.upper().endswith("-PE") or current_code.upper().endswith("-PE+"):
            for _ in range(current_count):
                energy.append(current_code)
        else:
            for _ in range(current_count):
                main.append(current_code)
                
    # Now resolve
    resolved_members = []
    resolved_lives = []
    resolved_energy = []
    
    for code in main:
        norm_code = normalize_code(code)
        found = False
        
        # Match members
        for mid, mdata in db_members.items():
            if normalize_code(mdata.get('card_no', '')) == norm_code:
                resolved_members.append(mid)
                found = True
                break
        
        if not found:
            # Match lives
            for lid, ldata in db_lives.items():
                if normalize_code(ldata.get('card_no', '')) == norm_code:
                    resolved_lives.append(lid)
                    found = True
                    break
        
        if not found:
            print(f"FAILED TO RESOLVE: '{code}' (normalized: '{norm_code}')")

    return resolved_members, resolved_lives

def main():
    with open(os.path.join(PROJECT_ROOT, 'data', 'cards.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # In reality, the database is split. Let's filter by type.
    members = {k: v for k, v in data.items() if v.get('type') == 'メンバー'}
    lives = {k: v for k, v in data.items() if v.get('type') == 'ライブ'}
    energy = {k: v for k, v in data.items() if v.get('type') == 'エネルギー'}

    deck_path = os.path.join(PROJECT_ROOT, 'ai', 'decks2', 'vividworld.txt')
    with open(deck_path, 'r', encoding='utf-8') as f:
        content = f.read()

    res_m, res_l = load_named_deck(content, members, lives, energy)
    
    print(f"\nResults:")
    print(f"Resolved Members: {len(res_m)}")
    print(f"Resolved Lives: {len(res_l)}")
    print(f"Total Main: {len(res_m) + len(res_l)}")
    
    # Check unique resolved
    print(f"Unique Members: {len(set(res_m))}")
    print(f"Unique Lives: {len(set(res_l))}")

if __name__ == "__main__":
    main()
