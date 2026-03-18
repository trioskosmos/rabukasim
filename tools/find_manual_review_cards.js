#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

// Load data
const canonicalWrapped = JSON.parse(fs.readFileSync("canonical_ability_model/drafts/canonical_full_draft.json", "utf8"));
const compiledDb = JSON.parse(fs.readFileSync("data/cards_compiled.json", "utf8"));

// Create a lookup for compiled cards
const compiledByCardNo = new Map();
for (const member of Object.values(compiledDb.member_db || {})) {
  compiledByCardNo.set(member.card_no, member);
}

// Simple comparison: check if pseudocode suggests something different than compiled
const mismatchDetails = [];

for (const entry of canonicalWrapped.entries) {
  const compiled = compiledByCardNo.get(entry.card_no);
  if (!compiled || !compiled.abilities || compiled.abilities.length === 0) continue;
  
  const canonicalObj = entry.canonical;
  if (!canonicalObj) continue;
  
  // Skip cards with known issues
  if (entry.issues && entry.issues.length > 0) continue;
  
  const compiledAb = compiled.abilities[0];
  
  // Basic structural comparison
  const canonTrigger = canonicalObj.trigger;
  const compilTrigger = compiledAb.trigger;
  
  // Check if they seem fundamentally misaligned
  const pseudoLines = (canonicalObj.pseudocode || "").split("\n");
  
  mismatchDetails.push({
    card_no: entry.card_no,
    confidence: canonicalObj.confidence,
    pseudocode_first_line: pseudoLines[0] || "",
    canonical_trigger: canonTrigger,
    compiled_trigger: compilTrigger,
    compiled_raw_text: compiledAb.raw_text?.substring(0, 80) || "(no text)",
  });
}

// Sort by confidence - HIGH confidence mismatches are highest priority
const byConfidence = {};
for (const detail of mismatchDetails) {
  if (!byConfidence[detail.confidence]) byConfidence[detail.confidence] = [];
  byConfidence[detail.confidence].push(detail);
}

console.log("=== CARDS NEEDING MANUAL VERIFICATION ===\n");
console.log(`Total cards analyzed: ${mismatchDetails.length}\n`);

// Show top HIGH confidence cards  
const highCards = (byConfidence.high || []).slice(0, 15);
if (highCards.length > 0) {
  console.log(`\n=== HIGH CONFIDENCE (${highCards.length} shown of ${byConfidence.high?.length || 0}) ===\n`);
  highCards.forEach((card, idx) => {
    console.log(`${idx + 1}. ${card.card_no}`);
    console.log(`   Pseudocode: ${card.pseudocode_first_line}`);
    console.log(`   Compiled: ${card.compiled_raw_text}`);
    console.log("");
  });
}

console.log("\n=== SUMMARY ===");
console.log(`High confidence: ${byConfidence.high?.length || 0} cards`);
console.log(`Medium confidence: ${byConfidence.medium?.length || 0} cards`);
console.log(`Low confidence: ${byConfidence.low?.length || 0} cards`);

// Export for reference
fs.writeFileSync("manual_review_cards.json", JSON.stringify({
  summary: {
    total: mismatchDetails.length,
    high: byConfidence.high?.length || 0,
    medium: byConfidence.medium?.length || 0,
    low: byConfidence.low?.length || 0,
  },
  high_priority: highCards,
  all: mismatchDetails
}, null, 2));

console.log("\n→ Full list saved to: manual_review_cards.json");

