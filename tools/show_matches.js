const fs = require("fs");
const path = require("path");
const { compareCanonicalToCompiled } = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

const draftPath = "canonical_ability_model/drafts/canonical_full_draft.normalized.json";
const draft = readJson(draftPath);
const entries = draft.entries || [];

const matches = [];

for (const entry of entries) {
  try {
    const canonical = entry.canonical;
    const cardNo = entry.card_no;
    
    const result = compareCanonicalToCompiled(canonical, cardNo, null);
    
    if (result.matches) {
      matches.push({
        card_no: cardNo,
        canonical: result.canonicalLowered,
        compiled: result.compiledLowered
      });
    }
  } catch (error) {
    // skip
  }
}

console.log(`Found ${matches.length} matches`);

for (const m of matches.slice(0, 3)) {
  console.log(`\n===== ${m.card_no} =====`);
  console.log(`Canonical:`, JSON.stringify(m.canonical, null, 2).split('\n').slice(0, 20).join('\n'));
}
