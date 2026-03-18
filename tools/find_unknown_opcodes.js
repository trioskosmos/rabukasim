const fs = require("fs");

// Find all runtime_opcode values that don't have mappings
const db = JSON.parse(fs.readFileSync("data/cards_compiled.json", "utf8"));

const EFFECT_IDS = {
  DRAW: 10,
  ADD_BLADES: 11,
  ADD_HEARTS: 12,
  REDUCE_COST: 13,
  RECOVER_LIVE: 15,
  BOOST_SCORE: 16,
  RECOVER_MEMBER: 17,
  SEARCH_DECK: 22,
  ENERGY_CHARGE: 23,
  SELECT_MODE: 30,
  TAP_OPPONENT: 32,
  ACTIVATE_MEMBER: 43,
  ADD_TO_HAND: 44,
  COLOR_SELECT: 45,
  REDUCE_HEART_REQ: 48,
  SET_TAPPED: 51,
  TAP_MEMBER: 53,
  MOVE_TO_DISCARD: 58,
  GRANT_ABILITY: 60,
  SELECT_MEMBER: 65,
  ACTIVATE_ENERGY: 81,
};

const knownIds = new Set(Object.values(EFFECT_IDS));
const unknownOpcodes = new Map(); // opcode -> name

for (const dbName of ["member_db", "live_db", "energy_db"]) {
  for (const card of Object.values(db[dbName] || {})) {
    for (const ability of (card.abilities || [])) {
      for (const effect of (ability.effects || [])) {
        const opcode = effect.runtime_opcode;
        if (!knownIds.has(opcode) && !unknownOpcodes.has(opcode)) {
          unknownOpcodes.set(opcode, null);
        }
      }
    }
  }
}

// Try to infer names from raw_text and pseudocode
const opcodeToName = {};
for (const dbName of ["member_db", "live_db", "energy_db"]) {
  for (const card of Object.values(db[dbName] || {})) {
    for (const ability of (card.abilities || [])) {
      for (const [idx, effect] of (ability.effects || []).entries()) {
        const opcode = effect.runtime_opcode;
        if (unknownOpcodes.has(opcode) && !opcodeToName[opcode]) {
          // Try to extract from raw_text or pseudocode
          const text = ability.raw_text || ability.pseudocode || "";
          const lines = text.split('\n');
          for (const line of lines) {
            if (line.includes("EFFECT:")) {
              const effectPart = line.substring(line.indexOf("EFFECT:") + 7).trim();
              const name = effectPart.split("(")[0].trim();
              if (name && !name.includes("TRIGGER")) {
                opcodeToName[opcode] = name;
                break;
              }
            }
          }
        }
      }
    }
  }
}

console.log("Unknown Opcodes Found:");
const sorted = Array.from(unknownOpcodes.keys()).sort((a, b) => a - b);
for (const opcode of sorted) {
  console.log(`  ${opcode}: "${opcodeToName[opcode] || "UNKNOWN"}",`);
}
