import re

try:
    # Test common ranges
    re.compile(r"[一-九]")
    print("Kanji range [一-九] is OK")
    re.compile(r"[1-3]")
    print("Digit range [1-3] is OK")
    re.compile(r"[一二三四五六七八九〇]")
    print("Explicit Kanji set is OK")

    # Test the problematic one if we can reconstruct it
    # re.error: bad character range ･-燿
    # ･ is likely \uff65 or \u30fb
    # 燿 is \u71ff
    # re.compile(r'[\uff65-\u71ff]') # This would be a HUGE range but valid if order is correct

    print("All tests passed")
except Exception as e:
    print(f"Error: {e}")
