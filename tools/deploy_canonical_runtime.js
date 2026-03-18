const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const RELEVANT_DBS = ['member_db', 'live_db', 'energy_db'];

/**
 * Deploys the canonical ability model into the production cards_compiled.json.
 * 
 * Flow:
 * 1. Load canonical runtime preview (the "truth" we want to deploy).
 * 2. Load current production cards_compiled.json.
 * 3. Back up production file.
 * 4. Merge canonical definitions into the production structures.
 * 5. Save updated production file.
 */
async function deploy() {
    console.log('--- Canonical Ability Model Deployment ---');

    const previewPath = path.join(__dirname, '..', 'canonical_ability_model', 'reports', 'fallback_runtime_preview.json');
    const targetPath = path.join(DATA_DIR, 'cards_compiled.json');
    const backupPath = path.join(DATA_DIR, 'cards_compiled.legacy_backup.json');

    if (!fs.existsSync(previewPath)) {
        console.error(`Error: Canonical runtime preview not found at ${previewPath}`);
        console.log('Please run tools/build_fallback_runtime.js first.');
        process.exit(1);
    }

    // 1. Load Data
    console.log(`Loading canonical runtime from ${previewPath}...`);
    const canonicalData = JSON.parse(fs.readFileSync(previewPath, 'utf8'));
    
    console.log(`Loading production data from ${targetPath}...`);
    const productionData = JSON.parse(fs.readFileSync(targetPath, 'utf8'));

    // 2. Backup
    console.log(`Creating backup at ${backupPath}...`);
    fs.writeFileSync(backupPath, JSON.stringify(productionData, null, 2));

    // 3. Merge
    console.log('Merging canonical definitions...');
    let canonicalCount = 0;
    let legacyCount = 0;

    for (const dbName of RELEVANT_DBS) {
        const previewDb = canonicalData[dbName];
        const targetDb = productionData[dbName];
        if (!previewDb || !targetDb) continue;

        for (const id in targetDb) {
            const card = targetDb[id];
            const previewCard = previewDb[id];

            if (previewCard && previewCard.abilities && card.abilities) {
                // Map canonical programs to production abilities based on index
                let appliedToCard = false;
                
                previewCard.abilities.forEach((previewAbility, idx) => {
                    if (card.abilities[idx] && previewAbility.canonical_program) {
                        card.abilities[idx].canonical_program = previewAbility.canonical_program;
                        card.abilities[idx].source = "canonical";
                        appliedToCard = true;
                    }
                });

                if (appliedToCard) {
                    card.canonical_applied = true;
                    canonicalCount++;
                } else {
                    legacyCount++;
                }
            } else {
                legacyCount++;
            }
        }
    }

    // 4. Save
    console.log(`Saving updated production data to ${targetPath}...`);
    fs.writeFileSync(targetPath, JSON.stringify(productionData, null, 2));

    console.log('\nDeployment Complete!');
    console.log(`Canonical Enhanced: ${canonicalCount} cards`);
    console.log(`Legacy Retained:   ${legacyCount} cards`);
    console.log(`Backup saved to:   ${backupPath}`);
}

deploy().catch(err => {
    console.error('Deployment failed:', err);
    process.exit(1);
});
