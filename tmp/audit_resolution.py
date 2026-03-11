
import json
import os

PROJECT_ROOT = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy'

def normalize(s):
    if not s: return ""
    return s.strip().replace('＋', "+").replace('－', "-").replace('ー', "-").upper()

def main():
    target_code = "PL!N-BP3-020-N"
    norm_target = normalize(target_code)
    
    with open(os.path.join(PROJECT_ROOT, 'data', 'cards.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    found = False
    for mid, mdata in data.items():
        c_no = mdata.get('card_no', '')
        norm_c_no = normalize(c_no)
        if norm_c_no == norm_target:
            print(f"MATCH FOUND!")
            print(f"  Key: '{mid}'")
            print(f"  card_no: '{c_no}'")
            print(f"  norm_c_no: '{norm_c_no}'")
            print(f"  Type: {mdata.get('type')}")
            found = True
            break
            
    if not found:
        print(f"NO MATCH FOUND for '{target_code}'")

if __name__ == "__main__":
    main()
