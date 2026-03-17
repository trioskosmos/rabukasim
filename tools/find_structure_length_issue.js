const fs = require("fs");
const path = require("path");
const {
  compareCanonicalToCompiled,
  lowerCanonicalAbility,
  normalizeCompiledAbility,
  findCompiledAbility,
  pruneNulls
} = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

const draftPath = "canonical_ability_model/drafts/canonical_full_draft.normalized.json";
const draft = readJson(draftPath);
const entries = draft.entries || [];

// Find examples of each major problem
for (const entry of entries) {
  try {
    const canonical = entry.canonical;
    const cardNo = entry.card_no;
    
    const result = compareCanonicalToCompiled(canonical, cardNo, null);
    
    if (!result.matches) {
      const canonLen = result.canonicalLowered.effects.length;
      const compiledLen = result.compiledLowered.effects.length;
      
      // Find structure_length issue
      if (canonLen !== compiledLen) {
        console.log(`\n========== STRUCTURE LENGTH MISMATCH: ${cardNo} ==========`);
        console.log(`Canonical effects: ${canonLen}, Compiled effects: ${compiledLen}\n`);
        
        console.log(`Canonical:`);
        console.log(JSON.stringify(result.canonicalLowered, null, 2).split('\n').slice(0, 40).join('\n'));
        
        console.log(`\nCompiled:`);
        console.log(JSON.stringify(result.compiledLowered, null, 2).split('\n').slice(0, 40).join('\n'));
        
        process.exit(0);
      }
    }
  } catch (error) {
    // skip errors
  }
}

console.log("No structure_length mismatch found");
