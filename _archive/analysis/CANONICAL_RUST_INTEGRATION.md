# Canonical ↔ Rust Engine Integration Investigation

## Current State

**Hybrid Preview System**: ✅ Working in Node.js
- `build_hybrid_runtime_preview.js` generates: 277 canonical-ready, 337 legacy-fallback
- Output: `hybrid_runtime_preview.json` with `canonical_plan` and `legacy_plan` for each ability
- Both formats normalized to same structure (trigger, effects, conditions, costs)

**Rust Engine State**: ✅ Loads compiled JSON 
- `CardDatabase::from_json()` expects JSON with `member_db` and `lives` keys
- Each card has `abilities: Vec<Ability>`
- Ability struct: trigger + effects + conditions + costs + bytecode + pseudocode

## Integration Path Analysis

### Phase 1: Direct JSON Compatibility (Current)
```
hybrid_preview.json
├─ entry.canonical_plan (normalized canonical format)
├─ entry.legacy_plan (normalized compiled format)
└─ entry.pseudocode (fallback text representation)
```

**What Rust needs**:
- Deserialize into `Ability` struct
- Current: Uses `effect_type` (enum u8) + `runtime_opcode` (i32)
- Canonical provides: `op` (string like "RECOVER_MEMBER")

**Current bottleneck**: String operations ("RECOVER_MEMBER") vs enum codes

### Phase 2: String-to-Enum Mapping (Minimum Change)
Add in Rust `models.rs`:
```rust
fn effect_op_to_type(op: &str) -> EffectType {
  match op {
    "RECOVER_MEMBER" => EffectType::RecoverMember,
    "DRAW" => EffectType::Draw,
    "ADD_HEARTS" => EffectType::AddHearts,
    // ... map all 40+ operations
  }
}
```

This allows:
1. Canonical JSON with `op: "RECOVER_MEMBER"` to load
2. Deserialize into `effect_type: EffectType::RecoverMember`
3. Bytecode generation proceeds as normal

### Phase 3: Fallback Mechanism
In `CardDatabase::from_value()` after loading member_db:
```rust
// For each ability:
if ability.bytecode.is_empty() && !ability.effects.is_empty() {
  // Canonical format (no bytecode)
  // Generate bytecode from effects/conditions/costs
  ability.bytecode = generate_bytecode_from_canonical(
    &ability.effects,
    &ability.conditions,
    &ability.costs,
    ability.trigger
  );
}
```

## Implementation Checklist

### A. Schema Compatibility Check ✅
- [x] Canonical `canonical_plan` format
- [x] Rust `Ability` struct requirements  
- [x] Trigger types map (ON_PLAY=1, etc.)
- [x] Effect/Cost/Condition support

### B. String Enum Mapping Needed
- [ ] Add EFFECT_IDS string→EffectType mapping to `core/enums.rs`
- [ ] Add CONDITION_IDS string→ConditionType mapping
- [ ] Add COST_IDS string→AbilityCostType mapping
- [ ] Add TRIGGER_IDS string→TriggerType mapping (if needed)

### C. Deserialization Support
- [ ] Modify `Effect` struct to accept both:
  - `effect_type: EffectType` (current)
  - `op: string` (canonical - will map to effect_type in custom deserializer)
- [ ] Similarly for `Cost` and `Condition` structs
- [ ] Custom serde deserializer for fallback handling

### D. Bytecode Generation (If Needed)
- [ ] Check if bytecode required for Rust execution
- [ ] If YES: Implement canonical→bytecode compiler in Rust
- [ ] If NO: Modify interpreter to work with structured effects directly

### E. Integration Testing
- [ ] Load `hybrid_runtime_preview.json` into Rust engine
- [ ] Test 10 canonical-selected abilities
- [ ] Compare output with legacy compiled versions
- [ ] Verify no regression in ability semantics

## CRITICAL FINDING: Bytecode Generation

**Current Architecture**:
- Bytecode is NOT generated from canonical—it's pre-compiled and stored
- Compiler (`compiler/main.py`) expects `bytecode` field already in raw cards
- Rust engine uses `resolve_bytecode()` to interpret pre-compiled bytecode
- **No pseudocode→bytecode generator exists in Rust** (only validation)

**Implications**:
1. Canonical entries in hybrid_preview WITHOUT bytecode → **Rust engine cannot execute**
2. Must either:
   - **Option A**: Generate bytecode from canonical effects BEFORE loading into Rust
   - **Option B**: Use fallback logic to detect missing bytecode and switch to `legacy_plan`
   - **Option C**: Implement bytecode generator in Rust (complex, new code)

**Recommended Path**: Option B (Fallback Handling)
- Easier: Check if ability has bytecode in CardDatabase loader
- If empty bytecode + effects exist: Use legacy_plan
- If empty bytecode + no effects: Error out

## Testing Strategy

### Test Variant 1: Direct Load (Easiest)
```rust
#[test]
fn test_hybrid_preview_load() {
  let hybrid_json = std::fs::read_to_string("hybrid_runtime_preview.json").unwrap();
  let db = CardDatabase::from_json(&hybrid_json);
  assert!(db.is_ok());
  
  // Verify canonical entries loaded
  let canonical_cards = db.unwrap().members
    .values()
    .filter(|card| card.abilities.iter().any(|ab| ab.bytecode.is_empty()))
    .count();
  assert!(canonical_cards > 0);
}
```

### Test Variant 2: Semantics Check
```rust
#[test]  
fn test_canonical_ability_execution_matches_legacy() {
  let card_no = "LL-bp1-001-R"; // Known canonical match
  
  let hybrid_data = load_hybrid_preview();
  let entry = hybrid_data.entries.iter()
    .find(|e| e.card_no == card_no && e.source == "canonical").unwrap();
  
  // Execute canonical version
  let state1 = execute_ability(&entry.canonical_plan);
  
  // Execute legacy version  
  let state2 = execute_ability(&entry.legacy_plan);
  
  // Results should be equivalent
  assert_eq!(state1.game_state, state2.game_state);
}
```

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Bytecode mismatch | HIGH | Ability executes wrong | Validate bytecode generation or use direct effect interpreter |
| String enum mapping incomplete | MEDIUM | Parse failures | Comprehensive enum coverage in mapping layer |
| Fallback logic breaks legacy | MEDIUM | Legacy fails | Feature-gate: only load canonical if flag set |
| Type resolver bugs | MEDIUM | Silent failures | Add verbose logging for enum resolution |

## Switch-Back Path

**IMPORTANT**: Ensure pseudocode→parser path still works

```javascript
// In build_hybrid_runtime_preview.js:
// If canonical fails:
entry.fallback_reason = "validation:invalid_step_kind"
entry.source = "legacy"
entry.canonical_plan = null  // Don't include broken canonical
entry.legacy_plan = normalizeCompiledAbility(compiled)  // Always have fallback
entry.pseudocode = canonical.pseudocode || compiled.pseudocode  // Dual source
```

**Current Path**: 
- Compiled JSON → Rust engine (via `cards_compiled.json`)
- Pseudocode string → Parser (if needed)

**Preserved Path** (if canonical fails):
- Can revert to only using `legacy_plan` 
- Can fallback to pseudocode parsing
- No breaking changes needed

## Immediate Next Steps

1. **Verify Hybrid Output Structure** ✅ (Already done - 277 ready)
2. **Create String-to-Enum Mapping File** (1 hr)
   - File: `engine_rust_src/src/core/canonical_enums.rs`
   - Maps "RECOVER_MEMBER" → EffectType::RecoverMember
3. **Add Canonical Deserializer** (2 hrs)
   - File: `engine_rust_src/src/core/logic/canonical_deserializer.rs`
   - Custom serde for Ability struct
4. **Load Test** (1 hr)
   - Try loading hybrid_runtime_preview.json
   - Check for parse errors
5. **Execution Test** (2 hrs)
   - Pick 1 canonical ability
   - Execute in Rust engine
   - Compare with legacy version

**Total Estimation**: 6 hours to full integration with testing

## Questions to Answer

1. **Does Rust engine use bytecode or structured effects?**
   - If bytecode required: Need canonical→bytecode compiler
   - If structured: Can skip bytecode generation

2. **Are all EFFECT_IDS mapped in Rust already?**
   - Check `enums.rs` for EffectType enum coverage
   - May need to add missing operations

3. **Is there a pseudocode→bytecode parser in Rust?**
   - If yes: Use it as fallback for failed canonical loads
   - If no: Manual bytecode generation needed

4. **What's the performance impact of per-ability enum resolution?**
   - Benchmark: 1000 abilities with string→enum mapping
   - Should be < 1ms for all 614 cards
