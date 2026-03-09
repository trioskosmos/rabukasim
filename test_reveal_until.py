import os
import re

with open("engine_rust_src/src/core/logic/interpreter/handlers/movement.rs") as f:
    content = f.read()

# Extract the block for O_REVEAL_UNTIL
start = content.find("O_REVEAL_UNTIL => {")
end = content.find("O_MOVE_TO_DECK => {", start)
if start != -1 and end != -1:
    print(content[start:end])
else:
    print("Could not find O_REVEAL_UNTIL block")
