---
description: Improve cost extraction by categorizing and parsing raw fallback costs
---

# Cost Categorization Workflow

This workflow improves cost extraction by identifying raw fallback costs, categorizing them, and adding parsing logic.

## Steps

1. **Analyze current coverage**
   - Run `cd tools && python analyze_cost_coverage.py`
   - Identify raw fallback costs that need parsing
   - Note patterns that aren't being recognized

2. **Categorize raw fallback costs**
   - Group similar patterns (e.g., member_to_wait with optional, reveal from hand, etc.)
   - Identify variable parts (numbers, zones, card types, groups)
   - Use `tools/ability_extraction/variable_config.json` for reference

3. **Add parsing logic to extract_costs.py**
   - For each category, add pattern matching in the `parse_cost` function
   - Extract variables (count, optional, target, group, exclude_member, etc.)
   - Return structured cost dictionary
   - Order checks from most specific to most general

4. **Test the extraction**
   - Run `cd tools/ability_extraction && python extract_costs.py`
   - Verify the specific abilities that were raw fallback are now structured

5. **Re-run coverage analysis**
   - Run `cd tools && python analyze_cost_coverage.py`
   - Check if raw fallback count decreased
   - Ensure structured cost count increased

## Current raw fallback patterns to address

- Member to wait with optional: "このメンバーをウェイトにしてもよい"
- Reveal from hand: "手札にあるメンバーカードを好きな枚数公開する"
- Reveal + deck bottom: "手札のライブカードを1枚公開し、デッキの一番下に置いてもよい"
- Member to wait with group: "『μ's』のメンバー1人をウェイトにしてもよい"
- Waitroom to deck: "控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい"
- Energy to member: "エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く"
- Reveal all: "手札をすべて公開する"

## File paths

- Analysis script: `tools/analyze_cost_coverage.py`
- Cost extraction: `tools/ability_extraction/extract_costs.py`
- Variable config: `tools/ability_extraction/variable_config.json`
- Output: `data/abilities_extracted_from_cards.json`
