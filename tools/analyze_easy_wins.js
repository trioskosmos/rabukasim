const fs = require("fs");
const path = require("path");
const { compareCanonicalToCompiled } = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

const draft = readJson("canonical_ability_model/drafts/canonical_full_draft.json");
const entries = draft.entries || [];

// Analyze easy patterns
const patterns = {
  draw_only: [],
  draw_discard: [],
  single_effect: [],
  simple_condition: [],
  by_count: {}
};

for (const entry of entries) {
  if (!entry.canonical) continue;
  
  try {
    const result = compareCanonicalToCompiled(entry.canonical, entry.card_no, null);
    
    if (!result.matches) {
      const canonOps = (result.canonicalLowered.effects || []).map(e => e.op);
      const compilOps = (result.compiledLowered.effects || []).map(e => e.op);
      
      // Categorize
      if (canonOps.length === 1 && compilOps.length === 1 && canonOps[0] === "DRAW") {
        patterns.draw_only.push(entry.card_no);
      } else if ((canonOps.join("+") === "DRAW+MOVE_TO_DISCARD" || 
                  canonOps.join("+") === "MOVE_TO_DISCARD+DRAW") &&
                 compilOps.length === 2) {
        patterns.draw_discard.push(entry.card_no);
      } else if (canonOps.length === 1 && compilOps.length === 1) {
        patterns.single_effect.push(entry.card_no);
      } else if (canonOps.length <= 2 && compilOps.length <= 2) {
        patterns.simple_condition.push(entry.card_no);
      }
      
      const key = `${canonOps.length}vs${compilOps.length}`;
      if (!patterns.by_count[key]) patterns.by_count[key] = [];
      patterns.by_count[key].push(entry.card_no);
    }
  } catch (error) {
    // skip
  }
}

console.log(`PHASE B: EASY SEMANTIC WINS\n`);
console.log(`Draw-only mismatches: ${patterns.draw_only.length}`);
if (patterns.draw_only.length > 0) {
  console.log(`  Examples: ${patterns.draw_only.slice(0, 5).join(", ")}`);
}

console.log(`\nDraw+Discard mismatches: ${patterns.draw_discard.length}`);
if (patterns.draw_discard.length > 0) {
  console.log(`  Examples: ${patterns.draw_discard.slice(0, 5).join(", ")}`);
}

console.log(`\nSingle effect (1v1 structure): ${patterns.single_effect.length}`);
if (patterns.single_effect.length > 0) {
  console.log(`  Examples: ${patterns.single_effect.slice(0, 5).join(", ")}`);
  
  // Show what operations are in these single-effect mismatches
  const ops = {};
  for (const card of patterns.single_effect.slice(0, 20)) {
    const entry = entries.find(e => e.card_no === card);
    try {
      const result = compareCanonicalToCompiled(entry.canonical, card, null);
      const op = result.canonicalLowered.effects[0]?.op;
      ops[op] = (ops[op] || 0) + 1;
    } catch (e) {}
  }
  console.log(`  Operation breakdown:`, Object.entries(ops).sort((a,b) => b[1]-a[1]).slice(0, 10).map(([op, count]) => `${op}(${count})`).join(", "));
}

console.log(`\nSimple 1-2 effect patterns: ${patterns.simple_condition.length}`);

console.log(`\nStructure mismatches by count:`);
const sorted = Object.entries(patterns.by_count).sort((a, b) => b[1].length - a[1].length);
for (const [pattern, cards] of sorted.slice(0, 8)) {
  console.log(`  ${pattern}: ${cards.length} cards`);
}
