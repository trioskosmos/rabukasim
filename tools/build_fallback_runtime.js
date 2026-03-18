/**
 * build_fallback_runtime.js
 * 
 * Phase 1 Fallback Handler Generator
 * 
 * Transforms hybrid_runtime_preview.json into a format compatible with Rust fallback logic.
 * Each runtime-ready canonical entry gets:
 * - source: "canonical" marker
 * - canonical_plan as main ability (no bytecode)
 * - fallback_bytecode from compiled data (if available)
 * 
 * This allows Rust engine to:
 * 1. Load canonical abilities efficiently
 * 2. Detect missing bytecode (needs_fallback flag)
 * 3. Use fallback_bytecode at runtime if canonical fails
 */

const fs = require('fs');
const path = require('path');

const HYBRID_PREVIEW = './canonical_ability_model/reports/hybrid_runtime_preview.json';
const COMPILED_DATA = './data/cards_compiled.json';
const args = process.argv.slice(2);
const canonicalOnlyMode = args.includes('--canonical-only') || args.includes('--no-fallback');
const outIndex = args.indexOf('--out');
const OUTPUT_PATH =
  outIndex >= 0 && args[outIndex + 1]
    ? args[outIndex + 1]
    : canonicalOnlyMode
      ? './canonical_ability_model/reports/canonical_runtime_preview.json'
      : './canonical_ability_model/reports/fallback_runtime_preview.json';

const logPrefix = canonicalOnlyMode ? '[CANONICAL]' : '[FALLBACK]';

function normalizeCompiledAbility(ability) {
  // Convert compiled format (with numeric enums) to normalized format
  return {
    trigger: ability.trigger || 0,
    effects: ability.effects || [],
    conditions: ability.conditions || [],
    costs: ability.costs || [],
    bytecode: ability.bytecode || [],
  };
}

function findAbilityIndex(card, entry) {
  const abilities = card.abilities || [];

  if (entry.pseudocode) {
    const byPseudocode = abilities.findIndex(
      (ability) => String(ability.pseudocode || "") === String(entry.pseudocode)
    );
    if (byPseudocode >= 0) {
      return byPseudocode;
    }
  }

  if (entry.raw_text) {
    const byRawText = abilities.findIndex(
      (ability) => String(ability.raw_text || "") === String(entry.raw_text)
    );
    if (byRawText >= 0) {
      return byRawText;
    }
  }

  return null;
}

function buildRuntimeAbility(compiledAb, entry) {
  if (entry.source === 'canonical') {
    const stripFallback = canonicalOnlyMode;
    return {
      raw_text: entry.raw_text || compiledAb.raw_text || '',
      trigger: compiledAb.trigger || 0,
      effects: compiledAb.effects || [],
      conditions: compiledAb.conditions || [],
      costs: compiledAb.costs || [],
      bytecode: [],
      modal_options: compiledAb.modal_options || {},
      option_names: compiledAb.option_names || [],
      pseudocode: entry.pseudocode || compiledAb.pseudocode || '',
      requires_selection: compiledAb.requires_selection || false,
      choice_flags: compiledAb.choice_flags || 0,
      choice_count: compiledAb.choice_count || 0,
      filters: compiledAb.filters || [],
      preparsed_modifiers: compiledAb.preparsed_modifiers || [],
      is_once_per_turn: compiledAb.is_once_per_turn || false,
      source: 'canonical',
      needs_fallback: stripFallback ? false : true,
      fallback_bytecode: stripFallback ? [] : (compiledAb.bytecode || []),
      canonical_program: entry.canonical_plan || null,
    };
  }

  return {
    raw_text: compiledAb.raw_text || '',
    trigger: compiledAb.trigger || 0,
    effects: compiledAb.effects || [],
    conditions: compiledAb.conditions || [],
    costs: compiledAb.costs || [],
    bytecode: compiledAb.bytecode || [],
    modal_options: compiledAb.modal_options || {},
    option_names: compiledAb.option_names || [],
    pseudocode: compiledAb.pseudocode || '',
    requires_selection: compiledAb.requires_selection || false,
    choice_flags: compiledAb.choice_flags || 0,
    choice_count: compiledAb.choice_count || 0,
    filters: compiledAb.filters || [],
    preparsed_modifiers: compiledAb.preparsed_modifiers || [],
    is_once_per_turn: compiledAb.is_once_per_turn || false,
    source: 'legacy',
    needs_fallback: false,
    fallback_bytecode: [],
    canonical_program: null,
  };
}

function buildFallbackRuntime() {
  console.log(`${logPrefix} Loading hybrid preview...`);
  const hybrid = JSON.parse(fs.readFileSync(HYBRID_PREVIEW, 'utf8'));
  
  console.log(`${logPrefix} Loading compiled data for bytecode reference...`);
  const compiled = JSON.parse(fs.readFileSync(COMPILED_DATA, 'utf8'));
  
  // Build quick lookup by card_no across ALL databases
  const compiledByCardNo = {};
  const dbNameByCardId = {}; // Map card_id -> dbName
  
  const dbs = ['member_db', 'live_db', 'energy_db'];
  
  for (const dbName of dbs) {
    for (const [cardId, card] of Object.entries(compiled[dbName] || {})) {
      compiledByCardNo[card.card_no] = card;
      dbNameByCardId[cardId] = dbName;
    }
  }
  
  const output = {
    member_db: {},
    live_db: {},
    energy_db: {},
    meta: {
      version: canonicalOnlyMode ? '1.0-canonical-only' : '1.0-fallback',
      source: canonicalOnlyMode
        ? 'hybrid_runtime_preview.json -> canonical_runtime_preview.json'
        : 'hybrid_runtime_preview.json -> fallback_runtime_preview.json',
      bytecode_layout_version: 1,
      bytecode_layout_name: canonicalOnlyMode ? 'canonical-only-v1' : 'fallback-v1',
      export_profile: canonicalOnlyMode ? 'canonical-only' : 'fallback',
      description: canonicalOnlyMode
        ? 'Hybrid preview stripped of fallback bytecode for canonical-only testing'
        : 'Hybrid preview with fallback bytecode for Phase 1 integration',
      canonical_count: 0,
      legacy_count: 0,
      total_count: 0,
      total_abilities: 0,
    }
  };
  
  let stats = {
    canonical_ready: 0,
    canonical_with_fallback: 0,
    canonical_no_fallback: 0,
    legacy_entries: 0,
    missing_compiled: 0,
    total_count: 0,
    total_abilities: 0,
    unmatched_preview_entries: 0,
  };

  // Populate output with initial legacy entries from all DBs
  for (const dbName of dbs) {
    for (const [cardId, card] of Object.entries(compiled[dbName] || {})) {
      output[dbName][cardId] = {
        ...card,
        abilities: (card.abilities || []).map((ability) => buildRuntimeAbility(ability, { source: 'legacy' })),
      };
      stats.total_count++;
      stats.total_abilities += (card.abilities || []).length;
      stats.legacy_entries += (card.abilities || []).length;
    }
  }
  
  console.log(`${logPrefix} Processing entries...`);
  const canonical_only_entries = [];
  
  for (const entry of hybrid.entries || []) {
    const card_no = entry.card_no;
    const compiledCard = compiledByCardNo[card_no];
    
    if (!compiledCard || !compiledCard.abilities || compiledCard.abilities.length === 0) {
      if (entry.source === 'canonical') {
        canonical_only_entries.push(entry);
        continue;
      } else {
        console.warn(`${logPrefix} Warning: No compiled data for ${card_no}`);
        stats.missing_compiled++;
        continue;
      }
    }

    const abilityIndex = findAbilityIndex(compiledCard, entry);
    if (abilityIndex === null) {
      if (entry.source === 'canonical') {
        canonical_only_entries.push(entry);
        continue;
      } else {
        console.warn(`${logPrefix} Warning: Could not match ability for ${card_no}`);
        stats.unmatched_preview_entries++;
        continue;
      }
    }

    const compiledAb = compiledCard.abilities[abilityIndex];
    const cardId = String(compiledCard.card_id);
    const dbName = dbNameByCardId[cardId];
    const runtimeCard = output[dbName][cardId];
    const previousSource = runtimeCard.abilities[abilityIndex]?.source || 'legacy';

    if (previousSource === 'legacy') {
      stats.legacy_entries -= 1;
    } else if (previousSource === 'canonical') {
      stats.canonical_with_fallback -= 1;
    }

    runtimeCard.abilities[abilityIndex] = buildRuntimeAbility(compiledAb, entry);

    if (entry.source === 'canonical') {
      stats.canonical_with_fallback++;
      stats.canonical_ready++;
    } else {
      stats.legacy_entries++;
    }
  }
  
  // NEW: Process canonical-only entries (no fallback bytecode)
  console.log(`${logPrefix} Processing ${canonical_only_entries.length} canonical-only entries...`);
  for (const entry of canonical_only_entries) {
    const card_no = entry.card_no;
    const compiledCard = compiledByCardNo[card_no];
    
    let card_id = null;
    let dbName = 'member_db'; // Default

    if (compiledCard) {
      card_id = String(compiledCard.card_id);
      dbName = dbNameByCardId[card_id];
    } else {
      // Search across all output dbs
      for (const possibleDb of dbs) {
        for (const [cid, card] of Object.entries(output[possibleDb])) {
          if (card.card_no === card_no) {
            card_id = cid;
            dbName = possibleDb;
            break;
          }
        }
        if (card_id) break;
      }
    }
    
    if (!card_id) {
      console.warn(`${logPrefix} Could not determine card_id for canonical entry ${card_no}`);
      continue;
    }
    
    const runtimeCard = output[dbName][card_id];
    const canonicalOnlyAbility = {
      raw_text: entry.raw_text || '',
      trigger: entry.trigger || 0, // FIXED: use entry.trigger
      effects: entry.canonical_plan?.effects || [],
      conditions: entry.canonical_plan?.conditions || [],
      costs: entry.canonical_plan?.costs || [],
      bytecode: [],
      modal_options: {},
      option_names: [],
      pseudocode: entry.pseudocode || '',
      requires_selection: false,
      choice_flags: 0,
      choice_count: 0,
      filters: entry.canonical_plan?.filters || [],
      preparsed_modifiers: [],
      is_once_per_turn: false,
      source: 'canonical',
      needs_fallback: canonicalOnlyMode ? false : false,
      fallback_bytecode: [],
      canonical_program: entry.canonical_plan || null,
    };
    
    runtimeCard.abilities.push(canonicalOnlyAbility);
    stats.canonical_ready++;
    stats.canonical_no_fallback++;
    stats.total_abilities++;
  }
  
  output.meta.canonical_count = stats.canonical_ready;
  output.meta.legacy_count = stats.legacy_entries;
  output.meta.total_count = stats.total_count;
  output.meta.total_abilities = stats.total_abilities;
  
  console.log(`${logPrefix} Writing output...`);
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(output, null, 2), 'utf8');
  
  const canonicalWithFallback = canonicalOnlyMode ? 0 : stats.canonical_with_fallback;
  const canonicalNoFallback = canonicalOnlyMode ? stats.canonical_ready : stats.canonical_no_fallback;

  console.log(`\n${canonicalOnlyMode ? '[CANONICAL SUMMARY]' : '[FALLBACK SUMMARY]'}`);
  console.log(`✓ Canonical ready (total): ${stats.canonical_ready}`);
  console.log(`✓ Canonical with fallback bytecode: ${canonicalWithFallback}`);
  console.log(`✓ Canonical canonical-only (no fallback): ${canonicalNoFallback}`);
  console.log(`✓ Legacy entries: ${stats.legacy_entries}`);
  console.log(`✓ Total cards processed: ${stats.total_count}`);
  console.log(`✓ Total abilities processed: ${stats.total_abilities}`);
  console.log(`✗ Missing compiled data: ${stats.missing_compiled}`);
  console.log(`✗ Unmatched preview entries: ${stats.unmatched_preview_entries}`);
  console.log(`\nCanonical Coverage: ${((stats.canonical_ready / stats.total_abilities) * 100).toFixed(1)}%`);
  console.log(`Output: ${OUTPUT_PATH}`);
  console.log(`\n${canonicalOnlyMode ? 'Canonical-only export complete!' : 'Phase 1 Complete!'}`);
}

buildFallbackRuntime();
