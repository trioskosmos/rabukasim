const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "../..");
const SOURCE_PATH = path.join(ROOT, "canonical_ability_model", "canonical_families.json");
const OUTPUT_PATH = path.join(ROOT, "canonical_ability_model", "drafts", "canonical_full_draft.json");

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function loadFamilies(filePath) {
  const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
  if (!Array.isArray(data.groups)) {
    throw new Error("Expected family source with a groups array.");
  }
  return data.groups;
}

function expandFamilies(groups) {
  const entries = [];
  for (const group of groups) {
    const canonical = group.canonical || {};
    const cards = Array.isArray(group.cards) ? group.cards : [];
    for (const card of cards) {
      const nextCanonical = clone(canonical);
      entries.push({
        card_no: card.card_no,
        canonical: nextCanonical,
        issues: [],
      });
    }
  }
  return entries;
}

function main() {
  const groups = loadFamilies(SOURCE_PATH);
  const entries = expandFamilies(groups);
  const summary = {
    total_entries: entries.length,
    family_groups: groups.length,
    source_file: path.basename(SOURCE_PATH),
  };

  const wrapped = {
    schema_version: "draft-wrapper-v1",
    source_file: path.basename(SOURCE_PATH),
    summary,
    entries,
  };

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(wrapped, null, 2) + "\n", "utf8");
  console.log(JSON.stringify(summary, null, 2));
  console.log(`Wrote: ${OUTPUT_PATH}`);
}

main();
