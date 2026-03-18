const fs = require("fs");

const db = JSON.parse(fs.readFileSync("data/cards_compiled.json", "utf8"));

// Find PL!-PR-003-PR
for (const dbName of ["member_db", "live_db", "energy_db"]) {
  for (const card of Object.values(db[dbName] || {})) {
    if (card.card_no === "PL!-PR-003-PR") {
      console.log(`Found: ${card.card_no}`);
      for (const [idx, ability] of (card.abilities || []).entries()) {
        if (ability.pseudocode && ability.pseudocode.includes("RECOVER")) {
          console.log(`\nAbility ${idx}:`);
          console.log(`Raw: ${ability.raw_text}`);
          console.log(`Costs:`, ability.costs || []);
          console.log(`Effects:`, (ability.effects || []).map(e => ({ op: e.runtime_opcode, value: e.value })));
        }
      }
      process.exit(0);
    }
  }
}
console.log("Card not found");
