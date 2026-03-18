const fs = require("fs");

const draft = JSON.parse(fs.readFileSync("canonical_ability_model/drafts/canonical_full_draft.json", "utf8"));
const entries = draft.entries || [];

const checkCards = ["PL!S-bp2-006-P", "PL!S-bp2-021-L"];

for (const cardNo of checkCards) {
  const entry = entries.find(e => e.card_no === cardNo);
  if (entry && entry.canonical && entry.canonical.steps) {
    console.log(`\n===== ${cardNo} =====`);
    console.log(`Steps count: ${entry.canonical.steps.length}`);
    for (let i = 0; i < entry.canonical.steps.length; i++) {
      const step = entry.canonical.steps[i];
      console.log(`[${i}] kind:${step.kind}, op:${step.op}, has-condition:${!!step.condition}, has-then:${!!step.then}`);
    }
    console.log(`\nFull structure:`);
    console.log(JSON.stringify(entry.canonical.steps, null, 2).split('\n').slice(0, 30).join('\n'));
  }
}
