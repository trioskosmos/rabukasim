#!/usr/bin/env node
const fs = require("fs");

// Load data
const canonicalWrapped = JSON.parse(fs.readFileSync("canonical_ability_model/drafts/canonical_full_draft.json", "utf8"));
const compiledDb = JSON.parse(fs.readFileSync("data/cards_compiled.json", "utf8"));

// Create lookup
const compiledByCardNo = new Map();
for (const member of Object.values(compiledDb.member_db || {})) {
  if (!compiledByCardNo.has(member.card_no)) {
    compiledByCardNo.set(member.card_no, []);
  }
  compiledByCardNo.get(member.card_no).push(member);
}

// Find trigger mismatches - use first compiledCard for each entry
const triggerMismatches = [];

for (const entry of canonicalWrapped.entries) {
  const compiledCards = compiledByCardNo.get(entry.card_no);
  if (!compiledCards || compiledCards.length === 0) continue;
  
  const canonicalObj = entry.canonical;
  if (!canonicalObj) continue;
  
  const compiledCard = compiledCards[0]; // Just use first card variant
  if (!compiledCard.abilities || compiledCard.abilities.length === 0) continue;
  
  // Canonical should have abilities array
  if (!canonicalObj.abilities || canonicalObj.abilities.length === 0) continue;
  
  // Check trigger of first ability
  const canonAb = canonicalObj.abilities[0];
  const compilAb = compiledCard.abilities[0];
  
  if (!canonAb || !compilAb) continue;
  
  const canonTrigger = canonAb.trigger;
  const compilTrigger = compilAb.trigger;
  
  if (canonTrigger !== compilTrigger) {
    triggerMismatches.push({
      card_no: entry.card_no,
      canonical_trigger: canonTrigger,
      compiled_trigger: compilTrigger,
      compiled_trigger_name: getTriggerName(compilTrigger),
      canonical_trigger_name: canonTrigger,
      pseudocode: canonAb.pseudocode?.split("\n")[0] || "",
      compiled_raw: compilAb.raw_text?.substring(0, 70) || "",
    });
  }
}

function getTriggerName(triggerCode) {
  const names = {
    1: "ON_PLAY",
    2: "ON_LIVE_START",
    3: "ON_LIVE_END",
    4: "ACTIVATED",
    5: "CONSTANT",
    6: "ON_MEMBER_TAP",
    7: "ON_LEAVES",
  };
  return names[triggerCode] || `TRIGGER_${triggerCode}`;
}

// Sort by frequency of mismatch
const mismatchFreq = {};
for (const m of triggerMismatches) {
  const key = `${m.canonical_trigger_name}→${m.compiled_trigger_name}`;
  if (!mismatchFreq[key]) mismatchFreq[key] = [];
  mismatchFreq[key].push(m);
}

console.log("=== TRIGGER MISMATCHES ===\n");
console.log(`Total cards with trigger mismatches: ${triggerMismatches.length}\n`);

// Show by pattern
const patterns = Object.entries(mismatchFreq).sort((a, b) => b[1].length - a[1].length);
for (const [pattern, cards] of patterns) {
  console.log(`\n[${cards.length}] ${pattern}`);
  cards.slice(0, 3).forEach(m => {
    console.log(`  - ${m.card_no}`);
    console.log(`    Canon: ${m.pseudocode.substring(0, 50)}`);
    console.log(`    Compiled: ${m.compiled_raw}`);
  });
  if (cards.length > 3) {
    console.log(`  ... and ${cards.length - 3} more`);
  }
}

// Save for reference
fs.writeFileSync("trigger_mismatches.json", JSON.stringify({
  total: triggerMismatches.length,
  patterns: patterns.map(([p, cards]) => ({
    pattern: p,
    count: cards.length,
    cards: cards.map(c => c.card_no)
  })),
}, null, 2));

console.log("\n→ Details saved to: trigger_mismatches.json");

