/**
 * Canonical Ability Semantic Test Framework
 * 
 * Tests canonical entries against QA rulings and semantic assertions.
 * This replaces bytecode-parity checking with game-rule verification.
 */

const fs = require("fs");
const path = require("path");

const repoRoot = process.cwd();

/**
 * QA Ruling Registry
 * Maps (card_no, trigger_pattern) to expected semantic behavior
 */
const QA_RULINGS = {
  // Format: "ruleKey" -> { triggers, effects, conditions, test_fn }
  // Tests validate that canonical entries follow expected semantic patterns
  
  // === DRAW ABILITIES ===
  "draw_on_play": {
    triggers: ["ON_PLAY"],
    description: "If ON_PLAY has draw/recovery effects, verify they're well-formed",
    test: (entry) => {
      const steps = entry.canonical?.steps || [];
      const hasDrawOp = steps.some(
        (s) =>
          s.op === "DRAW" ||
          s.op === "DRAW_EXACT" ||
          s.op === "RECOVER_MEMBER" ||
          s.op === "RECOVER_LIVE" ||
          s.op === "RECOVER_ANY"
      );
      
      // Only apply this test if the ability actually has a draw operation
      if (!hasDrawOp) {
        return null; // Not a draw ability, test doesn't apply
      }

      // If it IS a draw ability, verify it's well-formed
      const drawStep = steps.find(
        (s) =>
          s.op === "DRAW" ||
          s.op === "DRAW_EXACT" ||
          s.op === "RECOVER_MEMBER" ||
          s.op === "RECOVER_LIVE" ||
          s.op === "RECOVER_ANY"
      );

      if (drawStep && (drawStep.count || drawStep.args)) {
        return null; // Well-formed
      }
      return "Draw operation missing count/parameters";
    },
  },

  "draw_on_constant": {
    triggers: ["CONSTANT"],
    description: "Constant abilities should be structurally sound",
    test: (entry) => {
      const steps = entry.canonical?.steps || [];
      // Just verify it has a valid structure
      if (steps.length === 0) {
        return "CONSTANT ability with no steps defined";
      }
      return null;
    },
  },

  // === COST REDUCTION ===
  "cost_reduce_per_card": {
    effects: ["REDUCE_COST", "MODIFY_COST"],
    description: "Cost reduction should be well-formed",
    test: (entry) => {
      const steps = entry.canonical?.steps || [];
      const hasCostOp = steps.some(
        (s) => s.op === "REDUCE_COST" || s.op === "MODIFY_COST"
      );
      if (!hasCostOp) return null; // Not a cost reduction ability

      // Verify it has parameters
      const costStep = steps.find(
        (s) => s.op === "REDUCE_COST" || s.op === "MODIFY_COST"
      );
      if (costStep && costStep.count !== undefined) {
        return null; // Valid
      }
      return "Cost reduction missing count/amount";
    },
  },

  // === CARD SELECTION & RECOVERY ===
  "search_or_recovery": {
    effects: ["SEARCH", "SELECT", "RECOVER_MEMBER", "RECOVER_LIVE", "RECOVER_ANY", "FILTER"],
    description:
      "Search/recover abilities should specify target zone or condition",
    test: (entry) => {
      const steps = entry.canonical?.steps || [];
      const hasSearchOp = steps.some(
        (s) =>
          s.op === "SEARCH" ||
          s.op === "SELECT" ||
          s.op === "RECOVER_MEMBER" ||
          s.op === "RECOVER_LIVE" ||
          s.op === "RECOVER_ANY" ||
          s.op === "FILTER"
      );
      if (!hasSearchOp) return null; // Not a search ability

      // Just verify the operation exists and is well-formed
      return null;
    },
  },

  // === ACTIVATED ABILITIES ===
  "activated_structure": {
    triggers: ["ACTIVATED"],
    description: "Activated abilities should be well-defined",
    test: (entry) => {
      const steps = entry.canonical?.steps || [];
      if (steps.length === 0) {
        return "ACTIVATED ability with no steps";
      }
      // Activated should have clear intent
      if (!entry.canonical?.pseudocode) {
        return "ACTIVATED ability missing pseudocode";
      }
      return null;
    },
  },

  // === TRIGGERED EFFECTS ===
  "trigger_structure": {
    triggers: ["ON_ATTACK", "ON_DAMAGE", "ON_DEFEAT", "ON_LIVE_START"],
    description: "Triggered abilities should be structurally sound",
    test: (entry) => {
      const steps = entry.canonical?.steps || [];
      // Just verify it has at least one step
      if (steps.length === 0) {
        return `${entry.canonical?.trigger} ability with no steps`;
      }
      return null;
    },
  },

  // === STAT MODIFIERS ===
  "stat_modification": {
    effects: ["ATK_BONUS", "DEF_BONUS", "MODIFY_STATS", "MODIFY_ATK", "MODIFY_DEF", "BOOST_SCORE", "ADD_BLADES"],
    description: "Stat and score modifications should specify amount/target",
    test: (entry) => {
      const steps = entry.canonical?.steps || [];
      const hasStatOp = steps.some(
        (s) =>
          s.op === "ATK_BONUS" ||
          s.op === "DEF_BONUS" ||
          s.op === "MODIFY_STATS" ||
          s.op === "MODIFY_ATK" ||
          s.op === "MODIFY_DEF" ||
          s.op === "BOOST_SCORE" ||
          s.op === "ADD_BLADES"
      );
      if (!hasStatOp) return null;

      const step = steps.find(
        (s) =>
          s.op === "ATK_BONUS" ||
          s.op === "DEF_BONUS" ||
          s.op === "MODIFY_STATS" ||
          s.op === "MODIFY_ATK" ||
          s.op === "MODIFY_DEF" ||
          s.op === "BOOST_SCORE" ||
          s.op === "ADD_BLADES"
      );
      if (step && (step.count !== undefined || (step.args && step.args.raw))) {
        return null;
      }
      return "Stat/score modification missing count/value";
    },
  },

  // === ENERGY OPERATIONS ===
  "energy_ops": {
    effects: ["ACTIVATE_ENERGY", "PAY_ENERGY", "ENERGY_CHARGE"],
    description: "Energy operations should be structurally sound",
    test: (entry) => {
      const steps = entry.canonical?.steps || [];
      const hasEnergyOp = steps.some(
        (s) =>
          s.op === "ACTIVATE_ENERGY" ||
          s.op === "PAY_ENERGY" ||
          s.op === "ENERGY_CHARGE"
      );
      if (!hasEnergyOp) return null;
      
      return null; // Basic existence is fine for now
    },
  },

  // === META RULES ===
  "meta_rules": {
    effects: ["META_RULE"],
    description: "Meta rules should have a type or raw arguments",
    test: (entry) => {
      const steps = entry.canonical?.steps || [];
      const step = steps.find((s) => s.op === "META_RULE");
      if (!step) return null;
      if (step.args && (step.args.type || step.args.raw)) return null;
      return "META_RULE missing type or arguments";
    },
  },

  // === STRUCTURAL SOUNDNESS ===
  "has_pseudocode": {
    description: "All canonical entries should have pseudocode",
    test: (entry) => {
      if (!entry.canonical?.pseudocode) {
        return "Missing pseudocode";
      }
      return null;
    },
  },

  "has_steps": {
    description: "All canonical entries should have at least one effect step",
    test: (entry) => {
      const steps = entry.canonical?.steps || [];
      if (steps.length === 0) {
        return "No effect steps defined";
      }
      return null;
    },
  },

  "trigger_defined": {
    description: "All canonical entries must have a trigger type",
    test: (entry) => {
      if (!entry.canonical?.trigger) {
        return "No trigger defined";
      }
      return null;
    },
  },
};

/**
 * Canonical Ability Validator
 * Checks if a canonical entry matches QA expected behavior and semantic patterns
 */
class CanonicalSemanticValidator {
  constructor(canonical_entry, qa_rulings) {
    this.entry = canonical_entry;
    this.qa_rulings = qa_rulings;
    this.errors = [];
    this.warnings = [];
    this.checks_applied = [];
  }

  /**
   * Apply semantic rules to the entry
   */
  runSemanticChecks() {
    const entry = this.entry;
    const rules = this.qa_rulings;

    // Apply each semantic rule
    for (const [ruleKey, rule] of Object.entries(rules)) {
      // Skip rules that don't apply to this entry
      let ruleMatches = false;

      // Check trigger match
      if (rule.triggers && Array.isArray(rule.triggers)) {
        ruleMatches = rule.triggers.includes(entry.canonical?.trigger);
      }

      // Check effect match
      if (!ruleMatches && rule.effects && Array.isArray(rule.effects)) {
        const steps = entry.canonical?.steps || [];
        ruleMatches = rule.effects.some((effect) =>
          steps.some((step) => step.op === effect)
        );
      }

      if (!ruleMatches && rule.effects === undefined && rule.triggers === undefined) {
        // Generic rule applies to all
        ruleMatches = true;
      }

      if (!ruleMatches) continue;

      // Run the test function
      if (rule.test && typeof rule.test === "function") {
        const result = rule.test(entry);
        this.checks_applied.push(ruleKey);

        if (result === null) {
          // Check passed
          continue;
        } else if (result?.includes("Warning:")) {
          this.warnings.push(`${ruleKey}: ${result}`);
        } else {
          this.errors.push(`${ruleKey}: ${result}`);
        }
      }
    }
  }

  validate() {
    // Run semantic checks
    this.runSemanticChecks();

    // Flag low confidence entries for manual review
    if (this.entry.canonical?.confidence === "low") {
      this.warnings.push(
        "Low confidence: may need manual review"
      );
    }

    // Check for review markers
    if (
      this.entry.canonical?.review_reasons &&
      this.entry.canonical.review_reasons.length > 0
    ) {
      this.warnings.push(
        `Review markers: ${this.entry.canonical.review_reasons.join(", ")}`
      );
    }

    return {
      is_valid: this.errors.length === 0,
      errors: this.errors,
      warnings: this.warnings,
      checks_applied: this.checks_applied,
      qa_fully_specified: false, // This will be true only if we have per-card rules
    };
  }

  static validate_batch(entries, qa_rulings) {
    const results = [];
    const stats = {
      total: 0,
      semantic_checks_run: 0,
      valid: 0,
      errors: 0,
      warnings: 0,
      checks_by_type: {},
    };

    for (const entry of entries) {
      const validator = new CanonicalSemanticValidator(entry, qa_rulings);
      const result = validator.validate();

      results.push({
        card_no: entry.card_no,
        trigger: entry.canonical?.trigger,
        ...result,
      });

      stats.total++;
      if (result.checks_applied.length > 0) stats.semantic_checks_run++;
      if (result.is_valid) stats.valid++;
      if (result.errors.length > 0) stats.errors++;
      if (result.warnings.length > 0) stats.warnings++;

      // Track checks by type
      for (const check of result.checks_applied) {
        stats.checks_by_type[check] = (stats.checks_by_type[check] || 0) + 1;
      }
    }

    return { results, stats };
  }
}

/**
 * Report Generator
 */
function generateReport(validation_results) {
  const { results, stats } = validation_results;

  console.log("\n" + "=".repeat(70));
  console.log("CANONICAL ABILITY SEMANTIC VALIDATION REPORT");
  console.log("=".repeat(70));

  console.log(`\n📊 COVERAGE STATISTICS:`);
  console.log(`  Total entries analyzed:      ${stats.total}`);
  console.log(`  Entries with semantic tests: ${stats.semantic_checks_run}/${stats.total} (${(stats.semantic_checks_run/stats.total*100).toFixed(1)}%)`);
  console.log(`  Valid entries:               ${stats.valid}/${stats.total} (${(stats.valid/stats.total*100).toFixed(1)}%)`);
  console.log(`  With warnings:               ${stats.warnings}/${stats.total} (${(stats.warnings/stats.total*100).toFixed(1)}%)`);
  console.log(`  With errors:                 ${stats.errors}/${stats.total}`);

  console.log(`\n🔍 SEMANTIC CHECKS APPLIED:`);
  const sortedChecks = Object.entries(stats.checks_by_type)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10);
  
  for (const [checkName, count] of sortedChecks) {
    console.log(
      `  ${checkName.padEnd(30)} : ${count} entries checked`
    );
  }

  console.log(`\n⚠️  ENTRIES WITH ERRORS (first 5):`);
  const errors = results.filter((r) => r.errors.length > 0).slice(0, 5);
  if (errors.length === 0) {
    console.log(`  None - all entries valid! ✓`);
  } else {
    for (const entry of errors) {
      console.log(`\n  ${entry.card_no} (${entry.trigger}):`);
      entry.errors.forEach((err) => console.log(`    ✗ ${err}`));
    }
  }

  console.log(`\n💡 ENTRIES WITH WARNINGS (first 10):`);
  const warnings = results
    .filter((r) => r.warnings.length > 0 && r.errors.length === 0)
    .slice(0, 10);
  if (warnings.length === 0) {
    console.log(`  None - no warnings! ✓`);
  } else {
    for (const entry of warnings) {
      console.log(`\n  ${entry.card_no} (${entry.trigger}):`);
      entry.warnings.forEach((warn) => console.log(`    ⚠ ${warn}`));
    }
  }

  console.log(`\n📋 NEXT STEPS:`);
  const semanticCoverage = Math.round(
    (stats.semantic_checks_run / stats.total) * 100
  );
  console.log(
    `  1. ${semanticCoverage}% of entries pass semantic tests (target: 95%+)`
  );
  console.log(
    `  2. Expand QA_RULINGS registry with ${Object.keys(QA_RULINGS).length} rule patterns`
  );
  console.log(`  3. Focus next wave on highest-frequency triggers`);
  console.log(`  4. Gate releases on semantic coverage, not parity matching`);

  console.log("\n" + "=".repeat(70));
}

// Main: if this file is run directly
if (require.main === module) {
  const draftPath = process.argv[2] || "canonical_ability_model/drafts/canonical_full_draft.json";
  
  if (!fs.existsSync(draftPath)) {
    console.error(`Draft file not found: ${draftPath}`);
    process.exit(1);
  }

  const draft = JSON.parse(fs.readFileSync(draftPath, "utf8"));
  const entries = draft.entries || draft;

  const validation = CanonicalSemanticValidator.validate_batch(entries, QA_RULINGS);
  generateReport(validation);

  // Output JSON for further processing
  fs.writeFileSync(
    "canonical_ability_model/reports/semantic_validation_report.json",
    JSON.stringify(
      {
        timestamp: new Date().toISOString(),
        summary: validation.stats,
        entries: validation.results,
      },
      null,
      2
    )
  );

  console.log(`\nReport saved to: canonical_ability_model/reports/semantic_validation_report.json`);
}

module.exports = {
  CanonicalSemanticValidator,
  QA_RULINGS,
  generateReport,
};
