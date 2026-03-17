const fs = require("fs");
const path = require("path");

const repoRoot = process.cwd();

const TRIGGER_IDS = {
  NONE: 0,
  ON_PLAY: 1,
  ON_LIVE_START: 2,
  ON_LIVE_SUCCESS: 3,
  TURN_START: 4,
  TURN_END: 5,
  CONSTANT: 6,
  ACTIVATED: 7,
  ON_LEAVES: 8,
};

const CONDITION_IDS = {
  COUNT_SUCCESS_LIVE: 218,
};

const EFFECT_IDS = {
  DRAW: 10,
  ADD_HEARTS: 12,
  SELECT_MODE: 30,
  TAP_OPPONENT: 32,
  MOVE_TO_DISCARD: 58,
  SELECT_MEMBER: 65,
};

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, filePath), "utf8"));
}

function fail(message) {
  console.error(message);
  process.exit(1);
}

function pruneNulls(value) {
  if (Array.isArray(value)) {
    return value.map(pruneNulls);
  }
  if (!value || typeof value !== "object") {
    return value;
  }

  const result = {};
  for (const [key, child] of Object.entries(value)) {
    if (child === null || child === undefined) {
      continue;
    }
    result[key] = pruneNulls(child);
  }
  return result;
}

function normalizeFilter(filter) {
  if (!filter) return null;
  const all = (filter.all_of || []).map((clause) => ({
    field: clause.field,
    op: clause.op,
    value: clause.value,
  }));
  return { all_of: all };
}

function parseLegacyFilterString(filterText) {
  if (!filterText || typeof filterText !== "string") {
    return null;
  }

  const clauses = [];
  for (const token of filterText.split(",")) {
    const part = token.trim();
    if (!part) {
      continue;
    }
    let match = part.match(/^COST_LE[_=](\d+)$/i);
    if (match) {
      clauses.push({ field: "cost", op: "le", value: Number(match[1]) });
      continue;
    }
    match = part.match(/^COST_GE[_=](\d+)$/i);
    if (match) {
      clauses.push({ field: "cost", op: "ge", value: Number(match[1]) });
      continue;
    }
    match = part.match(/^GROUP_ID=(\d+)$/i);
    if (match) {
      clauses.push({ field: "group_id", op: "eq", value: Number(match[1]) });
      continue;
    }
    clauses.push({ field: "raw", op: "eq", value: part });
  }

  return clauses.length > 0 ? { all_of: clauses } : null;
}

function normalizeTarget(target) {
  if (!target) return null;
  if (target === "PLAYER" || target === "SELF") {
    return "$controller";
  }
  if (/^TARGET(_\d+)?$/.test(target)) {
    return "$branch_target";
  }
  return target;
}

function lowerCanonicalStep(step) {
  switch (step.kind) {
    case "condition":
      return {
        kind: "condition",
        op: step.op,
        value:
          step.args && step.args.min && step.args.min.kind === "literal"
            ? step.args.min.value
            : null,
        target:
          typeof step.args?.target === "string" ? normalizeTarget(step.args.target) : null,
      };
    case "select":
      return {
        kind: "effect",
        op: step.op,
        count: step.count?.value ?? null,
        filter: normalizeFilter(step.filter),
        target_binding: normalizeTarget(step.store_as),
      };
    case "effect":
      if (step.op === "DISCARD_HAND") {
        return {
          kind: "effect",
          op: "MOVE_TO_DISCARD",
          count: step.count?.value ?? null,
          target: normalizeTarget(step.target),
          source: "HAND",
          destination: "discard",
          filter: normalizeFilter(step.filter),
        };
      }
      return {
        kind: "effect",
        op: step.op,
        count: step.count?.value ?? null,
        target: normalizeTarget(step.target),
        duration: step.duration ?? null,
        heart_type: step.args?.heart_type ?? null,
        filter: normalizeFilter(step.filter),
      };
    case "choose_one":
      return {
        kind: "effect",
        op: "SELECT_MODE",
        branches: step.branches.map((branch) =>
          branch.steps.map((child) => lowerCanonicalStep(child))
        ),
      };
    default:
      return {
        kind: step.kind,
        unsupported: true,
      };
  }
}

function lowerCanonicalAbility(golden) {
  return {
    trigger: golden.trigger,
    conditions: golden.steps
      .filter((step) => step.kind === "condition")
      .map((step) => lowerCanonicalStep(step)),
    effects: golden.steps
      .filter((step) => step.kind !== "condition")
      .map((step) => lowerCanonicalStep(step)),
  };
}

function normalizeCompiledCondition(condition) {
  const opName =
    Object.entries(CONDITION_IDS).find(([, value]) => value === condition.type)?.[0] ??
    `COND_${condition.type}`;
  return {
    kind: "condition",
    op: opName,
    value: condition.value ?? null,
    target:
      typeof condition.params?.target === "string"
        ? normalizeTarget(condition.params.target.toUpperCase())
        : null,
  };
}

function normalizeCompiledEffect(effect) {
  const opName =
    Object.entries(EFFECT_IDS).find(([, value]) => value === effect.runtime_opcode)?.[0] ??
    `OP_${effect.runtime_opcode}`;
  if (opName === "SELECT_MODE") {
    return {
      kind: "effect",
      op: "SELECT_MODE",
      branches: (effect.modal_options || []).map((branch) =>
        branch.map((child) => normalizeCompiledEffect(child))
      ),
    };
  }

  if (opName === "SELECT_MEMBER") {
    return {
      kind: "effect",
      op: "SELECT_MEMBER",
      count: effect.value ?? null,
      filter: {
        all_of: [
          {
            field: "group_id",
            op: "eq",
            value: effect.params?.filter === "GROUP_ID=0" ? 0 : effect.params?.filter ?? null,
          },
        ],
      },
      target_binding: "$branch_target",
    };
  }

  if (opName === "ADD_HEARTS") {
    return {
      kind: "effect",
      op: "ADD_HEARTS",
      count: effect.value ?? null,
      target:
        String(effect.params?.destination || "").toUpperCase() === "TARGET"
          ? "$branch_target"
          : String(effect.params?.destination || effect.target || "").toUpperCase() || null,
      duration: effect.params?.duration ?? null,
      heart_type: effect.params?.heart_type ?? null,
    };
  }

  if (opName === "MOVE_TO_DISCARD") {
    return {
      kind: "effect",
      op: "MOVE_TO_DISCARD",
      count: effect.value ?? null,
      target: normalizeTarget("PLAYER"),
      source: String(effect.params?.source || "").toUpperCase() || null,
      destination: effect.params?.destination ?? null,
      filter: parseLegacyFilterString(effect.params?.filter),
    };
  }

  if (opName === "TAP_OPPONENT") {
    return {
      kind: "effect",
      op: "TAP_OPPONENT",
      count: effect.value ?? null,
      target: normalizeTarget("PLAYER"),
      filter: parseLegacyFilterString(effect.params?.filter),
    };
  }

  return {
    kind: "effect",
    op: opName,
    count: effect.value ?? null,
    target: normalizeTarget(
      typeof effect.target === "string" ? effect.target.toUpperCase() : "PLAYER"
    ),
  };
}

function normalizeCompiledAbility(ability) {
  const triggerName =
    Object.entries(TRIGGER_IDS).find(([, value]) => value === ability.trigger)?.[0] ??
    `TRIGGER_${ability.trigger}`;
  return {
    trigger: triggerName,
    conditions: (ability.conditions || []).map((condition) =>
      normalizeCompiledCondition(condition)
    ),
    effects: (ability.effects || []).map((effect) => normalizeCompiledEffect(effect)),
  };
}

function compareStructures(left, right) {
  return JSON.stringify(pruneNulls(left), null, 2) === JSON.stringify(pruneNulls(right), null, 2);
}

function main() {
  if (process.argv.length !== 5) {
    console.error(
      "usage: node tools/compare_canonical_to_compiled.js <golden-json> <card-no> <ability-index>"
    );
    process.exit(2);
  }

  const goldenPath = process.argv[2];
  const cardNo = process.argv[3];
  const abilityIndex = Number(process.argv[4]);

  const golden = readJson(goldenPath);
  const compiledDb = readJson("data/cards_compiled.json");

  let compiledAbility = null;
  for (const dbName of ["member_db", "live_db"]) {
    for (const card of Object.values(compiledDb[dbName] || {})) {
      if (card.card_no === cardNo) {
        compiledAbility = card.abilities?.[abilityIndex] ?? null;
        break;
      }
    }
    if (compiledAbility) break;
  }

  if (!compiledAbility) {
    fail(`Could not find compiled ability ${cardNo}#${abilityIndex}`);
  }

  const canonicalLowered = lowerCanonicalAbility(golden);
  const compiledLowered = normalizeCompiledAbility(compiledAbility);

  const matches = compareStructures(canonicalLowered, compiledLowered);
  console.log(
    JSON.stringify(
      {
        matches,
        canonicalLowered: pruneNulls(canonicalLowered),
        compiledLowered: pruneNulls(compiledLowered),
      },
      null,
      2
    )
  );
  process.exit(matches ? 0 : 1);
}

main();
