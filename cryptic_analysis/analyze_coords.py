from PIL import Image

img = Image.open('cryptic.jpg')
width, height = img.size
pixels = list(img.getdata())

print(f'Image: {width}x{height}')

# Check first row
print('\nFirst row (y=0):')
first_row = pixels[:width]
for i, p in enumerate(first_row[:20]):
    print(f'  x={i}: R={p[0]}, G={p[1]}, B={p[2]}')

# Check last row
print('\nLast row (y=' + str(height-1) + '):')
last_row = pixels[-width:]
for i, p in enumerate(last_row[:20]):
    print(f'  x={i}: R={p[0]}, G={p[1]}, B={p[2]}')

# Check first column
print('\nFirst column (x=0):')
for y in range(min(20, height)):
    p = pixels[y * width]
    print(f'  y={y}: R={p[0]}, G={p[1]}, B={p[2]}')

# Check last column
print('\nLast column (x=' + str(width-1) + '):')
for y in range(min(20, height)):
    p = pixels[y * width + width - 1]
    print(f'  y={y}: R={p[0]}, G={p[1]}, B={p[2]}')

# Look for patterns in pixel values that might be ASCII
print('\n--- Checking for ASCII patterns ---')

# Check if any row has pixel values in ASCII range
for y in range(height):
    row = pixels[y * width:(y+1) * width]
    ascii_count = sum(1 for p in row if 32 <= p[0] < 127)
    if ascii_count > width * 0.5:
        print(f'Row {y} has {ascii_count}/{width} pixels with R in ASCII range')
        text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for p in row[:100])
        print(f'  R as text: {text[:100]}')

# Check diagonal
print('\nDiagonal pixels:')
diag = [pixels[i * width + i] for i in range(min(width, height))]
for i, p in enumerate(diag[:30]):
    print(f'  ({i},{i}): R={p[0]}, G={p[1]}, B={p[2]}')

# Check if pixel coordinates spell something
print('\n--- Checking coordinate-based patterns ---')

# Extract pixels where x == y (diagonal)
diag_text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '' for p in diag)
print(f'Diagonal R values as text: {diag_text[:100]}')

# Anti-diagonal
anti_diag = [pixels[i * width + (width - 1 - i)] for i in range(min(width, height))]
anti_diag_text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '' for p in anti_diag)
print(f'Anti-diagonal R values as text: {anti_diag_text[:100]}')

# Check center row
center_y = height // 2
center_row = pixels[center_y * width:(center_y+1) * width]
center_text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for p in center_row)
print(f'\nCenter row ({center_y}) R as text: {center_text[:100]}')

# Check center column
center_x = width // 2
center_col = [pixels[y * width + center_x] for y in range(height)]
center_col_text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for p in center_col)
print(f'Center column ({center_x}) R as text: {center_col_text[:100]}')