const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "../..");
const SOURCE_PATH = path.join(ROOT, "canonical_ability_model", "canonical_families.json");
const JSON_OUTPUT_PATH = path.join(ROOT, "canonical_ability_model", "reports", "canonical_family_groups.json");
const MD_OUTPUT_PATH = path.join(ROOT, "canonical_ability_model", "reports", "canonical_family_groups.md");

function loadSource(filePath) {
  const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
  if (!Array.isArray(data.groups)) {
    throw new Error("Expected canonical family source with a groups array.");
  }
  return data;
}

function buildReport(source) {
  const groups = source.groups || [];
  const duplicateGroups = groups.filter((group) => (group.cards || []).length > 1);
  const totalEntries = groups.reduce((sum, group) => sum + (group.cards || []).length, 0);

  const payload = {
    schema_version: source.schema_version || "canonical-family-groups-v1",
    source_file: path.basename(SOURCE_PATH),
    summary: {
      total_entries: totalEntries,
      unique_pseudocode_groups: groups.length,
      duplicate_groups: duplicateGroups.length,
      singleton_groups: groups.length - duplicateGroups.length,
    },
    groups,
  };

  const lines = [
    "# Canonical Ability Family Groups",
    "",
    "This report consolidates the canonical source by exact pseudocode, so repeated card variants appear once with their card list attached.",
    "",
    `- Draft entries: ${payload.summary.total_entries}`,
    `- Unique pseudocode groups: ${payload.summary.unique_pseudocode_groups}`,
    `- Duplicate groups: ${payload.summary.duplicate_groups}`,
    `- Singleton groups omitted from the main body: ${payload.summary.singleton_groups}`,
    "",
    "## Duplicate Families",
    "",
  ];

  duplicateGroups.forEach((group, index) => {
    const cardList = (group.cards || []).map((card) => card.card_no).join(", ");
    lines.push(`### ${index + 1}. ${(group.cards || []).length} cards`);
    lines.push(`Cards: ${cardList}`);
    lines.push("");
    lines.push("```text");
    lines.push(group.pseudocode || "(empty pseudocode)");
    lines.push("```");
    lines.push("");
  });

  if (duplicateGroups.length === 0) {
    lines.push("No duplicate families were found.");
    lines.push("");
  }

  return { payload, markdown: lines.join("\n").replace(/\n+$/, "\n") };
}

function main() {
  const source = loadSource(SOURCE_PATH);
  const { payload, markdown } = buildReport(source);

  fs.mkdirSync(path.dirname(JSON_OUTPUT_PATH), { recursive: true });
  fs.writeFileSync(JSON_OUTPUT_PATH, JSON.stringify(payload, null, 2) + "\n", "utf8");
  fs.writeFileSync(MD_OUTPUT_PATH, markdown, "utf8");

  console.log(JSON.stringify(payload.summary, null, 2));
  console.log(`Wrote: ${JSON_OUTPUT_PATH}`);
  console.log(`Wrote: ${MD_OUTPUT_PATH}`);
}

main();
