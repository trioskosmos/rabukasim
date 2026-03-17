const fs = require("fs");

const COMPILED_PATH = "data/cards_compiled.json";
const DB_NAMES = ["member_db", "live_db", "energy_db"];
const SAMPLE_LIMIT = 5;

function loadCompiled() {
  return JSON.parse(fs.readFileSync(COMPILED_PATH, "utf8"));
}

function iterateAbilities(data, visitor) {
  for (const dbName of DB_NAMES) {
    for (const card of Object.values(data[dbName] || {})) {
      for (const [abilityIdx, ability] of (card.abilities || []).entries()) {
        const rawText = String(ability.raw_text || ability.pseudocode || "");
        if (!rawText) {
          continue;
        }
        visitor({
          dbName,
          card,
          ability,
          abilityIdx,
          rawText,
        });
      }
    }
  }
}

function makeSample(entry) {
  return {
    card_no: entry.card.card_no,
    card_id: entry.card.card_id,
    ability_idx: entry.abilityIdx,
    text: entry.rawText,
  };
}

function pushSample(samples, entry) {
  if (samples.length < SAMPLE_LIMIT) {
    samples.push(makeSample(entry));
  }
}

function main() {
  const data = loadCompiled();
  const effectHeads = new Map();
  const stats = {
    total_abilities: 0,
    unique_effect_heads: 0,
    with_brace_params: 0,
    with_condition_keyword: 0,
    with_inline_condition_effect: 0,
    with_option_blocks: 0,
    with_raw_or_filters: 0,
    with_chained_destinations: 0,
  };

  const samples = {
    inline_condition_effect: [],
    option_blocks: [],
    raw_or_filters: [],
    chained_destinations: [],
  };

  iterateAbilities(data, (entry) => {
    const text = entry.rawText;
    stats.total_abilities += 1;

    for (const line of text.split(/\r?\n/)) {
      const match = line.match(/^\s*EFFECT:\s*([A-Z_]+)/i);
      if (match) {
        const head = match[1].toUpperCase();
        effectHeads.set(head, (effectHeads.get(head) || 0) + 1);
      }
    }

    if (/\{[^\n]*\}/.test(text)) {
      stats.with_brace_params += 1;
    }
    if (/^\s*CONDITION:/mi.test(text)) {
      stats.with_condition_keyword += 1;
    }
    if (/^\s*EFFECT:\s*CONDITION:/mi.test(text)) {
      stats.with_inline_condition_effect += 1;
      pushSample(samples.inline_condition_effect, entry);
    }
    if (/^\s*OPTION:/mi.test(text)) {
      stats.with_option_blocks += 1;
      pushSample(samples.option_blocks, entry);
    }
    if (/\sOR\s/i.test(text)) {
      stats.with_raw_or_filters += 1;
      pushSample(samples.raw_or_filters, entry);
    }
    if (/->\s*\w+\s*->\s*\w+/.test(text)) {
      stats.with_chained_destinations += 1;
      pushSample(samples.chained_destinations, entry);
    }
  });

  stats.unique_effect_heads = effectHeads.size;

  const report = {
    compiled_path: COMPILED_PATH,
    stats,
    top_effect_heads: [...effectHeads.entries()]
      .sort((left, right) => right[1] - left[1])
      .slice(0, 30)
      .map(([name, count]) => ({ name, count })),
    samples,
  };

  console.log(JSON.stringify(report, null, 2));
}

main();
