# How to Read Cards in Lovecasim

This guide explains how to quickly find, read, and interpret card data across the project's various data files.

## 1. The Data Hierarchy
Card data lives in three main places. Always check them in this order:

| File | Role | What to look for |
| :--- | :--- | :--- |
| `data/cards.json` | **Master Source** | Basic stats, Japanese names, original card text. |
| `data/manual_pseudocode.json` | **Logic Overrides** | Manually written logic strings (Pseudocode) for complex abilities. |
| `data/cards_compiled.json` | **Final Output** | Compiled bytecode, final instructions, and translated text. |

## 2. Encoding and Search Precautions

> [!IMPORTANT]
> All core data files (`cards.json`, `manual_pseudocode.json`, `cards_compiled.json`) are stored in **UTF-8 (no BOM)**.

### Search Tools
*   **VS Code**: Ensure the "Encoding" is set to "UTF-8" in the bottom bar.
*   **CLI (Windows)**: Standard `findstr` or `grep` might fail with Japanese characters unless the pipe is handled correctly.
*   **PowerShell (Recommended)**: Always specify encoding if you experience "phantom" misses.
    ```powershell
    # Safe search with explicit encoding
    Get-Content -Path 'data\cards.json' -Encoding utf8 | Select-String -Pattern '安養寺'
    ```

## 3. Fast Identification
*   **Primary Key**: Use the `card_no` (e.g., `PL!HS-bp1-009-R`).
*   **Search Tool**: Use PowerShell `Select-String` with UTF-8 encoding to avoid Japanese character corruption.
    ```powershell
    # Find card by ID with context
    Get-Content -Path 'data\cards.json' | Select-String -Pattern 'PL!HS-bp1-009-R' -Context 0,50
    ```

## 3. Interpreting Card Structure

### Member Cards
Found in `data/cards.json` under `members` (or by ID in compiled data).
*   `hearts`: 7-element array (Pink, Red, Yellow, Green, Blue, Purple, Rainbow).
*   `blades`: Number of blades (stars) on the card.
*   `groups`: IDs for Series (e.g., `4` for Hasunosora).
*   `units`: IDs for Units (e.g., `15` for Mirakura Park).

### Ability Logic
The engine doesn't read the `original_text`. It reads `bytecode` and `instructions`.
1.  Check `manual_pseudocode.json` first. If an entry exists for the `card_no`, that logic is used.
2.  If no manual entry exists, the `compiler/patterns/` automatic parser is used.
3.  **Pseudocode Syntax**:
    *   `TRIGGER: ON_PLAY` (登場) / `ON_LEAVES` (退場)
    *   `EFFECT: DRAW(1)` -> Effect and its value.
    *   `{UNIT="Mirakura"}` -> Filters/params.

## 4. Understanding Bytecode
In `data/cards_compiled.json`, abilities are stored as a flat array of integers in chunks of 4: `[Opcode, Value, Attribute, Slot]`.

*   **Opcode**: Hex/Int ID (e.g., `41` for `LOOK_AND_CHOOSE`).
*   **Value**: Primary parameter (often a count).
*   **Attribute (`attr`)**: A bitmask encoding source zone, destination, optional flags, and filters.
*   **Slot**: Target slot index (0-2 for stage).

### Common Attribute Bits:
*   `0x01`: Destination Discard
*   `0x02`: Optional (May)
*   `0xF000`: Source Zone (6=Hand, 7=Discard, 8=Deck)
*   `0x10`: Enable Group Filter (ID in bits 5-11)
*   `0x10000`: Enable Unit Filter (ID in bits 17-23)

## 5. Troubleshooting Logic Gaps
If a card isn't behaving correctly:
1.  **Check `manual_pseudocode.json`**: Is the counts or filters wrong?
2.  **Check `cards_compiled.json`**: Inspect the `bytecode` chunks.
3.  **Run Sync**: After editing data, always re-compile:
    ```bash
    uv run python -m compiler.main
    ```
