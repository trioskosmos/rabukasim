"""
Audit the JS refactor by comparing function definitions in the old monolithic main.js
(from git HEAD) against all current JS module files.
"""

import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JS_DIR = os.path.join(ROOT, "frontend", "web_ui", "js")


def get_old_main():
    """Get the old main.js from git HEAD."""
    result = subprocess.run(
        ["git", "show", "HEAD:frontend/web_ui/js/main.js"],
        capture_output=True,
        cwd=ROOT,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def extract_functions(code, label=""):
    """Extract all function/method names from JS code."""
    funcs = set()
    # function name(
    for m in re.finditer(r"(?:^|\s)(?:async\s+)?function\s+(\w+)\s*\(", code, re.MULTILINE):
        funcs.add(m.group(1))
    # window.name = function
    for m in re.finditer(r"window\.(\w+)\s*=\s*(?:async\s+)?function", code, re.MULTILINE):
        funcs.add(m.group(1))
    # window.name = async (
    for m in re.finditer(r"window\.(\w+)\s*=\s*async\s*\(", code, re.MULTILINE):
        funcs.add(m.group(1))
    # window.name = (
    for m in re.finditer(r"window\.(\w+)\s*=\s*\(", code, re.MULTILINE):
        funcs.add(m.group(1))
    # const name = function / async function / () =>
    for m in re.finditer(
        r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>)", code, re.MULTILINE
    ):
        funcs.add(m.group(1))
    return funcs


def scan_current_modules():
    """Scan all current JS files for function definitions and window.X exports."""
    all_funcs = set()
    window_exports = set()

    for fname in os.listdir(JS_DIR):
        if not fname.endswith(".js"):
            continue
        filepath = os.path.join(JS_DIR, fname)
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        funcs = extract_functions(code, fname)
        all_funcs.update(funcs)

        # Also track window.X = exports
        for m in re.finditer(r"window\.(\w+)\s*=", code):
            window_exports.add(m.group(1))

    return all_funcs, window_exports


def scan_index_html():
    """Find all onclick/onchange references in index.html."""
    html_path = os.path.join(ROOT, "frontend", "web_ui", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    refs = set()
    for m in re.finditer(r'on(?:click|change|submit|input)\s*=\s*"([^"]*)"', html, re.IGNORECASE):
        handler = m.group(1)
        # Extract function name from handler string
        fn_match = re.match(r"(\w+)\s*\(", handler)
        if fn_match:
            refs.add(fn_match.group(1))
    return refs


def main():
    print("=" * 70)
    print("REFACTOR AUDIT: Old Monolith vs New Modules")
    print("=" * 70)

    # 1. Get old functions
    old_code = get_old_main()
    old_funcs = extract_functions(old_code, "old_main.js")
    print(f"\n[OLD main.js] Found {len(old_funcs)} functions:")
    for f in sorted(old_funcs):
        print(f"  - {f}")

    # 2. Get current functions
    cur_funcs, window_exports = scan_current_modules()
    print(f"\n[NEW modules] Found {len(cur_funcs)} functions, {len(window_exports)} window exports")

    # 3. Find missing
    missing = old_funcs - cur_funcs - window_exports
    # Filter out trivially unimportant names
    trivial = {
        "message",
        "source",
        "lineno",
        "colno",
        "error",
        "e",
        "idx",
        "btn",
        "shim",
        "name",
        "i",
        "j",
        "k",
        "v",
        "p",
        "c",
        "r",
        "s",
        "t",
        "n",
        "capturedErrors",
        "onerror",
    }
    missing = missing - trivial

    print(f"\n{'=' * 70}")
    print(f"MISSING FUNCTIONS ({len(missing)} total):")
    print(f"{'=' * 70}")
    for f in sorted(missing):
        print(f"  ❌ {f}")

    # 4. Check index.html references
    html_refs = scan_index_html()
    print(f"\n{'=' * 70}")
    print(f"INDEX.HTML ONCLICK REFERENCES ({len(html_refs)} total):")
    print(f"{'=' * 70}")
    for ref in sorted(html_refs):
        status = "✅" if ref in window_exports else "❌ NOT EXPORTED"
        print(f"  {status}  {ref}")

    # 5. Check for functions that ARE in modules but NOT exported to window
    print(f"\n{'=' * 70}")
    print("FUNCTIONS IN MODULES BUT NOT ON window.*:")
    print(f"{'=' * 70}")
    in_modules_not_exported = cur_funcs - window_exports - trivial
    for f in sorted(in_modules_not_exported):
        if f in html_refs:
            print(f"  ⚠️  {f} (NEEDED by index.html but not on window!)")


if __name__ == "__main__":
    main()
