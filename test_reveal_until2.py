import os

with open("engine_rust_src/src/core/logic/interpreter/handlers/movement.rs") as f:
    content = f.read()

start = content.find("O_REVEAL_UNTIL => {")
# Find the next closing brace at the same level
depth = 0
in_block = False
end_idx = -1
for i in range(start, len(content)):
    if content[i] == '{':
        depth += 1
        in_block = True
    elif content[i] == '}':
        depth -= 1
        if in_block and depth == 0:
            end_idx = i + 1
            break

if start != -1 and end_idx != -1:
    print(content[start:end_idx])
else:
    print("Could not find O_REVEAL_UNTIL block")
