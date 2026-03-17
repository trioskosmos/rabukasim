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
  HAS_COLOR: 202,
  IS_CENTER: 206,
  COUNT_GROUP: 208,
  BATON: 231,
  LIFE_LEAD: 207,
};

const EFFECT_IDS = {
  DRAW: 10,
  ADD_BLADES: 11,
  ADD_HEARTS: 12,
  REDUCE_COST: 13,
  RECOVER_LIVE: 15,
  BOOST_SCORE: 16,
  RECOVER_MEMBER: 17,
  SEARCH_DECK: 22,
  ENERGY_CHARGE: 23,
  SELECT_MODE: 30,
  TAP_OPPONENT: 32,
  ACTIVATE_MEMBER: 43,
  ADD_TO_HAND: 44,
  COLOR_SELECT: 45,
  REDUCE_HEART_REQ: 48,
  SET_TAPPED: 51,
  TAP_MEMBER: 53,
  MOVE_TO_DISCARD: 58,
  GRANT_ABILITY: 60,
  SELECT_MEMBER: 65,
  ACTIVATE_ENERGY: 81,
};

const COST_IDS = {
  ENERGY: 1,
  TAP_SELF: 2,
  DISCARD_HAND: 3,
  RETURN_HAND: 4,
  SACRIFICE_SELF: 5,
  TAP_MEMBER: 20,
  DISCARD_MEMBER: 24,
};

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, filePath), "utf8"));
}

let compiledAbilityIndex = null;

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
  if (!target || target === "PLAYER" || target === "SELF" || target === "CONTROLLER") {
    return "$controller";
  }
  if (/^TARGET(_\d+)?$/.test(target) || target === "TARGET_MEMBER") {
    return "$branch_target";
  }
  return target;
}

function lowerCanonicalStep(step) {
  switch (step.kind) {
    case "condition":
      return {
        kind: "condition",
        op: step.op ? step.op.toUpperCase() : null,
        value:
          step.args && step.args.min && step.args.min.kind === "literal"
            ? step.args.min.value
            : (step.args?.value ?? null),
        target: normalizeTarget(step.args?.target),
      };
    case "select":
      return {
        kind: "effect",
        op: step.op,
        count: step.count?.value ?? null,
        filter: normalizeFilter(step.filter),
        target_binding: normalizeTarget(step.store_as),
      };
    case "cost":
      return {
        kind: "cost",
        op: step.op,
        count: step.count?.value ?? null,
        target: normalizeTarget(step.target),
        optional: step.optional ?? false,
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
        is_optional: step.optional ?? false,
      };
    case "choose_one":
      return {
        kind: "effect",
        op: "SELECT_MODE",
        branches: step.branches.map((branch) =>
          branch.steps.map((child) => lowerCanonicalStep(child))
        ),
      };
    case "if":
       // For simple optional effects, we canonicalize by looking at 'then'
       // This is a bridge-only simplification to match v1 compiler flattening
       const results = (step.then || []).map(s => lowerCanonicalStep(s));
       // If it was an 'if' step, the resulting effects were likely optional in v1
       results.forEach(r => { if (r.kind === "effect") r.is_optional = true; });
       return results;
    default:
      return {
        kind: step.kind,
        unsupported: true,
      };
  }
}

function lowerCanonicalAbility(golden) {
  const steps = [];
  golden.steps.forEach(s => {
      const lowered = lowerCanonicalStep(s);
      if (Array.isArray(lowered)) steps.push(...lowered);
      else steps.push(lowered);
  });

  return {
    trigger: golden.trigger,
    conditions: steps
      .filter((step) => step.kind === "condition")
      .map((step) => step),
    effects: steps
      .filter((step) => step.kind !== "condition")
      .map((step) => step),
  };
}

function hasUnsupportedCanonicalStep(step) {
  if (!step || typeof step !== "object") {
    return true;
  }
  if (step.unsupported) {
    return true;
  }
  if (Array.isArray(step.branches)) {
    return step.branches.some((branch) => branch.some((child) => hasUnsupportedCanonicalStep(child)));
  }
  return false;
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

function normalizeCompiledCost(cost) {
  const opName =
    Object.entries(COST_IDS).find(([, value]) => value === cost.type)?.[0] ??
    `COST_${cost.type}`;
  return {
    kind: "cost",
    op: opName,
    count: cost.value ?? null,
    target: normalizeTarget(
      typeof cost.target === "string" ? cost.target.toUpperCase() : "PLAYER"
    ),
    optional: false, // Compiled costs are usually mandatory within their ability
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
      typeof effect.target === "string" ? effect.target.toUpperCase() : (effect.target || "PLAYER")
    ),
    is_optional: effect.is_optional ?? false,
  };
}

function normalizeCompiledAbility(ability) {
  const triggerName =
    Object.entries(TRIGGER_IDS).find(([, value]) => value === ability.trigger)?.[0] ??
    `TRIGGER_${ability.trigger}`;
  
  const costs = (ability.costs || []).map(normalizeCompiledCost);
  const conditions = (ability.conditions || []).map(normalizeCompiledCondition);
  const effects = (ability.effects || []).map(normalizeCompiledEffect);

  return {
    trigger: triggerName,
    conditions: conditions,
    effects: [...costs, ...effects],
  };
}

function compareStructures(left, right) {
  return JSON.stringify(pruneNulls(left), null, 2) === JSON.stringify(pruneNulls(right), null, 2);
}

function getCompiledAbilityIndex() {
  if (compiledAbilityIndex) {
    return compiledAbilityIndex;
  }

  const compiledDb = readJson("data/cards_compiled.json");
  const byCardAndIndex = new Map();
  const byCardAndPseudocode = new Map();
  const byCardAndRawText = new Map();

  for (const dbName of ["member_db", "live_db", "energy_db"]) {
    for (const card of Object.values(compiledDb[dbName] || {})) {
      for (const [abilityIndex, ability] of (card.abilities || []).entries()) {
        byCardAndIndex.set(`${card.card_no}::${abilityIndex}`, ability);
        byCardAndPseudocode.set(`${card.card_no}::${String(ability.pseudocode || "")}`, ability);
        byCardAndRawText.set(`${card.card_no}::${String(ability.raw_text || "")}`, ability);
      }
    }
  }

  compiledAbilityIndex = {
    byCardAndIndex,
    byCardAndPseudocode,
    byCardAndRawText,
  };
  return compiledAbilityIndex;
}

function findCompiledAbility(cardNo, abilityIndex, rawText = null, pseudocode = null) {
  const index = getCompiledAbilityIndex();
  let compiledAbility = null;

  if (Number.isInteger(abilityIndex)) {
    compiledAbility = index.byCardAndIndex.get(`${cardNo}::${abilityIndex}`) || null;
  } else if (pseudocode) {
    compiledAbility = index.byCardAndPseudocode.get(`${cardNo}::${String(pseudocode)}`) || null;
  } else if (rawText) {
    compiledAbility = index.byCardAndRawText.get(`${cardNo}::${String(rawText)}`) || null;
  } else {
    compiledAbility = index.byCardAndIndex.get(`${cardNo}::0`) || null;
  }

  if (!compiledAbility) {
    fail(`Could not find compiled ability ${cardNo}#${abilityIndex}`);
  }

  return compiledAbility;
}

function compareCanonicalToCompiled(golden, cardNo, abilityIndex = null) {
  const compiledAbility = findCompiledAbility(
    cardNo,
    abilityIndex,
    golden.raw_text || null,
    golden.pseudocode || null
  );

  const canonicalLowered = lowerCanonicalAbility(golden);
  const compiledLowered = normalizeCompiledAbility(compiledAbility);

  const matches = compareStructures(canonicalLowered, compiledLowered);
  return {
    matches,
    supported: !canonicalLowered.effects.some((effect) => hasUnsupportedCanonicalStep(effect))
      && !canonicalLowered.conditions.some((condition) => hasUnsupportedCanonicalStep(condition)),
    canonicalLowered: pruneNulls(canonicalLowered),
    compiledLowered: pruneNulls(compiledLowered),
  };
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
  const result = compareCanonicalToCompiled(golden, cardNo, abilityIndex);
  console.log(
    JSON.stringify(result, null, 2)
  );
  process.exit(result.matches ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = {
  compareCanonicalToCompiled,
  lowerCanonicalAbility,
  normalizeCompiledAbility,
  compareStructures,
  pruneNulls,
  findCompiledAbility,
};
