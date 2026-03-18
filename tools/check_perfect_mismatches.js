const fs = require("fs");
const path = require("path");
const { compareCanonicalToCompiled } = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

const draft = readJson("canonical_ability_model/drafts/canonical_full_draft.json");
const entries = draft.entries || [];

let perfectCount = 0;

for (const entry of entries) {
  if (!entry.canonical) continue;
  
  try {
    const result = compareCanonicalToCompiled(entry.canonical, entry.card_no, null);
    
    if (!result.matches) {
      const canonOps = (result.canonicalLowered.effects || []);
      const compilOps = (result.compiledLowered.effects || []);
      
      if (canonOps.length === 1 && compilOps.length === 1) {
        const canonStr = JSON.stringify(canonOps[0]);
        const compStr = JSON.stringify(compilOps[0]);
        
        if (canonStr === compStr) {
          perfectCount++;
          if (perfectCount <= 3) {
            console.log(`\n===== ${entry.card_no} =====`);
            console.log(`Canonical: ${canonStr}`);
            console.log(`Compiled:  ${compStr}`);
            console.log(`Full canonical lowered:`, JSON.stringify(result.canonicalLowered, null, 2).split('\n').slice(0, 15).join('\n'));
            console.log(`Full compiled lowered:`, JSON.stringify(result.compiledLowered, null, 2).split('\n').slice(0, 15).join('\n'));
          }
        }
      }
    }
  } catch (error) {
    // skip
  }
}

console.log(`\nTotal perfect matches not recognized: ${perfectCount}`);
