import os

from engine.game.data_loader import CardDataLoader

print("Initial Memory: N/A")

data_path = os.path.join(os.getcwd(), "data", "cards_compiled.json")
print(f"Loading from {data_path}")

loader = CardDataLoader(data_path)

try:
    m, l, e = loader.load()
    print(f"Loaded {len(m)} members, {len(l)} lives, {len(e)} energy")
except MemoryError:
    print("CRASHED with MemoryError!")
except Exception as e:
    print(f"Failed with error: {e}")
