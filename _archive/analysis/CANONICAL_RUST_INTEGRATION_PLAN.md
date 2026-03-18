# Canonical ↔ Rust Engine Integration: COMPLETE ANALYSIS

## CRITICAL FINDING: Bytecode Generation Requirement

**Current Architecture**:
- Compiled cards have full bytecode arrays (10+ elements per ability)
- Hybrid preview entries have normalized string format WITHOUT bytecode
- Rust engine's `resolve_bytecode()` requires pre-compiled bytecode
- **No pseudocode→bytecode generator exists in Rust** (only validation)

**Real Data Structures**:

### Compiled Format (cards_compiled.json)
```json
{
  "trigger": 1,
  "effects": [{
    "effect_type": 17,  // ENUM code
    "runtime_opcode": 17,
    "runtime_value": 1,
    "runtime_attr": 2368893403996881000,
    "runtime_slot": 458758
  }],
  "bytecode": [17, 1, 0, 551550976, 458758, 1, 0, 0, 0, 0],  // 5-entry array
  "pseudocode": "TRIGGER: ON_PLAY\nEFFECT: RECOVER_MEMBER(1)"
}
```

### Hybrid Preview Format (canonical_plan)
```json
{
  "trigger": "ON_PLAY",
  "conditions": [],
  "effects": [{
    "kind": "effect",
    "op": "RECOVER_MEMBER",  // STRING name
    "count": 1,
    "target": "$controller",
    "is_optional": false
  }]
  // NO bytecode field
}
```

## Integration Challenge

**Problem**: Hybrid preview format cannot be loaded directly into Rust engine
- Canonical format uses strings ("ON_PLAY", "RECOVER_MEMBER")
- Rust expects enums (TriggerType::OnPlay, EffectType::RecoverMember) + bytecode
- Bridge has 277 canonical entries with NO bytecode

**Options**:

| Approach | Pros | Cons | Effort |
|----------|------|------|--------|
| **A: Node.js bytecode gen** | Uses existing infra, tested before Rust, no engine changes | Must port bytecode generator | 6-8hr |
| **B: Rust bytecode gen** | Single place, transparent | Complex Rust code, risky interpreter changes | 8-12hr |
| **C: Structured effects** | Simplest semantically | Major interpreter rewrite | 12-16hr |
| **D: Fallback only** | No changes needed | Must always use legacy for canonical | 2hr (minimal) |

## RECOMMENDED: Option A + Fallback Handler

**Phase 1: Add Fallback Handler to Rust** (1-2 hours)
- When loading CardDatabase, detect empty bytecode
- If bytecode empty AND effects present: Flag for fallback
- Store `source: "canonical"` metadata for runtime tracking

**Phase 2: Generate Bytecode in Node.js** (Optional enhancement, 4-6 hours)
- If time permits, create bytecode generator
- Allows canonical path without fallback
- Not blocking for initial hybrid launch

**Phase 3: Runtime Fallback Logic** (2-3 hours)
- At execution time, if canonical bytecode not available:
  - Switch to legacy_plan (already has compiled bytecode)
  - Log metric for tracking success rate
- Ensures safe rollback without regression

## Implementation Checklist

### Phase 1: Fallback Handler ✅ EASY
- [ ] Add `source: string` field to Ability struct (nullable)
- [ ] Add `has_generated_bytecode: bool` to track fallback eligibility
- [ ] In CardDatabase::from_json():
  ```rust
  if ability.bytecode.is_empty() && !ability.effects.is_empty() {
    ability.source = Some("canonical".to_string());
    ability.has_generated_bytecode = false;
  }
  ```
- [ ] Modify ability execution to check `has_generated_bytecode`
  - If false: Try legacy_plan lookup
  - If success: Use legacy bytecode
  - If failure: Log warning and try canonical anyway

### Phase 2: Bytecode Generation (Optional) ⏸️ FUTURE
- [ ] Port compiler's bytecode generation to Node.js or Rust
- [ ] Add mapping layer: string effects → effect_type enum → bytecode opcodes
- [ ] Test bytecode correctness against known compiled output

### Phase 3: Runtime Switching ✅ MEDIUM
- [ ] Store pointer to legacy_plan in compiled data
- [ ] At execution: Check `source` field in Ability metadata
- [ ] If canonical: Check if bytecode exists
  - If yes: Execute normally
  - If no: Lookup legacy_plan, use that bytecode
- [ ] Add metrics: `canonical_executed`, `canonical_fallback`, `canonical_success`

## Testing Strategy

### Test 1: Load Hybrid Preview (Baseline)
```rust
#[test]
fn test_load_hybrid_preview_with_fallback() {
  let hybrid_json = std::fs::read_to_string("hybrid_runtime_preview.json").unwrap();
  let db = CardDatabase::from_json_with_fallback(&hybrid_json).unwrap();
  
  // Find one canonical entry
  let card = db.members.values()
    .find(|c| c.source == Some("canonical".to_string()))
    .expect("Should have canonical entries");
  
  // Verify fallback metadata present
  assert!(card.abilities.iter().any(|ab| !ab.bytecode.is_empty()),
    "At least some abilities should have bytecode (legacy fallback)");
}
```

### Test 2: Execution with Fallback
```rust
#[test]
fn test_canonical_ability_uses_legacy_fallback() {
  let ab = db.members[&card_id].abilities[0];
  
  // If canonical (no bytecode):
  if ab.source == Some("canonical") && ab.bytecode.is_empty() {
    // Should use legacy_plan instead
    let legacy_ab = lookup_legacy_ability(card_id);
    assert!(!legacy_ab.bytecode.is_empty(), "Legacy must have bytecode");
    
    // Execute with legacy
    state.resolve_bytecode(&db, legacy_ab.bytecode, &ctx);
    assert!(state.valid(), "Execution should succeed");
  }
}
```

### Test 3: Metrics Collection
```javascript
// In execution loop:
const metrics = {
  canonical_attempted: 0,
  canonical_failed: 0,
  canonical_fallback: 0,
  canonical_success: 0
};

for (const ab of abilities) {
  if (ab.source === "canonical") {
    metrics.canonical_attempted++;
    if (ab.bytecode.length === 0) {
      metrics.canonical_fallback++;
      // Use legacy
    } else {
      metrics.canonical_success++;
      // Use canonical
    }
  }
}
```

## Migration Path

### Step 1: Without Bytecode (Safe)
- Load hybrid_runtime_preview.json with fallback handler
- All canonical entries detected as "needs fallback"
- Runtime switches to legacy_plan automatically
- No visible change in behavior
- Safe to deploy

### Step 2: With Bytecode (Future)
- Generate bytecode from canonical effects (separate process)
- Add bytecode to canonical_plan in hybrid preview
- Re-load with bytecode present
- Fallback handler detects `bytecode.len() > 0`
- Runtime uses canonical directly
- Gradual percentage increase

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Fallback fails silently | MEDIUM | Canonical seems to work but doesn't | Add verbose logs + metrics |
| Legacy lookup fails | LOW | Execution crash | Fall through to pseudocode parsing |
| Performance regression | MEDIUM | Load time increases | Profile before/after |
| Bytecode mismatch | HIGH | Execution wrong semantics | Validate against known good output |

## Questions Answered

1. **Does Rust engine use bytecode or structured effects?**
   - ✅ Bytecode only (via resolve_bytecode)
   - Falling through to effects requires interpreter rewrite

2. **Is bytecode required for hybrid preview?**
   - ✅ YES, currently required
   - Fallback handler can defer to legacy with no bytecode needed

3. **Can pseudocode fallback be used?**
   - ⚠️ Pseudocode exists but no parser in Rust
   - Would need to implement pseudocode→bytecode parser (3-4 hr additional work)

4. **Is switch-back path preserved?**
   - ✅ YES via fallback handler
   - Can always revert to pure legacy format

## Immediate Actions

1. **✅ Investigation Complete** - Document ready
2. **[ ] Decision Point** - Choose implementation approach
3. **[ ] Option A Pick: Phase 1 + Fallback** (2-3 hours)
   - Add fallback handler to Rust
   - Load hybrid preview with safe degradation
   - Test 10 canonical entries execute correctly
4. **[ ] Option B Pick: Phase 1 + Phase 2** (8-10 hours)
   - Same as A, but add bytecode generation
   - Higher upside but more risk
5. **[ ] Production Deployment** - After testing passes

## Next Steps

**For User**: 
1. Review integration options
2. Choose implementation approach
3. Provide Rust engine code access for modifications
4. Set performance/risk tolerance

**For Agent**:
1. Implement selected approach
2. Run full integration tests
3. Generate deployment metrics
4. Document runtime fallback behavior

---

## Summary

The hybrid preview system is **semantically ready** but **needs bytecode generation** before Rust can execute canonical entries. Two safe paths forward:

1. **Fast (~2-3 hrs)**: Fallback handler + defer to legacy (guarantees safety)
2. **Complete (~8-10 hrs)**: Fallback handler + bytecode generation + direct execution

Initial recommendation: **Path 1** (fast) → Path 2 (future enhancement) once bytecode generation is mature.
