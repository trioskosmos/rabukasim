export class DeckValidator {
    constructor() {
        this.registry = null;
        this.isLoading = false;
    }

    async init() {
        if (this.registry) return;
        this.isLoading = true;
        try {
            const resp = await fetch('api/get_card_registry');
            const data = await resp.json();
            if (data.success) {
                this.registry = data.registry;
            }
        } catch (e) {
            console.error("Failed to load card registry", e);
        } finally {
            this.isLoading = false;
        }
    }

    validateDeckString(content) {
        if (!this.registry) return { success: false, error: "Registry not loaded" };

        const lines = content.split(/\r?\n|,\s*/);
        const results = {
            total: 0,
            members: 0,
            lives: 0,
            energy: 0,
            invalid: [],
            parsed: []
        };

        for (let line of lines) {
            line = line.trim();
            if (!line || line.startsWith('#')) continue;

            let count = 1;
            let code = line;

            const suffixMatch = line.match(/^(.+?)\s*[xX]\s*(\d+)$/);
            if (suffixMatch) {
                code = suffixMatch[1].trim();
                count = parseInt(suffixMatch[2]);
            } else {
                const prefixMatch = line.match(/^(\d+)\s*[xX]\s*(.+)$/);
                if (prefixMatch) {
                    count = parseInt(prefixMatch[1]);
                    code = prefixMatch[2].trim();
                }
            }

            const codeUpper = code.toUpperCase();
            const card = this.registry[codeUpper];

            if (card) {
                results.total += count;
                if (card.type === 'member') results.members += count;
                else if (card.type === 'live') results.lives += count;
                else if (card.type === 'energy') results.energy += count;

                results.parsed.push({
                    code: codeUpper,
                    count: count,
                    name: card.name,
                    type: card.type,
                    valid: true
                });
            } else {
                results.invalid.push(code);
                results.parsed.push({
                    code: code,
                    count: count,
                    valid: false
                });
            }
        }

        return results;
    }

    renderPreview(results, targetEl) {
        if (!targetEl) return;

        if (results.parsed.length === 0) {
            targetEl.innerHTML = '';
            return;
        }

        let html = `
            <div class="deck-validation-summary">
                <span class="stat ${results.members === 48 ? 'valid' : 'warning'}">Members: ${results.members}/48</span>
                <span class="stat ${results.lives === 12 ? 'valid' : 'warning'}">Lives: ${results.lives}/12</span>
                <span class="stat ${results.energy >= 12 ? 'valid' : 'warning'}">Energy: ${results.energy}</span>
            </div>
        `;

        if (results.invalid.length > 0) {
            html += `
                <div class="deck-validation-errors">
                    <strong>Invalid Codes:</strong>
                    <ul>
                        ${results.invalid.map(code => `<li class="error-text">${code}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        html += `
            <div class="deck-preview-grid">
                ${results.parsed.map(p => `
                    <div class="preview-item ${p.valid ? 'valid' : 'invalid'}" title="${p.name || 'Unknown'}">
                        <span class="count">${p.count}x</span>
                        <span class="code">${p.code}</span>
                    </div>
                `).join('')}
            </div>
        `;

        targetEl.innerHTML = html;
    }
}

export const validator = new DeckValidator();
