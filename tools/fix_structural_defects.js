const fs = require("fs");
const path = require("path");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

function writeJson(filePath, data) {
  fs.writeFileSync(path.join(process.cwd(), filePath), JSON.stringify(data, null, 2), "utf8");
}

// Fix pattern: condition at top level needs to be wrapped in an if statement
// steps[0] = if (optional move)
// steps[1] = condition -> should be steps[0].condition
// steps[2] = effect -> should be steps[0].then

const failingCards = [
  "PL!HS-PR-019-PR",
  "PL!HS-bp5-001-AR",
  "PL!HS-sd1-013-SD",
  "PL!S-bp2-006-P",
  "PL!S-bp2-021-L"
];

const draft = readJson("canonical_ability_model/drafts/canonical_full_draft.json");
const entries = draft.entries || [];

for (const cardNo of failingCards) {
  const entry = entries.find(e => e.card_no === cardNo);
  if (entry && entry.canonical && entry.canonical.steps) {
    const steps = entry.canonical.steps;
    
    // Pattern: if -> condition -> effect should become
    //          if with condition and then
    if (steps.length >= 3 &&
        steps[0].kind === "if" &&
        steps[1].kind === "condition" &&
        steps[2].kind === "effect") {
      
      console.log(`Fixing ${cardNo}`);
      
      // Move the condition into the if block
      steps[0].condition = steps[1];
      
      // Move the effect into then
      if (!steps[0].then) steps[0].then = [];
      steps[0].then.push(steps[2]);
      
      // Remove the old condition and effect steps
      entry.canonical.steps = [steps[0]];
      
      console.log(`  -> Restructured: moved condition and effect into if statement`);
    }
  }
}

// Write the fixed draft
writeJson("canonical_ability_model/drafts/canonical_full_draft.json", draft);
console.log(`\nFixed ${failingCards.length} cards and saved to canonical_full_draft.json`);
