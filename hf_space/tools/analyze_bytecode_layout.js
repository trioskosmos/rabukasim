const fs = require("fs");
const path = require("path");

function loadJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function formatPct(part, total) {
  if (!total) {
    return "0.00%";
  }
  return `${((part / total) * 100).toFixed(2)}%`;
}

function analyzeBytecodeLayout(db) {
  const zeroByWord = [0, 0, 0, 0, 0];
  const nonZeroByWord = [0, 0, 0, 0, 0];
  const profileCounts = {
    op_only: 0,
    op_v: 0,
    op_v_a: 0,
    op_v_s: 0,
    full: 0,
  };

  let abilities = 0;
  let instructions = 0;
  let compactWords = 0;
  let instructionsWithHighAttr = 0;
  let totalBits = 0;
  let zeroBits = 0;
  const uniqueInstructions = new Map();
  const opcodeHistogram = new Map();

  for (const dbName of ["member_db", "live_db"]) {
    for (const card of Object.values(db[dbName] || {})) {
      for (const ability of card.abilities || []) {
        abilities += 1;
        const bytecode = ability.bytecode || [];
        for (let i = 0; i + 4 < bytecode.length; i += 5) {
          const [op, v, aLow, aHigh, s] = bytecode.slice(i, i + 5);
          instructions += 1;
          const key = `${op},${v},${aLow},${aHigh},${s}`;
          uniqueInstructions.set(key, (uniqueInstructions.get(key) || 0) + 1);
          opcodeHistogram.set(op, (opcodeHistogram.get(op) || 0) + 1);

          const hasV = v !== 0;
          const hasA = aLow !== 0 || aHigh !== 0;
          const hasS = s !== 0;

          if (aHigh !== 0) {
            instructionsWithHighAttr += 1;
          }

          [op, v, aLow, aHigh, s].forEach((value, idx) => {
            if (value === 0) {
              zeroByWord[idx] += 1;
            } else {
              nonZeroByWord[idx] += 1;
            }
            totalBits += 32;
            zeroBits += 32 - popcount32(value);
          });

          if (!hasV && !hasA && !hasS) {
            profileCounts.op_only += 1;
          } else if (hasV && !hasA && !hasS) {
            profileCounts.op_v += 1;
          } else if (hasV && hasA && !hasS) {
            profileCounts.op_v_a += 1;
          } else if (hasV && !hasA && hasS) {
            profileCounts.op_v_s += 1;
          } else {
            profileCounts.full += 1;
          }

          // Compact estimate:
          // 1 word for opcode, optional V, 1-2 words for A, optional S.
          compactWords += 1;
          if (hasV) {
            compactWords += 1;
          }
          if (hasA) {
            compactWords += aHigh !== 0 ? 2 : 1;
          }
          if (hasS) {
            compactWords += 1;
          }
        }
      }
    }
  }

  const fixedWords = instructions * 5;
  return {
    abilities,
    instructions,
    zeroByWord,
    nonZeroByWord,
    zeroBits,
    totalBits,
    profileCounts,
    fixedWords,
    compactWords,
    savedWords: fixedWords - compactWords,
    savedPct: fixedWords ? ((fixedWords - compactWords) / fixedWords) * 100 : 0,
    instructionsWithHighAttr,
    uniqueInstructionCount: uniqueInstructions.size,
    topInstructions: [...uniqueInstructions.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15),
    topOpcodes: [...opcodeHistogram.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20),
  };
}

function popcount32(value) {
  let x = value >>> 0;
  let count = 0;
  while (x) {
    x &= x - 1;
    count += 1;
  }
  return count;
}

function main() {
  const root = path.resolve(__dirname, "..");
  const jsonPath = path.join(root, "data", "cards_compiled.json");
  const binPath = path.join(root, "data", "cards_compiled.bin");
  const db = loadJson(jsonPath);
  const analysis = analyzeBytecodeLayout(db);

  const jsonSize = fs.statSync(jsonPath).size;
  const binSize = fs.existsSync(binPath) ? fs.statSync(binPath).size : null;

  console.log("Bytecode Layout Analysis");
  console.log("=======================");
  console.log(`Abilities inspected: ${analysis.abilities}`);
  console.log(`Instructions:        ${analysis.instructions}`);
  console.log(`JSON size:           ${jsonSize} bytes`);
  if (binSize !== null) {
    console.log(`Binary snapshot:     ${binSize} bytes`);
  }
  console.log("");
  console.log("Word usage");
  console.log(`  OP non-zero:       ${analysis.nonZeroByWord[0]} / ${analysis.instructions} (${formatPct(analysis.nonZeroByWord[0], analysis.instructions)})`);
  console.log(`  V non-zero:        ${analysis.nonZeroByWord[1]} / ${analysis.instructions} (${formatPct(analysis.nonZeroByWord[1], analysis.instructions)})`);
  console.log(`  A_LOW non-zero:    ${analysis.nonZeroByWord[2]} / ${analysis.instructions} (${formatPct(analysis.nonZeroByWord[2], analysis.instructions)})`);
  console.log(`  A_HIGH non-zero:   ${analysis.nonZeroByWord[3]} / ${analysis.instructions} (${formatPct(analysis.nonZeroByWord[3], analysis.instructions)})`);
  console.log(`  S non-zero:        ${analysis.nonZeroByWord[4]} / ${analysis.instructions} (${formatPct(analysis.nonZeroByWord[4], analysis.instructions)})`);
  console.log(`  Zero bits:         ${analysis.zeroBits} / ${analysis.totalBits} (${formatPct(analysis.zeroBits, analysis.totalBits)})`);
  console.log("");
  console.log("Instruction profiles");
  for (const [name, count] of Object.entries(analysis.profileCounts)) {
    console.log(`  ${name.padEnd(12)} ${String(count).padStart(4)} (${formatPct(count, analysis.instructions)})`);
  }
  console.log("");
  console.log("Compact estimate");
  console.log(`  Fixed words:       ${analysis.fixedWords}`);
  console.log(`  Compact words:     ${analysis.compactWords}`);
  console.log(`  Saved words:       ${analysis.savedWords} (${analysis.savedPct.toFixed(2)}%)`);
  console.log(`  Attr high used:    ${analysis.instructionsWithHighAttr} instructions (${formatPct(analysis.instructionsWithHighAttr, analysis.instructions)})`);
  console.log("");
  console.log("Reuse");
  console.log(`  Unique instructions: ${analysis.uniqueInstructionCount} / ${analysis.instructions} (${formatPct(analysis.uniqueInstructionCount, analysis.instructions)})`);
  console.log("  Top repeated instructions:");
  for (const [instruction, count] of analysis.topInstructions) {
    console.log(`    ${String(count).padStart(4)}  ${instruction}`);
  }
  console.log("  Top opcodes:");
  for (const [opcode, count] of analysis.topOpcodes) {
    console.log(`    ${String(count).padStart(4)}  ${opcode}`);
  }
}

main();
