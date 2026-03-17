const fs = require("fs");

const COMPILED_PATH = "data/cards_compiled.json";
const DB_NAMES = ["member_db", "live_db", "energy_db"];
const SAMPLE_LIMIT = 8;

const RULES = [
  {
    id: "inline_effect_condition",
    description: "Standard profile forbids `EFFECT: CONDITION:` inline gating.",
    test: (text) => /^\s*EFFECT:\s*CONDITION:/mi.test(text),
  },
  {
    id: "option_blocks",
    description: "Standard profile forbids legacy `OPTION:` block syntax.",
    test: (text) => /^\s*OPTION:/mi.test(text),
  },
  {
    id: "raw_boolean_filter",
    description: "Standard profile forbids raw `OR` filter expressions inside pseudocode strings.",
    test: (text) => /\{[^}\n]*\bOR\b[^}\n]*\}/i.test(text),
  },
  {
    id: "chained_destinations",
    description: "Standard profile forbids chained `-> X -> Y` destination bindings.",
    test: (text) => /->\s*\w+\s*->\s*\w+/.test(text),
  },
  {
    id: "legacy_choice_mode_alias",
    description: "Standard profile uses `SELECT_MODE`, not `CHOICE_MODE`.",
    test: (text) => /^\s*EFFECT:\s*CHOICE_MODE\b/mi.test(text),
  },
  {
    id: "legacy_select_option_alias",
    description: "Standard profile uses `SELECT_MODE`, not `SELECT_OPTION`.",
    test: (text) => /^\s*EFFECT:\s*SELECT_OPTION\b/mi.test(text),
  },
  {
    id: "mixed_condition_placement",
    description: "Standard profile should not mix top-level `CONDITION:` and inline `EFFECT: CONDITION:` in one ability.",
    test: (text) => /^\s*CONDITION:/mi.test(text) && /^\s*EFFECT:\s*CONDITION:/mi.test(text),
  },
];

function loadCompiled() {
  return JSON.parse(fs.readFileSync(COMPILED_PATH, "utf8"));
}

function makeSample(entry) {
  return {
    card_no: entry.card.card_no,
    card_id: entry.card.card_id,
    ability_idx: entry.abilityIdx,
    text: entry.rawText,
  };
}

function main() {
  const data = loadCompiled();
  const report = {
    compiled_path: COMPILED_PATH,
    total_abilities: 0,
    standard_profile_pass: 0,
    standard_profile_fail: 0,
    violations: {},
  };

  for (const rule of RULES) {
    report.violations[rule.id] = {
      description: rule.description,
      count: 0,
      samples: [],
    };
  }

  for (const dbName of DB_NAMES) {
    for (const card of Object.values(data[dbName] || {})) {
      for (const [abilityIdx, ability] of (card.abilities || []).entries()) {
        const rawText = String(ability.raw_text || ability.pseudocode || "");
        if (!rawText) {
          continue;
        }

        report.total_abilities += 1;
        let failed = false;

        for (const rule of RULES) {
          if (!rule.test(rawText)) {
            continue;
          }
          failed = true;
          const bucket = report.violations[rule.id];
          bucket.count += 1;
          if (bucket.samples.length < SAMPLE_LIMIT) {
            bucket.samples.push(makeSample({ card, abilityIdx, rawText }));
          }
        }

        if (failed) {
          report.standard_profile_fail += 1;
        } else {
          report.standard_profile_pass += 1;
        }
      }
    }
  }

  report.pass_rate = report.total_abilities === 0 ? 0 : Number((report.standard_profile_pass / report.total_abilities).toFixed(4));

  console.log(JSON.stringify(report, null, 2));
}

main();
