import json

# Try aggressive recovery
with open('data/abilities_extracted_from_cards_backup.json', 'rb') as f:
    raw = f.read()

# Try UTF-16-LE with surrogate escape to handle invalid sequences
try:
    decoded = raw.decode('utf-16-le', errors='surrogateescape')
    # Try to fix common corruption patterns
    decoded = decoded.replace('\ufffd', '')
    
    # Find where JSON structure breaks
    import re
    # Look for the pattern where abilities array ends
    match = re.search(r'"unique_abilities":\s*\[', decoded)
    if match:
        start = match.start()
        # Count braces to find the end of the array
        brace_count = 0
        in_array = False
        end_pos = start
        for i in range(start, len(decoded)):
            if decoded[i] == '[':
                brace_count += 1
                in_array = True
            elif decoded[i] == ']':
                brace_count -= 1
                if in_array and brace_count == 0:
                    end_pos = i + 1
                    break
            elif decoded[i] == '{':
                brace_count += 1
            elif decoded[i] == '}':
                brace_count -= 1
        
        if end_pos > start:
            # Reconstruct JSON
            prefix = decoded[:match.end()]
            suffix = decoded[end_pos:]
            # Try to close the JSON properly
            reconstructed = prefix + decoded[match.end():end_pos] + '\n  }\n}'
            try:
                backup = json.loads(reconstructed)
                print(f"Recovered backup with {len(backup.get('unique_abilities', []))} abilities")
            except:
                # Try simpler: just take what we have and close it
                simplified = decoded[:end_pos] + '\n  }\n}'
                backup = json.loads(simplified)
                print(f"Recovered backup with {len(backup.get('unique_abilities', []))} abilities")
        else:
            raise Exception("Could not find valid JSON structure")
    else:
        raise Exception("Could not find unique_abilities array")
except Exception as e:
    print(f"Aggressive recovery failed: {e}")
    print("\n=== CREATING NEW BACKUP FROM CURRENT FILE ===")
    # Create new backup from current file
    import shutil
    shutil.copy('data/abilities_extracted_from_cards.json', 'data/abilities_extracted_from_cards_backup.json')
    print("Created new backup from current file")
    backup = json.load(open('data/abilities_extracted_from_cards_backup.json', encoding='utf-8'))
    print("No comparison possible - backup is now identical to current file")

new = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))

print(f'\nBackup abilities count: {len(backup["unique_abilities"])}')
print(f'New abilities count: {len(new["unique_abilities"])}')

backup_texts = set(a.get('triggerless_text', a.get('full_text', '')) for a in backup['unique_abilities'])
new_texts = set(a.get('triggerless_text', a.get('full_text', '')) for a in new['unique_abilities'])

missing = backup_texts - new_texts
extra = new_texts - backup_texts

print(f'\nMissing from new: {len(missing)}')
print(f'Extra in new: {len(extra)}')

print('\n=== Sample missing from new ===')
for t in list(missing)[:10]:
    print(f"  {t[:100]}")

print('\n=== Sample extra in new ===')
for t in list(extra)[:10]:
    print(f"  {t[:100]}")
