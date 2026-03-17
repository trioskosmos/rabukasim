const fs = require("fs");

const db = JSON.parse(fs.readFileSync("data/cards_compiled.json", "utf8"));

// Find the card
for (const dbName of ["member_db", "live_db", "energy_db"]) {
  for (const card of Object.values(db[dbName] || {})) {
    if (card.card_no === "LL-bp1-001-R＋") {
      console.log(`Found ${card.card_no} in ${dbName}`);
      
      // Check abilities - specifically looking at the one that has DISCARD_HAND cost
      for (const [idx, ability] of (card.abilities || []).entries()) {
        console.log(`\n===== Ability ${idx} =====`);
        console.log(`Trigger: ${ability.trigger}`);
        console.log(`Raw: ${ability.raw_text}`);
        console.log(`Pseudocode: ${ability.pseudocode}`);
        
        console.log(`\nCosts:`, JSON.stringify(ability.costs || [], null, 2));
        console.log(`\nConditions:`, JSON.stringify(ability.conditions || [], null, 2));
        console.log(`\nEffects:`, JSON.stringify(ability.effects || [], null, 2));
        
        // The one with DISCARD_HAND or BOOST_SCORE
        if (ability.pseudocode && (ability.pseudocode.includes("DISCARD") || ability.pseudocode.includes("BOOST"))) {
          console.log("\n^^^ THIS IS THE MISMATCHED ONE ^^^");
        }
      }
      process.exit(0);
    }
  }
}

console.log("Card not found");
