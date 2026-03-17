import json
import os

with open(r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\frontend\web_ui\js\i18n\locales\en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

with open(r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\frontend\web_ui\js\i18n\locales\jp.json', 'r', encoding='utf-8') as f:
    jp = json.load(f)

output = []

def compare_dicts(d1, d2, path=""):
    keys1 = set(d1.keys())
    keys2 = set(d2.keys())
    
    only1 = sorted(list(keys1 - keys2))
    only2 = sorted(list(keys2 - keys1))
    common = sorted(list(keys1 & keys2))
    
    if only1:
        output.append(f"Only in EN at {path}: {only1}")
    if only2:
        output.append(f"Only in JP at {path}: {only2}")
        
    for k in common:
        if isinstance(d1[k], dict) and isinstance(d2[k], dict):
            compare_dicts(d1[k], d2[k], path + "." + k if path else k)
        elif type(d1[k]) != type(d2[k]):
            output.append(f"Type mismatch at {path}.{k}: EN={type(d1[k])}, JP={type(d2[k])}")

output.append("--- Comparison START ---")
compare_dicts(en, jp)
output.append("--- Comparison END ---")

with open('compare_results.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
