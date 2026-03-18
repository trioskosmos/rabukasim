const fs = require("fs");
const path = require("path");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

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
  if (entry && entry.canonical) {
    console.log(`\n========== ${cardNo} ==========`);
    console.log(`Raw: ${entry.canonical.raw_text?.split('\n')[0]}`);
    console.log(`Issue: Invalid condition at steps[0].condition[0]`);
    console.log(`\nCanonical structure:`);
    console.log(JSON.stringify(entry.canonical, null, 2).split('\n').slice(0, 40).join('\n'));
  }
}
