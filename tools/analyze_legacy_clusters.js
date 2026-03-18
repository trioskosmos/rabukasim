const fs = require('fs');
const path = require('path');

const HYBRID_REPORT_PATH = 'canonical_ability_model/reports/fallback_runtime_preview.json';
const OUTPUT_REPORT_PATH = 'canonical_ability_model/reports/legacy_pattern_backlog.md';

function analyzeClusters() {
  console.log('Loading fallback runtime report...');
  if (!fs.existsSync(HYBRID_REPORT_PATH)) {
    console.error(`Error: ${HYBRID_REPORT_PATH} not found. Run tools/build_fallback_runtime.js first.`);
    return;
  }

  const report = JSON.parse(fs.readFileSync(HYBRID_REPORT_PATH, 'utf8'));
  
  // Extract all legacy abilities from all databases
  const legacyEntries = [];
  ['member_db', 'live_db', 'energy_db'].forEach(dbName => {
    if (!report[dbName]) return;
    Object.entries(report[dbName]).forEach(([cardId, card]) => {
      card.abilities.forEach((ability, index) => {
        if (ability.source === 'legacy') {
          legacyEntries.push({
            card_no: cardId, // Using card_id as card_no for summary
            trigger: ability.trigger,
            raw_text: ability.raw_text
          });
        }
      });
    });
  });

  console.log(`Analyzing ${legacyEntries.length} legacy entries...`);

  const clusters = {};

  for (const entry of legacyEntries) {
    const key = `${entry.trigger} || ${entry.raw_text}`;
    if (!clusters[key]) {
      clusters[key] = {
        trigger: entry.trigger,
        raw_text: entry.raw_text,
        cards: [],
        count: 0
      };
    }
    clusters[key].cards.push(entry.card_no);
    clusters[key].count++;
  }

  const sortedClusters = Object.values(clusters).sort((a, b) => b.count - a.count);

  let md = '# Legacy Ability Pattern Cluster Backlog\n\n';
  md += `Total legacy ability slots remaining: **${legacyEntries.length}**\n`;
  md += `Unique patterns identified: **${sortedClusters.length}**\n\n`;

  md += '## Top 20 Patterns by Frequency\n\n';
  md += '| Rank | Frequency | Trigger | Pattern (Raw Text) | Example Cards |\n';
  md += '|------|-----------|---------|--------------------|---------------|\n';

  sortedClusters.slice(0, 50).forEach((c, i) => {
    const examples = c.cards.slice(0, 3).join(', ');
    const more = c.cards.length > 3 ? ` (+${c.cards.length - 3} more)` : '';
    // Escape | in raw text for markdown table
    const safeText = c.raw_text.replace(/\|/g, '\\|').replace(/\n/g, ' ');
    md += `| ${i + 1} | ${c.count} | ${c.trigger} | ${safeText} | ${examples}${more} |\n`;
  });

  md += '\n\n## Summary of Migration Targets\n\n';
  
  const top5 = sortedClusters.slice(0, 5).reduce((sum, c) => sum + c.count, 0);
  const top10 = sortedClusters.slice(0, 10).reduce((sum, c) => sum + c.count, 0);
  const top20 = sortedClusters.slice(0, 20).reduce((sum, c) => sum + c.count, 0);

  md += `- **Top 5 patterns** cover **${top5}** abilities (${((top5 / legacyEntries.length) * 100).toFixed(1)}%)\n`;
  md += `- **Top 10 patterns** cover **${top10}** abilities (${((top10 / legacyEntries.length) * 100).toFixed(1)}%)\n`;
  md += `- **Top 20 patterns** cover **${top20}** abilities (${((top20 / legacyEntries.length) * 100).toFixed(1)}%)\n`;

  fs.writeFileSync(OUTPUT_REPORT_PATH, md, 'utf8');
  console.log(`Report generated: ${OUTPUT_REPORT_PATH}`);
}

analyzeClusters();
