const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "../..");
const INPUT_PATH = path.join(ROOT, "canonical_ability_model", "drafts", "canonical_full_draft.json");
const SOURCE_OUTPUT_PATH = path.join(ROOT, "canonical_ability_model", "canonical_families.json");
const JSON_OUTPUT_PATH = path.join(ROOT, "canonical_ability_model", "reports", "canonical_family_groups.json");
const MD_OUTPUT_PATH = path.join(ROOT, "canonical_ability_model", "reports", "canonical_family_groups.md");

function loadDraft(filePath) {
  const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
  if (!Array.isArray(data.entries)) {
    throw new Error("Expected draft wrapper with an entries array.");
  }
  return data.entries;
}

function groupByPseudocode(entries) {
  const groups = new Map();
  for (const entry of entries) {
    const canonical = entry.canonical || {};
    const key = (canonical.pseudocode || "").trim();
    const cardNo = entry.card_no || canonical.card_no || "UNKNOWN";
    if (!groups.has(key)) {
      groups.set(key, {
        canonical: JSON.parse(JSON.stringify(canonical)),
        cards: [],
      });
    }
    groups.get(key).cards.push({
      card_no: cardNo,
      trigger: canonical.trigger || null,
      confidence: canonical.confidence || null,
      source: canonical.source || null,
    });
  }
  return groups;
}

function buildReport(groups) {
  const ordered = [...groups.entries()].sort((a, b) => {
    const countDelta = b[1].cards.length - a[1].cards.length;
    if (countDelta !== 0) {
      return countDelta;
    }
    return a[0].localeCompare(b[0]);
  });
  const duplicateGroups = ordered.filter(([, group]) => group.cards.length > 1);

  const payload = {
    schema_version: "canonical-family-groups-v1",
    source_file: path.basename(INPUT_PATH),
    summary: {
      total_entries: ordered.reduce((sum, [, group]) => sum + group.cards.length, 0),
      unique_pseudocode_groups: ordered.length,
      duplicate_groups: duplicateGroups.length,
      singleton_groups: ordered.length - duplicateGroups.length,
    },
    groups: ordered.map(([pseudocode, cards]) => ({
      count: cards.cards.length,
      pseudocode,
      canonical: cards.canonical,
      cards: cards.cards,
    })),
  };

  const lines = [
    "# Canonical Ability Family Groups",
    "",
    "This report consolidates the canonical draft by exact pseudocode, so repeated card variants appear once with their card list attached.",
    "",
    `- Draft entries: ${payload.summary.total_entries}`,
    `- Unique pseudocode groups: ${payload.summary.unique_pseudocode_groups}`,
    `- Duplicate groups: ${payload.summary.duplicate_groups}`,
    `- Singleton groups omitted from the main body: ${payload.summary.singleton_groups}`,
    "",
    "## Duplicate Families",
    "",
  ];

  duplicateGroups.forEach(([pseudocode, group], index) => {
    const cardList = group.cards.map((card) => card.card_no).join(", ");
    lines.push(`### ${index + 1}. ${group.cards.length} cards`);
    lines.push(`Cards: ${cardList}`);
    lines.push("");
    lines.push("```text");
    lines.push(pseudocode || "(empty pseudocode)");
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
  const entries = loadDraft(INPUT_PATH);
  const groups = groupByPseudocode(entries);
  const { payload, markdown } = buildReport(groups);

  fs.mkdirSync(path.dirname(JSON_OUTPUT_PATH), { recursive: true });
  fs.writeFileSync(SOURCE_OUTPUT_PATH, JSON.stringify(payload, null, 2) + "\n", "utf8");
  fs.writeFileSync(JSON_OUTPUT_PATH, JSON.stringify(payload, null, 2) + "\n", "utf8");
  fs.writeFileSync(MD_OUTPUT_PATH, markdown, "utf8");

  console.log(JSON.stringify(payload.summary, null, 2));
  console.log(`Wrote: ${SOURCE_OUTPUT_PATH}`);
  console.log(`Wrote: ${JSON_OUTPUT_PATH}`);
  console.log(`Wrote: ${MD_OUTPUT_PATH}`);
}

main();
