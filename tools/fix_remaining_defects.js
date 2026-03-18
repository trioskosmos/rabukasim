const fs = require("fs");

const draft = JSON.parse(fs.readFileSync("canonical_ability_model/drafts/canonical_full_draft.json", "utf8"));
const entries = draft.entries || [];

const cardsToFix = ["PL!S-bp2-006-P", "PL!S-bp2-021-L"];

for (const cardNo of cardsToFix) {
  const entry = entries.find(e => e.card_no === cardNo);
  if (entry && entry.canonical && entry.canonical.steps) {
    console.log(`Fixing ${cardNo}`);
    
    for (const step of entry.canonical.steps) {
      if (step.kind === "if" && step.condition) {
        // The condition should be a valid step kind
        // If it's just { "op": "choose_yes" }, we need to add kind: "condition"
        if (!step.condition.kind) {
          step.condition.kind = "condition";
          console.log(`  -> Added kind:"condition" to if condition`);
        }
      }
    }
  }
}

fs.writeFileSync("canonical_ability_model/drafts/canonical_full_draft.json", JSON.stringify(draft, null, 2), "utf8");
console.log(`\nSaved fixes to canonical_full_draft.json`);
