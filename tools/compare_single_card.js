const fs = require("fs");
const {
  compareCanonicalToCompiled,
  lowerCanonicalAbility,
  normalizeCompiledAbility,
  findCompiledAbility,
  pruneNulls
} = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

const draftPath = process.argv[2] || "canonical_ability_model/drafts/canonical_full_draft.normalized.json";
const cardFilter = process.argv[3] || "LL-bp1-001";

const draft = readJson(draftPath);
const entries = draft.entries || [];

let targetEntry = null;
for (const entry of entries) {
  if (entry.card_no.includes(cardFilter)) {
    targetEntry = entry;
    break;
  }
}

if (!targetEntry) {
  console.log(`No cards matching "${cardFilter}"`);
  process.exit(1);
}

console.log(`\n========== CARD: ${targetEntry.card_no} ==========\n`);

try {
  const canonical = targetEntry.canonical;
  const cardNo = targetEntry.card_no;
  
  const result = compareCanonicalToCompiled(canonical, cardNo, null);
  
  console.log(`Canonical (lowered):`);
  console.log(JSON.stringify(result.canonicalLowered, null, 2));
  
  console.log(`\nCompiled (normalized):`);
  console.log(JSON.stringify(result.compiledLowered, null, 2));
  
  console.log(`\nMatches:`, result.matches);
  console.log(`Supported:`, result.supported);
  
} catch (error) {
  console.log(`Error: ${error.message}`);
  console.log(error.stack);
}
