const fs = require("fs");

// Load canonical and compiled
const canonicalWrapped = JSON.parse(fs.readFileSync("canonical_ability_model/drafts/canonical_full_draft.json", "utf8"));
const compiledDb = JSON.parse(fs.readFileSync("data/cards_compiled.json", "utf8"));

// Get card PL!-PR-005-PR
const canonicalEntry = canonicalWrapped.entries.find(c => c.card_no === "PL!-PR-005-PR");

// Find compiled card by looking through member_db
let compiledCard = null;
for (const member of Object.values(compiledDb.member_db || {})) {
  if (member.card_no === "PL!-PR-005-PR") {
    compiledCard = member;
    break;
  }
}

console.log("=== CANONICAL PL!-PR-005-PR ===");
if (canonicalEntry && canonicalEntry.canonical && canonicalEntry.canonical.abilities) {
  canonicalEntry.canonical.abilities.forEach((ab, idx) => {
    console.log(`Ability ${idx}: trigger=${ab.trigger}, effects=${ab.effects?.length || 0}, steps=${ab.steps?.length || 0}`);
    if (ab.steps) {
      ab.steps.forEach((step, sidx) => {
        console.log(`  Step ${sidx}: kind=${step.kind}, op=${step.op}`);
      });
    }
  });
}

console.log("\n=== COMPILED PL!-PR-005-PR ===");
if (compiledCard && compiledCard.abilities) {
  compiledCard.abilities.forEach((ab, idx) => {
    console.log(`Ability ${idx}: trigger=${ab.trigger}, effects=${ab.effects?.length || 0}`);
    if (ab.effects) {
      ab.effects.forEach((effect, eidx) => {
        console.log(`  Effect ${eidx}: runtime_opcode=${effect.runtime_opcode}, modal=${ab.modal_options?.length || 0} branches`);
      });
    }
  });
}
