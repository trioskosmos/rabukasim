const fs = require('fs');
const path = require('path');
const { translateAbility } = require(path.join(__dirname, '..', 'frontend', 'web_ui', 'js', 'ability_translator.js'));

function generateComparison() {
    const dataPath = path.join(__dirname, '..', 'data', 'cards_compiled.json');
    if (!fs.existsSync(dataPath)) {
        console.error("Data file not found at " + dataPath);
        return;
    }

    const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
    let results = [];

    const db = { ...data.member_db, ...data.live_db };
    for (const id in db) {
        const card = db[id];
        if (card.ability_text) {
            results.push({
                no: card.card_no,
                name: card.name,
                raw: card.ability_text,
                len: card.ability_text.length
            });
        }
    }

    results.sort((a, b) => b.len - a.len);

    let output = "COMPARISON: RAW vs CONCISE TRANSLATION\n";
    output += "========================================\n\n";

    results.slice(0, 5).forEach((r, i) => {
        output += `${i + 1}. CARD: ${r.no} (${r.name})\n`;
        output += `[RAW TEXT]\n${r.raw}\n\n`;
        output += `[JP CONCISE]\n${translateAbility(r.raw, 'jp')}\n\n`;
        output += `[EN CONCISE]\n${translateAbility(r.raw, 'en')}\n`;
        output += `----------------------------------------\n\n`;
    });

    const outPath = path.join(__dirname, 'concise_comparison.txt');
    fs.writeFileSync(outPath, output, 'utf8');
    console.log("Comparison generated in tools/concise_comparison.txt");
}

generateComparison();
