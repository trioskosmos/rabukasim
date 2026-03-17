const fs = require("fs");
const path = require("path");

const { compareCanonicalToCompiled, pruneNulls } = require("./compare_canonical_to_compiled");

const repoRoot = process.cwd();

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, filePath), "utf8"));
}

function diffObjects(left, right, path = "") {
  const diffs = [];
  const leftStr = JSON.stringify(pruneNulls(left));
  const rightStr = JSON.stringify(pruneNulls(right));

  if (leftStr === rightStr) {
    return diffs;
  }

  // Simple structural diff
  if (typeof left !== typeof right) {
    diffs.push(`${path}: type mismatch (${typeof left} vs ${typeof right})`);
    return diffs;
  }

  if (typeof left === "object" && left !== null && typeof right === "object" && right !== null) {
    if (Array.isArray(left) && Array.isArray(right)) {
      if (left.length !== right.length) {
        diffs.push(`${path}: array length mismatch (${left.length} vs ${right.length})`);
      }
      for (let i = 0; i < Math.min(left.length, right.length); i++) {
        diffs.push(...diffObjects(left[i], right[i], `${path}[${i}]`));
      }
    } else {
      const allKeys = new Set([...Object.keys(left), ...Object.keys(right)]);
      for (const key of allKeys) {
        if (!(key in left)) {
          diffs.push(`${path}.${key}: missing in canonical`);
        } else if (!(key in right)) {
          diffs.push(`${path}.${key}: missing in compiled`);
        } else {
          diffs.push(...diffObjects(left[key], right[key], `${path}.${key}`));
        }
      }
    }
  } else if (left !== right) {
    diffs.push(`${path}: ${JSON.stringify(left)} vs ${JSON.stringify(right)}`);
  }

  return diffs;
}

function categorizeDiff(diffs) {
  const categories = {};
  for (const diff of diffs) {
    let category = "other";
    
    if (diff.includes("array length mismatch")) {
      category = "structure_length";
    } else if (diff.includes("type mismatch")) {
      category = "type_mismatch";
    } else if (diff.includes("missing in")) {
      category = "missing_field";
    } else if (diff.includes(".op:")) {
      category = "operation_mismatch";
    } else if (diff.includes(".trigger:")) {
      category = "trigger_mismatch";
    } else if (diff.includes(".is_optional")) {
      category = "optional_mismatch";
    } else if (diff.includes(".target:")) {
      category = "target_mismatch";
    } else if (diff.includes(".count:")) {
      category = "count_mismatch";
    } else if (diff.includes(".filter")) {
      category = "filter_mismatch";
    }
    
    if (!categories[category]) {
      categories[category] = [];
    }
    categories[category].push(diff);
  }
  return categories;
}

function main() {
  const args = process.argv.slice(2);
  const draftPath = args[0] || "canonical_ability_model/drafts/canonical_full_draft.normalized.json";
  
  const draft = readJson(draftPath);
  const entries = Array.isArray(draft.entries) ? draft.entries : [];
  
  const mismatches = [];
  const matches = [];
  const unsupported = [];
  const errors = [];
  
  console.log(`Processing ${entries.length} entries...`);
  
  for (const entry of entries) {
    if (!entry.canonical) continue;
    
    try {
      const result = compareCanonicalToCompiled(entry.canonical, entry.card_no, null);
      
      if (result.matches) {
        matches.push({ card_no: entry.card_no });
      } else if (!result.supported) {
        unsupported.push({ 
          card_no: entry.card_no,
          canonical: entry.canonical
        });
      } else {
        // It's a supported but mismatched ability
        const diffs = diffObjects(result.canonicalLowered, result.compiledLowered);
        const categories = categorizeDiff(diffs);
        
        mismatches.push({
          card_no: entry.card_no,
          ability_uid: entry.ability_uid || "unknown",
          diff_count: diffs.length,
          categories,
          diffs: diffs.slice(0, 5),
          canonical: result.canonicalLowered,
          compiled: result.compiledLowered
        });
      }
    } catch (error) {
      errors.push({
        card_no: entry.card_no,
        error: String(error)
      });
    }
  }
  
  console.log(`\n========== VERIFICATION SUMMARY ==========`);
  console.log(`Total entries: ${entries.length}`);
  console.log(`Matches: ${matches.length} ✓`);
  console.log(`Mismatches: ${mismatches.length}`);
  console.log(`Unsupported: ${unsupported.length}`);
  console.log(`Errors: ${errors.length}`);
  
  // Cluster mismatches by primary issue category
  const categoryCluster = {};
  for (const mismatch of mismatches) {
    const mainCategory = Object.keys(mismatch.categories)[0] || "unknown";
    if (!categoryCluster[mainCategory]) {
      categoryCluster[mainCategory] = [];
    }
    categoryCluster[mainCategory].push(mismatch);
  }
  
  console.log(`\n========== TOP MISMATCH PATTERNS ==========`);
  const sortedCategories = Object.entries(categoryCluster)
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, 10);
  
  for (const [category, items] of sortedCategories) {
    console.log(`\n[${items.length.toString().padStart(3)}] ${category}`);
    for (const item of items.slice(0, 3)) {
      console.log(`      ${item.card_no}`);
      if (item.diffs && item.diffs.length > 0) {
        console.log(`      → ${item.diffs[0]}`);
      }
    }
    if (items.length > 3) {
      console.log(`      ... and ${items.length - 3} more`);
    }
  }
  
  // Detailed sample
  if (mismatches.length > 0) {
    console.log(`\n========== DETAILED SAMPLE ==========`);
    const sample = mismatches[0];
    console.log(`\nCard: ${sample.card_no}`);
    console.log(`Issues: ${Object.keys(sample.categories).join(", ")}`);
    console.log(`\nCanonical:`, JSON.stringify(sample.canonical, null, 2).split('\n').slice(0, 20).join('\n'));
    console.log(`\nCompiled:`, JSON.stringify(sample.compiled, null, 2).split('\n').slice(0, 20).join('\n'));
  }
  
  if (unsupported.length > 0) {
    console.log(`\n========== UNSUPPORTED PATTERNS ==========`);
    for (const item of unsupported.slice(0, 5)) {
      console.log(`${item.card_no}:`, item.canonical);
    }
    if (unsupported.length > 5) {
      console.log(`... and ${unsupported.length - 5} more unsupported`);
    }
  }
}

try {
  main();
} catch (err) {
  console.error("Fatal error:", err);
  process.exit(1);
}
