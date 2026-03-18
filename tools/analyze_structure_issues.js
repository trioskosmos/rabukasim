const fs = require("fs");
const path = require("path");
const {
  compareCanonicalToCompiled,
  lowerCanonicalAbility,
  normalizeCompiledAbility,
  pruneNulls
} = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

const draftPath = "canonical_ability_model/drafts/canonical_full_draft.normalized.json";
const draft = readJson(draftPath);
const entries = draft.entries || [];

// Find structure_length issues that are OPPOSITE (compiled > canonical)
const canonicalFewer = [];
const compiledFewer = [];

for (const entry of entries) {
  try {
    const canonical = entry.canonical;
    const cardNo = entry.card_no;
    
    const result = compareCanonicalToCompiled(canonical, cardNo, null);
    
    if (!result.matches) {
      const canonLen = result.canonicalLowered.effects.length;
      const compiledLen = result.compiledLowered.effects.length;
      
      if (canonLen > compiledLen) {
        canonicalFewer.push({ card_no: cardNo, canonLen, compiledLen, canonical: result.canonicalLowered, compiled: result.compiledLowered });
      } else if (compiledLen > canonLen) {
        compiledFewer.push({ card_no: cardNo, canonLen, compiledLen, canonical: result.canonicalLowered, compiled: result.compiledLowered });
      }
    }
  } catch (error) {
    // skip
  }
}

console.log(`Structure length issues: `);
console.log(`  Canonical > Compiled: ${canonicalFewer.length}`);
console.log(`  Compiled > Canonical: ${compiledFewer.length}`);

console.log(`\n=== SAMPLE: Canonical has MORE effects ===`);
if (canonicalFewer.length > 0) {
  const sample = canonicalFewer[0];
  console.log(`Card: ${sample.card_no} (canonical: ${sample.canonLen}, compiled: ${sample.compiledLen})`);
  console.log(`Canonical effects:`, sample.canonical.effects.map(e => e.op).join(", "));
  console.log(`Compiled effects:`, sample.compiled.effects.map(e => e.op).join(", "));
}

console.log(`\n=== SAMPLE: Compiled has MORE effects ===`);
if (compiledFewer.length > 0) {
  const sample = compiledFewer[0];
  console.log(`Card: ${sample.card_no} (canonical: ${sample.canonLen}, compiled: ${sample.compiledLen})`);
  console.log(`Canonical effects:`, sample.canonical.effects.map(e => e.op).join(", "));
  console.log(`Compiled effects:`, sample.compiled.effects.map(e => e.op).join(", "));
  console.log(`\nFull compiled:`, JSON.stringify(sample.compiled, null, 2).split('\n').slice(0, 30).join('\n'));
}
