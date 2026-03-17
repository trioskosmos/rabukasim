const fs = require("fs");
const path = require("path");
const { findCompiledAbility } = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

// Initialize the index by calling findCompiledAbility first time
try {
  findCompiledAbility("LL-bp1-001-R＋", 0);
} catch (e) {
  // Expected to fail first time, just initializing
}

const compiledDb = readJson("data/cards_compiled.json");

// Find the card in compiled database
for (const dbName of ["member_db", "live_db", "energy_db"]) {
  for (const [cardNo, card] of Object.entries(compiledDb[dbName] || {})) {
    if (cardNo === "LL-bp1-001-R＋") {
      console.log(`Found ${cardNo} in ${dbName}`);
      console.log(`\nAbilities (first 2):`);
      for (const [idx, ability] of (card.abilities || []).slice(0, 2).entries()) {
        console.log(`\nAbility ${idx}:`);
        console.log(JSON.stringify(ability, null, 2).split('\n').slice(0, 50).join('\n'));
      }
      process.exit(0);
    }
  }
}

console.log("Card not found in compiled database");
