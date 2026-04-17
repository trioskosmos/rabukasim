with open('tools/ability_extraction/extract_card_abilities.py', 'rb') as f:
    data = f.read()
decoded = data.decode('utf-16-le', errors='ignore')
with open('tools/ability_extraction/extract_card_abilities.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(decoded)
print('Converted from UTF-16-LE to UTF-8')
