const fs = require("fs");
const path = require("path");

const draftPath = process.argv[2] || "canonical_ability_model/drafts/canonical_full_draft.normalized.json";
const cardFilter = process.argv[3] || "LL-bp1-001-R";

const draft = JSON.parse(fs.readFileSync(draftPath, "utf8"));
const entries = draft.entries || [];

const matches = entries.filter(e => e.card_no.includes(cardFilter));

if (matches.length === 0) {
  console.log(`No cards matching "${cardFilter}"`);
  process.exit(1);
}

for (const entry of matches.slice(0, 1)) {
  console.log(`\nCard: ${entry.card_no}`);
  console.log(`Ability UID: ${entry.ability_uid}`);
  console.log(`\nCanonical Structure:`);
  console.log(JSON.stringify(entry.canonical, null, 2));
}
