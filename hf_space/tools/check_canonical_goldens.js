const fs = require("fs");
const path = require("path");

const repoRoot = process.cwd();
const manifestPath = path.join(repoRoot, "canonical_ability_model", "MANIFEST.json");

function fail(message) {
  console.error(message);
  process.exitCode = 1;
}

function isObject(value) {
  return value && typeof value === "object" && !Array.isArray(value);
}

function checkExpr(expr, pathLabel) {
  if (!isObject(expr)) {
    fail(`${pathLabel}: expected expression object`);
    return;
  }
  if (!["literal", "reference", "binary"].includes(expr.kind)) {
    fail(`${pathLabel}: unknown expression kind '${expr.kind}'`);
  }
  if (expr.kind === "reference" && typeof expr.name !== "string") {
    fail(`${pathLabel}: reference expression requires string name`);
  }
  if (expr.kind === "binary") {
    if (!["add", "sub", "eq", "gt", "lt", "ge", "le"].includes(expr.op)) {
      fail(`${pathLabel}: unknown binary op '${expr.op}'`);
    }
    checkExpr(expr.left, `${pathLabel}.left`);
    checkExpr(expr.right, `${pathLabel}.right`);
  }
}

function checkFilter(filterSpec, pathLabel) {
  if (!isObject(filterSpec)) {
    fail(`${pathLabel}: expected filter object`);
    return;
  }
  for (const key of ["all_of", "any_of"]) {
    if (filterSpec[key] !== undefined && !Array.isArray(filterSpec[key])) {
      fail(`${pathLabel}.${key}: expected array`);
    }
  }
}

function checkStep(step, pathLabel) {
  const allowedKinds = new Set(["cost", "condition", "effect", "select", "assign", "if", "choose_one", "repeat"]);
  if (!isObject(step)) {
    fail(`${pathLabel}: expected step object`);
    return;
  }
  if (!allowedKinds.has(step.kind)) {
    fail(`${pathLabel}: unknown step kind '${step.kind}'`);
  }
  if (step.count) {
    checkExpr(step.count, `${pathLabel}.count`);
  }
  if (step.expr) {
    checkExpr(step.expr, `${pathLabel}.expr`);
  }
  if (step.filter) {
    checkFilter(step.filter, `${pathLabel}.filter`);
  }
  if (step.condition) {
    checkStep(step.condition, `${pathLabel}.condition`);
  }
  if (Array.isArray(step.then)) {
    step.then.forEach((child, idx) => checkStep(child, `${pathLabel}.then[${idx}]`));
  }
  if (Array.isArray(step.else)) {
    step.else.forEach((child, idx) => checkStep(child, `${pathLabel}.else[${idx}]`));
  }
  if (Array.isArray(step.body)) {
    step.body.forEach((child, idx) => checkStep(child, `${pathLabel}.body[${idx}]`));
  }
  if (Array.isArray(step.branches)) {
    step.branches.forEach((branch, idx) => {
      if (!Array.isArray(branch.steps)) {
        fail(`${pathLabel}.branches[${idx}].steps: expected array`);
        return;
      }
      branch.steps.forEach((child, childIdx) =>
        checkStep(child, `${pathLabel}.branches[${idx}].steps[${childIdx}]`)
      );
    });
  }
  if (isObject(step.args)) {
    for (const [key, value] of Object.entries(step.args)) {
      if (isObject(value) && value.kind) {
        checkExpr(value, `${pathLabel}.args.${key}`);
      }
    }
  }
}

function checkGolden(filePath) {
  const fullPath = path.join(repoRoot, filePath);
  const raw = fs.readFileSync(fullPath, "utf8");
  const data = JSON.parse(raw);

  if (data.schema_version !== "v0") {
    fail(`${filePath}: expected schema_version 'v0'`);
  }
  if (typeof data.trigger !== "string") {
    fail(`${filePath}: trigger must be a string`);
  }
  if (!Array.isArray(data.steps)) {
    fail(`${filePath}: steps must be an array`);
    return;
  }
  data.steps.forEach((step, idx) => checkStep(step, `${filePath}.steps[${idx}]`));
}

const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
if (!Array.isArray(manifest.entries)) {
  fail("canonical_ability_model/MANIFEST.json: entries must be an array");
} else {
  manifest.entries.forEach((entry) => {
    if (!entry.golden) {
      fail("manifest entry missing golden path");
      return;
    }
    checkGolden(entry.golden);
  });
}

if (process.exitCode) {
  process.exit(process.exitCode);
}

console.log("OK: canonical goldens passed static shape checks");
