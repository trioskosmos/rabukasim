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

let fixCount = 0;
let processCount = 0;

// Find and fix mismatches
for (let i = 0; i < canonicalWrapped.entries.length; i++) {
  const entry = canonicalWrapped.entries[i];
  const compiled = compiledByCardNo.get(entry.card_no);
  
  if (!compiled || !compiled[0]) continue;
  if (!entry.canonical) continue;
  
  processCount++;
  
  const canonicalObj = entry.canonical;
  const compiledCard = compiled[0];
  const compiledAb = compiledCard.abilities[0];
  
  if (!compiledAb) continue;
  
  // Check if first ability trigger mismatches
  if (entry.canonical.trigger !== compiledAb.trigger) {
    console.log(`FIXING: ${entry.card_no} - trigger mismatch`);
    
    // Update canonical to match compiled first ability
    entry.canonical.trigger = compiledAb.trigger;
    entry.canonical.once_per_turn = compiledAb.is_once_per_turn || false;
    entry.canonical.raw_text = compiledAb.raw_text;
    entry.canonical.pseudocode = extractPseudocode(compiledAb);
    entry.canonical.confidence = "manual-corrected";
    
    fixCount++;
    console.log(`  → Updated trigger to ${compiledAb.trigger}`);
  }
}

function extractPseudocode(compiledAb) {
  // Extract simplified pseudocode from compiled ability
  const trigger = getTriggerName(compiledAb.trigger);
  const triggerStr = compiledAb.is_once_per_turn ? `${trigger} (Once per turn)` : trigger;
  
  let result = `TRIGGER: ${triggerStr}`;
  
  // Add costs if present
  if (compiledAb.costs && compiledAb.costs.length > 0) {
    result += "\nCOST: ";
    result += compiledAb.costs.map(c => formatCost(c)).join("; ");
  }
  
  // Add effects
  if (compiledAb.effects && compiledAb.effects.length > 0) {
    result += "\nEFFECT: ";
    result += compiledAb.effects.map(e => formatEffect(e)).join("; ");
  }
  
  return result;
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

function formatCost(cost) {
  // Basic cost formatting
  const opName = cost.op || `COST_${cost.type}`;
  const value = cost.count || cost.value || "";
  return `${opName}(${value})`;
}

function formatEffect(effect) {
  // Basic effect formatting
  const opName = effect.op || `EFFECT_${effect.runtime_opcode}`;
  const value = effect.count || effect.value || "";
  return `${opName}(${value})`;
}

// Save updated draft
fs.writeFileSync(
  "canonical_ability_model/drafts/canonical_full_draft.json",
  JSON.stringify(canonicalWrapped, null, 2)
);

console.log(`\n=== SUMMARY ===`);
console.log(`Processed: ${processCount} cards`);
console.log(`Fixed: ${fixCount} cards`);
console.log(`Saved to: canonical_ability_model/drafts/canonical_full_draft.json`);
