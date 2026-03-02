---
description: Quickly generate and read a comprehensive report for any card to analyze its full logic stack (Names, JP text, Pseudocode, Compiled Bytecode, Decoded Bytecode).
---

# Analyze Card Workflow

When you need to analyze a card, understand its logic, or find its bytecode, **DO NOT manually search through `cards.json` or `manual_pseudocode.json` using grep or file views.** Manual searches are slow and prone to UTF-8 encoding failures on Windows.

Instead, use this automated workflow to instantly retrieve "every detail of the card and every detail of the details."

## Steps

1. **Generate the Report**: Run `card_finder.py` targeting a specific card ID, Card No, or Japanese name, outputting to a markdown report in the reports directory.
   ```powershell
   uv run python tools/card_finder.py "<CARD_ID_OR_NAME>" --output "reports/card_<CARD_ID>.md"
   ```
   *Replace `<CARD_ID_OR_NAME>` with the packed ID (e.g., 275), Card No (e.g., PL!N-bp3-007-P), or Name.*

2. **Read the Report**: Immediately use the `view_file` tool to read the generated markdown report in its entirety.
   ```json
   {
     "AbsolutePath": "c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\reports\\card_<CARD_ID>.md"
   }
   ```

3. **Analyze**: The report contains all necessary information in one place:
   - **IDs**: Packed ID, Logic ID, Variant
   - **Metadata**: Name, JP Ability Text, Raw Pseudocode
   - **Overrides/Consolidated**: Consolidated pseudocode and any manual overrides
   - **Cross-References**:
     - *QA Rulings*: Official rulings associated with this card.
     - *Shared Ability Cards*: Other cards with this exact ability.
     - *Rust Engine Tests*: Which tests cover this card, its shared peers, or its QA items.
   - **Engine Logic**: The fully decoded bytecode, clearly mapping opcodes and their parameters.

Always execute these steps sequentially when investigating a card's implementation, testing coverage, or debugging anomalous behavior.
