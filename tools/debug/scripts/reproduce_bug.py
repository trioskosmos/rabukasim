import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from server import serialize_state

    print("Testing serialize_state()...")
    try:
        serialize_state()
        print("serialize_state() worked with no arguments!")
    except TypeError as e:
        print(f"serialize_state() failed: {e}")
except Exception as e:
    print(f"Import failed: {e}")
