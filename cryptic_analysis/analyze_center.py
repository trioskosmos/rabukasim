from PIL import Image

img = Image.open('cryptic.jpg')
width, height = img.size
pixels = list(img.getdata())

print(f'Image: {width}x{height}')

# Find non-black pixels
print('\n--- Finding non-black pixels ---')
non_black = []
for i, p in enumerate(pixels):
    if p[0] > 20 or p[1] > 20 or p[2] > 20:
        x = i % width
        y = i // width
        non_black.append((x, y, p))

print(f'Found {len(non_black)} non-black pixels')

# Show first 50 non-black pixels
print('\nFirst 50 non-black pixels:')
for x, y, p in non_black[:50]:
    print(f'  ({x}, {y}): R={p[0]}, G={p[1]}, B={p[2]}')

# Check if there's a pattern in the coordinates
print('\n--- Coordinate analysis ---')
if non_black:
    xs = [x for x, y, p in non_black]
    ys = [y for x, y, p in non_black]
    print(f'X range: {min(xs)} to {max(xs)}')
    print(f'Y range: {min(ys)} to {max(ys)}')
    
    # Check if coordinates spell something
    print('\nX coordinates as ASCII:')
    x_text = ''.join(chr(x) if 32 <= x < 127 else '.' for x in xs[:100])
    print(x_text)
    
    print('\nY coordinates as ASCII:')
    y_text = ''.join(chr(y) if 32 <= y < 127 else '.' for y in ys[:100])
    print(y_text)
    
    # Check R values of non-black pixels
    print('\nR values of non-black pixels as ASCII:')
    r_text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for x, y, p in non_black[:200])
    print(r_text[:200])
    
    # Check G values
    print('\nG values of non-black pixels as ASCII:')
    g_text = ''.join(chr(p[1]) if 32 <= p[1] < 127 else '.' for x, y, p in non_black[:200])
    print(g_text[:200])
    
    # Check B values
    print('\nB values of non-black pixels as ASCII:')
    b_text = ''.join(chr(p[2]) if 32 <= p[2] < 127 else '.' for x, y, p in non_black[:200])
    print(b_text[:200])

# Look for specific patterns
print('\n--- Looking for text patterns ---')

# Group by rows
rows = {}
for x, y, p in non_black:
    if y not in rows:
        rows[y] = []
    rows[y].append((x, p))

print(f'\nRows with non-black pixels: {len(rows)}')
for y in sorted(rows.keys())[:20]:
    pixels_in_row = sorted(rows[y], key=lambda t: t[0])
    text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for x, p in pixels_in_row)
    print(f'Row {y}: {text[:100]}')