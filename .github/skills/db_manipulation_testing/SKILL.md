---
name: db_manipulation_testing
description: Use when mutating cards_compiled.json or injected card data to test complex rules.
---
# DB Manipulation Testing
## Do
- Copy the smallest card record that proves the case.
- Mutate only the fields needed for the test.
- Keep the test isolated from shared fixtures.
## Do not
- Do not change unrelated card data.
- Do not leave temporary mutations in shared state.
## Verify
- Run the smallest targeted Rust test and confirm the rule.