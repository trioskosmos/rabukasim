const fs = require("fs");
const path = require("path");

const RESERVED_TARGET_NAMES = new Set([
  "SELF",
  "PLAYER",
  "OPPONENT",
  "TARGET",
  "TARGET_MEMBER",
  "TARGET_STAGE",
  "TARGET_DISCARD",
]);

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function normalizeStep(step, issues, pathLabel) {
  const next = clone(step);

  if (
    next.store_as &&
    RESERVED_TARGET_NAMES.has(next.store_as) &&
    ["effect", "cost", "select"].includes(next.kind)
  ) {
    if (!next.target) {
      next.target = next.store_as;
    }
    delete next.store_as;
    issues.push({
      code: "reserved_store_as_rewritten",
      path: pathLabel,
      message: "Rewrote reserved store_as binding into target.",
    });
  }

  if (next.kind === "effect" && next.op === "CONDITION") {
    next.review_markers = Array.from(
      new Set([...(next.review_markers || []), "unsupported_pattern", "needs_review"])
    );
    issues.push({
      code: "effect_condition_not_normalized",
      path: pathLabel,
      message: "Legacy EFFECT: CONDITION pattern still needs semantic normalization.",
    });
  }

  if (Array.isArray(next.branches)) {
    next.branches = next.branches.map((branch, branchIdx) => ({
      ...branch,
      steps: (branch.steps || []).map((child, childIdx) =>
        normalizeStep(child, issues, `${pathLabel}.branches[${branchIdx}].steps[${childIdx}]`)
      ),
    }));
  }

  if (Array.isArray(next.then)) {
    next.then = next.then.map((child, idx) => normalizeStep(child, issues, `${pathLabel}.then[${idx}]`));
  }

  if (Array.isArray(next.else)) {
    next.else = next.else.map((child, idx) => normalizeStep(child, issues, `${pathLabel}.else[${idx}]`));
  }

  if (Array.isArray(next.body)) {
    next.body = next.body.map((child, idx) => normalizeStep(child, issues, `${pathLabel}.body[${idx}]`));
  }

  return next;
}

function normalizeEntry(entry, index) {
  const issues = [];
  const canonical = clone(entry);

  const card_no = canonical.card_no || null;
  delete canonical.card_no;

  if (!card_no) {
    issues.push({
      code: "missing_card_no",
      path: `$[${index}]`,
      message: "Entry did not include card_no metadata.",
    });
  }

  canonical.steps = (canonical.steps || []).map((step, stepIdx) =>
    normalizeStep(step, issues, `steps[${stepIdx}]`)
  );

  return {
    card_no,
    canonical,
    issues,
  };
}

function main() {
  if (process.argv.length < 3 || process.argv.length > 4) {
    console.error(
      "usage: node tools/normalize_canonical_draft.js <input-json> [output-json]"
    );
    process.exit(2);
  }

  const inputPath = process.argv[2];
  const outputPath =
    process.argv[3] ||
    inputPath.replace(/\.json$/i, ".normalized.json");

  const raw = fs.readFileSync(inputPath, "utf8");
  const data = JSON.parse(raw);
  if (!Array.isArray(data)) {
    console.error("Expected top-level draft JSON array.");
    process.exit(1);
  }

  const entries = data.map((entry, index) => normalizeEntry(entry, index));
  const summary = {
    total_entries: entries.length,
    entries_with_issues: entries.filter((entry) => entry.issues.length > 0).length,
    total_issues: entries.reduce((sum, entry) => sum + entry.issues.length, 0),
    issue_counts: {},
  };

  for (const entry of entries) {
    for (const issue of entry.issues) {
      summary.issue_counts[issue.code] = (summary.issue_counts[issue.code] || 0) + 1;
    }
  }

  const wrapped = {
    schema_version: "draft-wrapper-v1",
    source_file: path.basename(inputPath),
    summary,
    entries,
  };

  fs.writeFileSync(outputPath, `${JSON.stringify(wrapped, null, 2)}\n`, "utf8");
  console.log(JSON.stringify({ output: outputPath, summary }, null, 2));
}

main();
