import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

print(f"CWD: {os.getcwd()}")
try:
    import engine_rust

    print("engine_rust imported successfully")
except ImportError as e:
    print(f"Failed to import engine_rust: {e}")
    sys.exit(1)

DATA_DIR = os.path.join(os.path.abspath("."), "data")
path = os.path.join(DATA_DIR, "cards_compiled.json")
print(f"Loading data from: {path}")

if not os.path.exists(path):
    print("File does not exist!")
    sys.exit(1)

try:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        print(f"Read {len(content)} bytes.")
        db = engine_rust.PyCardDatabase(content)
        print("Success: RUST_DB initialized")
except Exception as e:
    print(f"Error initializing RUST_DB: {e}")
    import traceback

    traceback.print_exc()
