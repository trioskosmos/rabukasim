with open('tools/ability_extraction/extract_card_abilities.py', 'rb') as f:
    data = f.read()
null_count = data.count(b'\x00')
print(f'Null bytes: {null_count}')
data = data.replace(b'\x00', b'')
with open('tools/ability_extraction/extract_card_abilities.py', 'wb') as f:
    f.write(data)
print('Removed null bytes')
