import sys
from io import TextIOWrapper

from engine.models.bytecode_readable import decode_bytecode


if __name__ == "__main__":
    # Standardized UTF-8 Handling
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print('Usage: python bytecode_decoder.py "[41, 3, 385876097, 0, 1, 0, 0, 0]"')
        sys.exit(1)

    raw = sys.argv[1]
    # Clean up input if it's bracketed
    raw = raw.strip("[] ")
    try:
        data = [int(x.strip()) for x in raw.split(",")]
        print(decode_bytecode(data))
    except Exception as e:
        print(f"Error decoding: {e}")
