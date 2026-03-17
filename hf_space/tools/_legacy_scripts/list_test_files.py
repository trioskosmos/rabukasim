import os

batches_dir = "engine/tests/cards/batches"
files = sorted([f for f in os.listdir(batches_dir) if f.startswith("test_") and f.endswith(".py")])
print(f"Found {len(files)} test files in {batches_dir}:")
for f in files:
    print(f)
