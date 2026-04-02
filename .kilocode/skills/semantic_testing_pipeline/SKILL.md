---
name: semantic_testing_pipeline
description: Use when turning card text or rules into a repeatable semantic test pipeline.
---
# Semantic Testing Pipeline
## Do
- Break the rule into trigger, condition, effect, and outcome.
- Map each step to a test action.
- Keep the pipeline readable enough to reuse.
## Do not
- Do not overfit to one card if the rule is broader.
- Do not skip the final outcome check.
## Verify
- Reuse the same pipeline on a second similar case.