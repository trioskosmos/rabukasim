from PIL import Image

img = Image.open('cryptic.jpg')
print(f'Size: {img.size}, Mode: {img.mode}')

pixels = list(img.getdata())

# Extract LSB from each color channel
bits = []
for pixel in pixels:
    for channel in pixel[:3]:  # RGB
        bits.append(channel & 1)

# Convert bits to bytes
bytes_data = []
for i in range(0, len(bits) - 7, 8):
    byte = 0
    for j in range(8):
        byte = (byte << 1) | bits[i + j]
    bytes_data.append(byte)

# Try to find readable text
result = bytes(bytes_data[:2000])
text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in result)
print('LSB extracted text:')
print(text[:1000])

# Also try reading just red channel LSB
bits_r = []
for pixel in pixels:
    bits_r.append(pixel[0] & 1)

bytes_r = []
for i in range(0, len(bits_r) - 7, 8):
    byte = 0
    for j in range(8):
        byte = (byte << 1) | bits_r[i + j]
    bytes_r.append(byte)

result_r = bytes(bytes_r[:2000])
text_r = ''.join(chr(b) if 32 <= b < 127 else '.' for b in result_r)
print('\nRed channel LSB:')
print(text_r[:500])
