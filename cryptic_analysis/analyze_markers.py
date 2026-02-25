import struct

with open('cryptic.jpg', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Parse JPEG markers
i = 0
while i < len(data) - 1:
    if data[i] == 0xFF:
        marker = data[i+1]
        if marker == 0xD8:
            print(f'{i:06d}: SOI (Start of Image)')
        elif marker == 0xD9:
            print(f'{i:06d}: EOI (End of Image)')
        elif marker == 0xDB:
            length = struct.unpack('>H', data[i+2:i+4])[0]
            print(f'{i:06d}: DQT (Quantization Table), length={length}')
        elif marker == 0xC0:
            length = struct.unpack('>H', data[i+2:i+4])[0]
            height = struct.unpack('>H', data[i+5:i+7])[0]
            width = struct.unpack('>H', data[i+7:i+9])[0]
            print(f'{i:06d}: SOF0 (Baseline), length={length}, {width}x{height}')
        elif marker == 0xC4:
            length = struct.unpack('>H', data[i+2:i+4])[0]
            print(f'{i:06d}: DHT (Huffman Table), length={length}')
        elif marker == 0xDA:
            length = struct.unpack('>H', data[i+2:i+4])[0]
            print(f'{i:06d}: SOS (Start of Scan), length={length}')
        elif marker == 0xDD:
            length = struct.unpack('>H', data[i+2:i+4])[0]
            restart = struct.unpack('>H', data[i+4:i+6])[0]
            print(f'{i:06d}: DRI (Restart Interval), length={length}, restart={restart}')
        elif marker == 0xE0:
            length = struct.unpack('>H', data[i+2:i+4])[0]
            app_data = data[i+4:i+2+length]
            print(f'{i:06d}: APP0 (JFIF), length={length}')
            print(f'        Data: {app_data[:20]}')
        elif marker == 0xE1:
            length = struct.unpack('>H', data[i+2:i+4])[0]
            app_data = data[i+4:i+2+length]
            print(f'{i:06d}: APP1 (EXIF), length={length}')
            # Check for EXIF header
            if app_data[:4] == b'Exif':
                print(f'        EXIF found!')
                print(f'        First 100 bytes: {app_data[:100]}')
        elif marker == 0xFE:
            length = struct.unpack('>H', data[i+2:i+4])[0]
            comment = data[i+4:i+2+length]
            print(f'{i:06d}: COM (Comment), length={length}')
            print(f'        Comment: {comment}')
        elif 0xD0 <= marker <= 0xD7:
            print(f'{i:06d}: RST{marker-0xD0} (Restart)')
        elif marker == 0x00:
            pass  # Escaped FF
        else:
            if marker >= 0xE0 and marker <= 0xEF:
                length = struct.unpack('>H', data[i+2:i+4])[0]
                print(f'{i:06d}: APP{marker-0xE0}, length={length}')
            else:
                print(f'{i:06d}: Unknown marker 0x{marker:02X}')
    i += 1

# Check for hidden data after EOI
eoi_pos = data.rfind(b'\xff\xd9')
if eoi_pos != -1 and eoi_pos + 2 < len(data):
    hidden = data[eoi_pos+2:]
    print(f'\nHidden data after EOI ({len(hidden)} bytes):')
    print(hidden[:500])
    # Try to decode as text
    try:
        text = hidden.decode('utf-8', errors='replace')
        print(f'\nAs text: {text[:500]}')
    except:
        pass