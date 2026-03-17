const fs = require("fs");
const path = require("path");

function splitTopLevel(text, delimiter = ";") {
  const parts = [];
  let current = "";
  let paren = 0;
  let brace = 0;
  let inDouble = false;
  let inSingle = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"' && !inSingle) inDouble = !inDouble;
    else if (ch === "'" && !inDouble) inSingle = !inSingle;
    else if (!inDouble && !inSingle) {
      if (ch === "(") paren++;
      else if (ch === ")") paren = Math.max(0, paren - 1);
      else if (ch === "{") brace++;
      else if (ch === "}") brace = Math.max(0, brace - 1);
      else if (ch === delimiter && paren === 0 && brace === 0) {
        if (current.trim()) parts.push(current.trim());
        current = "";
        continue;
      }
    }
    current += ch;
  }
  if (current.trim()) parts.push(current.trim());
  return parts;
}

function parseParams(block) {
  const params = {};
  if (!block) return params;
  const inner = block.trim().replace(/^\{/, "").replace(/\}$/, "");
  for (const part of splitTopLevel(inner, ",")) {
    const eq = part.indexOf("=");
    if (eq === -1) continue;
    const key = part.slice(0, eq).trim().toUpperCase();
    let value = part.slice(eq + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    params[key] = value;
  }
  return params;
}

function parseFilter(filterText) {
  if (!filterText) return undefined;
  const clauses = [];
  for (const token of splitTopLevel(filterText, ",")) {
    const part = token.trim();
    if (!part) continue;
    let m = part.match(/^COST_LE[_=](\d+)$/i);
    if (m) {
      clauses.push({ field: "cost", op: "le", value: Number(m[1]) });
      continue;
    }
    m = part.match(/^COST_GE[_=](\d+)$/i);
    if (m) {
      clauses.push({ field: "cost", op: "ge", value: Number(m[1]) });
      continue;
    }
    m = part.match(/^GROUP_ID=(\d+)$/i);
    if (m) {
      clauses.push({ field: "group_id", op: "eq", value: Number(m[1]) });
      continue;
    }
    m = part.match(/^HEART_TYPE=(\d+)$/i);
    if (m) {
      clauses.push({ field: "heart_type", op: "eq", value: Number(m[1]) });
      continue;
    }
    clauses.push({ field: "raw", op: "eq", value: part });
  }
  return clauses.length ? { all_of: clauses } : undefined;
}

function defaultTargetFor(op) {
  if (["DRAW", "ADD_BLADES", "ADD_HEARTS", "BOOST_SCORE", "ACTIVATE_ENERGY", "MOVE_TO_DISCARD", "DISCARD_HAND"].includes(op)) {
    return "PLAYER";
  }
  if (["TAP_OPPONENT"].includes(op)) {
    return "PLAYER";
  }
  return undefined;
}

function normalizeGenericStep(step, issues) {
  const next = JSON.parse(JSON.stringify(step));

  if (next.store_as === "(Optional)") {
    next.optional = true;
    delete next.store_as;
    issues.push("optional_marker_rewritten");
  }

  if (typeof next.store_as === "string" && next.store_as.includes(";")) {
    next.review_markers = Array.from(new Set([...(next.review_markers || []), "needs_review", "unknown_binding"]));
    delete next.store_as;
    issues.push("contaminated_store_as_removed");
  }

  if (next.kind === "effect" && !next.target && typeof next.op === "string") {
    const fallbackTarget = defaultTargetFor(next.op.toUpperCase());
    if (fallbackTarget) {
      next.target = fallbackTarget;
      issues.push("default_target_applied");
    }
  }

  if (next.kind === "cost" && !next.target && typeof next.op === "string") {
    if (["DISCARD_HAND", "PAY_ENERGY", "TAP_SELF"].includes(next.op.toUpperCase())) {
      next.target = "PLAYER";
      issues.push("default_target_applied");
    }
  }

  if (next.kind === "if" && next.condition && next.condition.kind && !next.condition.op) {
    next.review_markers = Array.from(new Set([...(next.review_markers || []), "needs_review", "unsupported_pattern"]));
    issues.push("if_condition_expr_needs_normalization");
  }

  if (Array.isArray(next.then)) {
    next.then = next.then.map((child) => normalizeGenericStep(child, issues));
  }
  if (Array.isArray(next.else)) {
    next.else = next.else.map((child) => normalizeGenericStep(child, issues));
  }
  if (Array.isArray(next.body)) {
    next.body = next.body.map((child) => normalizeGenericStep(child, issues));
  }
  if (Array.isArray(next.branches)) {
    next.branches = next.branches.map((branch) => ({
      ...branch,
      steps: (branch.steps || []).map((child) => normalizeGenericStep(child, issues)),
    }));
  }

  return next;
}

function parseSimpleEffect(part) {
  const match = part.match(/^([A-Z_]+)(?:\((.*?)\))?\s*(\{.*\})?\s*(?:->\s*([A-Z0-9_]+))?$/i);
  if (!match) return null;
  const [, rawOp, rawCount, rawParams, rawTarget] = match;
  const op = rawOp.toUpperCase();
  const params = parseParams(rawParams);
  const step = {
    kind: "effect",
    op,
    args: {},
  };

  if (rawCount && /^\d+$/.test(rawCount.trim())) {
    step.count = { kind: "literal", value: Number(rawCount.trim()) };
  }

  const target = rawTarget ? rawTarget.toUpperCase() : defaultTargetFor(op);
  if (target) {
    step.target = target;
  }

  if (params.FILTER) {
    step.filter = parseFilter(params.FILTER);
  }
  if (params.DURATION) {
    step.duration = params.DURATION;
  }
  if (params.HEART_TYPE && /^\d+$/.test(params.HEART_TYPE)) {
    step.args.heart_type = Number(params.HEART_TYPE);
  }
  if (params.FROM) {
    step.args.from = params.FROM;
  }
  if (params.TO) {
    step.args.to = params.TO;
  }

  if (Object.keys(step.args).length === 0) {
    delete step.args;
  }
  if (!step.filter) {
    delete step.filter;
  }

  return step;
}

function canSimpleRewrite(pseudocode) {
  return (
    /^\s*TRIGGER:/mi.test(pseudocode) &&
    /^\s*EFFECT:/mi.test(pseudocode) &&
    !/^\s*COST:/mi.test(pseudocode) &&
    !/^\s*CONDITION:/mi.test(pseudocode) &&
    !/^\s*OPTION:/mi.test(pseudocode) &&
    !/EFFECT:\s*CONDITION:/mi.test(pseudocode) &&
    !/LOOK_AND_CHOOSE|GRANT_ABILITY|CHOICE_MODE|SELECT_OPTION|SELECT_MODE/i.test(pseudocode)
  );
}

function rewriteEntry(entry) {
  const next = JSON.parse(JSON.stringify(entry));
  const issueCodes = [];
  const pseudo = String(next.canonical?.pseudocode || "");
  if (Array.isArray(next.canonical?.steps)) {
    next.canonical.steps = next.canonical.steps.map((step) => normalizeGenericStep(step, issueCodes));
  }
  if (!canSimpleRewrite(pseudo)) {
    if (issueCodes.length > 0) {
      next.issues = Array.from([...(next.issues || []), ...issueCodes]).map((issue) =>
        typeof issue === "string" ? { code: issue, path: "$", message: issue } : issue
      );
    }
    return { entry: next, changed: false };
  }

  const effectParts = [];
  for (const line of pseudo.split(/\r?\n/)) {
    const m = line.match(/^\s*EFFECT:\s*(.*)$/i);
    if (!m) continue;
    effectParts.push(...splitTopLevel(m[1], ";"));
  }
  const steps = effectParts.map(parseSimpleEffect);
  if (steps.some((step) => !step)) {
    if (issueCodes.length > 0) {
      next.issues = Array.from([...(next.issues || []), ...issueCodes]).map((issue) =>
        typeof issue === "string" ? { code: issue, path: "$", message: issue } : issue
      );
    }
    return { entry: next, changed: false };
  }

  next.canonical.steps = steps;
  next.issues = Array.from(new Set([...(next.issues || []), "simple_effect_rewrite_applied", ...issueCodes])).map((issue) =>
    typeof issue === "string" ? { code: issue, path: "$", message: issue } : issue
  );
  return { entry: next, changed: true };
}

function main() {
  if (process.argv.length < 3 || process.argv.length > 4) {
    console.error("usage: node tools/fix_canonical_draft_semantics.js <input-wrapper-json> [output-wrapper-json]");
    process.exit(2);
  }

  const inputPath = process.argv[2];
  const outputPath = process.argv[3] || inputPath.replace(/\.json$/i, ".fixed.json");
  const data = JSON.parse(fs.readFileSync(inputPath, "utf8"));
  const entries = Array.isArray(data.entries) ? data.entries : [];
  let changed = 0;
  data.entries = entries.map((entry) => {
    const result = rewriteEntry(entry);
    if (result.changed) changed++;
    return result.entry;
  });
  data.summary = data.summary || {};
  data.summary.simple_effect_rewrites = changed;
  fs.writeFileSync(outputPath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
  console.log(JSON.stringify({ output: outputPath, simple_effect_rewrites: changed }, null, 2));
}

main();
