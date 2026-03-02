---
name: unified_card_search
description: Unified workflow for finding card information via URL, ID, or Card No.
---

# Unified Card Search Skill

This skill provides a "no-hassle" way to retrieve full information on any card (Member, Live, or Energy) using various inputs.

## RECOMMENDED WORKFLOW: Report Generation

To avoid terminal encoding issues (especially with Japanese characters on Windows/PowerShell) and to get the most detailed analysis, **always use the report generation workflow**.

1.  **Generate the Report**: Use the `-o` or `--output` flag.
    ```bash
    uv run python tools/card_finder.py "<INPUT>" --output reports/card_analysis.md
    ```
2.  **View File**: Use `view_file` on the generated Markdown file. This ensures proper **UTF-8 decoding** and avoids the common `utf-16le` or `cp1252` crashes in the terminal.
3.  **Review Logic**: The report contains:
    -   **Metadata**: Names, JP text, and standard pseudocode.
    -   **Manual Pseudocode**: Any overrides from `manual_pseudocode.json`.
    -   **Compiled Bytecode**: The raw numbers stored in `cards_compiled.json`.
    -   **Decoded Bytecode**: A human-readable breakdown of what the engine actually executes.

## Encoding Safety Warning

> [!IMPORTANT]
> **Windows Terminal (PowerShell/CMD)** often uses `utf-16le` or `cp1252` which will corrupt Japanese names or fail to display them entirely.
> **ALWAYS** redirect output to a file or use the `--output` flag to ensure the data is written in **UTF-8**, then read that file using development tools.

## Core Tool: `tools/card_finder.py`

The `card_finder.py` utility is the primary entry point for card lookup.

### Supported Input Formats

1.  **Card Number**: Exact identifier from the physical card.
    ```bash
    uv run python tools/card_finder.py "PL!S-bp2-005-P"
    ```
2.  **URL**: Extracts the card number automatically from image URLs or paths.
    ```bash
    uv run python tools/card_finder.py "http://127.0.0.1:8000/img/cards_webp/PL!S-bp2-005-P.webp"
    ```
3.  **Engine IDs**:
    - **Packed ID**: The 16-bit identifier used by the engine (e.g., `419`).
    - **Logic ID**: The raw index in the database (0-4095).
    ```bash
    uv run python tools/card_finder.py 419
    ```
4.  **Text Search**: If no exact match is found, it searches for the query within the entire card metadata.
    ```bash
    uv run python tools/card_finder.py "渡辺 曜"
    ```
5.  **Report Generation (Recommended)**: Use the `-o` or `--output` flag to save the results to a Markdown file. This is the **most robust way** to view card data as it avoids shell encoding issues and allows for direct viewing in the editor.
    ```bash
    uv run python tools/card_finder.py "PL!S-bp2-005-P" --output reports/card_report.md
    ```
    *Note: The report includes Manual Pseudocode overrides from `data/manual_pseudocode.json` if available.*

## Workflow: Verifying Card Logic

When you need to understand how a card works in the engine:

1.  **Run Card Finder with Report**: Execute `uv run python tools/card_finder.py <INPUT> --output reports/<FILENAME>.md`.
2.  **View File**: Use `view_file` on the generated `.md` file. This ensures proper UTF-8 decoding and beautiful formatting.
3.  **Review Content**: Check the `--- CONTENT ---` section for the intended logic (Japanese text and pseudocode).
4.  **Review Logic**: Check the `--- LOGIC ---` section for the compiled bytecode and its **Legendary Decoded** representation.
    - **Variable Labels**: Parameters are labeled for clarity (e.g., `v(Reveal)`, `a(Source)`, `s(Target)`).
    - **Value Legend**: Numeric IDs for Zones, Slots, and Comparisons are automatically mapped to names.
5.  **Verify Bytecode**: If the decoded bytecode seems wrong, refer to `tools/verify/bytecode_decoder.py` or the `ability_verification` skill.

## Common IDs to Know

- **Packed ID**: `(logic_id & 0x0FFF) | (variant_idx << 12)`
- **Logic ID**: The "base" identity of the card, shared across variants.
- **Variant**: `0` for base, `1` for R+, `2` for P+, etc.

## Diagnostic Shortcuts

These are quick commands or patterns to use for common diagnostic tasks.

1.  **"What is the ID?" (Lookup ID)**
    -   **Alias**: `id_lookup <CARD_NO>`
    -   **Command**: `uv run python tools/card_finder.py "<CARD_NO>" | Select-String "ID"`

2.  **"Show me the bytecode" (Raw Bytecode)**
    -   **Alias**: `show_bc <CARD_NO>`
    -   **Command**: `uv run python tools/card_finder.py "<CARD_NO>" | Select-String "Bytecode"`

3.  **"Check the decoding" (Decoded Logic)**
    -   **Alias**: `check_decoding <CARD_NO>`
    -   **Command / Workflow**:
        1. `uv run python tools/card_finder.py "<CARD_NO>" --output reports/diag.md`
        2. View `reports/diag.md` and check the **Decoded Bytecode** section.
