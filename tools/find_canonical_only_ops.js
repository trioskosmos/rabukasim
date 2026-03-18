const fs = require("fs");
const path = require("path");
const { compareCanonicalToCompiled } = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

const CANONICAL_ONLY_OPS = [
  "SELECT_RECOVER_LIVE", "LOOK_AND_CHOOSE_SPLIT", "HEART_SELECT",
  "PREVENT_LIVE", "SELECT_SUCCESS_LIVE", "PLAY_MEMBER", "LOOK_AND_CHOOSE_REVEAL"
];

const draftPath = "canonical_ability_model/drafts/canonical_full_draft.normalized.json";
const draft = readJson(draftPath);
const entries = draft.entries || [];

// Find cards with these operations
for (const op of CANONICAL_ONLY_OPS.slice(0, 3)) {
  console.log(`\n===== Cards with ${op} =====`);
  let count = 0;
  
  for (const entry of entries) {
    try {
      const canonical = entry.canonical;
      const cardNo = entry.card_no;
      
      const result = compareCanonicalToCompiled(canonical, cardNo, null);
      
      const hasOp = (result.canonicalLowered.effects || []).some(e => e.op === op);
      if (hasOp) {
        console.log(`\nCard: ${cardNo}`);
        console.log(`Raw: ${canonical.raw_text?.split('\n')[0]}`);
        console.log(`Canonical effects:`, result.canonicalLowered.effects.map(e => e.op).join(", "));
        console.log(`Compiled effects:`, result.compiledLowered.effects.map(e => e.op).join(", "));
        
        count++;
        if (count >= 2) break;
      }
    } catch (error) {
      // skip
    }
  }
  
  if (count === 0) {
    console.log("(No cards found - might be in unsupported steps)");
  }
}
