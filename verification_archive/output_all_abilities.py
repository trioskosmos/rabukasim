import json
from engine.compiler.semantic_simple import extract_semantic_simple

with open('data/ability_semantic_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

with open('ability_extraction_review.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("COMPLETE EXTRACTION RESULTS FOR ALL 612 ABILITIES\n")
    f.write("="*80 + "\n")
    
    for i, ability in enumerate(abilities):
        text = ability['primary_text_jp']
        result = extract_semantic_simple(text)
        
        f.write(f"\n{'='*80}\n")
        f.write(f"Ability {i+1}/{len(abilities)} - Index: {ability['ability_index']}\n")
        f.write(f"Trigger: {ability['trigger']}\n")
        f.write(f"{'='*80}\n")
        f.write(f"Original Text:\n{text}\n")
        f.write(f"\nExtraction:\n")
        
        if isinstance(result, list):
            f.write(f"[Multi-trigger: {len(result)} abilities]\n")
            for j, r in enumerate(result):
                f.write(f"\n  Ability {j+1}:\n")
                f.write(f"    Trigger: {r['when']}\n")
                f.write(f"    Condition: {r['if']}\n")
                f.write(f"    Actions: {len(r['then'])}\n")
                for action in r['then']:
                    f.write(f"      - {action['type']}: {action['matched'][:60]}...\n")
                f.write(f"    Choices: {len(r['choices'])}\n")
                f.write(f"    Sequences: {len(r['sequences'])}\n")
                f.write(f"    Costs: {len(r['costs'])}\n")
                f.write(f"    With: {r['with']}\n")
        else:
            f.write(f"  Trigger: {result['when']}\n")
            f.write(f"  Condition: {result['if']}\n")
            f.write(f"  Actions: {len(result['then'])}\n")
            for action in result['then']:
                f.write(f"    - {action['type']}: {action['matched'][:60]}...\n")
            f.write(f"  Choices: {len(result['choices'])}\n")
            f.write(f"  Sequences: {len(result['sequences'])}\n")
            f.write(f"  Costs: {len(result['costs'])}\n")
            f.write(f"  With: {result['with']}\n")
        
        # Brief verification
        if isinstance(result, list):
            has_trigger = any(r['when'] for r in result)
            has_content = any(len(r['then']) > 0 or len(r['costs']) > 0 or r['if'] for r in result)
        else:
            has_trigger = result['when'] is not None
            has_content = len(result['then']) > 0 or len(result['costs']) > 0 or result['if']
        
        if has_trigger and has_content:
            f.write(f"\n  ✓ PASS: Has trigger and meaningful content\n")
        elif not has_trigger:
            f.write(f"\n  ⚠ WARNING: No trigger detected\n")
        elif not has_content:
            f.write(f"\n  ⚠ WARNING: No meaningful content (actions/condition/cost)\n")
    
    f.write(f"\n{'='*80}\n")
    f.write("REVIEW COMPLETE\n")
    f.write("="*80 + "\n")

print("Extraction review written to ability_extraction_review.txt")
