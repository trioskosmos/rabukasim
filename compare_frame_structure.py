"""Compare authored vs generated ability_frame_source.json structure."""
import json

with open('data/ability_frame_source_authored.json', encoding='utf-8-sig') as f:
    authored = json.load(f)

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    generated = json.load(f)

print(f'Authored: {len(authored["abilities"])} abilities')
print(f'Generated: {len(generated["abilities"])} abilities')
print(f'Authored schema: {authored.get("schema")}')
print(f'Generated schema: {generated.get("schema")}')

# Compare first ability structure
if authored["abilities"] and generated["abilities"]:
    auth_first = authored["abilities"][0]
    gen_first = generated["abilities"][0]
    
    print('\n=== Authored first ability keys ===')
    print(sorted(auth_first.keys()))
    
    print('\n=== Generated first ability keys ===')
    print(sorted(gen_first.keys()))
    
    print('\n=== Authored first ability frames ===')
    print(auth_first.get('frames', []))
    
    print('\n=== Generated first ability frames ===')
    print(gen_first.get('frames', []))
