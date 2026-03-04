---
description: Quickly generate and read a comprehensive report for any card to analyze its full logic stack (Names, JP text, Pseudocode, Compiled Bytecode, Decoded Bytecode).
---

# Analyze Card Workflow

When you need to analyze a card, understand its logic, or find its bytecode, **DO NOT manually search through `cards.json` or `manual_pseudocode.json` using grep or file views.** Do NOT run searches for the card anywhere else once a report is generated.

> [!IMPORTANT]
> **The Two Sources of Truth**: 
> 1.  **`data/cards.json`**: Contains all metadata (JP Text, Name, Stats).
> 2.  **`data/consolidated_abilities.json`**: Contains all card logic (Pseudocode).
> 
> Everything is in these two files. The tools below read from them directly. **You MUST generate and use persistent report files (in `reports/`)** to analyze cards. This ensures you have a readable, stable reference for the duration of your task.

## Step 1: Generate the Full Card Report

// turbo-all

```powershell
uv run python tools/card_finder.py "<CARD_ID_OR_NAME>" --output "reports/card_<CARD_ID>.md"
```
*Replace `<CARD_ID_OR_NAME>` with the packed ID (e.g., 275), Card No (e.g., PL!N-bp3-007-P), or Name.*

## Step 2: Read the Report — Do the Side-by-Side Analysis

Read with `view_file`. Check ALL three layers in order:

| Layer | What to check |
|---|---|
| **JP Ability (JP)** | Trigger icon (`起動`=ACTIVATED, `自動`=AUTO, `登場`=ON_PLAY, `常時`=CONSTANT). Cost zone (手札=Hand, 控え室=Discard, ステージ=Stage). Effect zone. Any filters (cost comparisons, type, group). |
| **Pseudocode (Consolidated DB)** | Does trigger match JP? Does cost zone/filter match? Does effect zone/destination match? Are comparators present (e.g., `COST_LT_TARGET_VAL`, `COST_GE`)? |
| **Decoded Bytecode** | Does each instruction match the pseudocode? Check source/dest zone values against the legend at the bottom of the report. **Any `[Unknown(<large_number>)]` in a filter field is a bug.** |

## 🚨 Instant Red Flags — Spot These Immediately

| Symptom in Report | What it means |
|---|---|
| `[Unknown(<large_number>)]` in decoded filter | Filter bitmask unrecognized → filter is **ignored by engine**. The card effect has no filter applied. |
| Decoded source zone ≠ pseudocode cost zone | Wrong zone constant compiled. E.g., bytecode says `Hand (Generic)` but pseudocode says `DISCARD`. |
| `TRIGGER: ACTIVATED` but game allows activation from hand | Should be `TRIGGER: ACTIVATED (From Hand)` in pseudocode. |
| `TRIGGER: ACTIVATED (From Hand)` but card is on Stage | Wrong trigger annotation — remove `(From Hand)`. |
| `-> TARGET_VAL` in cost pseudocode but no matching comparator decoded | Cost-value comparison filter was lost at compile time. The comparison (e.g., lower cost check) is not running. |
| Pseudocode has `(Once per turn)` but bytecode shows no OPT flag | Once-per-turn limit not enforced in engine. |

## Step 3: Quick Pseudocode Testing (For Iteration)

After identifying the bug and writing a fix, test it instantly before updating the DB:

```powershell
uv run python tools/test_pseudocode.py "TRIGGER: ACTIVATED (Once per turn)\nCOST: DISCARD_HAND(1)\nEFFECT: DRAW(1)"
```

Check the keyword cheat sheet if needed:
```powershell
uv run python tools/test_pseudocode.py --reference
```
