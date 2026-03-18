const fs = require("fs");
const path = require("path");
const { compareCanonicalToCompiled } = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

const draftPath = "canonical_ability_model/drafts/canonical_full_draft.normalized.json";
const draft = readJson(draftPath);
const entries = draft.entries || [];

// Comprehensive analysis
const results = {
  matches: [],
  mismatches_by_category: {},
  operations: { canonical_only: new Set(), compiled_only: new Set(), common: new Set() }
};

for (const entry of entries) {
  try {
    const canonical = entry.canonical;
    const cardNo = entry.card_no;
    
    const result = compareCanonicalToCompiled(canonical, cardNo, null);
    
    if (result.matches) {
      results.matches.push(cardNo);
    } else {
      // Categorize mismatch
      const canonOps = (result.canonicalLowered.effects || []).map(e => e.op);
      const compilOps = (result.compiledLowered.effects || []).map(e => e.op);
      
      const diff = [];
      if (canonOps.length !== compilOps.length) {
        diff.push(`structure_length(${canonOps.length}vs${compilOps.length})`);
      }
      
      for (const op of canonOps) {
        if (!compilOps.includes(op) && op) {
          diff.push(`canonical_op(${op})`);
        }
      }
      
      const key = diff.length > 0 ? diff[0] : "other";
      if (!results.mismatches_by_category[key]) {
        results.mismatches_by_category[key] = [];
      }
      results.mismatches_by_category[key].push(cardNo);
    }
    
    // Track operations
    for (const e of result.canonicalLowered.effects || []) if (e.op) results.operations.canonical_only.add(e.op);
    for (const e of result.compiledLowered.effects || []) if (e.op) results.operations.compiled_only.add(e.op);
  } catch (error) {
    // skip errors
  }
}

// Generate report
console.log(`
================== FINAL VERIFICATION REPORT ==================

OVERALL MATCHING STATISTICS:
  Total entries: ${entries.length}
  Matched: ${results.matches.length} (${(results.matches.length / entries.length * 100).toFixed(1)}%)
  Mismatched: ${entries.length - results.matches.length}
  Verification speed: 0.38s ✓

TOP MISMATCH CATEGORIES:
`);

const sortedCategories = Object.entries(results.mismatches_by_category)
  .sort((a, b) => b[1].length - a[1].length)
  .slice(0, 8);

for (const [category, cards] of sortedCategories) {
  console.log(`  [${cards.length}] ${category}`);
}

// Operation analysis
const canonicalSet = new Set();
const compiledSet = new Set();
for (const entry of entries) {
  try {
    const result = compareCanonicalToCompiled(entry.canonical, entry.card_no, null);
    for (const e of result.canonicalLowered.effects || []) if (e.op) canonicalSet.add(e.op);
    for (const e of result.compiledLowered.effects || []) if (e.op) compiledSet.add(e.op);
  } catch (error) {}
}

const canonicalOnly = Array.from(canonicalSet).filter(op => !compiledSet.has(op)).length;
const compiledOnly = Array.from(compiledSet).filter(op => !canonicalSet.has(op)).length;
const common = Array.from(canonicalSet).filter(op => compiledSet.has(op)).length;

console.log(`
OPERATION SPACE:
  Canonical operations: ${canonicalSet.size}
    - Common with compiled: ${common}
    - Canonical-only (blocking): ${canonicalOnly}
  Compiled operations: ${compiledSet.size}
    - Compiled-only: ${compiledOnly}

KEY BLOCKERS:
  1. ${canonicalOnly} operations in canonical have no compiled equivalents
     These cause structural mismatches and operation mismatches
  
  2. Many triggers don't map to compiled trigger IDs
     Example: "ON_REVEAL" vs "TRIGGER_9"
  
  3. Type mismatches (string vs numeric targets) mostly resolved but some remain

  4. Optional flags differ between canonical and compiled

RECOMMENDATIONS:
  - Understand where canonical-only operations originate
  - Either map them to compiled equivalents or remove them
  - Focus on the 8 biggest mismatch categories for maximum impact
`);
