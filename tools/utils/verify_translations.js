
const fs = require('fs');
const path = require('path');
const { translateAbility } = require('../frontend/web_ui/js/ability_translator.js');

const cardsPath = path.join(__dirname, '../data/cards_compiled.json');
const mappingPath = path.join(__dirname, '../opcode_map_utf8.md');

const rawData = fs.readFileSync(cardsPath, 'utf8');
const data = JSON.parse(rawData);

const mappingRaw = fs.readFileSync(mappingPath, 'utf8');

function extractTargetCards(content) {
    const cards = new Set();
    const lines = content.split('\n');
    lines.forEach(line => {
        if (line.includes('|') && !line.includes('Val | Name')) {
            const parts = line.split('|');
            if (parts.length >= 4) {
                const cardList = parts[3].split(',');
                cardList.forEach(c => {
                    const trimmed = c.trim();
                    if (trimmed && trimmed !== 'MISSING' && trimmed !== 'Cards') {
                        cards.add(trimmed);
                    }
                });
            }
        }
    });
    return Array.from(cards);
}

const targetCards = extractTargetCards(mappingRaw);

let output = "# Exhaustive Translation Verification\n";
output += `Verifying ${targetCards.length} representative cards...\n\n`;

targetCards.forEach(cardNo => {
    let card = Object.values(data.member_db).find(c => c.card_no === cardNo);
    if (!card) card = Object.values(data.live_db).find(c => c.card_no === cardNo);

    if (!card) return;

    output += `### ${card.name} (${card.card_no})\n`;
    for (const ab of card.abilities || []) {
        const raw = ab.raw_text;
        output += `JP: ${translateAbility(raw, 'jp').replace(/\n/g, ' ')}\n`;
        output += `EN: ${translateAbility(raw, 'en').replace(/\n/g, ' ')}\n`;
    }
    output += "\n";
});

// Use Buffer to ensure UTF-8 writing
fs.writeFileSync(path.join(__dirname, '../exhaustive_translation_results.txt'), Buffer.from(output, 'utf8'));
console.log('Results written to exhaustive_translation_results.txt');
