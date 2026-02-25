from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import os

img = Image.open('cryptic.jpg')
width, height = img.size

# Create output directory
os.makedirs('output', exist_ok=True)

# 1. Invert the image
inverted = ImageOps.invert(img)
inverted.save('output/inverted.png')
print('Saved inverted.png')

# 2. Enhance contrast
enhancer = ImageEnhance.Contrast(img)
high_contrast = enhancer.enhance(5.0)
high_contrast.save('output/high_contrast.png')
print('Saved high_contrast.png')

# 3. Equalize histogram
equalized = ImageOps.equalize(img)
equalized.save('output/equalized.png')
print('Saved equalized.png')

# 4. Solarize
solarized = ImageOps.solarize(img, threshold=128)
solarized.save('output/solarized.png')
print('Saved solarized.png')

# 5. Posterize (reduce colors)
posterized = ImageOps.posterize(img, 2)
posterized.save('output/posterized.png')
print('Saved posterized.png')

# 6. Edge detection
edges = img.filter(ImageFilter.FIND_EDGES)
edges.save('output/edges.png')
print('Saved edges.png')

# 7. Extract only high value pixels
pixels = list(img.getdata())
high_value = []
for p in pixels:
    if p[0] > 200:
        high_value.append((255, 255, 255))
    else:
        high_value.append((0, 0, 0))
high_val_img = Image.new('RGB', (width, height))
high_val_img.putdata(high_value)
high_val_img.save('output/high_value_only.png')
print('Saved high_value_only.png')

# 8. Extract only specific range
mid_range = []
for p in pixels:
    if 50 < p[0] < 100:
        mid_range.append((255, 255, 255))
    else:
        mid_range.append((0, 0, 0))
mid_range_img = Image.new('RGB', (width, height))
mid_range_img.putdata(mid_range)
mid_range_img.save('output/mid_range.png')
print('Saved mid_range.png')

# 9. Check for hidden text in specific color ranges
print('\n--- Analyzing pixel value distribution ---')
values = [p[0] for p in pixels]
print(f'Min: {min(values)}, Max: {max(values)}')
print(f'Unique values: {len(set(values))}')

# Count pixels in ASCII range
ascii_range = [v for v in values if 32 <= v < 127]
print(f'Pixels in ASCII range (32-126): {len(ascii_range)}')

# 10. Try extracting pixels where value is in ASCII range
ascii_pixels = []
for p in pixels:
    if 32 <= p[0] < 127:
        ascii_pixels.append((p[0], p[0], p[0]))
    else:
        ascii_pixels.append((0, 0, 0))
ascii_img = Image.new('RGB', (width, height))
ascii_img.putdata(ascii_pixels)
ascii_img.save('output/ascii_range.png')
print('Saved ascii_range.png')

# 11. Create a map of pixel values
value_map = {}
for p in pixels:
    v = p[0]
    if v not in value_map:
        value_map[v] = 0
    value_map[v] += 1

print('\nMost common pixel values:')
sorted_values = sorted(value_map.items(), key=lambda x: x[1], reverse=True)
for v, count in sorted_values[:20]:
    char = chr(v) if 32 <= v < 127 else '.'
    print(f'  Value {v} ({char}): {count} pixels')

print('\nAnalysis complete. Check the output folder for generated images.')
