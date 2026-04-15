# Algorithmic Complexity Analysis & Optimization Opportunities

## Critical Performance Bottlenecks Identified

### 1. check_pattern_overlap() - O(n^3) complexity
**Location:** Lines 1856-1915
**Current Complexity:** O(T × P × M^2)
- T = number of texts (~627 abilities)
- P = number of patterns (168)
- M = average matches per text
- Nested loops: texts → patterns → matches → matches (O(n^3))

**Problem:**
```python
for text in ability_texts:                    # O(T)
    for pattern in compiled_patterns:         # O(P)
        matches = list(pattern["compiled"].finditer(text))  # O(M)
        for match in matches:                  # O(M)
            matches_in_text.append(...)
    
    for i, match1 in enumerate(matches_in_text):    # O(M)
        for match2 in matches_in_text[i+1:]:          # O(M)
            if overlap_check(...):                    # O(1)
                overlaps.append(...)
```

**Optimization:** O(T × P × M) → O(T × P)
- Sort matches by start position
- Use linear scan instead of nested comparison
- Early termination when gaps exceed threshold

### 2. match_dsl_patterns() - O(n^2) complexity  
**Location:** Lines 1954-2050+
**Current Complexity:** O(T × P × L)
- T = number of texts (~627)
- P = number of patterns (168)
- L = average text length

**Problem:**
```python
for text_data in texts:                    # O(T)
    for pattern in LITERAL_PATTERNS:       # O(P)
        match_start = text.find(literal)    # O(L)
        # ... processing ...
    
    for pattern in FAMILY_PATTERNS:        # O(P)  
        start = text.find(prefix)           # O(L)
        end = text.find(suffix, start)      # O(L)
        # ... processing ...
```

**Optimization:** O(T × P × L) → O(T × P)
- Pre-compile all regex patterns
- Use regex search instead of string find where possible
- Cache pattern matching results for repeated texts

### 3. Pattern Matching Inefficiency
**Current:** 168 patterns, each matched against each text
**Optimization:** 
- Pattern grouping by structure
- Early pattern rejection based on text characteristics
- Pattern priority ordering (most specific first)

## Pattern Consolidation Opportunities

### Similar Pattern Structures
Analysis shows patterns could be consolidated by:
1. **Card type variations:** "メンバーカード" vs "ライブカード" vs "エネルギーカード"
   - Unify as: `([^。]+(?:カード|ハート|ブレード))`
   
2. **Zone variations:** "ステージ" vs "控え室" vs "手札" vs "エネルギー置き場"
   - Unify as: `([^。]+(?:ステージ|控え室|手札|エネルギー(?:カード)?置き場))`

3. **Demonstrative variations:** "この" vs "その" vs "あの"
   - Add optional: `(?:この|その|あの)?`

4. **Player reference variations:** "自分" vs "相手" vs "プレイヤー"
   - Add optional: `(?:自分|相手)?`

### Specific Consolidation Candidates
1. **Draw patterns:** Multiple "draw X card" patterns could unify
2. **Place patterns:** Multiple "place X in Y zone" patterns could unify  
3. **Gain patterns:** Multiple "gain X resource" patterns could unify
4. **Condition patterns:** Multiple "if X then Y" patterns could unify

## Implementation Priority

### HIGH PRIORITY (Performance)
1. **Optimize check_pattern_overlap()** - Remove O(n^3) bottleneck
2. **Pre-compile regex patterns** - Cache compiled patterns
3. **Optimize nested loops in match_dsl_patterns()** - Reduce complexity

### MEDIUM PRIORITY (Consolidation)
1. **Unify card type patterns** - Replace hardcoded types with variables
2. **Unify zone patterns** - Replace hardcoded zones with variables
3. **Add optional demonstratives** - Improve pattern flexibility

### LOW PRIORITY (Refinement)
1. **Pattern priority ordering** - Match most specific patterns first
2. **Pattern grouping** - Group similar patterns for efficient matching
3. **Caching strategy** - Cache repeated pattern matches

## Expected Performance Improvements

- **check_pattern_overlap:** O(n^3) → O(n^2) → 10-100x faster
- **match_dsl_patterns:** O(n^2) → O(n log n) → 2-5x faster
- **Pattern consolidation:** 168 → ~100 patterns → 40% reduction
- **Overall runtime:** ~30-60 seconds → ~5-10 seconds

## Manual Inspection Required

1. **Verify overlap detection accuracy** after optimization
2. **Test pattern consolidation** doesn't break coverage
3. **Profile actual runtime** before/after optimizations
4. **Validate atomic variable extraction** after pattern changes
