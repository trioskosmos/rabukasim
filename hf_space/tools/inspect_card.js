const fs = require("fs");
const path = require("path");
const { compareCanonicalToCompiled } = require("./compare_canonical_to_compiled");

const repoRoot = process.cwd();

function main() {
    if (process.argv.length < 3) {
        console.error("usage: node tools/inspect_card.js <card-no> [draft-json-path]");
        process.exit(2);
    }

    const cardNo = process.argv[2];
    const draftPath = process.argv[3] || "canonical_ability_model/drafts/canonical_full_draft.json";
    
    const draft = JSON.parse(fs.readFileSync(path.join(repoRoot, draftPath), "utf8"));
    const entries = draft.filter(e => e.card_no === cardNo);

    if (entries.length === 0) {
        console.error(`Card ${cardNo} not found in ${draftPath}`);
        process.exit(1);
    }

    entries.forEach((entry, idx) => {
        console.log(`\n=== Ability ${idx} (${entry.trigger}) ===`);
        try {
            const result = compareCanonicalToCompiled(entry, cardNo, idx);
            console.log(JSON.stringify(result, null, 2));
        } catch (e) {
            console.error(`Error comparing ability ${idx}: ${e.message}`);
        }
    });
}

main();
