const fs = require("fs");
const path = require("path");

const { compareCanonicalToCompiled } = require("./compare_canonical_to_compiled");

const repoRoot = process.cwd();

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, filePath), "utf8"));
}

async function main() {
  const args = process.argv.slice(2);
  const draftPath = args[0] || "canonical_ability_model/drafts/canonical_full_draft.normalized.json";
  
  const draft = readJson(draftPath);
  const compiledCards = readJson("data/cards_compiled.json");
  
  const mismatches = [];
  const matches = [];
  const errors = [];
  
  for (const entry of draft.entries || []) {
    const cardNo = entry.card_no;
    const canonical = entry.canonical;
    
    const result = await compareCanonicalToCompiled(cardNo, canonical, compiledCards);
    
    if (result.match) {
      matches.push({
        card_no: cardNo,
        ability_uid: entry.ability_uid,
        issues: result.issues || []
      });
    } else {
      mismatches.push({
        card_no: cardNo,
        ability_uid: entry.ability_uid,
        reason: result.reason || "unknown",
        canonical: canonical,
        compiled: result.compiled || null,
        issues: result.issues || []
      });
    }
  }
  
  // Cluster by mismatch reason
  const clusters = {};
  for (const m of mismatches) {
    const reason = m.reason || "unknown";
    if (!clusters[reason]) {
      clusters[reason] = [];
    }
    clusters[reason].push(m);
  }
  
  console.log(`\n=== MISMATCH ANALYSIS ===`);
  console.log(`Total entries: ${draft.entries.length}`);
  console.log(`Matches: ${matches.length}`);
  console.log(`Mismatches: ${mismatches.length}`);
  
  console.log(`\n=== MISMATCH CLUSTERS ===`);
  const sortedClusters = Object.entries(clusters)
    .sort((a, b) => b[1].length - a[1].length);
  
  for (const [reason, items] of sortedClusters) {
    console.log(`\n[${items.length}] ${reason}`);
    for (const item of items.slice(0, 5)) {
      console.log(`  - ${item.card_no} (${item.ability_uid})`);
      if (item.issues && item.issues.length > 0) {
        for (const issue of item.issues.slice(0, 2)) {
          console.log(`    * ${issue.code || issue}`);
        }
      }
    }
    if (items.length > 5) {
      console.log(`  ... and ${items.length - 5} more`);
    }
  }
  
  // Sample details for the top 3 mismatches
  console.log(`\n=== DETAILED SAMPLES ===`);
  for (const m of mismatches.slice(0, 3)) {
    console.log(`\nCard: ${m.card_no} (${m.ability_uid})`);
    console.log(`Reason: ${m.reason}`);
    console.log(`Canonical:`, JSON.stringify(m.canonical, null, 2).split('\n').slice(0, 10).join('\n'));
    if (m.compiled) {
      console.log(`Compiled:`, JSON.stringify(m.compiled, null, 2).split('\n').slice(0, 10).join('\n'));
    }
    if (m.issues && m.issues.length > 0) {
      console.log(`Issues:`, m.issues.slice(0, 3));
    }
  }
}

main().catch(err => {
  console.error("Error:", err);
  process.exit(1);
});
