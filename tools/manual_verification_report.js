const fs = require("fs");

// Load data
const canonicalWrapped = JSON.parse(fs.readFileSync("canonical_ability_model/drafts/canonical_full_draft.json", "utf8"));
const compiledDb = JSON.parse(fs.readFileSync("data/cards_compiled.json", "utf8"));

// Create a lookup for compiled cards
const compiledByCardNo = new Map();
for (const member of Object.values(compiledDb.member_db || {})) {
  compiledByCardNo.set(member.card_no, member);
}

// Find mismatches and show Japanese text for manual review
const mismatches = [];

for (const entry of canonicalWrapped.entries) {
  const compiled = compiledByCardNo.get(entry.card_no);
  if (!compiled) continue;
  
  // Check if canonical matches compiled
  const canonicalObj = entry.canonical;
  const compiledAb = compiled.abilities[0];
  
  if (!canonicalObj || !compiledAb) continue;
  
  // Get the issues
  if (entry.issues && entry.issues.length > 0) {
    continue; // Skip entries with known structural issues
  }
  
  // Extract pseudocode vs original text
  mismatches.push({
    card_no: entry.card_no,
    pseudocode: canonicalObj.pseudocode,
    raw_text: canonicalObj.raw_text,
    original_text_jp: compiled.original_text,
    original_text_en: compiledAb.raw_text,
    confidence: canonicalObj.confidence,
  });
}

// Sort by confidence and show sample cards for manual review
const lowConfidence = mismatches.filter(m => m.confidence === "medium" || m.confidence === "low");
const highConfidence = mismatches.filter(m => m.confidence === "high");

console.log(`HIGH CONFIDENCE (${highConfidence.length}): Show first 10 for random verification\n`);
highConfidence.slice(0, 10).forEach(m => {
  console.log(`\n==== ${m.card_no} ====`);
  console.log(`PSEUDOCODE:\n${m.pseudocode}\n`);
  console.log(`RAW EXTRACT:\n${m.raw_text}\n`);
  console.log(`ORIGINAL JP:\n${m.original_text_jp}\n`);
  console.log(`COMPILED:\n${m.original_text_en}\n`);
  console.log("---");
});

console.log(`\n\nMEDIUM/LOW CONFIDENCE (${lowConfidence.length}): Priority for manual fix`);
lowConfidence.slice(0, 15).forEach(m => {
  console.log(`\n==== ${m.card_no} [${m.confidence}] ====`);
  console.log(`PSEUDOCODE:\n${m.pseudocode}\n`);
  console.log(`ORIGINAL JP:\n${m.original_text_jp}`);
});
