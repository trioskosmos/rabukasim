const fs = require("fs");
const path = require("path");

// Import comparison functions
const source = fs.readFileSync("tools/compare_canonical_to_compiled.js", "utf8");
eval(source.split("module.exports")[0]);

// Load data
const canonicalWrapped = JSON.parse(fs.readFileSync("canonical_ability_model/drafts/canonical_full_draft.json", "utf8"));
const compiledDb = JSON.parse(fs.readFileSync("data/cards_compiled.json", "utf8"));

// Find a SELECT_MODE card from the mismatches
const testCard = "PL!-PR-005-PR";
const canonicalEntry = canonicalWrapped.entries.find(c => c.card_no === testCard);
let compiledCard = null;
for (const member of Object.values(compiledDb.member_db || {})) {
  if (member.card_no === testCard) {
    compiledCard = member;
    break;
  }
}

if (!canonicalEntry || !compiledCard) {
  console.log("Card not found");
  process.exit(1);
}

console.log("=== Analyzing", testCard, "===\n");

// Get canonical ability (should have steps with choose_one)
const canonicalObj = canonicalEntry.canonical;
console.log("Canonical trigger:", canonicalObj.trigger);
console.log("Canonical steps count:", canonicalObj.steps?.length);
if (canonicalObj.steps) {
  canonicalObj.steps.forEach((step, idx) => {
    console.log(`  Step ${idx}:`, step.kind, step.op?.[0]?.toUpperCase());
  });
}

// Get compiled ability
const compiledAb = compiledCard.abilities[0];
console.log("\nCompiled trigger:", compiledAb.trigger);
console.log("Compiled effects count:", compiledAb.effects?.length);
if (compiledAb.modal_options) {
  console.log("Compiled modal_options branches:", compiledAb.modal_options.length);
}

// Try to compare them
console.log("\n=== Attempting Comparison ===");
const canonicalNormalized = lowerCanonicalAbility(canonicalObj);
const compiledNormalized = normalizeCompiledAbility(compiledAb);

console.log("\nCanonical normalized effects:", canonicalNormalized.effects?.length);
if (canonicalNormalized.effects) {
  canonicalNormalized.effects.forEach((e, i) => {
    console.log(`  Effect ${i}: op=${e.op}, branches=${e.branches?.length || "none"}`);
  });
}

console.log("\nCompiled normalized effects:", compiledNormalized.effects?.length);
if (compiledNormalized.effects) {
  compiledNormalized.effects.forEach((e, i) => {
    console.log(`  Effect ${i}: op=${e.op}, branches=${e.branches?.length || "none"}`);
  });
}

// Check match
const matches = compareStructures(canonicalNormalized, compiledNormalized);
console.log("\nMatches:", matches);
