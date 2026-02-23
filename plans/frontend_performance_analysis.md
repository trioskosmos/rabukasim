# Frontend Performance Analysis

## Overview
This document identifies potential performance bottlenecks and excessive resource usage in the LovecaSim frontend.

---

## Critical Issues

### 1. Excessive DOM Rebuilding (HIGH IMPACT)

**Location:** [`ui_rendering.js`](frontend/web_ui/js/ui_rendering.js)

**Problem:** The `renderInternal()` function completely rebuilds DOM elements on every state change:
- `el.innerHTML = ''` is used extensively to clear containers
- All card elements are recreated from scratch each render
- No virtual DOM or diffing mechanism

**Affected Functions:**
- `renderCards()` - Lines 191-282
- `renderStage()` - Lines 284-343
- `renderEnergy()` - Lines 345-381
- `renderLiveZone()` - Lines 383-437
- `renderActions()` - Lines 559-800+

**Impact:** Every state update triggers full DOM reconstruction, causing:
- Layout thrashing
- Reflow and repaint storms
- Memory churn from discarded DOM nodes

**Recommendation:** Implement DOM diffing or keyed reconciliation:
```javascript
// Instead of innerHTML = '', use conditional updates:
if (existingCardEl && existingCardEl.dataset.cardId == card.id) {
    // Update existing element
} else {
    // Create new element
}
```

---

### 2. Unoptimized Regex Operations (MEDIUM IMPACT)

**Location:** [`ui_tooltips.js`](frontend/web_ui/js/ui_tooltips.js) - `enrichAbilityText()`

**Problem:** Multiple regex operations create new RegExp objects on every call:
```javascript
// Lines 41-64: Each regex is compiled on every call
text = text.replace(/(ピンク|レッド|...)/g, ...);
const zoneRegex = new RegExp(`(${zoneList.join('|')})`, 'g');
```

**Impact:** Called for every card tooltip, every log entry, every action button.

**Recommendation:** Pre-compile regex patterns:
```javascript
// At module level:
const COLOR_REGEX = /(ピンク|レッド|赤|...)/g;
const ZONE_REGEX = /(控え室|メンバー置場|...)/g;
```

---

### 3. Linear Card Lookups (MEDIUM IMPACT)

**Location:** [`state.js`](frontend/web_ui/js/state.js) - `resolveCardData()`

**Problem:** Card lookup searches all zones linearly:
```javascript
// Lines 74-108: Nested loops through all players and zones
for (const p of state.players) {
    if (p.hand) {
        const c = p.hand.find(x => x && x.id === cid);  // O(n)
    }
    // ... repeated for stage, live_zone, energy, discard, waiting_room
}
```

**Impact:** Called frequently from tooltips and rendering. O(n*m) where n=cards, m=zones.

**Recommendation:** Build and maintain a card ID index:
```javascript
// Build index on state update:
State.cardIndex = {};
state.players.forEach((p, pi) => {
    p.hand?.forEach(c => { if (c) State.cardIndex[c.id] = c; });
    // ... other zones
});
```

---

### 4. Log Rendering Inefficiency (MEDIUM IMPACT)

**Location:** [`ui_logs.js`](frontend/web_ui/js/ui_logs.js) - `renderRuleLog()`

**Problem:** 
- Entire log is re-rendered on every state change
- Regex parsing performed on every log entry every render
- No virtualization for long logs

**Lines 28-143:** Complete rebuild of all log entries.

**Recommendation:**
- Implement log entry caching
- Use virtual scrolling for long logs
- Only append new entries instead of full rebuild

---

### 5. Asset Hash Calculation (LOW-MEDIUM IMPACT)

**Location:** [`ui_rendering.js`](frontend/web_ui/js/ui_rendering.js) - Lines 74-88

**Problem:** Asset list is built and hashed on every render:
```javascript
const assetsToLoad = [];
state.players.forEach(p => {
    if (p.hand) p.hand.forEach(c => { if (c && c.img) assetsToLoad.push(fixImg(c.img)); });
    // ...
});
const assetsHash = assetsToLoad.join('|');  // String concatenation
```

**Impact:** Creates large temporary arrays and strings every frame.

**Recommendation:** Only recalculate when state actually changes:
```javascript
if (State.lastStateJson !== JSON.stringify(state)) {
    // Recalculate assets
    State.lastStateJson = JSON.stringify(state);
}
```

---

## Secondary Issues

### 6. Multiple getElementById Calls

**Location:** Throughout rendering code

**Problem:** Same elements queried repeatedly:
```javascript
const turnEl = document.getElementById('turn');
const phaseEl = document.getElementById('phase');
const scoreEl = document.getElementById('score');
// ... repeated every render
```

**Recommendation:** Cache element references at module level.

---

### 7. Event Handler Recreation

**Location:** [`ui_rendering.js`](frontend/web_ui/js/ui_rendering.js) - `createActionButton()`

**Problem:** New onclick/onmouseenter/onmouseleave functions created for every button on every render.

**Recommendation:** Use event delegation on parent containers.

---

### 8. Tooltip Processing Overhead

**Location:** [`ui_tooltips.js`](frontend/web_ui/js/ui_tooltips.js)

**Problem:** `getEffectiveRawText()` and `enrichAbilityText()` called excessively:
- Once for rendering (data-text attribute)
- Again on hover
- Multiple times for same card in different contexts

**Recommendation:** Cache processed text on card objects.

---

## Memory Concerns

### 9. No Cleanup of Discarded DOM Nodes

**Problem:** When `innerHTML = ''` is used, event listeners and references may not be garbage collected if there are closures referencing them.

### 10. Growing Log Data

**Location:** State management

**Problem:** `rule_log` array grows unbounded throughout game.

---

## Recommended Priority

1. **HIGH:** Implement DOM diffing/keyed reconciliation in render functions
2. **HIGH:** Pre-compile regex patterns in ui_tooltips.js
3. **MEDIUM:** Add card ID index for O(1) lookups
4. **MEDIUM:** Cache DOM element references
5. **LOW:** Implement event delegation
6. **LOW:** Add log virtualization

---

## Quick Wins

These changes can be made immediately with minimal risk:

1. Move regex compilation to module level
2. Cache frequently accessed DOM elements
3. Add early returns when state hasn't changed
4. Debounce rapid state updates

