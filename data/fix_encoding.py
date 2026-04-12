import sys

# Read the file as binary
with open('ability_frame_source.json', 'rb') as f:
    raw = f.read()

# The file appears to have UTF-8 bytes that were interpreted as Windows-1252
# To fix: decode as Windows-1252, then encode as UTF-8
try:
    # Decode the current bytes as Windows-1252 (what they were misinterpreted as)
    misinterpreted = raw.decode('windows-1252', errors='replace')
    # Now encode back to Windows-1252 to get the original UTF-8 bytes
    original_bytes = misinterpreted.encode('windows-1252', errors='replace')
    # Decode those bytes as UTF-8
    fixed = original_bytes.decode('utf-8', errors='replace')
    with open('ability_frame_source.json', 'w', encoding='utf-8', newline='') as f:
        f.write(fixed)
    print('Fixed successfully')
except Exception as e:
    print(f'Failed: {e}')
    import traceback
    traceback.print_exc()
