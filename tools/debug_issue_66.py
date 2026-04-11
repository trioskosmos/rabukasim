import json
import sys
from engine.compiler.semantic_simple import extract_semantic_simple, normalize_text

sys.stdout = open(1, 'w', encoding='utf-8', closefd=False)

with open('data/ability_semantic_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

ability = data['abilities'][66]
print(f"Original Text:")
print(ability['primary_text_jp'])
print(f"\nNormalized Text:")
print(normalize_text(ability['primary_text_jp']))
print(f"\n" + "="*80)
print(f"Semantic Extraction:")
result = extract_semantic_simple(ability['primary_text_jp'])
print(json.dumps(result, ensure_ascii=False, indent=2))
