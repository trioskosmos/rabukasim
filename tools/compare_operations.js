const fs = require("fs");
const path = require("path");
const {
  compareCanonicalToCompiled,
  lowerCanonicalAbility,
  findCompiledAbility
} = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

const draftPath = "canonical_ability_model/drafts/canonical_full_draft.normalized.json";
const draft = readJson(draftPath);
const entries = draft.entries || [];

// Find all operations in canonical
const canonicalOps = new Set();
const compiledOps = new Set();

for (const entry of entries) {
  try {
    const canonical = entry.canonical;
    const cardNo = entry.card_no;
    
    const result = compareCanonicalToCompiled(canonical, cardNo, null);
    
    for (const effect of result.canonicalLowered.effects || []) {
      if (effect.op) canonicalOps.add(effect.op);
    }
    for (const effect of result.compiledLowered.effects || []) {
      if (effect.op) compiledOps.add(effect.op);
    }
  } catch (error) {
    // skip
  }
}

const canonicalOnly = Array.from(canonicalOps).filter(op => !compiledOps.has(op)).sort();
const compiledOnly = Array.from(compiledOps).filter(op => !canonicalOps.has(op)).sort();
const common = Array.from(canonicalOps).filter(op => compiledOps.has(op)).sort();

console.log(`Canonical operations: ${canonicalOps.size}`);
console.log(`Compiled operations: ${compiledOps.size}`);
console.log(`\nCommon operations: ${common.length}`);
console.log(common.join(", "));

console.log(`\nCanonical-ONLY operations (${canonicalOnly.length}):`);
console.log(canonicalOnly.join(", "));

console.log(`\nCompiled-ONLY operations (${compiledOnly.length}):`);
console.log(compiledOnly.join(", "));

// Count how many mismatches are due to canonical-only ops
let canonicalOnlyCount = 0;
for (const entry of entries) {
  try {
    const canonical = entry.canonical;
    const cardNo = entry.card_no;
    
    const result = compareCanonicalToCompiled(canonical, cardNo, null);
    
    if (!result.matches) {
      const hasCanonicalOnly = (result.canonicalLowered.effects || []).some(e => canonicalOnlyCount.has(e.op));
      if (hasCanonicalOnly) canonicalOnlyCount++;
    }
  } catch (error) {
    // skip
  }
}

console.log(`\nMismatches involving canonical-only ops: ${canonicalOnlyCount}`);
