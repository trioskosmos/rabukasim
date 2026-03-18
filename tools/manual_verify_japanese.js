#!/usr/bin/env node
const fs = require("fs");

// Load data
const canonicalWrapped = JSON.parse(fs.readFileSync("canonical_ability_model/drafts/canonical_full_draft.json", "utf8"));
const compiledDb = JSON.parse(fs.readFileSync("data/cards_compiled.json", "utf8"));

// Create compiled lookup
const compiledByCardNo = new Map();
for (const member of Object.values(compiledDb.member_db || {})) {
  if (!compiledByCardNo.has(member.card_no)) {
    compiledByCardNo.set(member.card_no, []);
  }
  compiledByCardNo.get(member.card_no).push(member);
}

// Low confidence cards should be manually reviewed against Japanese
const lowConfidenceCards = canonicalWrapped.entries
  .filter(e => e.canonical && (e.canonical.confidence === "low" || e.canonical.confidence === "medium"))
  .slice(0, 20);

console.log("=== MANUAL VERIFICATION REQUIRED: Low/Medium Confidence Cards ===\n");
console.log(`Showing ${lowConfidenceCards.length} cards for manual Japanese text review\n`);

lowConfidenceCards.forEach((entry, idx) => {
  const compiled = compiledByCardNo.get(entry.card_no);
  if (!compiled || !compiled[0]) return;
  
  const compiledCard = compiled[0];
  const canonicalObj = entry.canonical;
  
  console.log(`\n${"=".repeat(70)}`);
  console.log(`${idx + 1}. ${entry.card_no} [CONFIDENCE: ${canonicalObj.confidence}]`);
  console.log(`${"=".repeat(70)}\n`);
  
  console.log("ORIGINAL JAPANESE TEXT:");
  console.log(compiledCard.original_text);
  
  console.log("\n" + "-".repeat(70));
  console.log("CANONICAL PSEUDOCODE:");
  console.log(canonicalObj.pseudocode);
  
  console.log("\n" + "-".repeat(70));
  console.log("COMPILED EXTRACTION:");
  if (compiledCard.abilities && compiledCard.abilities[0]) {
    console.log(compiledCard.abilities[0].raw_text);
  }
  
  console.log("\n" + "-".repeat(70));
  console.log(`VERDICT: [ ] MATCHES | [ ] NEEDS FIX`);
  console.log(`NOTES: _________________________________________________________________\n`);
});

console.log("\n" + "=".repeat(70));
console.log("INSTRUCTIONS:");
console.log("1. Review each card's Japanese text above");
console.log("2. Compare with canonical pseudocode");
console.log("3. If pseudocode doesn't match Japanese → needs manual fix");
console.log("4. Edit canonical_ability_model/drafts/canonical_full_draft.json");
console.log("5. Update the 'pseudocode' and 'steps' fields to match actual Japanese");

console.log("\nAfter corrections, run:");
console.log("  node tools/test_normalized_canonical_draft.js canonical_ability_model/drafts/canonical_full_draft.json");
