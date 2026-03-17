const fs = require("fs");

const COMPILED_PATH = "data/cards_compiled.json";
const DB_NAMES = ["member_db", "live_db", "energy_db"];
const SAMPLE_LIMIT = 10;

const PROFILE_RULES = [
  (text) => /^\s*EFFECT:\s*CONDITION:/mi.test(text),
  (text) => /^\s*OPTION:/mi.test(text),
  (text) => /\{[^}\n]*\bOR\b[^}\n]*\}/i.test(text),
  (text) => /->\s*\w+\s*->\s*\w+/.test(text),
  (text) => /^\s*EFFECT:\s*CHOICE_MODE\b/mi.test(text),
  (text) => /^\s*EFFECT:\s*SELECT_OPTION\b/mi.test(text),
  (text) => /^\s*CONDITION:/mi.test(text) && /^\s*EFFECT:\s*CONDITION:/mi.test(text),
];

const HARD_PATTERNS = [
  { id: "grant_ability", test: (text) => /\bGRANT_ABILITY\b/i.test(text) },
  { id: "look_and_choose", test: (text) => /\bLOOK_AND_CHOOSE|\bLOOK_AND_CHOOSE_REVEAL|\bLOOK_AND_CHOOSE_SPLIT/i.test(text) },
  { id: "reveal_until", test: (text) => /\bREVEAL_UNTIL\b/i.test(text) },
  { id: "calc_or_math", test: (text) => /\bCALC_SUM_COST\b|\bDIV_VALUE\b|BASE_COST_MINUS|\+\d+\b/i.test(text) },
  { id: "transform_or_meta", test: (text) => /\bTRANSFORM_|\bMETA_RULE\b/i.test(text) },
];

const MEDIUM_PATTERNS = [
  { id: "has_binding", test: (text) => /->\s*[A-Z_][A-Z0-9_]*/.test(text) },
  { id: "has_condition", test: (text) => /^\s*CONDITION:/mi.test(text) },
  { id: "has_cost", test: (text) => /^\s*COST:/mi.test(text) },
  { id: "multi_effect", test: (text) => text.split(/\r?\n/).filter((line) => /^\s*EFFECT:/i.test(line)).length > 1 },
  { id: "select_or_count", test: (text) => /\bSELECT_|\bCOUNT_|\bGET_COST\b/i.test(text) },
  { id: "optional", test: (text) => /\(Optional\)/i.test(text) },
];

function loadCompiled() {
  return JSON.parse(fs.readFileSync(COMPILED_PATH, "utf8"));
}

function profilePasses(text) {
  return !PROFILE_RULES.some((rule) => rule(text));
}

function classify(text) {
  const hardHits = HARD_PATTERNS.filter((pattern) => pattern.test(text)).map((pattern) => pattern.id);
  if (hardHits.length > 0) {
    return { bucket: "hard", reasons: hardHits };
  }

  const mediumHits = MEDIUM_PATTERNS.filter((pattern) => pattern.test(text)).map((pattern) => pattern.id);
  if (mediumHits.length > 0) {
    return { bucket: "medium", reasons: mediumHits };
  }

  return { bucket: "easy", reasons: [] };
}

function addSample(samples, bucket, card, abilityIdx, text, reasons) {
  if (samples[bucket].length >= SAMPLE_LIMIT) {
    return;
  }
  samples[bucket].push({
    card_no: card.card_no,
    card_id: card.card_id,
    ability_idx: abilityIdx,
    reasons,
    text,
  });
}

function main() {
  const data = loadCompiled();
  const report = {
    compiled_path: COMPILED_PATH,
    total_standard_profile_candidates: 0,
    buckets: {
      easy: 0,
      medium: 0,
      hard: 0,
    },
    samples: {
      easy: [],
      medium: [],
      hard: [],
    },
  };

  for (const dbName of DB_NAMES) {
    for (const card of Object.values(data[dbName] || {})) {
      for (const [abilityIdx, ability] of (card.abilities || []).entries()) {
        const text = String(ability.raw_text || ability.pseudocode || "");
        if (!text || !profilePasses(text)) {
          continue;
        }

        report.total_standard_profile_candidates += 1;
        const { bucket, reasons } = classify(text);
        report.buckets[bucket] += 1;
        addSample(report.samples, bucket, card, abilityIdx, text, reasons);
      }
    }
  }

  report.easy_rate = Number((report.buckets.easy / Math.max(report.total_standard_profile_candidates, 1)).toFixed(4));
  report.medium_rate = Number((report.buckets.medium / Math.max(report.total_standard_profile_candidates, 1)).toFixed(4));
  report.hard_rate = Number((report.buckets.hard / Math.max(report.total_standard_profile_candidates, 1)).toFixed(4));

  console.log(JSON.stringify(report, null, 2));
}

main();
