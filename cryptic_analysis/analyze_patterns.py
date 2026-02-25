from PIL import Image

img = Image.open('cryptic.jpg')
width, height = img.size
pixels = list(img.getdata())

print(f'Image: {width}x{height}')

# Hint: "Coordinates are aligning"
# Try reading pixels at specific coordinate patterns

# 1. Read every Nth pixel
for step in [10, 20, 50, 100]:
    sampled = [pixels[i] for i in range(0, len(pixels), step)]
    text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for p in sampled[:200])
    print(f'\nEvery {step}th pixel R as text:')
    print(text[:200])

# 2. Read pixels at prime indices
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

prime_indices = [i for i in range(len(pixels)) if is_prime(i)][:500]
prime_pixels = [pixels[i] for i in prime_indices]
text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for p in prime_pixels)
print(f'\nPrime index pixels R as text:')
print(text[:200])

# 3. Read pixels at Fibonacci indices
def fib(n):
    a, b = 0, 1
    result = []
    while len(result) < n:
        result.append(a)
        a, b = b, a + b
    return result

fib_indices = [f for f in fib(100) if f < len(pixels)]
fib_pixels = [pixels[i] for i in fib_indices]
text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for p in fib_pixels)
print(f'\nFibonacci index pixels R as text:')
print(text)

# 4. Read pixels where x and y have specific relationship
print('\n--- Coordinate relationship patterns ---')

# x + y = constant
for const in [100, 500, 1000]:
    line_pixels = []
    for y in range(height):
        x = const - y
        if 0 <= x < width:
            line_pixels.append(pixels[y * width + x])
    text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for p in line_pixels[:100])
    print(f'x + y = {const}: {text[:100]}')

# x - y = constant
for const in [0, 100, -100]:
    line_pixels = []
    for y in range(height):
        x = y + const
        if 0 <= x < width:
            line_pixels.append(pixels[y * width + x])
    text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for p in line_pixels[:100])
    print(f'x - y = {const}: {text[:100]}')

# 5. Read pixels in spiral pattern
print('\n--- Spiral pattern ---')
def spiral_order(w, h):
    result = []
    top, bottom, left, right = 0, h - 1, 0, w - 1
    while top <= bottom and left <= right:
        for x in range(left, right + 1):
            result.append((x, top))
        top += 1
        for y in range(top, bottom + 1):
            result.append((right, y))
        right -= 1
        if top <= bottom:
            for x in range(right, left - 1, -1):
                result.append((x, bottom))
            bottom -= 1
        if left <= right:
            for y in range(bottom, top - 1, -1):
                result.append((left, y))
            left += 1
    return result

spiral = spiral_order(width, height)
spiral_pixels = [pixels[y * width + x] for x, y in spiral[:500]]
text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for p in spiral_pixels)
print(f'Spiral order R as text:')
print(text[:200])

# 6. Read only non-black pixels in order
non_black = [(i, p) for i, p in enumerate(pixels) if p[0] > 20]
print(f'\n--- Non-black pixels ({len(non_black)} total) ---')
# Sort by position and extract
sorted_non_black = sorted(non_black, key=lambda x: x[0])
text = ''.join(chr(p[0]) if 32 <= p[0] < 127 else '.' for i, p in sorted_non_black[:500])
print(f'Non-black pixels R as text (sorted by position):')
print(text[:300])

# 7. Try XOR with position
print('\n--- XOR patterns ---')
xor_text = ''
for i, p in enumerate(pixels[:500]):
    val = p[0] ^ (i % 256)
    xor_text += chr(val) if 32 <= val < 127 else '.'
print(f'R XOR position:')
print(xor_text[:200])
