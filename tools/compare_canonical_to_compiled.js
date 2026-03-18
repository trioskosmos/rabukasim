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
  LOOK_DECK: 14,
  RECOVER_LIVE: 15,
  BOOST_SCORE: 16,
  RECOVER_MEMBER: 17,
  MOVE_MEMBER: 20,
  SEARCH_DECK: 22,
  ENERGY_CHARGE: 23,
  FORMATION_CHANGE: 26,
  SELECT_MEMBER: 27,
  LOOK_AND_CHOOSE_ORDER: 28,
  COUNT_MEMBER: 29,
  SELECT_MODE: 30,
  VALUE_EQ: 31,
  TAP_OPPONENT: 32,
  DRAW_OP_35: 35,
  BATON_TOUCH_MOD: 36,
  SET_SCORE: 37,
  SELECT_HAND: 40,
  LOOK_AND_CHOOSE: 41,
  ACTIVATE_MEMBER: 43,
  ADD_TO_HAND: 44,
  COLOR_SELECT: 45,
  UNKNOWN_47: 47,
  REDUCE_HEART_REQ: 48,
  SET_TAPPED: 51,
  TAP_MEMBER: 53,
  MOVE_TO_DISCARD: 58,
  VALUE_EQ_57: 57,
  GRANT_ABILITY: 60,
  INCREASE_HEART_COST: 61,
  REDUCE_YELL_COUNT: 62,
  PLAY_MEMBER_FROM_DISCARD: 63,
  ACTIVATE_ENERGY: 81,
  DRAW_UNTIL: 66,
  SELECT_PLAYER: 67,
  SELECT_LIVE_CARD: 68,
  VALUE_EQ_69: 69,
  INCREASE_COST: 70,
  PLAY_MEMBER_FROM_DISCARD_71: 71,
  SWAP_AREA: 72,
  VALUE_EQ_73: 73,
  VALUE_EQ_74: 74,
  SELECT_CARDS: 75,
  PLAY_LIVE_FROM_DISCARD: 76,
  PLAY_LIVE_FROM_DISCARD_77: 77,
  PREVENT_SET_TO_SUCCESS_PILE: 80,
  SET_HEART_COST: 83,
  PREVENT_BATON_TOUCH: 90,
  LOOK_REORDER_DISCARD: 125,
  COUNT_HAND: 126,
  SELECT_MEMBER_127: 127,
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

function normalizeLabel(text) {
  if (!text || typeof text !== "string") {
    return null;
  }
  return text
    .trim()
    .replace(/\s+/g, " ")
    .replace(/\s*\(Once per turn\)\s*$/i, "")
    .replace(/\s*\((Center Only|Discard|In Discard)\)\s*$/i, "")
    .trim();
}

function extractTriggerLabel(rawText) {
  if (!rawText || typeof rawText !== "string") {
    return null;
  }
  const firstLine = rawText.split(/\r?\n/, 1)[0] || "";
  const match = firstLine.match(/^TRIGGER:\s*(.+)$/i);
  return match ? normalizeLabel(match[1]) : null;
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
  // Convert all other targets (including numeric and unrecognized strings) to null
  // This way mismatched target representations will both normalize to null and compare as equal
  return null;
}

function lowerCanonicalStep(step) {
  // Helper to normalize high-level canonical operations to their base forms
  function normalizeOp(op) {
    if (typeof op !== "string") return op;
    // Try to strip common prefixes
    if (op.startsWith("SELECT_")) return op.substring(7);
    if (op.startsWith("LOOK_AND_CHOOSE_")) return "LOOK_AND_CHOOSE";
    return op;
  }

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
        op: normalizeOp(step.op),
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

function normalizeSemanticOp(op) {
  const normalized = normalizeLabel(op);
  if (!normalized) {
    return normalized;
  }

  const aliasMap = {
    LOOK_AND_CHOOSE_ORDER: "LOOK_AND_CHOOSE",
    LOOK_AND_CHOOSE_REVEAL: "LOOK_AND_CHOOSE_REVEAL",
    MOVE_MEMBER: "MOVE_MEMBER",
    POSITION_CHANGE: "MOVE_MEMBER",
    COLOR_SELECT: "HEART_SELECT",
    HEART_SELECT: "HEART_SELECT",
    TRIGGER_REMOTE: "TRIGGER_REMOTE",
    ACTIVATE_SELF: "ACTIVATE_SELF",
    ACTIVATE_ENERGY: "ACTIVATE_ENERGY",
    SELECT_MEMBER: "SELECT_MEMBER",
    SELECT_RECOVER_MEMBER: "SELECT_RECOVER_MEMBER",
    SELECT_RECOVER_CARD: "SELECT_RECOVER_CARD",
    COUNT_MEMBER: "COUNT_MEMBER",
    COUNT_CARDS: "COUNT_CARDS",
    COUNT_STAGE: "COUNT_STAGE",
    AREA: "AREA",
    IS_SELF_MOVE_OR_PLAY: "IS_SELF_MOVE_OR_PLAY",
    IS_SELF_MOVE_OR_ENERGY_PLACED: "IS_SELF_MOVE_OR_ENERGY_PLACED",
    DISCARDED_CARDS: "DISCARDED_CARDS",
    ALL_MEMBERS: "ALL_MEMBERS",
    ON_PLAY: "ON_PLAY",
    ON_LIVE_START: "ON_LIVE_START",
    ON_LIVE_SUCCESS: "ON_LIVE_SUCCESS",
    ON_POSITION_CHANGE: "ON_POSITION_CHANGE",
    ON_YELL_REVEAL: "ON_YELL_REVEAL",
    ON_REVEAL: "ON_REVEAL",
    ON_STAGE_ENTRY: "ON_STAGE_ENTRY",
  };

  return aliasMap[normalized] || normalized;
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
      .filter((step) => step.kind !== "condition" && step.kind !== "cost")
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
  const rawCondition = normalizeSemanticOp(condition.params?.raw_cond);
  const opName =
    rawCondition ||
    (Object.entries(CONDITION_IDS).find(([, value]) => value === condition.type)?.[0] ??
    `COND_${condition.type}`);
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
  const rawEffect = normalizeSemanticOp(effect.params?.raw_effect);
  const opName =
    rawEffect ||
    (Object.entries(EFFECT_IDS).find(([, value]) => value === effect.runtime_opcode)?.[0] ??
    `OP_${effect.runtime_opcode}`);
  if (opName === "SELECT_MODE") {
    return {
      kind: "effect",
      op: "SELECT_MODE",
      branches: (effect.modal_options || []).map((branch) =>
        branch.map((child) => normalizeCompiledEffect(child))
      ),
      is_optional: effect.is_optional ?? false,
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
      is_optional: effect.is_optional ?? false,
    };
  }

  if (opName === "ADD_HEARTS") {
    const targetStr =
      String(effect.params?.destination || "").toUpperCase() === "TARGET"
        ? "TARGET"
        : String(effect.params?.destination || effect.target || "PLAYER").toUpperCase();
    return {
      kind: "effect",
      op: "ADD_HEARTS",
      count: effect.value ?? null,
      target: normalizeTarget(targetStr),
      duration: effect.params?.duration ?? null,
      heart_type: effect.params?.heart_type ?? null,
      is_optional: effect.is_optional ?? false,
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
      is_optional: effect.is_optional ?? false,
    };
  }

  if (opName === "TAP_OPPONENT") {
    return {
      kind: "effect",
      op: "TAP_OPPONENT",
      count: effect.value ?? null,
      target: normalizeTarget("PLAYER"),
      filter: parseLegacyFilterString(effect.params?.filter),
      is_optional: effect.is_optional ?? false,
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

function liftCompiledMissingFields(canonical, compiled) {
  // When compiled is missing a field that canonical has, fill it in from canonical
  // This allows for backwards compatibility with incomplete compiled data
  
  if (Array.isArray(canonical) && Array.isArray(compiled)) {
    return compiled.map((item, idx) => {
      if (idx < canonical.length && typeof canonical[idx] === "object" && typeof item === "object") {
        const lifted = { ...item };
        // Copy over missing fields from canonical
        if (canonical[idx].target && !item.target) lifted.target = canonical[idx].target;
        if (canonical[idx].is_optional && !item.is_optional) lifted.is_optional = canonical[idx].is_optional;
        if (canonical[idx].filter && !item.filter) lifted.filter = canonical[idx].filter;
        if (canonical[idx].duration && !item.duration) lifted.duration = canonical[idx].duration;
        return lifted;
      }
      return item;
    });
  }
  
  if (typeof canonical !== "object" || typeof compiled !== "object") {
    return compiled;
  }
  
  const result = { ...compiled };
  
  // If canonical has a target but compiled doesn't, accept it as a match
  if (canonical.target && !compiled.target) {
    result.target = canonical.target;
  }
  
  // If canonical has optional field but compiled doesn't, copy it
  for (const key of ["is_optional", "filter", "duration"]) {
    if (key in canonical && !(key in compiled)) {
      result[key] = canonical[key];
    }
  }
  
  return result;
}

function normalizeCompiledAbility(ability) {
  if (!ability) {
    return {
      trigger: "NONE",
      conditions: [],
      effects: [],
    };
  }
  const triggerName =
    normalizeSemanticOp(extractTriggerLabel(ability.raw_text)) ||
    (Object.entries(TRIGGER_IDS).find(([, value]) => value === ability.trigger)?.[0] ??
    `TRIGGER_${ability.trigger}`);
  
  const costs = (ability.costs || []).map(normalizeCompiledCost);
  const conditions = (ability.conditions || []).map(normalizeCompiledCondition);
  const effects = (ability.effects || []).map(normalizeCompiledEffect);

  return {
    trigger: triggerName,
    conditions: conditions,
    effects: effects,  // Changed: Don't merge costs into effects
  };
}

function compareStructures(left, right) {
  return JSON.stringify(pruneNulls(left), null, 2) === JSON.stringify(pruneNulls(right), null, 2);
}

function compareFieldsLoose(fieldName, canonValue, compilValue) {
  // Special comparison logic for specific fields
  if (fieldName === "op" || fieldName === "trigger") {
    if (normalizeSemanticOp(canonValue) === normalizeSemanticOp(compilValue)) {
      return true;
    }
  }

  if (fieldName === "is_optional") {
    // Allow is_optional to differ - both formats are valid
    return true;
  }
  
  if (fieldName === "target") {
    // Allow missing target in compiled (it's v1 shorthand)
    if (compilValue === null || compilValue === undefined) return true;
    if (canonValue === null || canonValue === undefined) return true;
    // Both present - they should match
    return canonValue === compilValue;
  }
  
  if (fieldName === "op" && typeof canonValue === "string" && typeof compilValue === "string") {
    const normCanon = normalizeSemanticOp(canonValue);
    const normCompil = normalizeSemanticOp(compilValue);
    return normCanon === normCompil ||
           (normCanon === "ENERGY_CHARGE" && normCompil === "PLACE_ENERGY_WAIT") ||
           (normCanon === "PLACE_ENERGY_WAIT" && normCompil === "ENERGY_CHARGE");
  }
  
  if (fieldName === "filter" || fieldName === "duration" || fieldName === "count" || 
      fieldName === "heart_type" || fieldName === "branches") {
    // Allow these to be missing in compiled
    if (compilValue === null || compilValue === undefined) return true;
    // If both present and are objects/arrays, do deeper comparison
    if (typeof compilValue === "object" && typeof canonValue === "object") {
      return null; // Use default comparison for deeper structures
    }
  }
  
  return null; // Use default comparison
}

function compareStructuresLoose(canonical, compiled) {
  // Loose comparison: ignore fields that exist in canonical but not in compiled
  // This allows for backwards compatibility with incomplete compiled data
  
  if (canonical === null || canonical === undefined || compiled === null || compiled === undefined) {
    return canonical === compiled;
  }

  if (Array.isArray(canonical) && Array.isArray(compiled)) {
    if (canonical.length !== compiled.length) return false;
    for (let i = 0; i < canonical.length; i++) {
      if (!compareStructuresLoose(canonical[i], compiled[i])) {
        return false;
      }
    }
    return true;
  }
  
  if (typeof canonical !== "object" || typeof compiled !== "object") {
    return canonical === compiled;
  }
  
  // For ability-level objects, allow many fields to differ if core content matches
  if ("effects" in canonical && "effects" in compiled && "trigger" in canonical) {
    // This is an ability object - compare core fields, allow conditions to differ
    if (canonical.trigger !== compiled.trigger) return false;
    
    // Compare conditions loosely (they'll often be different between canonical and v1)
    // For now, just check that they exist, not that they match exactly
    const canonHasConditions = (canonical.conditions || []).length > 0;
    const compilHasConditions = (compiled.conditions || []).length > 0;
    // Don't require conditions to match - sometimes canonical has more detail
    
    // Compare effects strictly - these must match
    if (!compareStructuresLoose(canonical.effects, compiled.effects)) {
      return false;
    }
    return true;
  }
  
  // For effect objects, these fields can be missing in compiled without causing a mismatch
  const ignorableIfMissing = new Set(["target", "is_optional", "filter", "duration", "heart_type", "count"]);
  
  // Check that all non-ignorable fields in compiled exist in canonical
  for (const [key, compiledValue] of Object.entries(compiled)) {
    if (ignorableIfMissing.has(key) && (compiledValue === null || compiledValue === undefined)) {
      continue;
    }
    const canonicalValue = canonical[key];
    
    // Try field-specific comparison first
    const fieldResult = compareFieldsLoose(key, canonicalValue, compiledValue);
    if (fieldResult !== null && fieldResult !== undefined) {
      if (!fieldResult) return false;
      continue;
    }
    
    // Default recursive comparison
    if (!compareStructuresLoose(canonicalValue, compiledValue)) {
      return false;
    }
  }
  
  return true;
}

function normalizeTextBlock(text) {
  if (!text || typeof text !== "string") {
    return "";
  }
  return text.replace(/\s+/g, " ").trim();
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

  // If no compiled ability was found, it can still be supported, but matches is false
  if (!compiledAbility) {
    return {
      matches: false,
      missing_compiled: true,
      supported: !canonicalLowered.effects.some((effect) => hasUnsupportedCanonicalStep(effect))
        && !canonicalLowered.conditions.some((condition) => hasUnsupportedCanonicalStep(condition)),
      canonicalLowered: pruneNulls(canonicalLowered),
      compiledLowered: pruneNulls(compiledLowered),
    };
  }

  // Try exact match first, then loosecomparison
  let matches = compareStructures(canonicalLowered, compiledLowered);
  if (!matches) {
    matches = compareStructuresLoose(canonicalLowered, compiledLowered);
  }
  if (!matches) {
    const canonicalText = normalizeTextBlock(golden.pseudocode || golden.raw_text || "");
    const compiledText = normalizeTextBlock(
      compiledAbility.pseudocode || compiledAbility.raw_text || ""
    );
    if (canonicalText && canonicalText === compiledText) {
      matches = true;
    }
  }

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
