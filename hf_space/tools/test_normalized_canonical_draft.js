const fs = require("fs");
const path = require("path");

const { compareCanonicalToCompiled } = require("./compare_canonical_to_compiled");

const repoRoot = process.cwd();
const RESERVED_BINDINGS = new Set([
  "SELF",
  "PLAYER",
  "OPPONENT",
  "TARGET",
  "TARGET_MEMBER",
  "TARGET_STAGE",
  "TARGET_DISCARD",
]);
const ALLOWED_STEP_KINDS = new Set([
  "cost",
  "condition",
  "effect",
  "select",
  "assign",
  "if",
  "choose_one",
  "repeat",
]);

function isObject(value) {
  return value && typeof value === "object" && !Array.isArray(value);
}

function validateExpr(expr, issues, pathLabel, scope) {
  if (!isObject(expr)) {
    issues.push({ code: "invalid_expr", path: pathLabel });
    return;
  }
  if (expr.kind === "reference") {
    if (!scope.has(expr.name) && !RESERVED_BINDINGS.has(expr.name)) {
      issues.push({ code: "unknown_binding", path: pathLabel });
    }
    return;
  }
  if (expr.kind === "binary") {
    validateExpr(expr.left, issues, `${pathLabel}.left`, scope);
    validateExpr(expr.right, issues, `${pathLabel}.right`, scope);
  }
}

function validateSteps(steps, issues, scope, pathLabel) {
  const localScope = new Set(scope);
  for (const [idx, step] of (steps || []).entries()) {
    const stepPath = `${pathLabel}[${idx}]`;
    if (!isObject(step) || !ALLOWED_STEP_KINDS.has(step.kind)) {
      issues.push({ code: "invalid_step_kind", path: stepPath });
      continue;
    }
    if (step.store_as) {
      if (RESERVED_BINDINGS.has(step.store_as)) {
        issues.push({ code: "reserved_binding", path: `${stepPath}.store_as` });
      } else {
        localScope.add(step.store_as);
      }
    }
    if (step.count) {
      validateExpr(step.count, issues, `${stepPath}.count`, localScope);
    }
    if (step.expr) {
      validateExpr(step.expr, issues, `${stepPath}.expr`, localScope);
    }
    if (isObject(step.args)) {
      for (const [key, value] of Object.entries(step.args)) {
        if (isObject(value) && value.kind) {
          validateExpr(value, issues, `${stepPath}.args.${key}`, localScope);
        }
      }
    }
    if (step.kind === "if") {
      if (step.condition) {
        validateSteps([step.condition], issues, localScope, `${stepPath}.condition`);
      }
      validateSteps(step.then || [], issues, localScope, `${stepPath}.then`);
      validateSteps(step.else || [], issues, localScope, `${stepPath}.else`);
    }
    if (step.kind === "choose_one") {
      for (const [branchIdx, branch] of (step.branches || []).entries()) {
        validateSteps(branch.steps || [], issues, localScope, `${stepPath}.branches[${branchIdx}].steps`);
      }
    }
    if (step.kind === "repeat") {
      validateSteps(step.body || [], issues, localScope, `${stepPath}.body`);
    }
  }
}

function validateCanonical(canonical) {
  const issues = [];
  if (!isObject(canonical)) {
    issues.push({ code: "invalid_canonical", path: "$" });
    return issues;
  }
  if (canonical.schema_version !== "v0") {
    issues.push({ code: "schema_version", path: "schema_version" });
  }
  if (typeof canonical.trigger !== "string") {
    issues.push({ code: "missing_trigger", path: "trigger" });
  }
  if (!Array.isArray(canonical.steps)) {
    issues.push({ code: "missing_steps", path: "steps" });
    return issues;
  }
  validateSteps(canonical.steps, issues, new Set(), "steps");
  return issues;
}

function main() {
  if (process.argv.length !== 3) {
    console.error("usage: node tools/test_normalized_canonical_draft.js <normalized-wrapper-json>");
    process.exit(2);
  }

  const inputPath = path.join(repoRoot, process.argv[2]);
  const data = JSON.parse(fs.readFileSync(inputPath, "utf8"));
  const entries = Array.isArray(data.entries) ? data.entries : [];

  const summary = {
    total_entries: entries.length,
    wrapper_issue_free: 0,
    wrapper_with_issues: 0,
    canonical_validation_pass: 0,
    canonical_validation_fail: 0,
    bridge_supported: 0,
    bridge_match: 0,
    bridge_mismatch: 0,
    samples: {
      validation_fail: [],
      bridge_match: [],
      bridge_mismatch: [],
    },
  };

  for (const [idx, entry] of entries.entries()) {
    const wrapperIssues = Array.isArray(entry.issues) ? entry.issues : [];
    if (wrapperIssues.length === 0) {
      summary.wrapper_issue_free += 1;
    } else {
      summary.wrapper_with_issues += 1;
    }

    const canonicalIssues = validateCanonical(entry.canonical);
    if (canonicalIssues.length === 0) {
      summary.canonical_validation_pass += 1;
    } else {
      summary.canonical_validation_fail += 1;
      if (summary.samples.validation_fail.length < 8) {
        summary.samples.validation_fail.push({
          card_no: entry.card_no,
          issues: canonicalIssues.slice(0, 5),
        });
      }
      continue;
    }

    try {
      const result = compareCanonicalToCompiled(entry.canonical, entry.card_no, null);
      if (result.supported) {
        summary.bridge_supported += 1;
      }
      if (result.matches) {
        summary.bridge_match += 1;
        if (summary.samples.bridge_match.length < 8) {
          summary.samples.bridge_match.push({ card_no: entry.card_no });
        }
      } else {
        summary.bridge_mismatch += 1;
        if (summary.samples.bridge_mismatch.length < 8) {
          summary.samples.bridge_mismatch.push({ card_no: entry.card_no });
        }
      }
    } catch (error) {
      summary.bridge_mismatch += 1;
      if (summary.samples.bridge_mismatch.length < 8) {
        summary.samples.bridge_mismatch.push({ card_no: entry.card_no, error: String(error) });
      }
    }
  }

  console.log(JSON.stringify(summary, null, 2));
}

main();
