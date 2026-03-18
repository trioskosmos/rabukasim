# Semantic Validator Implementation Guide

## Overview

The semantic validator replaces bytecode-parity checking with game-rule verification. This document explains how the system works and how to extend it.

## Architecture

```
Canonical Entry (JSON)
        ↓
    [Semantic Validator]
        ├─ Load QA_RULINGS registry
        ├─ For each rule:
        │  ├─ Check if rule applies (triggers/effects match)
        │  ├─ Run test function on entry
        │  ├─ Collect results (pass/fail/warning)
        │  └─ Track which tests ran
        └─ Generate report with:
           ├─ Per-entry results
           ├─ Coverage statistics
           └─ Recommendations
```

## Core Components

### 1. QA_RULINGS Registry

Location: [tools/canonical_semantic_validator.js](tools/canonical_semantic_validator.js) (lines 10-170)

Core structure:

```javascript
const QA_RULINGS = {
  "rule_name": {
    // Optional: only apply if entry has these triggers
    triggers: ["ON_PLAY", "CONSTANT"],
    
    // Optional: only apply if entry has these effect operations
    effects: ["DRAW", "RECOVER_MEMBER"],
    
    // Required: human-readable description
    description: "What this rule validates",
    
    // Required: validation function
    test: (entry) => {
      // entry.card_no, entry.canonical, etc.
      // return null for pass
      // return "error message" for fail
      // return "Warning: ..." for warning
    },
  },
};
```

### 2. CanonicalSemanticValidator Class

Location: Lines 175-250

**Key Method**: `runSemanticChecks()`

```javascript
// Iterates through QA_RULINGS
for (const [ruleKey, rule] of Object.entries(rules)) {
  // Skip if rule doesn't apply
  if (!ruleApplies(rule, entry)) continue;
  
  // Run the test
  const result = rule.test(entry);
  
  // Collect result
  if (result === null) {
    // Pass - no error
  } else if (result.includes("Warning:")) {
    this.warnings.push(...);
  } else {
    this.errors.push(...);
  }
}
```

**Key Method**: `validate_batch(entries, qa_rulings)`

```javascript
// Static method that processes all entries
for (const entry of entries) {
  validator = new CanonicalSemanticValidator(entry, rules);
  result = validator.validate();
  results.push(result);
  
  // Accumulate statistics
  stats.semantic_checks_run += result.checks_applied.length;
  stats.valid += result.is_valid ? 1 : 0;
  // etc.
}
```

### 3. Report Generator

Location: Lines 253-290

Generates human-readable output:
- Coverage statistics
- Semantic checks applied
- Entries with errors/warnings
- Next steps and recommendations

---

## How to Add a Semantic Rule

### Step 1: Identify the Pattern

**Question**: What should ALL (or MOST) canonical entries of this type do?

**Examples**:
- "All ON_PLAY abilities should have an effect step"
- "All REDUCE_COST operations should specify an amount"
- "All ACTIVATED abilities should be triggered by condition or cost"

### Step 2: Write the Rule

```javascript
const QA_RULINGS = {
  // ... existing rules ...
  
  "my_new_rule": {
    // WHO: Only apply to entries with these triggers
    triggers: ["ON_PLAY", "ACTIVATED"],
    
    // OR/ALSO: Only apply to entries with these effects
    effects: ["DRAW", "RECOVER_MEMBER"],
    
    // WHAT: Human description
    description: "ON_PLAY abilities should have a clear game effect",
    
    // HOW: Validation logic
    test: (entry) => {
      // Step 1: Check if rule is applicable
      const steps = entry.canonical?.steps || [];
      if (steps.length === 0) {
        return "No effect steps defined";
      }
      
      // Step 2: Validate the pattern
      const hasEffect = steps.some(s => s.op === "DRAW");
      if (!hasEffect) {
        return null; // Not an error if not a draw ability
      }
      
      // Step 3: Validate the structure if it IS that effect
      // ... specific checks ...
      
      // Return null for pass, error string for fail
      return null;
    },
  },
};
```

### Step 3: Test the Rule

Run the validator to see how many entries are affected:

```bash
node tools/canonical_semantic_validator.js canonical_ability_model/drafts/canonical_full_draft.json
```

**Look for**:
- `checks_by_type`: Your rule name should appear with a count
- `With errors`: If many fail, rule might be too strict

### Step 4: Refine

If too many entries fail:

**Option A: Make rule more specific**
```javascript
// Before: too broad
triggers: ["ON_PLAY"] // All ON_PLAY abilities

// After: narrower
test: (entry) => {
  const has_draw = ... // Only check if card actually draws
  if (!has_draw) return null; // Not applicable
  // ... then validate ...
}
```

**Option B: Make it a warning**
```javascript
return "Warning: No target specified (may be implicit)";
```

**Option C: Adjust expectations**
```javascript
// If some legacy bytecode doesn't match pattern, expect it
const isLegacy = entry.source === "legacy";
if (isLegacy) return null; // Skip for legacy
```

### Step 5: Document

Add comments explaining:
- What property the rule validates
- Why this pattern matters
- When exceptions are OK

```javascript
"draw_on_play": {
  triggers: ["ON_PLAY"],
  description: "ON_PLAY abilities with DRAW should be well-formed",
  // RATIONALE: Draw operations need explicit count to avoid power creep
  // EXCEPTION: If it's not a draw ability, rule doesn't apply
  test: (entry) => {
    // ... validation logic ...
  },
}
```

---

## Example: Complete Rule Walkthrough

### Goal: Validate cost operations

**Pattern**: "Any ability with REDUCE_COST should specify the amount"

```javascript
"cost_reduce_must_have_amount": {
  // Apply to entries with cost reduction effects
  effects: ["REDUCE_COST", "MODIFY_COST"],
  
  description: "Cost modifications must specify the reduction amount",
  
  test: (entry) => {
    const steps = entry.canonical?.steps || [];
    
    // Find cost operations
    const costOps = steps.filter(s => 
      s.op === "REDUCE_COST" || s.op === "MODIFY_COST"
    );
    
    if (costOps.length === 0) {
      return null; // Not applicable, no cost ops
    }
    
    // For each cost operation, verify it has a count/amount
    for (const op of costOps) {
      if (op.count === undefined && op.value === undefined) {
        return `${op.op} missing amount parameter`;
      }
      
      // Verify amount is sensible (not negative)
      const amount = op.count?.value || op.value;
      if (amount < 0) {
        return `${op.op} has negative amount (${amount})`;
      }
    }
    
    return null; // All cost operations valid
  },
}
```

**Test**:
```bash
node tools/canonical_semantic_validator.js canonical_ability_model/drafts/canonical_full_draft.json
```

**Output**:
```
🔍 SEMANTIC CHECKS APPLIED:
  cost_reduce_must_have_amount     : 6 entries checked
```

**If errors**:
- Review the 6 entries that have cost reduction
- Check if they actually have `count` or `value` fields
- Adjust test or entries

---

## Advanced: Conditional Rules

### Rule with Multiple Conditions

```javascript
"multi_stage_effect_ordering": {
  description: "Multi-step abilities should have logical ordering",
  
  test: (entry) => {
    const steps = entry.canonical?.steps || [];
    
    // Only check if multi-step
    if (steps.length <= 1) return null;
    
    // Find specific operations
    const selectIdx = steps.findIndex(s => s.op === "SELECT");
    const costIdx = steps.findIndex(s => s.op === "REDUCE_COST");
    const drawIdx = steps.findIndex(s => s.op === "DRAW");
    
    // Validate ordering: select → draw → cost (typical)
    if (selectIdx >= 0 && drawIdx >= 0 && selectIdx > drawIdx) {
      return "Select should come before Draw";
    }
    
    if (selectIdx >= 0 && costIdx >= 0 && selectIdx > costIdx) {
      return "Select should come after Cost check";
    }
    
    return null;
  },
}
```

### Per-Card Rules

```javascript
"card_specific_validation": {
  description: "Special rules for specific cards",
  
  test: (entry) => {
    // Only check specific card
    if (entry.card_no !== "LL-bp1-001-R＋") {
      return null;
    }
    
    // Validate this card's specific semantics
    const steps = entry.canonical?.steps || [];
    const hasRecover = steps.some(s => s.op === "RECOVER_MEMBER");
    
    if (!hasRecover) {
      return `Card ${entry.card_no} should recover a member`;
    }
    
    return null;
  },
}
```

### Optional vs Required

```javascript
"optional_once_per_turn": {
  triggers: ["ACTIVATED"],
  
  description: "Activated abilities typically have once_per_turn",
  
  test: (entry) => {
    // This check is informational only (warning, not error)
    if (entry.canonical?.once_per_turn === undefined) {
      return "Warning: no once_per_turn constraint (may be implicit)";
    }
    return null;
  },
}
```

---

## Testing a New Rule

### Scenario 1: Rule passes for all entries

```
✅ SEMANTIC VALIDATION COMPLETE
  Entries checked with new rule: 614
  Entries that failed: 0
  Entries that warned: 0
```

✓ Rule is ready to merge

### Scenario 2: Rule has some warnings but no errors

```
⚠️  ENTRIES WITH WARNINGS (sample):
  LL-bp1-001-R＋: Warning: no once_per_turn constraint (may be implicit)
  LL-bp2-001-R＋: Warning: no once_per_turn constraint (may be implicit)
```

✓ Rule is informational only, ready to merge

### Scenario 3: Rule has errors for many entries

```
❌ ENTRIES WITH ERRORS (first 5):
  LL-bp1-001-R＋: REDUCE_COST missing amount
  LL-bp2-001-R＋: REDUCE_COST missing amount
  LL-bp3-001-R＋: REDUCE_COST missing amount
```

❌ Rule too strict, needs refinement

**Fix**:
1. Review why many entries fail
2. Make rule more lenient or specific
3. OR fix the entries themselves
4. Retest

---

## Integration: Rule Lifecycle

```
1. AUTHOR
   └─ Write test function in QA_RULINGS

2. TEST
   └─ Run validator, check coverage and errors

3. REFINE
   ├─ If too strict: narrow rule or make it warning
   ├─ If too lenient: tighten validation
   └─ Repeat test

4. DOCUMENT
   └─ Add comments explaining rationale

5. MERGE
   └─ Include in canonical_semantic_validator.js

6. MONITOR
   └─ Track how many entries this rule covers
   └─ Adjust if patterns change
```

---

## Performance Notes

**Runtime**: Validator runs all rules on 614 entries in < 1 second

**Optimization**: Each entry processes only applicable rules
```javascript
// Rule processes ~613 entries quickly
if (!ruleApplies(rule, entry)) return null

// Only entries with ON_PLAY trigger run ON_PLAY rules
triggers: ["ON_PLAY"] // Only 185 entries
```

---

## Reporting & Output

### Report File Structure

```json
{
  "timestamp": "2024-03-18T10:30:00Z",
  "summary": {
    "total": 614,
    "semantic_checks_run": 614,
    "valid": 614,
    "errors": 0,
    "warnings": 0,
    "checks_by_type": {
      "has_pseudocode": 614,
      "has_steps": 614,
      "trigger_defined": 614,
      "draw_on_play": 185,
      // ... more rules ...
    }
  },
  "entries": [
    {
      "card_no": "LL-bp1-001-R＋",
      "trigger": "ON_PLAY",
      "is_valid": true,
      "errors": [],
      "warnings": [],
      "checks_applied": ["has_pseudocode", "has_steps", "trigger_defined", "draw_on_play"]
    },
    // ... more entries ...
  ]
}
```

### Custom Report Generation

Want different output format?

```javascript
const { CanonicalSemanticValidator, QA_RULINGS } = 
  require('./canonical_semantic_validator.js');

const entries = JSON.parse(fs.readFileSync('canonical_ability_model/drafts/canonical_full_draft.json'));
const results = CanonicalSemanticValidator.validate_batch(entries, QA_RULINGS);

// Custom processing
results.entries
  .filter(e => e.errors.length > 0)
  .forEach(e => {
    console.log(`${e.card_no}: ${e.errors.join(', ')}`);
  });
```

---

## Troubleshooting

### Q: My rule runs on 0 entries

**Problem**: Triggers or effects don't match any entries

**Solution**:
```javascript
// Debug: Check what triggers/effects exist
console.log(entry.canonical?.trigger);
console.log(entry.canonical?.steps.map(s => s.op));

// Fix rule to match existing patterns
triggers: ["CONSTANT"] // Not "BUFF"
effects: ["MODIFY_ATK"] // Not "ATK_UP"
```

### Q: Rule always returns null (never fails)

**Problem**: Test logic always passes

**Solution**: Add defensive checks
```javascript
// Before: test always returns null
test: (entry) => {
  // Check for existence of expected field
  if (!entry.canonical?.pseudocode) {
    return "Missing pseudocode"; // Add this check
  }
  return null;
}
```

### Q: Too many warnings, should they be errors?

**Decision criteria**:
- **Error**: Ability cannot work without this property
- **Warning**: Ability works but might be suboptimal

```javascript
// Error: ability won't execute
return "Missing effect steps";

// Warning: ability works but unusual
return "Warning: no cost defined (free ability)";
```

---

## Best Practices

1. **One rule per semantic concept**
   ```javascript
   // Good: focused rule
   "draw_requires_count": { /* ... */ }
   
   // Bad: multiple concepts
   "draw_cost_recovery_structure": { /* ... */ }
   ```

2. **Return early for rule applicability**
   ```javascript
   // Good: quick exit if not applicable
   if (!hasDrawOp) return null;
   // ... then detailed checks ...
   
   // Avoid: complex nested conditions
   if (hasDrawOp && hasCount && hasTarget) { /* ... */ }
   ```

3. **Descriptive error messages**
   ```javascript
   // Good
   return "REDUCE_COST missing count parameter";
   
   // Bad
   return "Invalid";
   ```

4. **Document assumptions**
   ```javascript
   "cost_reduction": {
     description: "Cost reductions should specify amount",
     // ASSUMES: count field contains reduction value
     // EXCEPTION: if not detected as cost-reduction ability
     test: (entry) => { /* ... */ }
   }
   ```

---

## Summary

The semantic validator is a **pluggable rule engine** for validating canonical abilities against game semantics rather than bytecode parity.

**Key Points**:
- ✅ Add rules to `QA_RULINGS` registry
- ✅ Each rule has conditions (triggers/effects) and test function
- ✅ Test returns null (pass) or error/warning string
- ✅ Validator runs applicable rules on each entry
- ✅ Report shows coverage and failures

**Next**: Add semantic rules specific to your game mechanics!
