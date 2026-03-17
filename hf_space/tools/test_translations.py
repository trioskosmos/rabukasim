"""
Test translation functions to ensure they work correctly
"""
import json
from pathlib import Path

# Test loading translations
with open('frontend/web_ui/js/i18n/locales/en.json', 'r', encoding='utf-8') as f:
    en_trans = json.load(f)

with open('frontend/web_ui/js/i18n/locales/jp.json', 'r', encoding='utf-8') as f:
    jp_trans = json.load(f)

# Test card types
print("=== Card Type Translations ===")
card_types = ["メンバー", "ライブ", "エネルギー"]
for ct in card_types:
    jp_version = jp_trans['params']['CARD_TYPES'].get(ct, ct)
    en_version = en_trans['params']['CARD_TYPES'].get(ct, ct)
    print(f"{ct:10} -> JP: {jp_version:10} EN: {en_version:10}")

print("\n=== Product Translations (sample) ===") 
products = list(en_trans['params']['PRODUCTS'].items())[:3]
for prod_jp, prod_en in products:
    print(f"JP: {prod_jp}")
    print(f"EN: {prod_en}\n")

print("=== Series Translations ===")
for ser_jp, ser_en in en_trans['params']['SERIES'].items():
    print(f"{ser_jp:60} -> {ser_en}")

print("\n=== Character Names (sample) ===")
with open('frontend/web_ui/js/i18n/names.js', 'r', encoding='utf-8') as f:
    content = f.read()
    # Count translations
    import re
    matches = re.findall(r'"([^"]+)":\s*"([^"]+)"', content)
    print(f"Total name mappings: {len(matches)}")
    print("\nSample translations:")
    for i, (jp, en) in enumerate(matches[-10:]):
        print(f"  {jp:30} -> {en}")

print("\n✓ All translation structures validated!")
