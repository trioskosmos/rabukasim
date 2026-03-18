const fs = require("fs");
const path = require("path");

const {
  compareCanonicalToCompiled,
  findCompiledAbility,
  normalizeCompiledAbility,
  pruneNulls,
} = require("./compare_canonical_to_compiled");
const {
  validateCanonical,
  dedupeEntries,
  normalizeDraftEntries,
} = require("./test_normalized_canonical_draft");

const repoRoot = process.cwd();

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, relativePath), "utf8"));
}

function summarizeReason(entry, canonicalIssues, bridgeResult, requireParity = false) {
  if (canonicalIssues.length > 0) {
    return `validation:${canonicalIssues[0].code}`;
  }
  if (!bridgeResult.supported) {
    return "unsupported_lowering";
  }
  if (requireParity && !bridgeResult.matches) {
    return "bridge_mismatch";
  }
  return null;
}

function main() {
  if (process.argv.length < 3) {
    console.error(
      "usage: node tools/build_hybrid_runtime_preview.js <draft-json> [--unique] [--out <output-json>] [--require-parity]"
    );
    process.exit(2);
  }

  const args = process.argv.slice(2);
  const inputArg = args[0];
  const uniqueMode = args.includes("--unique");
  const requireParity = args.includes("--require-parity");
  const outIndex = args.indexOf("--out");
  const outArg =
    outIndex >= 0 && args[outIndex + 1]
      ? args[outIndex + 1]
      : "canonical_ability_model/reports/hybrid_runtime_preview.json";

  const data = readJson(inputArg);
  const rawEntries = normalizeDraftEntries(data);
  const entries = uniqueMode ? dedupeEntries(rawEntries) : rawEntries;

  const summary = {
    input_mode: Array.isArray(data) ? "raw_array" : "wrapper",
    unique_mode: uniqueMode,
    selection_mode: requireParity ? "require_parity" : "runtime_ready",
    total_entries: entries.length,
    original_entry_count: rawEntries.length,
    canonical_selected: 0,
    legacy_fallback: 0,
    validation_fail: 0,
    supported_canonical: 0,
    runtime_ready: 0,
    bridge_match: 0,
    bridge_mismatch: 0,
    canonical_with_parity_warning: 0,
    compiled_match_found: 0,
    compiled_match_missing: 0,
    fallback_reasons: {},
    samples: {
      canonical_selected: [],
      legacy_fallback: [],
    },
  };

  const outputEntries = [];

  for (const entry of entries) {
    const canonical = entry.canonical;
    const canonicalIssues = validateCanonical(canonical);
    const compiledAbility = findCompiledAbility(
      entry.card_no,
      null,
      canonical.raw_text || null,
      canonical.pseudocode || null
    );
    const compiledLowered = normalizeCompiledAbility(compiledAbility);

    let bridgeResult = {
      matches: false,
      supported: false,
      canonicalLowered: null,
      compiledLowered,
    };

    if (canonicalIssues.length === 0) {
      bridgeResult = compareCanonicalToCompiled(canonical, entry.card_no, null);
      if (bridgeResult.supported) {
        summary.supported_canonical += 1;
        summary.runtime_ready += 1;
      }
      if (bridgeResult.missing_compiled) {
        summary.compiled_match_missing += 1;
      } else {
        summary.compiled_match_found += 1;
        if (bridgeResult.matches) {
          summary.bridge_match += 1;
        } else {
          summary.bridge_mismatch += 1;
        }
      }
    } else {
      summary.validation_fail += 1;
    }

    const canUseCanonical =
      canonicalIssues.length === 0
      && bridgeResult.supported
      && (!requireParity || bridgeResult.matches);
    const parityWarning =
      canonicalIssues.length === 0 && bridgeResult.supported && !bridgeResult.matches
        ? "bridge_mismatch"
        : null;

    if (canUseCanonical) {
      summary.canonical_selected += 1;
      if (parityWarning) {
        summary.canonical_with_parity_warning += 1;
      }
      if (summary.samples.canonical_selected.length < 8) {
        summary.samples.canonical_selected.push({
          card_no: entry.card_no,
          trigger: canonical.trigger,
          parity_warning: parityWarning,
        });
      }
    } else {
      summary.legacy_fallback += 1;
      const reason = summarizeReason(entry, canonicalIssues, bridgeResult, requireParity);
      summary.fallback_reasons[reason] = (summary.fallback_reasons[reason] || 0) + 1;
      if (summary.samples.legacy_fallback.length < 8) {
        summary.samples.legacy_fallback.push({
          card_no: entry.card_no,
          reason,
        });
      }
    }

    outputEntries.push({
      card_no: entry.card_no,
      source: canUseCanonical ? "canonical" : "legacy",
      trigger: canonical.trigger,
      canonical_confidence: canonical.confidence || null,
      fallback_reason: canUseCanonical
        ? null
        : summarizeReason(entry, canonicalIssues, bridgeResult, requireParity),
      parity_warning: canUseCanonical ? parityWarning : null,
      canonical_validation_issues: canonicalIssues,
      canonical_supported: bridgeResult.supported,
      runtime_ready: canonicalIssues.length === 0 && bridgeResult.supported,
      bridge_match: bridgeResult.matches,
      canonical_plan: bridgeResult.supported ? pruneNulls(bridgeResult.canonicalLowered) : null,
      legacy_plan: !canUseCanonical || parityWarning ? pruneNulls(compiledLowered) : null,
      pseudocode: canonical.pseudocode || (compiledAbility ? compiledAbility.pseudocode : ""),
      raw_text: canonical.raw_text || (compiledAbility ? compiledAbility.raw_text : ""),
    });
  }

  const payload = {
    summary,
    entries: outputEntries,
  };

  const outputPath = path.join(repoRoot, outArg);
  fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2));
  console.log(JSON.stringify(summary, null, 2));
}

main();
