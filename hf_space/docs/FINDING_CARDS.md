# How to Find Cards in Lovecasim

If you are having trouble finding a specific card in `data/cards.json`, follow these tips.

## 1. Use Broad Patterns
Instead of searching for the full ID which might have variations in dashes or prefixes (e.g., `PL!N-bp3-012-P` vs `PL-bp3-012`), search for the core numeric part.
- **Good**: `012`
- **Better**: `"card_no": ".*012"` (Regex)

## 2. Search by Name
If you know the Japanese name, searching for it is often more reliable.
- **Example**: `鐘 嵐珠`

## 3. Recommended Method for Large Files (Windows)
Standard search tools like `grep` or `findstr` may fail on large JSON files (`cards.json`, `cards_compiled.json`) due to line length, encoding, or file size. The most reliable method in this environment is using **PowerShell's `Get-Content` piped to `Select-String`**.

### Usage
```powershell
Get-Content -Path 'data\cards.json' | Select-String -Pattern 'bp3-012' -Context 0,5
```

- **`-Pattern`**: Supports Regex.
- **`-Context 0,5`**: Shows 5 lines *after* the match (good for JSON block context).
- **Encoding**: PowerShell handles UTF-8 and UTF-16 more gracefully for Japanese text.

### Why Standard Search Might Fail
- **Line Length**: Compiled JSON often has extremely long lines that buffer-overflow simple `grep` implementations.
- **Encoding**: `cards.json` contains Japanese characters; many CLI tools default to ASCII or the system locale (Shift-JIS), causing mismatches. `Get-Content` correctly interprets the file stream.

## 4. Check the Card Directory
Images are stored in `frontend/img/cards/`. You can browse directories to find the exact naming convention used for a specific set.
- **Path**: `frontend/img/cards/BP03/`

## 5. Use the Source of Truth
Always refer to `data/cards.json` as the master source. If `cards_compiled.json` is out of sync, run the compiler:
```bash
uv run python -m compiler.main
```
