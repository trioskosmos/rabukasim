const fs = require("fs");
const path = require("path");
const { compareCanonicalToCompiled } = require("./compare_canonical_to_compiled");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), filePath), "utf8"));
}

function simpleDiff(left, right, depth = 1) {
  if (depth > 2) return [];
  if (JSON.stringify(left) === JSON.stringify(right)) return [];
  
  const diffs = [];
  if (typeof left !== "object" || typeof right !== "object") {
    return [`type_mismatch`];
  }
  
  const allKeys = new Set([...Object.keys(left || {}), ...Object.keys(right || {})]);
  for (const key of allKeys) {
    if (!(key in left)) {
      diffs.push(`missing_in_canonical.${key}`);
    } else if (!(key in right)) {
      diffs.push(`missing_in_compiled.${key}`);
    } else if (left[key] !== right[key]) {
      if (typeof left[key] === "object" && typeof right[key] === "object") {
        diffs.push(...simpleDiff(left[key], right[key], depth + 1).map(d => `${key}.${d}`));
      } else {
        diffs.push(`${key}_mismatch(${left[key]}vs${right[key]})`);
      }
    }
  }
  return diffs;
}

const draft = readJson("canonical_ability_model/drafts/canonical_full_draft.json");
const entries = draft.entries || [];

const one_v_one_issues = {};

for (const entry of entries) {
  if (!entry.canonical) continue;
  
  try {
    const result = compareCanonicalToCompiled(entry.canonical, entry.card_no, null);
    
    if (!result.matches) {
      const canonOps = (result.canonicalLowered.effects || []);
      const compilOps = (result.compiledLowered.effects || []);
      
      if (canonOps.length === 1 && compilOps.length === 1) {
        const diffs = simpleDiff(canonOps[0], compilOps[0]);
        const key = diffs.slice(0, 3).join(" + ");
        
        if (!one_v_one_issues[key]) {
          one_v_one_issues[key] = { count: 0, examples: [] };
        }
        one_v_one_issues[key].count++;
        if (one_v_one_issues[key].examples.length < 2) {
          one_v_one_issues[key].examples.push({
            card: entry.card_no,
            canonical: canonOps[0],
            compiled: compilOps[0]
          });
        }
      }
    }
  } catch (error) {
    // skip
  }
}

console.log(`\nTOP 1v1 MISMATCH PATTERNS:\n`);
const sorted = Object.entries(one_v_one_issues)
  .sort((a, b) => b[1].count - a[1].count)
  .slice(0, 15);

for (const [pattern, data] of sorted) {
  console.log(`[${data.count}] ${pattern}`);
  if (data.examples.length > 0) {
    const ex = data.examples[0];
    console.log(`    Card: ${ex.card}`);
    console.log(`    Canon: op=${ex.canonical.op}, target=${ex.canonical.target}, is_opt=${ex.canonical.is_optional}`);
    console.log(`    Comp:  op=${ex.compiled.op}, target=${ex.compiled.target}, is_opt=${ex.compiled.is_optional}`);
  }
  console.log();
}
